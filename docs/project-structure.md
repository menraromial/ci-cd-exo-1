# Structure du Projet et Fichiers de Configuration

Ce document décrit en détail la structure du projet, le rôle de chaque fichier et les configurations importantes.

## Vue d'Ensemble de la Structure

```
python-cicd-pipeline/
├── app/                           # 📁 Application Python Flask
│   ├── __init__.py               # Module Python
│   ├── main.py                   # 🚀 Point d'entrée de l'application
│   └── api/                      # 📁 Modules API REST
│       ├── __init__.py           # Module Python
│       ├── health.py             # 💚 Endpoint de santé
│       ├── hello.py              # 👋 Endpoint de bienvenue
│       └── calculator.py         # 🧮 Endpoint de calcul
├── tests/                         # 📁 Tests unitaires et d'intégration
│   ├── __init__.py               # Module Python
│   ├── conftest.py               # Configuration pytest
│   ├── test_health.py            # Tests endpoint santé
│   ├── test_hello.py             # Tests endpoint hello
│   └── test_calculator.py        # Tests endpoint calcul
├── .github/                       # 📁 Configuration GitHub
│   └── workflows/                # 📁 Workflows GitHub Actions
│       ├── test-and-merge.yml    # 🔄 Tests et merge automatique
│       └── build-and-deploy.yml  # 🏗️ Build et déploiement
├── argocd/                        # 📁 Configuration ArgoCD
│   ├── application.yaml          # 📋 Application ArgoCD
│   ├── project.yaml              # 📂 Projet ArgoCD
│   ├── argocd-config.yaml        # ⚙️ Configuration serveur ArgoCD
│   ├── webhook-config.yaml       # 🔗 Configuration webhooks
│   ├── setup-argocd.sh          # 🛠️ Script d'installation
│   ├── validate-config.sh        # ✅ Script de validation
│   ├── validate-security.sh      # 🔒 Script de validation sécurité
│   ├── test-deployment.sh        # 🧪 Script de test déploiement
│   └── README.md                 # 📖 Documentation ArgoCD
├── gitops-example/                # 📁 Exemple repository GitOps
│   ├── helm-chart/               # 📁 Chart Helm
│   │   ├── Chart.yaml            # 📊 Métadonnées du chart
│   │   ├── values.yaml           # 🎛️ Valeurs par défaut
│   │   └── templates/            # 📁 Templates Kubernetes
│   │       ├── NOTES.txt         # 📝 Notes d'installation
│   │       ├── _helpers.tpl      # 🔧 Helpers Helm
│   │       ├── configmap.yaml    # 📋 ConfigMap
│   │       ├── deployment.yaml   # 🚀 Deployment
│   │       ├── service.yaml      # 🌐 Service
│   │       ├── serviceaccount.yaml # 👤 Service Account
│   │       ├── ingress.yaml      # 🌍 Ingress
│   │       ├── hpa.yaml          # 📈 Horizontal Pod Autoscaler
│   │       ├── networkpolicy.yaml # 🔒 Network Policy
│   │       ├── poddisruptionbudget.yaml # 🛡️ Pod Disruption Budget
│   │       └── secret.yaml       # 🔐 Secrets
│   └── README.md                 # 📖 Documentation GitOps
├── docs/                          # 📁 Documentation complète
│   ├── setup-guide.md            # 📋 Guide de mise en place
│   ├── project-structure.md      # 📁 Structure du projet (ce fichier)
│   ├── github-actions-setup.md   # ⚙️ Configuration GitHub Actions
│   ├── github-secrets-setup.md   # 🔐 Configuration des secrets
│   └── security-implementation.md # 🔒 Implémentation sécurité
├── .coverage                      # 📊 Rapport de couverture de code
├── .dockerignore                  # 🐳 Fichiers ignorés par Docker
├── .flake8                        # 🔍 Configuration linting flake8
├── .gitignore                     # 📝 Fichiers ignorés par Git
├── Dockerfile                     # 🐳 Configuration container
├── README.md                      # 📖 Documentation principale
├── requirements.txt               # 📦 Dépendances Python
├── pyproject.toml                # ⚙️ Configuration projet Python
├── pytest.ini                    # 🧪 Configuration pytest
└── test_endpoints.py             # 🧪 Tests d'intégration endpoints
```

## Détail des Composants

### 📁 Application Python (`app/`)

#### `app/main.py`
**Rôle** : Point d'entrée principal de l'application Flask
**Configuration** :
```python
from flask import Flask
from api.health import health_bp
from api.hello import hello_bp
from api.calculator import calculator_bp

app = Flask(__name__)
app.register_blueprint(health_bp)
app.register_blueprint(hello_bp, url_prefix='/api')
app.register_blueprint(calculator_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### `app/api/health.py`
**Rôle** : Endpoint de santé pour les health checks Kubernetes
**Endpoints** :
- `GET /health` → Status de santé de l'application
- Utilisé par les liveness et readiness probes

#### `app/api/hello.py`
**Rôle** : Endpoint de bienvenue simple
**Endpoints** :
- `GET /api/hello` → Message de bienvenue JSON

#### `app/api/calculator.py`
**Rôle** : Endpoint de calcul avec validation
**Endpoints** :
- `POST /api/calculate` → Opérations mathématiques (add, subtract, multiply, divide)
- Validation des entrées et gestion d'erreurs

### 📁 Tests (`tests/`)

#### `tests/conftest.py`
**Rôle** : Configuration globale pytest et fixtures
**Contenu** :
```python
import pytest
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

#### Tests Unitaires
- **`test_health.py`** : Tests de l'endpoint de santé
- **`test_hello.py`** : Tests de l'endpoint hello
- **`test_calculator.py`** : Tests complets des opérations de calcul

**Configuration pytest** (`pytest.ini`) :
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
```

### 📁 GitHub Actions (`.github/workflows/`)

#### `test-and-merge.yml`
**Déclencheur** : Push sur branche `dev`
**Étapes** :
1. Setup Python 3.11
2. Installation des dépendances
3. Linting avec flake8 et black
4. Tests avec pytest et couverture
5. Merge automatique vers `main` si succès

**Configuration clé** :
```yaml
on:
  push:
    branches: [ dev ]
  pull_request:
    branches: [ dev ]

permissions:
  contents: write
  checks: write
  pull-requests: write
```

#### `build-and-deploy.yml`
**Déclencheur** : Push sur branche `main`
**Étapes** :
1. Build image Docker multi-platform
2. Scan de sécurité avec Trivy
3. Push vers GitHub Container Registry
4. Mise à jour du repository GitOps

**Configuration clé** :
```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write
  security-events: write
```

### 📁 Configuration ArgoCD (`argocd/`)

#### `application.yaml`
**Rôle** : Définition de l'application ArgoCD
**Configuration principale** :
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-cicd-app
  namespace: argocd
spec:
  project: python-cicd-project
  source:
    repoURL: https://github.com/your-username/your-repo-gitops.git
    targetRevision: HEAD
    path: helm-chart
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

#### `project.yaml`
**Rôle** : Projet ArgoCD pour la sécurité et l'organisation
**Fonctionnalités** :
- Whitelist des repositories autorisés
- RBAC pour différents groupes d'utilisateurs
- Contrôle des ressources Kubernetes autorisées

#### `argocd-config.yaml`
**Rôle** : Configuration serveur ArgoCD
**Inclut** :
- Health checks personnalisés
- Configuration RBAC
- Paramètres de synchronisation

#### Scripts de Gestion
- **`setup-argocd.sh`** : Installation automatisée complète
- **`validate-config.sh`** : Validation des configurations
- **`validate-security.sh`** : Vérifications de sécurité
- **`test-deployment.sh`** : Tests de déploiement

### 📁 GitOps Example (`gitops-example/`)

#### Chart Helm (`helm-chart/`)

**`Chart.yaml`** :
```yaml
apiVersion: v2
name: python-cicd-app
description: A Helm chart for Python CI/CD application
type: application
version: 0.1.0
appVersion: "1.0.0"
```

**`values.yaml`** - Valeurs configurables :
```yaml
replicaCount: 1

image:
  repository: ghcr.io/your-username/your-repo-name
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: 5000

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 100
  targetCPUUtilizationPercentage: 80
```

#### Templates Kubernetes

**`deployment.yaml`** :
- Configuration du déploiement principal
- Security context renforcé
- Health checks (liveness/readiness probes)
- Variables d'environnement

**`service.yaml`** :
- Exposition de l'application
- Configuration des ports
- Sélecteurs de pods

**`configmap.yaml`** :
- Configuration de l'application
- Variables d'environnement non sensibles

**`secret.yaml`** :
- Gestion des secrets (optionnel)
- Support pour External Secrets Operator

**`ingress.yaml`** :
- Exposition externe (optionnel)
- Configuration TLS
- Annotations pour ingress controller

**`hpa.yaml`** :
- Auto-scaling horizontal
- Métriques CPU/mémoire
- Configuration des seuils

**`networkpolicy.yaml`** :
- Sécurité réseau
- Restriction du trafic entrant/sortant
- Isolation des pods

**`poddisruptionbudget.yaml`** :
- Haute disponibilité
- Protection contre les interruptions
- Configuration `minAvailable`

### 📁 Documentation (`docs/`)

#### Fichiers de Documentation
- **`setup-guide.md`** : Guide complet de mise en place
- **`project-structure.md`** : Ce fichier - structure détaillée
- **`github-actions-setup.md`** : Configuration GitHub Actions
- **`github-secrets-setup.md`** : Gestion des secrets
- **`security-implementation.md`** : Mesures de sécurité

### 🐳 Configuration Docker

#### `Dockerfile`
**Build multi-stage** :
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim AS production
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/
USER appuser
EXPOSE 5000
CMD ["python", "app/main.py"]
```

#### `.dockerignore`
**Fichiers exclus du build** :
```
.git
.github
tests/
docs/
*.md
.coverage
htmlcov/
.pytest_cache/
venv/
```

### ⚙️ Configuration Python

#### `pyproject.toml`
**Configuration moderne Python** :
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "python-cicd-pipeline"
version = "1.0.0"
description = "CI/CD Pipeline for Python applications"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
dependencies = [
    "flask>=2.3.0",
    "gunicorn>=21.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.7.0",
    "flake8>=6.0.0",
    "bandit>=1.7.5",
    "safety>=2.3.0",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers --cov=app --cov-report=html --cov-report=xml"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
]
```

#### `requirements.txt`
**Dépendances de production** :
```
Flask==2.3.3
gunicorn==21.2.0
Werkzeug==2.3.7
```

### 🔍 Configuration Linting

#### `.flake8`
**Configuration flake8** :
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503
max-complexity = 10
select = B,C,E,F,W,T4,B9
exclude = 
    .git,
    __pycache__,
    .pytest_cache,
    .coverage,
    htmlcov,
    venv,
    build,
    dist
```

## Flux de Données

### 1. Développement
```
Développeur → Code → Push dev → GitHub Actions (Tests) → Merge main
```

### 2. Build et Déploiement
```
Main branch → GitHub Actions → Docker Build → GHCR → GitOps Update
```

### 3. Déploiement Kubernetes
```
GitOps Repo → ArgoCD → Kubernetes → Application Running
```

## Variables d'Environnement

### Application
- `FLASK_ENV` : Environnement Flask (development/production)
- `PORT` : Port d'écoute (défaut: 5000)
- `DEBUG` : Mode debug (défaut: False)

### GitHub Actions
- `GITHUB_TOKEN` : Token automatique GitHub
- `GITOPS_TOKEN` : Token pour repository GitOps
- `REGISTRY` : Registry Docker (ghcr.io)
- `IMAGE_NAME` : Nom de l'image Docker

### Kubernetes
- `APP_NAME` : Nom de l'application
- `NAMESPACE` : Namespace Kubernetes
- `REPLICAS` : Nombre de replicas

## Sécurité

### Mesures Implémentées
1. **Container Security** : Utilisateur non-root, image minimale
2. **Code Security** : Scan avec Bandit, Safety
3. **Image Security** : Scan avec Trivy
4. **Network Security** : Network Policies
5. **RBAC** : Contrôle d'accès ArgoCD et Kubernetes
6. **Secrets Management** : GitHub Secrets, Kubernetes Secrets

### Permissions Minimales
- GitHub Actions : Lecture code, écriture packages
- ArgoCD : Accès limité aux ressources autorisées
- Kubernetes : Service Account avec permissions minimales

## Monitoring et Observabilité

### Métriques Exposées
- Health checks endpoints
- Métriques applicatives (optionnel)
- Métriques Kubernetes natives

### Logs
- Logs applicatifs structurés
- Logs GitHub Actions
- Logs ArgoCD
- Logs Kubernetes

## Maintenance

### Mises à Jour Régulières
- **Images de base** : Mensuel
- **Dépendances Python** : Hebdomadaire
- **Outils de sécurité** : Automatique
- **Configuration** : Selon les besoins

### Sauvegarde
- Configuration ArgoCD
- Secrets Kubernetes
- Historique des déploiements
- Documentation

Cette structure modulaire permet une maintenance facile, une sécurité renforcée et une évolutivité du pipeline CI/CD.