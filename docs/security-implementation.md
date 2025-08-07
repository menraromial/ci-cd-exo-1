# Implémentation de la Sécurité - Pipeline CI/CD

## Vue d'ensemble

Ce document décrit toutes les mesures de sécurité implémentées dans le pipeline CI/CD pour respecter les meilleures pratiques de sécurité DevSecOps.

## 1. Gestion des Secrets GitHub

### Configuration des Secrets
Les secrets suivants doivent être configurés dans GitHub :

- `GITOPS_TOKEN`: Token d'accès personnel pour le repository GitOps
- `DOCKER_REGISTRY_TOKEN`: Token pour registries Docker privés (optionnel)
- `SECURITY_SCAN_TOKEN`: Token pour services de scan externes (optionnel)

### Bonnes Pratiques
- Rotation des tokens tous les 90 jours
- Permissions minimales (principe du moindre privilège)
- Monitoring de l'utilisation des tokens
- Révocation immédiate en cas de compromission

## 2. Scan de Vulnérabilités des Images Docker

### Outils Utilisés
- **Trivy**: Scanner de vulnérabilités intégré dans le pipeline
- **Format SARIF**: Upload des résultats vers GitHub Security tab
- **Seuils de sécurité**: Échec du build pour vulnérabilités CRITICAL/HIGH

### Configuration
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:main-${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
```

### Résultats
- Rapports automatiques dans l'onglet Security de GitHub
- Blocage des déploiements avec vulnérabilités critiques
- Historique des scans pour traçabilité

## 3. Permissions Minimales GitHub Actions

### Permissions Globales
```yaml
permissions:
  contents: read  # Minimal par défaut
```

### Permissions par Job
- **Test Job**: `contents: read`, `checks: write`, `pull-requests: write`
- **Build Job**: `contents: read`, `packages: write`, `security-events: write`
- **Deploy Job**: `contents: write` (uniquement pour GitOps)

### Principe du Moindre Privilège
- Aucune permission `admin` ou `owner`
- Permissions spécifiques par tâche
- Révision régulière des permissions

## 4. Sécurité des Images Docker

### Image de Base Sécurisée
```dockerfile
FROM python:3.11-slim AS production

# Mises à jour de sécurité
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root avec UID/GID spécifiques
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -s /sbin/nologin appuser
```

### Hardening du Container
- Utilisateur non-root (UID 1001)
- Système de fichiers en lecture seule
- Suppression des capacités dangereuses
- Variables d'environnement sécurisées

## 5. Analyse de Sécurité Statique du Code

### Outils Intégrés
- **Bandit**: Analyse de sécurité Python
- **Safety**: Vérification des vulnérabilités des dépendances
- **Black**: Formatage de code (prévention d'injection)
- **Flake8**: Analyse statique et détection d'erreurs

### Configuration Bandit
```bash
bandit -r app/ -f json -o bandit-report.json
bandit -r app/ -f txt  # Affichage console
```

### Configuration Safety
```bash
safety check --json --output safety-report.json
safety check  # Affichage console
```

## 6. Sécurité Kubernetes

### Security Context Renforcé
```yaml
podSecurityContext:
  fsGroup: 1001
  runAsGroup: 1001
  runAsNonRoot: true
  runAsUser: 1001
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1001
  seccompProfile:
    type: RuntimeDefault
```

### Network Policies
- Restriction du trafic entrant et sortant
- Isolation des pods par namespace
- Autorisation uniquement des connexions nécessaires

### Pod Disruption Budget
- Haute disponibilité avec `minAvailable: 1`
- Protection contre les interruptions non planifiées

## 7. Gestion Sécurisée des Secrets Kubernetes

### Secrets Manuels (Développement)
```yaml
secrets:
  manual:
    database:
      enabled: true
      username: "app_user"
      password: "secure_password"
```

### External Secrets Operator (Production)
```yaml
secrets:
  externalSecrets:
    enabled: true
    secretStore:
      name: "vault-backend"
      kind: "SecretStore"
```

### Bonnes Pratiques
- Chiffrement au repos avec etcd
- Rotation automatique des secrets
- Accès basé sur les rôles (RBAC)
- Audit des accès aux secrets

## 8. Monitoring et Alerting de Sécurité

### Métriques de Sécurité
- Nombre de vulnérabilités détectées
- Temps de résolution des failles
- Échecs d'authentification
- Tentatives d'accès non autorisées

### Alertes Configurées
- Vulnérabilités critiques détectées
- Échecs de scan de sécurité
- Modifications non autorisées
- Accès suspects aux secrets

## 9. Conformité et Audit

### Traçabilité
- Logs de tous les accès aux secrets
- Historique des scans de sécurité
- Audit trail des déploiements
- Versioning des configurations de sécurité

### Rapports de Conformité
- Rapports automatiques de vulnérabilités
- Dashboard de sécurité en temps réel
- Métriques de conformité aux standards
- Documentation des exceptions de sécurité

## 10. Procédures d'Incident

### Réponse aux Vulnérabilités
1. Détection automatique par les scans
2. Notification immédiate de l'équipe
3. Évaluation de l'impact et de la criticité
4. Correction et test de la solution
5. Déploiement d'urgence si nécessaire
6. Post-mortem et amélioration des processus

### Compromission de Secrets
1. Révocation immédiate des tokens
2. Rotation de tous les secrets associés
3. Analyse des logs d'accès
4. Notification des parties prenantes
5. Renforcement des mesures préventives

## 11. Formation et Sensibilisation

### Bonnes Pratiques Développeurs
- Ne jamais committer de secrets dans le code
- Utiliser des outils de pre-commit hooks
- Révision de code axée sur la sécurité
- Formation régulière aux menaces de sécurité

### Outils Recommandés
- `git-secrets`: Prévention des commits de secrets
- `pre-commit`: Hooks de validation avant commit
- `gitleaks`: Détection de secrets dans l'historique Git
- `semgrep`: Analyse de sécurité avancée

## 12. Maintenance et Mise à Jour

### Mise à Jour Régulière
- Images de base mises à jour mensuellement
- Dépendances Python mises à jour hebdomadairement
- Outils de sécurité mis à jour automatiquement
- Révision trimestrielle des configurations

### Tests de Sécurité
- Tests de pénétration semestriels
- Audit de sécurité annuel
- Validation continue des configurations
- Tests de récupération après incident