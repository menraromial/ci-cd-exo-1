# Configuration des GitHub Secrets

## Vue d'ensemble

Ce document décrit la configuration des secrets GitHub nécessaires pour le pipeline CI/CD sécurisé.

## Secrets requis

### 1. GITOPS_TOKEN
- **Description**: Token d'accès personnel pour mettre à jour le repository GitOps
- **Permissions requises**: 
  - `repo` (accès complet aux repositories)
  - `workflow` (mise à jour des workflows)
- **Durée de vie**: 90 jours (rotation recommandée)

### 2. DOCKER_REGISTRY_TOKEN (optionnel)
- **Description**: Token pour accéder à des registries Docker privés
- **Utilisation**: Si vous utilisez un registry privé autre que GHCR

### 3. SECURITY_SCAN_TOKEN (optionnel)
- **Description**: Token pour les services de scan de sécurité externes
- **Utilisation**: Pour intégrer des outils comme Snyk ou Veracode

## Configuration étape par étape

### Étape 1: Créer un Personal Access Token

1. Aller dans GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Cliquer sur "Generate new token (classic)"
3. Donner un nom descriptif: `GitOps-Pipeline-Token`
4. Sélectionner les permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
5. Définir une expiration de 90 jours
6. Cliquer sur "Generate token"
7. **IMPORTANT**: Copier le token immédiatement (il ne sera plus visible)

### Étape 2: Ajouter le secret au repository

1. Aller dans le repository → Settings → Secrets and variables → Actions
2. Cliquer sur "New repository secret"
3. Nom: `GITOPS_TOKEN`
4. Valeur: Coller le token généré
5. Cliquer sur "Add secret"

### Étape 3: Vérifier la configuration

Les secrets configurés doivent apparaître dans la liste des secrets du repository.

## Bonnes pratiques de sécurité

### Rotation des tokens
- Configurer des rappels pour renouveler les tokens avant expiration
- Utiliser des tokens avec la durée de vie la plus courte possible
- Documenter les dates d'expiration

### Permissions minimales
- Ne donner que les permissions strictement nécessaires
- Éviter les tokens avec des permissions `admin` ou `owner`
- Utiliser des tokens spécifiques par fonction

### Monitoring
- Surveiller l'utilisation des tokens dans les logs GitHub
- Configurer des alertes pour les échecs d'authentification
- Révoquer immédiatement les tokens compromis

## Dépannage

### Erreur "Bad credentials"
- Vérifier que le token n'a pas expiré
- Confirmer que les permissions sont correctes
- Régénérer le token si nécessaire

### Erreur "Resource not accessible"
- Vérifier que le token a les permissions `repo`
- Confirmer que le repository GitOps existe
- Vérifier l'orthographe du nom du repository

## Sécurité avancée

### Utilisation d'OIDC (recommandé)
Pour une sécurité renforcée, considérer l'utilisation d'OpenID Connect au lieu de tokens:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/GitHubActions
      aws-region: us-east-1
```

### Environnements protégés
- Utiliser des environnements GitHub pour les déploiements en production
- Configurer des règles d'approbation manuelle
- Limiter les branches autorisées à déployer