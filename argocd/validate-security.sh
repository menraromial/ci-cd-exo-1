#!/bin/bash

# Script de validation de la sécurité du pipeline CI/CD
# Ce script vérifie que toutes les mesures de sécurité sont correctement implémentées

# Ne pas arrêter sur les erreurs pour permettre de compter tous les échecs
# set -e

echo "🔒 Validation de la sécurité du pipeline CI/CD"
echo "=============================================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les résultats
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Compteurs
PASSED=0
FAILED=0
WARNINGS=0

echo ""
echo "1. Validation des workflows GitHub Actions"
echo "----------------------------------------"

# Vérifier la présence des workflows
if [ -f ".github/workflows/test-and-merge.yml" ] && [ -f ".github/workflows/build-and-deploy.yml" ]; then
    print_result 0 "Workflows GitHub Actions présents"
    ((PASSED++))
else
    print_result 1 "Workflows GitHub Actions manquants"
    ((FAILED++))
fi

# Vérifier les permissions minimales dans les workflows
if grep -q "permissions:" .github/workflows/test-and-merge.yml && grep -q "contents: read" .github/workflows/test-and-merge.yml; then
    print_result 0 "Permissions minimales configurées dans test-and-merge.yml"
    ((PASSED++))
else
    print_result 1 "Permissions minimales non configurées dans test-and-merge.yml"
    ((FAILED++))
fi

if grep -q "permissions:" .github/workflows/build-and-deploy.yml && grep -q "contents: read" .github/workflows/build-and-deploy.yml; then
    print_result 0 "Permissions minimales configurées dans build-and-deploy.yml"
    ((PASSED++))
else
    print_result 1 "Permissions minimales non configurées dans build-and-deploy.yml"
    ((FAILED++))
fi

# Vérifier la présence du scan de vulnérabilités
if grep -q "trivy-action" .github/workflows/build-and-deploy.yml; then
    print_result 0 "Scan de vulnérabilités Trivy configuré"
    ((PASSED++))
else
    print_result 1 "Scan de vulnérabilités Trivy manquant"
    ((FAILED++))
fi

# Vérifier la présence des outils de sécurité statique
if grep -q "bandit" .github/workflows/test-and-merge.yml && grep -q "safety" .github/workflows/test-and-merge.yml; then
    print_result 0 "Outils de sécurité statique (bandit, safety) configurés"
    ((PASSED++))
else
    print_result 1 "Outils de sécurité statique manquants"
    ((FAILED++))
fi

echo ""
echo "2. Validation du Dockerfile"
echo "-------------------------"

# Vérifier l'utilisateur non-root
if grep -q "useradd.*appuser" Dockerfile && grep -q "USER appuser" Dockerfile; then
    print_result 0 "Utilisateur non-root configuré dans le Dockerfile"
    ((PASSED++))
else
    print_result 1 "Utilisateur non-root manquant dans le Dockerfile"
    ((FAILED++))
fi

# Vérifier les mises à jour de sécurité
if grep -q "apt-get update.*apt-get upgrade" Dockerfile; then
    print_result 0 "Mises à jour de sécurité configurées dans le Dockerfile"
    ((PASSED++))
else
    print_result 1 "Mises à jour de sécurité manquantes dans le Dockerfile"
    ((FAILED++))
fi

# Vérifier les labels de sécurité
if grep -q "LABEL.*security" Dockerfile; then
    print_result 0 "Labels de sécurité présents dans le Dockerfile"
    ((PASSED++))
else
    print_result 1 "Labels de sécurité manquants dans le Dockerfile"
    ((FAILED++))
fi

echo ""
echo "3. Validation des configurations Helm"
echo "-----------------------------------"

# Vérifier la présence des templates de sécurité
if [ -f "gitops-example/helm-chart/templates/networkpolicy.yaml" ]; then
    print_result 0 "Template NetworkPolicy présent"
    ((PASSED++))
else
    print_result 1 "Template NetworkPolicy manquant"
    ((FAILED++))
fi

if [ -f "gitops-example/helm-chart/templates/poddisruptionbudget.yaml" ]; then
    print_result 0 "Template PodDisruptionBudget présent"
    ((PASSED++))
else
    print_result 1 "Template PodDisruptionBudget manquant"
    ((FAILED++))
fi

if [ -f "gitops-example/helm-chart/templates/secret.yaml" ]; then
    print_result 0 "Template Secret présent"
    ((PASSED++))
else
    print_result 1 "Template Secret manquant"
    ((FAILED++))
fi

# Vérifier le security context dans values.yaml
if grep -q "runAsNonRoot: true" gitops-example/helm-chart/values.yaml && grep -q "runAsUser: 1001" gitops-example/helm-chart/values.yaml; then
    print_result 0 "Security context configuré dans values.yaml"
    ((PASSED++))
else
    print_result 1 "Security context manquant dans values.yaml"
    ((FAILED++))
fi

# Vérifier la configuration des network policies
if grep -q "networkPolicy:" gitops-example/helm-chart/values.yaml && grep -q "enabled: true" gitops-example/helm-chart/values.yaml; then
    print_result 0 "Network policies configurées dans values.yaml"
    ((PASSED++))
else
    print_result 1 "Network policies manquantes dans values.yaml"
    ((FAILED++))
fi

echo ""
echo "4. Validation des configurations ArgoCD"
echo "-------------------------------------"

# Vérifier la présence des configurations ArgoCD
if [ -f "argocd/application.yaml" ] && [ -f "argocd/project.yaml" ]; then
    print_result 0 "Configurations ArgoCD présentes"
    ((PASSED++))
else
    print_result 1 "Configurations ArgoCD manquantes"
    ((FAILED++))
fi

# Vérifier les restrictions de repositories dans le projet
if grep -q "sourceReposDeny" argocd/project.yaml; then
    print_result 0 "Restrictions de repositories configurées"
    ((PASSED++))
else
    print_result 1 "Restrictions de repositories manquantes"
    ((FAILED++))
fi

# Vérifier les ressources blacklistées
if grep -q "namespaceResourceBlacklist" argocd/project.yaml; then
    print_result 0 "Ressources blacklistées configurées"
    ((PASSED++))
else
    print_result 1 "Ressources blacklistées manquantes"
    ((FAILED++))
fi

# Vérifier les sync windows de sécurité
if grep -q "Production changes require manual approval" argocd/project.yaml; then
    print_result 0 "Fenêtres de synchronisation sécurisées configurées"
    ((PASSED++))
else
    print_result 1 "Fenêtres de synchronisation sécurisées manquantes"
    ((FAILED++))
fi

echo ""
echo "5. Validation de la documentation"
echo "-------------------------------"

# Vérifier la présence de la documentation de sécurité
if [ -f "docs/security-implementation.md" ]; then
    print_result 0 "Documentation de sécurité présente"
    ((PASSED++))
else
    print_result 1 "Documentation de sécurité manquante"
    ((FAILED++))
fi

if [ -f "docs/github-secrets-setup.md" ]; then
    print_result 0 "Documentation des secrets GitHub présente"
    ((PASSED++))
else
    print_result 1 "Documentation des secrets GitHub manquante"
    ((FAILED++))
fi

echo ""
echo "6. Vérifications supplémentaires"
echo "------------------------------"

# Vérifier qu'il n'y a pas de secrets hardcodés dans le code
if find . -name "*.py" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l "password\|secret\|token\|key" | grep -v "docs/" | grep -v "README" | grep -v ".git/" > /dev/null 2>&1; then
    print_warning "Possibles secrets détectés dans le code - vérification manuelle requise"
    ((WARNINGS++))
else
    print_result 0 "Aucun secret apparent détecté dans le code"
    ((PASSED++))
fi

# Vérifier la présence de .gitignore pour éviter les commits de secrets
if [ -f ".gitignore" ] && grep -q "*.env" .gitignore; then
    print_result 0 "Fichier .gitignore configuré pour éviter les secrets"
    ((PASSED++))
else
    print_result 1 "Fichier .gitignore manquant ou incomplet"
    ((FAILED++))
fi

echo ""
echo "=============================================="
echo "📊 Résumé de la validation de sécurité"
echo "=============================================="
echo -e "${GREEN}✅ Tests réussis: $PASSED${NC}"
echo -e "${RED}❌ Tests échoués: $FAILED${NC}"
echo -e "${YELLOW}⚠️  Avertissements: $WARNINGS${NC}"

TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / TOTAL))
    echo "📈 Score de sécurité: $PERCENTAGE%"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Toutes les vérifications de sécurité sont passées avec succès!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Veuillez examiner les avertissements ci-dessus.${NC}"
    fi
    exit 0
else
    echo -e "${RED}🚨 Des problèmes de sécurité ont été détectés. Veuillez les corriger avant de continuer.${NC}"
    exit 1
fi