# Guide de Mise en Place Étape par Étape

Ce guide vous accompagne dans la mise en place complète du pipeline CI/CD Python avec GitHub Actions, ArgoCD et Kubernetes.

## Prérequis

### 1. Outils à Installer

#### Docker et Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Kubernetes (kubectl)
```bash
# Installer kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Vérifier l'installation
kubectl version --client
```

#### Helm
```bash
# Installer Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Vérifier l'installation
helm version
```

#### Cluster Kubernetes Local (Minikube)
```bash
# Installer minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Démarrer minikube
minikube start --driver=docker --memory=4096 --cpus=2

# Vérifier le cluster
kubectl get nodes
```

### 2. Comptes et Permissions

#### GitHub
- Compte GitHub avec accès aux Actions et Packages
- Permissions pour créer des repositories
- Accès au GitHub Container Registry

#### Cluster Kubernetes
- Accès administrateur au cluster
- Possibilité d'installer des applications (ArgoCD)

## Étape 1 : Configuration du Repository Principal

### 1.1 Cloner le Repository
```bash
git clone https://github.com/votre-username/python-cicd-pipeline.git
cd python-cicd-pipeline
```

### 1.2 Tester l'Application Localement
```bash
# Créer un environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer les tests
pytest tests/ -v --cov=app

# Tester l'application
python app/main.py &
curl http://localhost:5000/health
curl http://localhost:5000/api/hello
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"operation": "add", "a": 5, "b": 3}'

# Arrêter l'application
pkill -f "python app/main.py"
```

### 1.3 Tester le Build Docker
```bash
# Construire l'image
docker build -t python-cicd-app .

# Tester l'image
docker run -d -p 5000:5000 --name test-app python-cicd-app

# Tester les endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/hello

# Nettoyer
docker stop test-app
docker rm test-app
```

## Étape 2 : Configuration du Repository GitOps

### 2.1 Créer le Repository GitOps
```bash
# Créer un nouveau repository sur GitHub
# Nom suggéré : python-cicd-pipeline-gitops

# Cloner le nouveau repository
git clone https://github.com/votre-username/python-cicd-pipeline-gitops.git
cd python-cicd-pipeline-gitops
```

### 2.2 Copier la Configuration Helm
```bash
# Copier le chart Helm depuis le repository principal
cp -r ../python-cicd-pipeline/gitops-example/helm-chart .

# Mettre à jour values.yaml avec votre repository
sed -i 's|ghcr.io/your-username/your-repo-name|ghcr.io/votre-username/python-cicd-pipeline|g' helm-chart/values.yaml

# Committer les changements
git add .
git commit -m "Initial Helm chart setup"
git push origin main
```

### 2.3 Valider le Chart Helm
```bash
# Valider la syntaxe du chart
helm lint helm-chart/

# Générer les manifestes pour vérification
helm template python-cicd-app helm-chart/ --values helm-chart/values.yaml
```

## Étape 3 : Configuration des Secrets GitHub

### 3.1 Créer un Personal Access Token
1. Aller sur GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Cliquer "Generate new token (classic)"
3. Nom : `GitOps-Pipeline-Token`
4. Expiration : 90 jours
5. Sélectionner les scopes :
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
6. Générer et copier le token

### 3.2 Configurer les Secrets du Repository
1. Aller dans le repository principal → Settings → Secrets and variables → Actions
2. Cliquer "New repository secret"
3. Ajouter les secrets suivants :

```
Nom: GITOPS_TOKEN
Valeur: [le token créé à l'étape 3.1]

Nom: GITHUB_TOKEN
Valeur: [automatiquement fourni par GitHub]
```

### 3.3 Vérifier la Configuration
```bash
# Dans le repository principal, vérifier les workflows
cat .github/workflows/test-and-merge.yml
cat .github/workflows/build-and-deploy.yml

# Mettre à jour le nom du repository GitOps si nécessaire
sed -i 's/python-cicd-demo-gitops/python-cicd-pipeline-gitops/g' .github/workflows/build-and-deploy.yml
```

## Étape 4 : Installation et Configuration d'ArgoCD

### 4.1 Installation Automatique
```bash
cd argocd
./setup-argocd.sh
```

### 4.2 Installation Manuelle (Alternative)
```bash
# Créer le namespace ArgoCD
kubectl create namespace argocd

# Installer ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendre que tous les pods soient prêts
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Appliquer les configurations personnalisées
kubectl apply -f project.yaml
kubectl apply -f argocd-config.yaml
kubectl apply -f application.yaml
```

### 4.3 Accéder à l'Interface ArgoCD
```bash
# Port forward vers ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Récupérer le mot de passe admin
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Ouvrir https://localhost:8080
# Username: admin
# Password: [mot de passe récupéré ci-dessus]
```

### 4.4 Installer ArgoCD CLI (Optionnel)
```bash
# Télécharger et installer ArgoCD CLI
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# Se connecter via CLI
argocd login localhost:8080 --username admin --password [mot-de-passe] --insecure
```

## Étape 5 : Configuration de l'Application ArgoCD

### 5.1 Mettre à Jour la Configuration
```bash
# Éditer application.yaml pour pointer vers votre repository GitOps
sed -i 's|https://github.com/your-username/your-repo-gitops.git|https://github.com/votre-username/python-cicd-pipeline-gitops.git|g' application.yaml

# Appliquer la configuration mise à jour
kubectl apply -f application.yaml
```

### 5.2 Vérifier l'Application
```bash
# Vérifier le statut de l'application
kubectl get application python-cicd-app -n argocd

# Via CLI ArgoCD
argocd app get python-cicd-app
```

## Étape 6 : Test du Pipeline Complet

### 6.1 Test du Workflow de Développement
```bash
# Créer une branche de développement
git checkout -b dev

# Faire un changement mineur (par exemple, modifier un message)
echo "# Test change" >> README.md

# Committer et pousser
git add .
git commit -m "Test: minor change for pipeline testing"
git push origin dev
```

### 6.2 Vérifier l'Exécution des Tests
1. Aller sur GitHub → Actions
2. Vérifier que le workflow "Test and Merge" s'exécute
3. Confirmer que les tests passent
4. Vérifier le merge automatique vers main

### 6.3 Vérifier le Build et le Déploiement
1. Vérifier que le workflow "Build and Deploy" s'exécute sur main
2. Confirmer la construction de l'image Docker
3. Vérifier le push vers GitHub Container Registry
4. Confirmer la mise à jour du repository GitOps

### 6.4 Vérifier le Déploiement ArgoCD
```bash
# Vérifier la synchronisation ArgoCD
argocd app sync python-cicd-app

# Vérifier le déploiement Kubernetes
kubectl get pods -l app=python-cicd-app

# Tester l'application déployée
kubectl port-forward svc/python-cicd-app 8080:80 &
curl http://localhost:8080/health
curl http://localhost:8080/api/hello
```

## Étape 7 : Validation et Tests

### 7.1 Tests de Sécurité
```bash
# Scanner l'image Docker pour les vulnérabilités
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasecurity/trivy image ghcr.io/votre-username/python-cicd-pipeline:latest

# Vérifier les rapports de sécurité sur GitHub
# Aller sur GitHub → Security → Code scanning alerts
```

### 7.2 Tests de Performance
```bash
# Test de charge simple avec curl
for i in {1..100}; do
  curl -s http://localhost:8080/health > /dev/null &
done
wait

# Vérifier les métriques des pods
kubectl top pods -l app=python-cicd-app
```

### 7.3 Tests de Rollback
```bash
# Voir l'historique des déploiements
argocd app history python-cicd-app

# Effectuer un rollback vers une version précédente
argocd app rollback python-cicd-app [revision-number]

# Vérifier le rollback
kubectl get pods -l app=python-cicd-app
```

## Étape 8 : Configuration de Production

### 8.1 Optimisation des Ressources
```bash
# Éditer values.yaml pour la production
cat >> helm-chart/values.yaml << EOF

# Configuration production
replicaCount: 3

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
EOF
```

### 8.2 Configuration de Monitoring
```bash
# Ajouter des labels pour Prometheus
kubectl label namespace default monitoring=enabled

# Vérifier les métriques exposées
kubectl port-forward svc/python-cicd-app 8080:80 &
curl http://localhost:8080/metrics
```

## Dépannage

### Problèmes Courants

#### 1. Échec d'Installation d'ArgoCD
```bash
# Vérifier les ressources du cluster
kubectl top nodes
kubectl describe nodes

# Vérifier les logs d'installation
kubectl logs -n argocd deployment/argocd-server
```

#### 2. Problèmes de Permissions GitHub
```bash
# Vérifier les secrets configurés
# GitHub → Repository → Settings → Secrets and variables → Actions

# Tester l'accès au repository GitOps
git clone https://github.com/votre-username/python-cicd-pipeline-gitops.git test-access
```

#### 3. Échecs de Synchronisation ArgoCD
```bash
# Vérifier les logs ArgoCD
kubectl logs -n argocd deployment/argocd-application-controller

# Forcer une synchronisation
argocd app sync python-cicd-app --force
```

#### 4. Problèmes de Réseau Kubernetes
```bash
# Vérifier la connectivité des pods
kubectl exec -it [pod-name] -- curl http://localhost:5000/health

# Vérifier les services
kubectl get svc
kubectl describe svc python-cicd-app
```

## Nettoyage

### Nettoyage Complet
```bash
# Supprimer l'application ArgoCD
argocd app delete python-cicd-app

# Supprimer ArgoCD
kubectl delete namespace argocd

# Supprimer les images Docker locales
docker rmi python-cicd-app
docker system prune -f

# Arrêter minikube (si utilisé)
minikube stop
minikube delete
```

## Prochaines Étapes

Après avoir terminé cette configuration :

1. **Monitoring** : Installer Prometheus et Grafana
2. **Alerting** : Configurer des alertes Slack/email
3. **Sécurité** : Implémenter des politiques de sécurité supplémentaires
4. **Multi-environnements** : Configurer staging et production
5. **Documentation** : Créer des runbooks pour l'équipe opérationnelle

## Support

En cas de problème :
1. Consulter les logs détaillés de chaque composant
2. Vérifier la documentation officielle des outils
3. Utiliser les GitHub Issues pour signaler des bugs
4. Consulter la communauté ArgoCD et Kubernetes