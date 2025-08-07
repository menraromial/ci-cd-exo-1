#!/bin/bash

# ArgoCD Setup Script for Python CI/CD Pipeline
# This script sets up ArgoCD with the necessary configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if ArgoCD CLI is available
if ! command -v argocd &> /dev/null; then
    print_warning "ArgoCD CLI is not installed. Installing..."
    # Install ArgoCD CLI
    curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
    rm argocd-linux-amd64
    print_status "ArgoCD CLI installed successfully"
fi

# Function to check if ArgoCD is installed
check_argocd_installation() {
    if kubectl get namespace argocd &> /dev/null; then
        print_status "ArgoCD namespace exists"
        return 0
    else
        print_warning "ArgoCD namespace does not exist"
        return 1
    fi
}

# Function to install ArgoCD
install_argocd() {
    print_status "Installing ArgoCD..."
    
    # Create namespace
    kubectl create namespace argocd
    
    # Install ArgoCD
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD to be ready
    print_status "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-application-controller -n argocd
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-repo-server -n argocd
    
    print_status "ArgoCD installed successfully"
}

# Function to apply ArgoCD configurations
apply_configurations() {
    print_status "Applying ArgoCD configurations..."
    
    # Apply project configuration
    kubectl apply -f project.yaml
    print_status "Applied AppProject configuration"
    
    # Apply ArgoCD configuration
    kubectl apply -f argocd-config.yaml
    print_status "Applied ArgoCD configuration"
    
    # Apply application configuration
    kubectl apply -f application.yaml
    print_status "Applied Application configuration"
    
    # Restart ArgoCD server to pick up configuration changes
    kubectl rollout restart deployment/argocd-server -n argocd
    kubectl rollout restart deployment/argocd-application-controller -n argocd
    
    print_status "Waiting for ArgoCD components to restart..."
    kubectl rollout status deployment/argocd-server -n argocd
    kubectl rollout status deployment/argocd-application-controller -n argocd
}

# Function to get ArgoCD admin password
get_admin_password() {
    print_status "Getting ArgoCD admin password..."
    ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    echo "ArgoCD Admin Password: $ARGOCD_PASSWORD"
}

# Function to setup port forwarding
setup_port_forward() {
    print_status "Setting up port forwarding to ArgoCD server..."
    print_warning "Run the following command in a separate terminal to access ArgoCD UI:"
    echo "kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo "Then access ArgoCD at: https://localhost:8080"
    echo "Username: admin"
    echo "Password: (see above)"
}

# Function to configure ArgoCD CLI
configure_argocd_cli() {
    print_status "Configuring ArgoCD CLI..."
    
    # Start port forwarding in background
    kubectl port-forward svc/argocd-server -n argocd 8080:443 &
    PORT_FORWARD_PID=$!
    
    # Wait a moment for port forwarding to establish
    sleep 5
    
    # Login to ArgoCD
    ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    argocd login localhost:8080 --username admin --password "$ARGOCD_PASSWORD" --insecure
    
    # Kill port forwarding
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    print_status "ArgoCD CLI configured successfully"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying ArgoCD installation..."
    
    # Check if all components are running
    if kubectl get pods -n argocd | grep -E "(Running|Completed)" | wc -l | grep -q "7"; then
        print_status "All ArgoCD components are running"
    else
        print_warning "Some ArgoCD components may not be ready yet"
        kubectl get pods -n argocd
    fi
    
    # Check if application is created
    if kubectl get application python-cicd-app -n argocd &> /dev/null; then
        print_status "Python CI/CD application is configured in ArgoCD"
        kubectl get application python-cicd-app -n argocd
    else
        print_error "Python CI/CD application is not found in ArgoCD"
    fi
    
    # Check if project is created
    if kubectl get appproject python-cicd-project -n argocd &> /dev/null; then
        print_status "Python CI/CD project is configured in ArgoCD"
    else
        print_error "Python CI/CD project is not found in ArgoCD"
    fi
}

# Main execution
main() {
    print_status "Starting ArgoCD setup for Python CI/CD Pipeline..."
    
    # Check if ArgoCD is already installed
    if ! check_argocd_installation; then
        install_argocd
    else
        print_status "ArgoCD is already installed"
    fi
    
    # Apply configurations
    apply_configurations
    
    # Get admin password
    get_admin_password
    
    # Setup port forwarding instructions
    setup_port_forward
    
    # Configure ArgoCD CLI
    configure_argocd_cli
    
    # Verify installation
    verify_installation
    
    print_status "ArgoCD setup completed successfully!"
    print_status "Next steps:"
    echo "1. Update the GitOps repository URL in application.yaml with your actual repository"
    echo "2. Create the GitOps repository and copy the helm-chart directory"
    echo "3. Configure GitHub secrets for GITOPS_TOKEN"
    echo "4. Test the pipeline by pushing code to the dev branch"
}

# Run main function
main "$@"