# GitHub Actions Setup Guide

This guide explains how to configure the GitHub Actions workflows for the CI/CD pipeline.

## Required Secrets

### 1. GITOPS_TOKEN

This token is required for the build-and-deploy workflow to update the GitOps repository.

**Steps to create:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Set expiration and select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
4. Copy the generated token
5. In your main repository, go to Settings → Secrets and variables → Actions
6. Click "New repository secret"
7. Name: `GITOPS_TOKEN`
8. Value: Paste the token

### 2. GITHUB_TOKEN (Automatic)

The `GITHUB_TOKEN` is automatically provided by GitHub Actions and doesn't need manual setup. It's used for:
- Pushing Docker images to GitHub Container Registry
- Basic repository operations

## Workflow Configuration

### build-and-deploy.yml

This workflow triggers on pushes to the `main` branch and:

1. **Builds Docker Image**: Uses multi-platform build (amd64, arm64)
2. **Pushes to GHCR**: Tags with commit SHA and latest
3. **Updates GitOps**: Modifies the Helm values file with new image tag

**Key Features:**
- Multi-platform Docker builds
- Efficient caching with GitHub Actions cache
- Automatic tagging strategy
- GitOps repository updates
- Deployment summaries

### Image Tagging Strategy

The workflow creates the following tags:
- `latest`: Most recent build from main branch
- `main-{commit-sha}`: Specific version for rollbacks
- `main`: Branch-based tag

## GitOps Repository Setup

### 1. Create GitOps Repository

Create a separate repository named `{your-repo}-gitops`:

```bash
# Example: if your repo is "python-cicd-demo"
# Create: "python-cicd-demo-gitops"
```

### 2. Repository Structure

```
your-repo-gitops/
├── helm-chart/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
└── README.md
```

### 3. Update values.yaml

Ensure your GitOps repository's `values.yaml` contains:

```yaml
image:
  repository: ghcr.io/your-username/your-repo-name
  tag: "latest"
```

## Permissions Required

### Repository Permissions

The workflows require these permissions:

**build-and-push job:**
- `contents: read` - Read repository content
- `packages: write` - Push to GitHub Container Registry

**update-gitops job:**
- `contents: write` - Update GitOps repository

### GitHub Container Registry

Ensure GitHub Container Registry is enabled:
1. Go to repository Settings → General
2. Scroll to "Features" section
3. Enable "Packages"

## Testing the Workflow

### 1. Test Docker Build Locally

```bash
# Build the image locally to verify Dockerfile
docker build -t test-app .

# Run the container
docker run -p 5000:5000 test-app

# Test the endpoints
curl http://localhost:5000/health
```

### 2. Test Workflow Trigger

1. Make a change to your code
2. Push to `dev` branch (triggers test-and-merge)
3. If tests pass, code auto-merges to `main`
4. Push to `main` triggers build-and-deploy

### 3. Verify Image in GHCR

1. Go to your repository on GitHub
2. Click "Packages" tab
3. Verify your Docker image appears with correct tags

## Troubleshooting

### Common Issues

**1. Permission Denied on GHCR Push**
- Verify `packages: write` permission is set
- Check if GITHUB_TOKEN has correct scopes

**2. GitOps Repository Access Denied**
- Verify GITOPS_TOKEN has correct permissions
- Ensure token hasn't expired
- Check repository name format: `{main-repo}-gitops`

**3. Docker Build Failures**
- Test Dockerfile locally first
- Check if all required files are included in build context
- Verify base image availability

**4. Sed Command Fails in GitOps Update**
- Ensure values.yaml has the expected format
- Check if the `tag:` line exists in the file
- Verify file path: `helm-chart/values.yaml`

### Debug Steps

1. **Check workflow logs**: Go to Actions tab in GitHub
2. **Verify secrets**: Ensure all required secrets are set
3. **Test locally**: Build and run Docker image locally
4. **Check permissions**: Verify repository and token permissions

## Security Best Practices

1. **Use minimal token permissions**: Only grant necessary scopes
2. **Regular token rotation**: Update GITOPS_TOKEN periodically
3. **Separate repositories**: Keep GitOps config separate from application code
4. **Review workflow permissions**: Regularly audit required permissions
5. **Monitor package access**: Check who has access to your container images

## Next Steps

After setting up the workflows:

1. Configure ArgoCD to monitor your GitOps repository
2. Set up Kubernetes cluster and Helm charts
3. Configure monitoring and alerting
4. Set up additional environments (staging, production)