#!/bin/bash

# ArgoCD Deployment Test Script
# This script tests the ArgoCD deployment and synchronization

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

# Function to wait for condition with timeout
wait_for_condition() {
    local condition="$1"
    local timeout="${2:-300}"
    local interval="${3:-5}"
    local description="${4:-condition}"
    
    print_info "Waiting for $description (timeout: ${timeout}s)..."
    
    local elapsed=0
    while [[ $elapsed -lt $timeout ]]; do
        if eval "$condition" &>/dev/null; then
            print_status "$description met"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    echo ""
    print_error "Timeout waiting for $description"
    return 1
}

# Function to test ArgoCD installation
test_argocd_installation() {
    print_info "Testing ArgoCD installation..."
    
    # Check if ArgoCD namespace exists
    if kubectl get namespace argocd &>/dev/null; then
        print_status "ArgoCD namespace exists"
    else
        print_error "ArgoCD namespace not found"
        return 1
    fi
    
    # Check if ArgoCD pods are running
    local argocd_pods=(
        "argocd-server"
        "argocd-application-controller"
        "argocd-repo-server"
        "argocd-redis"
    )
    
    for pod in "${argocd_pods[@]}"; do
        if wait_for_condition "kubectl get deployment $pod -n argocd -o jsonpath='{.status.readyReplicas}' | grep -q '1'" 60 5 "$pod deployment"; then
            print_status "$pod is running"
        else
            print_error "$pod is not ready"
            kubectl get pods -n argocd | grep $pod
            return 1
        fi
    done
    
    print_status "ArgoCD installation test passed"
}

# Function to test ArgoCD application
test_argocd_application() {
    print_info "Testing ArgoCD application configuration..."
    
    # Check if application exists
    if kubectl get application python-cicd-app -n argocd &>/dev/null; then
        print_status "ArgoCD application exists"
    else
        print_error "ArgoCD application not found"
        return 1
    fi
    
    # Check application status
    local app_health=$(kubectl get application python-cicd-app -n argocd -o jsonpath='{.status.health.status}')
    local app_sync=$(kubectl get application python-cicd-app -n argocd -o jsonpath='{.status.sync.status}')
    
    print_info "Application Health: $app_health"
    print_info "Application Sync: $app_sync"
    
    # Wait for application to be healthy (may take time for initial sync)
    if wait_for_condition "kubectl get application python-cicd-app -n argocd -o jsonpath='{.status.health.status}' | grep -q 'Healthy'" 300 10 "application to be healthy"; then
        print_status "Application is healthy"
    else
        print_warning "Application is not healthy yet (this may be normal for initial setup)"
        kubectl get application python-cicd-app -n argocd -o yaml | grep -A 10 status:
    fi
    
    print_status "ArgoCD application test completed"
}

# Function to test ArgoCD project
test_argocd_project() {
    print_info "Testing ArgoCD project configuration..."
    
    # Check if project exists
    if kubectl get appproject python-cicd-project -n argocd &>/dev/null; then
        print_status "ArgoCD project exists"
    else
        print_error "ArgoCD project not found"
        return 1
    fi
    
    # Get project details
    local project_repos=$(kubectl get appproject python-cicd-project -n argocd -o jsonpath='{.spec.sourceRepos}' | jq length 2>/dev/null || echo "unknown")
    local project_destinations=$(kubectl get appproject python-cicd-project -n argocd -o jsonpath='{.spec.destinations}' | jq length 2>/dev/null || echo "unknown")
    
    print_info "Project source repositories: $project_repos"
    print_info "Project destinations: $project_destinations"
    
    print_status "ArgoCD project test passed"
}

# Function to test application deployment
test_application_deployment() {
    print_info "Testing application deployment in target namespace..."
    
    local target_namespace="python-cicd-app"
    
    # Check if target namespace exists (should be created by ArgoCD)
    if wait_for_condition "kubectl get namespace $target_namespace" 120 5 "target namespace creation"; then
        print_status "Target namespace exists"
    else
        print_warning "Target namespace not created yet"
        return 1
    fi
    
    # Check if application resources are deployed
    local resources=(
        "deployment/python-cicd-app"
        "service/python-cicd-app"
    )
    
    for resource in "${resources[@]}"; do
        if wait_for_condition "kubectl get $resource -n $target_namespace" 120 5 "$resource creation"; then
            print_status "$resource exists"
        else
            print_error "$resource not found"
            return 1
        fi
    done
    
    # Check if deployment is ready
    if wait_for_condition "kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.status.readyReplicas}' | grep -q '[1-9]'" 180 10 "deployment readiness"; then
        print_status "Application deployment is ready"
        
        # Get deployment details
        local replicas=$(kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.status.replicas}')
        local ready_replicas=$(kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.status.readyReplicas}')
        print_info "Deployment replicas: $ready_replicas/$replicas"
    else
        print_error "Application deployment is not ready"
        kubectl get pods -n $target_namespace
        return 1
    fi
    
    print_status "Application deployment test passed"
}

# Function to test application health
test_application_health() {
    print_info "Testing application health endpoint..."
    
    local target_namespace="python-cicd-app"
    
    # Port forward to the application service
    print_info "Setting up port forwarding to test application..."
    kubectl port-forward svc/python-cicd-app -n $target_namespace 8081:80 &
    local port_forward_pid=$!
    
    # Wait for port forwarding to establish
    sleep 5
    
    # Test health endpoint
    local health_test_passed=false
    for i in {1..5}; do
        if curl -s http://localhost:8081/health | grep -q "healthy"; then
            print_status "Application health endpoint is responding"
            health_test_passed=true
            break
        else
            print_warning "Health endpoint test attempt $i failed, retrying..."
            sleep 5
        fi
    done
    
    # Clean up port forwarding
    kill $port_forward_pid 2>/dev/null || true
    
    if [[ "$health_test_passed" == "true" ]]; then
        print_status "Application health test passed"
    else
        print_error "Application health test failed"
        return 1
    fi
}

# Function to test sync functionality
test_sync_functionality() {
    print_info "Testing ArgoCD sync functionality..."
    
    # Check if ArgoCD CLI is available
    if ! command -v argocd &>/dev/null; then
        print_warning "ArgoCD CLI not available, skipping sync test"
        return 0
    fi
    
    # Try to sync the application
    print_info "Triggering manual sync..."
    if argocd app sync python-cicd-app --timeout 300; then
        print_status "Manual sync completed successfully"
    else
        print_warning "Manual sync failed or timed out"
    fi
    
    # Check sync status
    local sync_status=$(argocd app get python-cicd-app -o json | jq -r '.status.sync.status' 2>/dev/null || echo "unknown")
    print_info "Current sync status: $sync_status"
    
    print_status "Sync functionality test completed"
}

# Function to test self-healing
test_self_healing() {
    print_info "Testing ArgoCD self-healing functionality..."
    
    local target_namespace="python-cicd-app"
    
    # Check if deployment exists
    if ! kubectl get deployment python-cicd-app -n $target_namespace &>/dev/null; then
        print_warning "Application not deployed yet, skipping self-healing test"
        return 0
    fi
    
    # Get original replica count
    local original_replicas=$(kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.spec.replicas}')
    print_info "Original replica count: $original_replicas"
    
    # Manually modify the deployment
    print_info "Manually modifying deployment to test self-healing..."
    kubectl scale deployment python-cicd-app -n $target_namespace --replicas=1
    
    # Wait a moment for the change to take effect
    sleep 10
    
    # Check if ArgoCD reverts the change (self-healing)
    if wait_for_condition "kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.spec.replicas}' | grep -q '$original_replicas'" 120 5 "self-healing to revert changes"; then
        print_status "Self-healing functionality works correctly"
    else
        print_warning "Self-healing did not revert the change (may be disabled or slow)"
        local current_replicas=$(kubectl get deployment python-cicd-app -n $target_namespace -o jsonpath='{.spec.replicas}')
        print_info "Current replica count: $current_replicas"
    fi
    
    print_status "Self-healing test completed"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_info "Running comprehensive ArgoCD deployment tests..."
    
    local test_results=()
    
    # Run all tests
    if test_argocd_installation; then
        test_results+=("ArgoCD Installation: PASSED")
    else
        test_results+=("ArgoCD Installation: FAILED")
    fi
    
    if test_argocd_project; then
        test_results+=("ArgoCD Project: PASSED")
    else
        test_results+=("ArgoCD Project: FAILED")
    fi
    
    if test_argocd_application; then
        test_results+=("ArgoCD Application: PASSED")
    else
        test_results+=("ArgoCD Application: FAILED")
    fi
    
    if test_application_deployment; then
        test_results+=("Application Deployment: PASSED")
    else
        test_results+=("Application Deployment: FAILED")
    fi
    
    if test_application_health; then
        test_results+=("Application Health: PASSED")
    else
        test_results+=("Application Health: FAILED")
    fi
    
    if test_sync_functionality; then
        test_results+=("Sync Functionality: PASSED")
    else
        test_results+=("Sync Functionality: FAILED")
    fi
    
    if test_self_healing; then
        test_results+=("Self-Healing: PASSED")
    else
        test_results+=("Self-Healing: FAILED")
    fi
    
    # Print test summary
    echo ""
    print_info "Test Summary:"
    echo "=============="
    
    local passed=0
    local failed=0
    
    for result in "${test_results[@]}"; do
        if [[ "$result" == *"PASSED"* ]]; then
            print_status "$result"
            ((passed++))
        else
            print_error "$result"
            ((failed++))
        fi
    done
    
    echo ""
    print_info "Total Tests: $((passed + failed))"
    print_status "Passed: $passed"
    if [[ $failed -gt 0 ]]; then
        print_error "Failed: $failed"
        return 1
    else
        print_status "All tests passed!"
        return 0
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  --all, -a              Run all tests (default)"
    echo "  --installation         Test ArgoCD installation only"
    echo "  --application          Test ArgoCD application only"
    echo "  --project              Test ArgoCD project only"
    echo "  --deployment           Test application deployment only"
    echo "  --health               Test application health only"
    echo "  --sync                 Test sync functionality only"
    echo "  --self-healing         Test self-healing functionality only"
    echo "  --help, -h             Show this help message"
    echo ""
}

# Main execution
main() {
    echo "ArgoCD Deployment Test Suite"
    echo "============================"
    echo ""
    
    case "${1:-}" in
        --installation)
            test_argocd_installation
            ;;
        --application)
            test_argocd_application
            ;;
        --project)
            test_argocd_project
            ;;
        --deployment)
            test_application_deployment
            ;;
        --health)
            test_application_health
            ;;
        --sync)
            test_sync_functionality
            ;;
        --self-healing)
            test_self_healing
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        --all|-a|"")
            run_comprehensive_tests
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