# GitOps Repository Setup

This directory contains an example of how to set up a GitOps repository for the CI/CD pipeline.

## Setup Instructions

### 1. Create a Separate GitOps Repository

Create a new repository named `{your-repo-name}-gitops` (e.g., if your main repo is `python-cicd-demo`, create `python-cicd-demo-gitops`).

### 2. Copy Helm Chart Structure

Copy the contents of this `gitops-example` directory to your GitOps repository:

```bash
# In your GitOps repository
mkdir -p helm-chart
cp gitops-example/helm-chart/values.yaml helm-chart/
```

### 3. Configure GitHub Secrets

In your main repository, add the following secrets:

- `GITOPS_TOKEN`: A GitHub Personal Access Token with write access to your GitOps repository

### 4. Update Workflow Configuration

In `.github/workflows/build-and-deploy.yml`, update the following:

```yaml
# Replace with your actual GitOps repository name
repository: ${{ github.repository }}-gitops
```

### 5. Update values.yaml

In your GitOps repository's `helm-chart/values.yaml`, update:

```yaml
image:
  repository: ghcr.io/your-username/your-repo-name  # Update with your actual repository
  tag: "latest"
```

## How It Works

1. When code is pushed to the `main` branch, the build-and-deploy workflow:
   - Builds a Docker image
   - Pushes it to GitHub Container Registry with tags:
     - `main-{commit-sha}`
     - `latest`
   - Updates the `helm-chart/values.yaml` file in the GitOps repository with the new image tag

2. ArgoCD monitors the GitOps repository and automatically deploys changes to Kubernetes

## Image Tagging Strategy

- **Latest**: Always points to the most recent build from main
- **Commit SHA**: Specific version for rollbacks (format: `main-{sha}`)
- **Branch**: Branch-based tagging for feature branches

## Security Considerations

- The GitOps repository should be separate from the application code
- Use minimal permissions for the GITOPS_TOKEN
- Consider using GitHub Apps instead of personal access tokens for production