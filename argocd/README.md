# ArgoCD Configuration for Python CI/CD Pipeline

This directory contains the ArgoCD configuration files for implementing GitOps-based continuous deployment for the Python CI/CD pipeline.

## Overview

ArgoCD is configured to:
- Monitor a GitOps repository for changes
- Automatically sync and deploy applications to Kubernetes
- Provide self-healing capabilities
- Support custom health checks
- Enable secure RBAC-based access control

## Files Description

### Core Configuration Files

- **`application.yaml`**: Main ArgoCD Application manifest that defines the deployment configuration
- **`project.yaml`**: AppProject configuration for organizing and securing applications
- **`argocd-config.yaml`**: ArgoCD server configuration including custom health checks and RBAC
- **`setup-argocd.sh`**: Automated setup script for installing and configuring ArgoCD
- **`README.md`**: This documentation file

## Prerequisites

Before setting up ArgoCD, ensure you have:

1. **Kubernetes Cluster**: A running Kubernetes cluster (minikube, kind, or cloud provider)
2. **kubectl**: Configured to access your cluster
3. **Helm**: For managing Kubernetes applications (optional but recommended)
4. **Git Repository**: A separate GitOps repository for storing deployment manifests

## Quick Setup

### 1. Automated Setup

Run the setup script to install and configure ArgoCD:

```bash
cd argocd
./setup-argocd.sh
```

This script will:
- Install ArgoCD if not already present
- Apply all configuration files
- Set up the AppProject and Application
- Configure custom health checks
- Provide access instructions

### 2. Manual Setup

If you prefer manual setup:

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Apply configurations
kubectl apply -f project.yaml
kubectl apply -f argocd-config.yaml
kubectl apply -f application.yaml

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Configuration Details

### Application Configuration

The `application.yaml` defines:

- **Source Repository**: GitOps repository containing Helm charts
- **Destination**: Target Kubernetes cluster and namespace
- **Sync Policy**: Automated sync with self-healing enabled
- **Health Checks**: Custom health check configurations
- **Retry Policy**: Automatic retry on sync failures

Key features:
```yaml
syncPolicy:
  automated:
    prune: true        # Remove resources not in Git
    selfHeal: true     # Revert manual changes
  syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true
```

### Project Configuration

The `project.yaml` provides:

- **Security**: Whitelist of allowed resources and repositories
- **RBAC**: Role-based access control for different user groups
- **Sync Windows**: Control when automatic syncs can occur
- **Multi-environment**: Support for staging and production deployments

### Custom Health Checks

Custom health checks are configured for:

- **Deployments**: Check replica readiness and availability conditions
- **Services**: Verify service endpoints and load balancer status
- **Application-specific**: Custom checks for the Python CI/CD app

## GitOps Repository Setup

### 1. Create GitOps Repository

Create a separate repository for GitOps (e.g., `python-cicd-demo-gitops`):

```bash
# Create new repository on GitHub
gh repo create python-cicd-demo-gitops --public

# Clone and setup
git clone https://github.com/your-username/python-cicd-demo-gitops.git
cd python-cicd-demo-gitops

# Copy Helm chart
cp -r ../gitops-example/helm-chart .
git add .
git commit -m "Initial Helm chart setup"
git push origin main
```

### 2. Update Application Configuration

Update the repository URL in `application.yaml`:

```yaml
source:
  repoURL: https://github.com/your-username/python-cicd-demo-gitops.git
```

### 3. Configure GitHub Secrets

In your main repository, add these secrets:

- `GITOPS_TOKEN`: GitHub Personal Access Token with write access to GitOps repo
- `GHCR_TOKEN`: GitHub Container Registry token (usually same as GITHUB_TOKEN)

## Accessing ArgoCD

### Web UI

1. Port forward to ArgoCD server:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

2. Access at: https://localhost:8080
   - Username: `admin`
   - Password: Get from secret:
   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

### CLI Access

1. Install ArgoCD CLI:
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
```

2. Login:
```bash
argocd login localhost:8080 --username admin --password <password> --insecure
```

## Monitoring and Troubleshooting

### Check Application Status

```bash
# View application status
kubectl get application python-cicd-app -n argocd

# Get detailed application info
argocd app get python-cicd-app

# View sync history
argocd app history python-cicd-app
```

### Common Issues

1. **Sync Failures**:
   - Check repository access and credentials
   - Verify Helm chart syntax
   - Review ArgoCD server logs

2. **Health Check Failures**:
   - Verify custom health check Lua scripts
   - Check application pod logs
   - Ensure readiness/liveness probes are configured

3. **Permission Issues**:
   - Review RBAC configuration
   - Check AppProject resource whitelists
   - Verify namespace permissions

### Logs and Debugging

```bash
# ArgoCD server logs
kubectl logs -n argocd deployment/argocd-server

# Application controller logs
kubectl logs -n argocd deployment/argocd-application-controller

# Repository server logs
kubectl logs -n argocd deployment/argocd-repo-server
```

## Security Considerations

### RBAC Configuration

- **Developers**: Read and sync access to applications
- **Admins**: Full access to applications and repositories
- **Groups**: Integration with external identity providers

### Repository Security

- Use separate GitOps repository
- Implement branch protection rules
- Use signed commits for production
- Regular security scanning of manifests

### Secrets Management

- Store sensitive data in Kubernetes Secrets
- Use external secret management (e.g., Vault)
- Rotate access tokens regularly
- Implement least-privilege access

## Advanced Configuration

### Multi-Environment Setup

For staging and production environments:

1. Create separate applications for each environment
2. Use different GitOps repository branches
3. Configure environment-specific sync policies
4. Implement promotion workflows

### Image Update Automation

ArgoCD can be configured with tools like:
- **ArgoCD Image Updater**: Automatically update image tags
- **Flux Image Automation**: Alternative image update solution
- **Custom webhooks**: Trigger syncs on image pushes

### Monitoring Integration

Integrate with monitoring tools:
- **Prometheus**: Metrics collection from ArgoCD
- **Grafana**: Dashboards for ArgoCD metrics
- **AlertManager**: Alerts on sync failures

## Testing the Setup

### 1. Verify ArgoCD Installation

```bash
# Check all pods are running
kubectl get pods -n argocd

# Verify application is synced
argocd app get python-cicd-app
```

### 2. Test Automatic Sync

1. Make a change to the GitOps repository
2. Commit and push the change
3. Verify ArgoCD detects and syncs the change
4. Check the application is updated in Kubernetes

### 3. Test Self-Healing

1. Manually modify a deployed resource
2. Verify ArgoCD reverts the change automatically
3. Check the sync status remains healthy

## Next Steps

After setting up ArgoCD:

1. **Configure Monitoring**: Set up Prometheus and Grafana
2. **Implement Notifications**: Configure Slack/email alerts
3. **Security Hardening**: Implement additional security measures
4. **Backup Strategy**: Set up ArgoCD configuration backups
5. **Documentation**: Create runbooks for operations team

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://www.gitops.tech/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)