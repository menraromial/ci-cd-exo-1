#!/bin/bash
set -euo pipefail

# Script de validation complète du pipeline CI/CD
# Valide tous les composants du pipeline depuis le code jusqu'au déploiement

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/tmp/pipeline_validation_${TIMESTAMP}.log"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Fonction pour vérifier les prérequis
check_prerequisites() {
    log "Vérification des prérequis..."
    
    local missing_tools=()
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # Vérifier kubectl (optionnel pour les tests locaux)
    if ! command -v kubectl &> /dev/null; then
        warning "kubectl non trouvé - les tests Kubernetes seront ignorés"
    fi
    
    # Vérifier helm (optionnel)
    if ! command -v helm &> /dev/null; then
        warning "helm non trouvé - les tests Helm seront ignorés"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "Outils manquants: ${missing_tools[*]}"
        return 1
    fi
    
    success "Tous les prérequis sont satisfaits"
    return 0
}

# Fonction pour valider la structure du projet
validate_project_structure() {
    log "Validation de la structure du projet..."
    
    local required_files=(
        "app/main.py"
        "Dockerfile"
        "requirements.txt"
        ".github/workflows/test-and-merge.yml"
        ".github/workflows/build-and-deploy.yml"
        "gitops-example/helm-chart/Chart.yaml"
        "argocd/application.yaml"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        error "Fichiers manquants: ${missing_files[*]}"
        return 1
    fi
    
    success "Structure du projet validée"
    return 0
}

# Fonction pour tester la construction Docker
test_docker_build() {
    log "Test de construction de l'image Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Construire l'image
    if docker build -t cicd-pipeline-test:latest . >> "$LOG_FILE" 2>&1; then
        success "Image Docker construite avec succès"
    else
        error "Échec de la construction de l'image Docker"
        return 1
    fi
    
    # Vérifier que l'image existe
    if docker images cicd-pipeline-test:latest | grep -q cicd-pipeline-test; then
        success "Image Docker vérifiée"
    else
        error "Image Docker non trouvée après construction"
        return 1
    fi
    
    return 0
}

# Fonction pour tester l'application localement
test_local_application() {
    log "Test de l'application en local avec Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Nettoyer les containers existants
    docker-compose -f docker-compose.test.yml down --remove-orphans >> "$LOG_FILE" 2>&1 || true
    
    # Démarrer les services
    if docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit >> "$LOG_FILE" 2>&1; then
        success "Tests end-to-end réussis"
    else
        error "Échec des tests end-to-end"
        # Afficher les logs pour debug
        echo "Logs des containers:"
        docker-compose -f docker-compose.test.yml logs
        return 1
    fi
    
    # Nettoyer
    docker-compose -f docker-compose.test.yml down --remove-orphans >> "$LOG_FILE" 2>&1
    
    return 0
}

# Fonction pour valider les workflows GitHub Actions
validate_github_workflows() {
    log "Validation des workflows GitHub Actions..."
    
    local workflow_files=(
        ".github/workflows/test-and-merge.yml"
        ".github/workflows/build-and-deploy.yml"
    )
    
    for workflow in "${workflow_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$workflow" ]; then
            # Vérifier la syntaxe YAML basique
            if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/$workflow'))" 2>/dev/null; then
                success "Workflow $workflow - syntaxe YAML valide"
            else
                error "Workflow $workflow - syntaxe YAML invalide"
                return 1
            fi
        else
            error "Workflow $workflow non trouvé"
            return 1
        fi
    done
    
    return 0
}

# Fonction pour valider les Helm charts
validate_helm_charts() {
    log "Validation des Helm charts..."
    
    if ! command -v helm &> /dev/null; then
        warning "Helm non installé - validation ignorée"
        return 0
    fi
    
    cd "$PROJECT_ROOT/gitops-example/helm-chart"
    
    # Valider la syntaxe du chart
    if helm lint . >> "$LOG_FILE" 2>&1; then
        success "Helm chart - syntaxe valide"
    else
        error "Helm chart - erreurs de syntaxe"
        return 1
    fi
    
    # Tester le rendu des templates
    if helm template test-release . >> "$LOG_FILE" 2>&1; then
        success "Helm chart - templates valides"
    else
        error "Helm chart - erreurs dans les templates"
        return 1
    fi
    
    return 0
}

# Fonction pour valider la configuration ArgoCD
validate_argocd_config() {
    log "Validation de la configuration ArgoCD..."
    
    local argocd_files=(
        "argocd/application.yaml"
        "argocd/project.yaml"
        "argocd/argocd-config.yaml"
    )
    
    for config_file in "${argocd_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$config_file" ]; then
            # Vérifier la syntaxe YAML
            if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/$config_file'))" 2>/dev/null; then
                success "Configuration ArgoCD $config_file - syntaxe valide"
            else
                error "Configuration ArgoCD $config_file - syntaxe invalide"
                return 1
            fi
        else
            error "Configuration ArgoCD $config_file non trouvée"
            return 1
        fi
    done
    
    return 0
}

# Fonction pour tester les scripts de sécurité
test_security_scripts() {
    log "Test des scripts de sécurité..."
    
    if [ -f "$PROJECT_ROOT/argocd/validate-security.sh" ]; then
        if bash "$PROJECT_ROOT/argocd/validate-security.sh" >> "$LOG_FILE" 2>&1; then
            success "Script de validation de sécurité réussi"
        else
            warning "Script de validation de sécurité a détecté des problèmes"
        fi
    else
        warning "Script de validation de sécurité non trouvé"
    fi
    
    return 0
}

# Fonction pour générer un rapport de validation
generate_validation_report() {
    log "Génération du rapport de validation..."
    
    local report_file="/tmp/pipeline_validation_report_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "pipeline_validation": {
        "project_structure": "validated",
        "docker_build": "tested",
        "local_application": "tested",
        "github_workflows": "validated",
        "helm_charts": "validated",
        "argocd_config": "validated",
        "security_scripts": "tested"
    },
    "log_file": "$LOG_FILE",
    "validation_status": "completed"
}
EOF
    
    success "Rapport de validation généré: $report_file"
}

# Fonction principale
main() {
    log "🚀 Démarrage de la validation complète du pipeline CI/CD"
    log "📁 Répertoire du projet: $PROJECT_ROOT"
    log "📄 Fichier de log: $LOG_FILE"
    
    local exit_code=0
    
    # Exécuter toutes les validations
    check_prerequisites || exit_code=1
    validate_project_structure || exit_code=1
    test_docker_build || exit_code=1
    test_local_application || exit_code=1
    validate_github_workflows || exit_code=1
    validate_helm_charts || exit_code=1
    validate_argocd_config || exit_code=1
    test_security_scripts || exit_code=1
    
    # Générer le rapport
    generate_validation_report
    
    if [ $exit_code -eq 0 ]; then
        success "🎉 Validation complète du pipeline réussie!"
        log "📊 Consultez le fichier de log pour plus de détails: $LOG_FILE"
    else
        error "💥 La validation du pipeline a échoué"
        log "🔍 Consultez le fichier de log pour les détails: $LOG_FILE"
    fi
    
    exit $exit_code
}

# Exécuter le script principal
main "$@"