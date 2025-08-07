# Scripts de Test et Validation End-to-End

Ce répertoire contient tous les scripts nécessaires pour tester et valider le pipeline CI/CD complet, depuis les tests locaux jusqu'aux scénarios de rollback et récupération.

## 📋 Vue d'ensemble des scripts

### 🧪 `run_e2e_tests.py`
Script principal de tests end-to-end qui valide tous les endpoints de l'API.

**Fonctionnalités :**
- Tests de tous les endpoints (`/health`, `/api/hello`, `/api/calculate`)
- Validation des cas d'erreur (division par zéro, opérations invalides)
- Tests de performance basiques
- Génération de rapports JSON
- Support pour environnements Docker et déploiements distants

**Usage :**
```bash
# Test local
python scripts/run_e2e_tests.py

# Test avec URL personnalisée
API_BASE_URL=http://your-api.com python scripts/run_e2e_tests.py

# Avec Docker Compose
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 🔍 `validate_pipeline.sh`
Script de validation complète du pipeline CI/CD qui vérifie tous les composants.

**Validations effectuées :**
- Structure du projet et fichiers requis
- Construction des images Docker
- Syntaxe des workflows GitHub Actions
- Validation des Helm charts
- Configuration ArgoCD
- Scripts de sécurité
- Tests end-to-end complets

**Usage :**
```bash
# Validation complète
./scripts/validate_pipeline.sh

# Les logs sont sauvegardés dans /tmp/pipeline_validation_*.log
```

### 🔄 `test_rollback_recovery.py`
Script de test des scénarios de rollback et récupération en cas d'échec de déploiement.

**Scénarios testés :**
- Simulation d'échec de déploiement
- Mécanismes de rollback automatique
- Récupération des services
- Tests de rollback Kubernetes (si disponible)
- Tests de rollback ArgoCD (si disponible)
- Validation post-rollback

**Usage :**
```bash
# Tests de rollback complets
python scripts/test_rollback_recovery.py

# Avec URL personnalisée
python scripts/test_rollback_recovery.py --url http://your-api.com

# Avec rapport personnalisé
python scripts/test_rollback_recovery.py --report /path/to/report.json
```

## 🚀 Utilisation rapide

### Tests locaux avec Docker Compose

1. **Démarrer les tests end-to-end :**
```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

2. **Validation complète du pipeline :**
```bash
./scripts/validate_pipeline.sh
```

3. **Tests de rollback :**
```bash
python scripts/test_rollback_recovery.py
```

### Tests manuels des endpoints

Le fichier `test_endpoints.py` à la racine du projet permet de tester manuellement tous les endpoints :

```bash
# Tests complets
python test_endpoints.py

# Test d'un endpoint spécifique
python test_endpoints.py --endpoint health
python test_endpoints.py --endpoint calculator

# Test de performance
python test_endpoints.py --endpoint performance --performance-requests 50

# Avec URL personnalisée
python test_endpoints.py --url http://your-api.com
```

## 📊 Rapports et logs

### Rapports générés

1. **Tests E2E :** `/tmp/e2e_test_report.json`
2. **Validation pipeline :** `/tmp/pipeline_validation_report_*.json`
3. **Tests rollback :** `/tmp/rollback_recovery_report.json`

### Logs

- **Validation pipeline :** `/tmp/pipeline_validation_*.log`
- **Tous les scripts :** Sortie console avec timestamps

### Format des rapports JSON

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_tests": 10,
  "passed_tests": 9,
  "failed_tests": 1,
  "results": [
    {
      "name": "Health Endpoint",
      "status": "PASS",
      "error": null
    }
  ]
}
```

## 🔧 Configuration

### Variables d'environnement

- `API_BASE_URL` : URL de base de l'API (défaut: `http://localhost:5000`)
- `PYTHONPATH` : Chemin Python pour les imports

### Prérequis

**Outils requis :**
- Python 3.11+
- Docker et Docker Compose
- Bash
- `requests`, `pytest` (installés automatiquement)

**Outils optionnels :**
- `kubectl` (pour tests Kubernetes)
- `helm` (pour validation des charts)
- `argocd` CLI (pour tests ArgoCD)

## 🧪 Scénarios de test couverts

### Tests fonctionnels
- ✅ Endpoint de santé (`/health`)
- ✅ Endpoint de bienvenue (`/api/hello`)
- ✅ Calculatrice - toutes opérations (`/api/calculate`)
- ✅ Gestion des erreurs (400, 404, 500)
- ✅ Validation des paramètres d'entrée

### Tests de performance
- ✅ Temps de réponse des endpoints
- ✅ Tests de charge basiques
- ✅ Statistiques de performance

### Tests d'intégration
- ✅ Construction Docker
- ✅ Déploiement avec Docker Compose
- ✅ Communication entre services
- ✅ Health checks

### Tests de rollback
- ✅ Simulation d'échec de déploiement
- ✅ Mécanismes de rollback
- ✅ Récupération automatique
- ✅ Validation post-rollback
- ✅ Tests Kubernetes (si disponible)
- ✅ Tests ArgoCD (si disponible)

## 🚨 Dépannage

### Problèmes courants

1. **API non accessible :**
```bash
# Vérifier que l'application est démarrée
docker-compose -f docker-compose.test.yml ps

# Vérifier les logs
docker-compose -f docker-compose.test.yml logs app
```

2. **Tests qui échouent :**
```bash
# Vérifier les logs détaillés
cat /tmp/pipeline_validation_*.log

# Tester manuellement un endpoint
curl -X GET http://localhost:5000/health
```

3. **Problèmes Docker :**
```bash
# Nettoyer les containers
docker-compose -f docker-compose.test.yml down --remove-orphans

# Reconstruire les images
docker-compose -f docker-compose.test.yml build --no-cache
```

### Codes de sortie

- `0` : Tous les tests réussis
- `1` : Certains tests ont échoué
- `2` : Erreur de configuration ou prérequis manquants

## 📚 Exemples d'utilisation

### Intégration dans CI/CD

```yaml
# GitHub Actions
- name: Run E2E Tests
  run: |
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    
- name: Validate Pipeline
  run: |
    ./scripts/validate_pipeline.sh
    
- name: Test Rollback Scenarios
  run: |
    python scripts/test_rollback_recovery.py
```

### Tests en local

```bash
# Workflow complet de test
./scripts/validate_pipeline.sh && \
python scripts/run_e2e_tests.py && \
python scripts/test_rollback_recovery.py
```

### Monitoring continu

```bash
# Script de monitoring (à exécuter périodiquement)
while true; do
  python test_endpoints.py --endpoint health
  sleep 30
done
```

## 🔗 Liens utiles

- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [Guide des tests Python](https://docs.python.org/3/library/unittest.html)
- [Documentation Kubernetes](https://kubernetes.io/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)

---

**Note :** Ces scripts sont conçus pour être utilisés dans le cadre du pipeline CI/CD Python. Ils peuvent être adaptés pour d'autres projets en modifiant les URLs et configurations appropriées.