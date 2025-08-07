#!/bin/bash

# ArgoCD Configuration Validation Script
# This script validates the ArgoCD configuration files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# Function to validate YAML syntax
validate_yaml() {
    local file=$1
    print_info "Validating YAML syntax for $file..."
    
    if command -v yq &> /dev/null; then
        if yq eval '.' "$file" > /dev/null 2>&1; then
            print_status "$file has valid YAML syntax"
        else
            print_error "$file has invalid YAML syntax"
            return 1
        fi
    elif python3 -c "import yaml" &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" &> /dev/null; then
            print_status "$file has valid YAML syntax"
        else
            print_error "$file has invalid YAML syntax"
            return 1
        fi
    else
        print_warning "No YAML validator found (yq or python yaml). Skipping syntax validation for $file"
    fi
}

# Function to validate Kubernetes resource syntax
validate_k8s_resource() {
    local file=$1
    print_info "Validating Kubernetes resource syntax for $file..."
    
    if command -v kubectl &> /dev/null; then
        if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
            print_status "$file has valid Kubernetes resource syntax"
        else
            print_error "$file has invalid Kubernetes resource syntax"
            kubectl apply --dry-run=client -f "$file" 2>&1 | head -5
            return 1
        fi
    else
        print_warning "kubectl not found. Skipping Kubernetes validation for $file"
    fi
}

# Function to validate ArgoCD Application
validate_application() {
    print_info "Validating ArgoCD Application configuration..."
    
    # Check required fields
    local app_file="application.yaml"
    
    if [[ ! -f "$app_file" ]]; then
        print_error "Application file $app_file not found"
        return 1
    fi
    
    # Validate YAML and K8s syntax
    validate_yaml "$app_file" || return 1
    validate_k8s_resource "$app_file" || return 1
    
    # Check specific ArgoCD Application fields
    if command -v yq &> /dev/null; then
        # Check if it's an ArgoCD Application
        local kind=$(yq eval '.kind' "$app_file")
        if [[ "$kind" != "Application" ]]; then
            print_error "Expected kind 'Application', found '$kind'"
            return 1
        fi
        
        # Check required fields
        local project=$(yq eval '.spec.project' "$app_file")
        local source_repo=$(yq eval '.spec.source.repoURL' "$app_file")
        local destination=$(yq eval '.spec.destination.server' "$app_file")
        
        if [[ "$project" == "null" ]]; then
            print_error "spec.project is required"
            return 1
        fi
        
        if [[ "$source_repo" == "null" ]]; then
            print_error "spec.source.repoURL is required"
            return 1
        fi
        
        if [[ "$destination" == "null" ]]; then
            print_error "spec.destination.server is required"
            return 1
        fi
        
        print_status "ArgoCD Application configuration is valid"
        print_info "  Project: $project"
        print_info "  Source Repository: $source_repo"
        print_info "  Destination: $destination"
    fi
}

# Function to validate ArgoCD Project
validate_project() {
    print_info "Validating ArgoCD Project configuration..."
    
    local project_file="project.yaml"
    
    if [[ ! -f "$project_file" ]]; then
        print_error "Project file $project_file not found"
        return 1
    fi
    
    # Validate YAML and K8s syntax
    validate_yaml "$project_file" || return 1
    validate_k8s_resource "$project_file" || return 1
    
    # Check specific ArgoCD Project fields
    if command -v yq &> /dev/null; then
        local kind=$(yq eval '.kind' "$project_file")
        if [[ "$kind" != "AppProject" ]]; then
            print_error "Expected kind 'AppProject', found '$kind'"
            return 1
        fi
        
        local project_name=$(yq eval '.metadata.name' "$project_file")
        local source_repos=$(yq eval '.spec.sourceRepos | length' "$project_file")
        local destinations=$(yq eval '.spec.destinations | length' "$project_file")
        
        print_status "ArgoCD Project configuration is valid"
        print_info "  Project Name: $project_name"
        print_info "  Source Repositories: $source_repos"
        print_info "  Destinations: $destinations"
    fi
}

# Function to validate ArgoCD configuration
validate_argocd_config() {
    print_info "Validating ArgoCD server configuration..."
    
    local config_file="argocd-config.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        print_error "ArgoCD config file $config_file not found"
        return 1
    fi
    
    # Validate YAML syntax
    validate_yaml "$config_file" || return 1
    
    # Check if it contains ConfigMaps
    if command -v yq &> /dev/null; then
        local configmaps=$(yq eval 'select(.kind == "ConfigMap") | .metadata.name' "$config_file")
        if [[ -n "$configmaps" ]]; then
            print_status "ArgoCD configuration contains valid ConfigMaps:"
            echo "$configmaps" | while read -r cm; do
                print_info "  - $cm"
            done
        else
            print_warning "No ConfigMaps found in ArgoCD configuration"
        fi
    fi
}

# Function to validate webhook configuration
validate_webhook_config() {
    print_info "Validating webhook configuration..."
    
    local webhook_file="webhook-config.yaml"
    
    if [[ ! -f "$webhook_file" ]]; then
        print_warning "Webhook config file $webhook_file not found (optional)"
        return 0
    fi
    
    # Validate YAML syntax
    validate_yaml "$webhook_file" || return 1
    
    print_status "Webhook configuration is valid"
}

# Function to check script permissions
validate_scripts() {
    print_info "Validating script permissions..."
    
    local setup_script="setup-argocd.sh"
    
    if [[ ! -f "$setup_script" ]]; then
        print_error "Setup script $setup_script not found"
        return 1
    fi
    
    if [[ ! -x "$setup_script" ]]; then
        print_warning "Setup script $setup_script is not executable"
        print_info "Run: chmod +x $setup_script"
    else
        print_status "Setup script has correct permissions"
    fi
    
    # Basic syntax check for bash script
    if bash -n "$setup_script"; then
        print_status "Setup script has valid bash syntax"
    else
        print_error "Setup script has syntax errors"
        return 1
    fi
}

# Function to validate GitOps repository structure
validate_gitops_structure() {
    print_info "Validating GitOps repository structure..."
    
    local gitops_dir="../gitops-example"
    
    if [[ ! -d "$gitops_dir" ]]; then
        print_error "GitOps example directory not found at $gitops_dir"
        return 1
    fi
    
    # Check for required files
    local required_files=(
        "$gitops_dir/helm-chart/Chart.yaml"
        "$gitops_dir/helm-chart/values.yaml"
        "$gitops_dir/helm-chart/templates/deployment.yaml"
        "$gitops_dir/helm-chart/templates/service.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_status "Found required file: $(basename "$file")"
        else
            print_error "Missing required file: $file"
            return 1
        fi
    done
    
    print_status "GitOps repository structure is valid"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v helm &> /dev/null; then
        missing_tools+=("helm")
    fi
    
    # Optional tools
    if ! command -v yq &> /dev/null; then
        print_warning "yq not found - some validations will be skipped"
    fi
    
    if ! command -v argocd &> /dev/null; then
        print_warning "argocd CLI not found - will be installed by setup script"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Please install the missing tools before proceeding"
        return 1
    else
        print_status "All required tools are available"
    fi
}

# Function to validate complete configuration
validate_complete_setup() {
    print_info "Performing complete configuration validation..."
    
    local errors=0
    
    # Run all validations
    check_prerequisites || ((errors++))
    validate_application || ((errors++))
    validate_project || ((errors++))
    validate_argocd_config || ((errors++))
    validate_webhook_config || ((errors++))
    validate_scripts || ((errors++))
    validate_gitops_structure || ((errors++))
    
    if [[ $errors -eq 0 ]]; then
        print_status "All validations passed! ArgoCD configuration is ready for deployment."
        return 0
    else
        print_error "Validation failed with $errors error(s). Please fix the issues before proceeding."
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  --all, -a          Run all validations (default)"
    echo "  --application      Validate Application configuration only"
    echo "  --project          Validate Project configuration only"
    echo "  --config           Validate ArgoCD server configuration only"
    echo "  --webhook          Validate webhook configuration only"
    echo "  --scripts          Validate script permissions only"
    echo "  --gitops           Validate GitOps structure only"
    echo "  --prerequisites    Check prerequisites only"
    echo "  --help, -h         Show this help message"
    echo ""
}

# Main execution
main() {
    echo "ArgoCD Configuration Validator"
    echo "=============================="
    echo ""
    
    case "${1:-}" in
        --application)
            validate_application
            ;;
        --project)
            validate_project
            ;;
        --config)
            validate_argocd_config
            ;;
        --webhook)
            validate_webhook_config
            ;;
        --scripts)
            validate_scripts
            ;;
        --gitops)
            validate_gitops_structure
            ;;
        --prerequisites)
            check_prerequisites
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        --all|-a|"")
            validate_complete_setup
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"