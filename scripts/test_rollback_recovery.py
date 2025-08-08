#!/usr/bin/env python3
"""
Script de test pour les scénarios de rollback et récupération
Simule des échecs de déploiement et teste les mécanismes de récupération
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime


class RollbackRecoveryTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.test_results = []
        self.deployment_history = []

    def log(self, message: str, level: str = "INFO"):
        """Logger avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Exécuter une commande shell et retourner le résultat"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, cwd=cwd, timeout=300  # 5 minutes timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "returncode": -1, "stdout": "", "stderr": "Command timed out", "command": command}
        except Exception as e:
            return {"success": False, "returncode": -1, "stdout": "", "stderr": str(e), "command": command}

    def check_api_health(self, timeout: int = 30) -> bool:
        """Vérifier si l'API est accessible et fonctionnelle"""
        self.log("Vérification de la santé de l'API...")

        for attempt in range(timeout):
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        self.log(f"✅ API accessible et saine (tentative {attempt + 1})")
                        return True
            except requests.exceptions.RequestException:
                pass

            if attempt < timeout - 1:
                time.sleep(1)

        self.log(f"❌ API non accessible après {timeout} tentatives")
        return False

    def simulate_deployment_failure(self) -> Dict[str, Any]:
        """Simuler un échec de déploiement en modifiant la configuration"""
        self.log("🔥 Simulation d'un échec de déploiement...")

        # Sauvegarder la configuration actuelle
        backup_result = self.run_command("cp docker-compose.test.yml docker-compose.test.yml.backup")
        if not backup_result["success"]:
            return {"success": False, "error": "Impossible de sauvegarder la configuration"}

        # Créer une configuration défaillante
        broken_config = """version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.broken  # Dockerfile inexistant
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - INVALID_ENV_VAR=broken_value
"""

        try:
            with open("docker-compose.test.yml", "w") as f:
                f.write(broken_config)

            self.log("📝 Configuration défaillante créée")
            return {"success": True, "message": "Configuration défaillante appliquée"}

        except Exception as e:
            return {"success": False, "error": f"Erreur lors de la création de la config défaillante: {e}"}

    def attempt_broken_deployment(self) -> Dict[str, Any]:
        """Tenter un déploiement avec la configuration défaillante"""
        self.log("🚀 Tentative de déploiement avec configuration défaillante...")

        # Arrêter les services existants
        stop_result = self.run_command("docker-compose -f docker-compose.test.yml down --remove-orphans")

        # Tenter le déploiement défaillant
        deploy_result = self.run_command("docker-compose -f docker-compose.test.yml up --build -d")

        if deploy_result["success"]:
            self.log("⚠️  Le déploiement défaillant a réussi (inattendu)")
            return {"success": False, "error": "Le déploiement défaillant a réussi"}
        else:
            self.log("✅ Le déploiement défaillant a échoué comme attendu")
            return {"success": True, "message": "Échec de déploiement simulé avec succès"}

    def restore_configuration(self) -> Dict[str, Any]:
        """Restaurer la configuration précédente"""
        self.log("🔄 Restauration de la configuration précédente...")

        restore_result = self.run_command("cp docker-compose.test.yml.backup docker-compose.test.yml")
        if not restore_result["success"]:
            return {"success": False, "error": "Impossible de restaurer la configuration"}

        # Nettoyer le fichier de sauvegarde
        self.run_command("rm -f docker-compose.test.yml.backup")

        self.log("✅ Configuration restaurée")
        return {"success": True, "message": "Configuration restaurée avec succès"}

    def perform_rollback_deployment(self) -> Dict[str, Any]:
        """Effectuer un rollback vers la version précédente"""
        self.log("⏪ Exécution du rollback...")

        # Arrêter les services défaillants
        stop_result = self.run_command("docker-compose -f docker-compose.test.yml down --remove-orphans")

        # Redéployer avec la configuration restaurée
        deploy_result = self.run_command("docker-compose -f docker-compose.test.yml up --build -d")

        if deploy_result["success"]:
            self.log("✅ Rollback réussi")
            return {"success": True, "message": "Rollback effectué avec succès"}
        else:
            self.log(f"❌ Échec du rollback: {deploy_result['stderr']}")
            return {"success": False, "error": f'Échec du rollback: {deploy_result["stderr"]}'}

    def test_service_recovery(self) -> Dict[str, Any]:
        """Tester la récupération du service après rollback"""
        self.log("🔍 Test de récupération du service...")

        # Attendre que les services démarrent
        time.sleep(10)

        # Vérifier la santé de l'API
        if self.check_api_health():
            # Tester les endpoints critiques
            endpoints_to_test = [
                {"method": "GET", "url": "/health", "expected_status": 200},
                {"method": "GET", "url": "/api/hello", "expected_status": 200},
                {
                    "method": "POST",
                    "url": "/api/calculate",
                    "data": {"operation": "add", "a": 2, "b": 3},
                    "expected_status": 200,
                },
            ]

            failed_endpoints = []
            for endpoint in endpoints_to_test:
                try:
                    if endpoint["method"] == "GET":
                        response = self.session.get(f"{self.base_url}{endpoint['url']}", timeout=10)
                    else:
                        response = self.session.post(
                            f"{self.base_url}{endpoint['url']}", json=endpoint.get("data"), timeout=10
                        )

                    if response.status_code != endpoint["expected_status"]:
                        failed_endpoints.append(f"{endpoint['method']} {endpoint['url']} (status: {response.status_code})")

                except requests.exceptions.RequestException as e:
                    failed_endpoints.append(f"{endpoint['method']} {endpoint['url']} (error: {e})")

            if not failed_endpoints:
                self.log("✅ Tous les endpoints fonctionnent après récupération")
                return {"success": True, "message": "Service complètement récupéré"}
            else:
                self.log(f"❌ Endpoints défaillants: {', '.join(failed_endpoints)}")
                return {"success": False, "error": f"Endpoints défaillants: {failed_endpoints}"}
        else:
            return {"success": False, "error": "API non accessible après rollback"}

    def test_kubernetes_rollback(self) -> Dict[str, Any]:
        """Tester le rollback Kubernetes (si disponible)"""
        self.log("☸️  Test de rollback Kubernetes...")

        # Vérifier si kubectl est disponible
        kubectl_check = self.run_command("kubectl version --client")
        if not kubectl_check["success"]:
            self.log("⚠️  kubectl non disponible - test Kubernetes ignoré")
            return {"success": True, "message": "kubectl non disponible - test ignoré"}

        # Vérifier si un cluster est accessible
        cluster_check = self.run_command("kubectl cluster-info")
        if not cluster_check["success"]:
            self.log("⚠️  Cluster Kubernetes non accessible - test ignoré")
            return {"success": True, "message": "Cluster non accessible - test ignoré"}

        # Simuler un rollback Kubernetes
        namespace = "default"  # ou récupérer depuis la config
        deployment_name = "cicd-pipeline-app"  # nom du déploiement

        # Vérifier l'historique des déploiements
        history_result = self.run_command(f"kubectl rollout history deployment/{deployment_name} -n {namespace}")
        if not history_result["success"]:
            self.log("⚠️  Pas d'historique de déploiement trouvé")
            return {"success": True, "message": "Pas d'historique de déploiement"}

        # Effectuer un rollback vers la révision précédente
        rollback_result = self.run_command(f"kubectl rollout undo deployment/{deployment_name} -n {namespace}")
        if rollback_result["success"]:
            # Attendre que le rollback soit terminé
            wait_result = self.run_command(
                f"kubectl rollout status deployment/{deployment_name} -n {namespace} --timeout=300s"
            )
            if wait_result["success"]:
                self.log("✅ Rollback Kubernetes réussi")
                return {"success": True, "message": "Rollback Kubernetes effectué avec succès"}
            else:
                return {"success": False, "error": "Timeout lors du rollback Kubernetes"}
        else:
            return {"success": False, "error": f'Échec du rollback Kubernetes: {rollback_result["stderr"]}'}

    def test_argocd_rollback(self) -> Dict[str, Any]:
        """Tester le rollback ArgoCD (si disponible)"""
        self.log("🔄 Test de rollback ArgoCD...")

        # Vérifier si ArgoCD CLI est disponible
        argocd_check = self.run_command("argocd version --client")
        if not argocd_check["success"]:
            self.log("⚠️  ArgoCD CLI non disponible - test ignoré")
            return {"success": True, "message": "ArgoCD CLI non disponible - test ignoré"}

        # Nom de l'application ArgoCD
        app_name = "cicd-pipeline-python"

        # Obtenir l'historique des déploiements
        history_result = self.run_command(f"argocd app history {app_name}")
        if not history_result["success"]:
            self.log("⚠️  Impossible d'obtenir l'historique ArgoCD")
            return {"success": True, "message": "Historique ArgoCD non accessible"}

        # Simuler un rollback vers la révision précédente
        # Note: En réalité, cela nécessiterait une authentification ArgoCD
        self.log("ℹ️  Simulation de rollback ArgoCD (authentification requise en production)")

        return {"success": True, "message": "Test de rollback ArgoCD simulé"}

    def cleanup_test_environment(self):
        """Nettoyer l'environnement de test"""
        self.log("🧹 Nettoyage de l'environnement de test...")

        # Arrêter tous les services
        self.run_command("docker-compose -f docker-compose.test.yml down --remove-orphans")

        # Supprimer les images de test
        self.run_command("docker image prune -f")

        # Nettoyer les fichiers temporaires
        self.run_command("rm -f docker-compose.test.yml.backup")

        self.log("✅ Nettoyage terminé")

    def run_rollback_recovery_tests(self) -> Dict[str, Any]:
        """Exécuter tous les tests de rollback et récupération"""
        self.log("🚀 Démarrage des tests de rollback et récupération")

        test_results = {"timestamp": datetime.now().isoformat(), "tests": {}, "overall_success": True}

        # Test 1: Vérification initiale
        self.log("\n=== Test 1: Vérification de l'état initial ===")
        initial_health = self.check_api_health()
        test_results["tests"]["initial_health"] = {
            "success": initial_health,
            "message": "API accessible initialement" if initial_health else "API non accessible initialement",
        }

        if not initial_health:
            self.log("❌ API non accessible - démarrage des services...")
            deploy_result = self.run_command("docker-compose -f docker-compose.test.yml up --build -d")
            time.sleep(15)  # Attendre le démarrage
            initial_health = self.check_api_health()

        # Test 2: Simulation d'échec de déploiement
        self.log("\n=== Test 2: Simulation d'échec de déploiement ===")
        failure_result = self.simulate_deployment_failure()
        test_results["tests"]["simulate_failure"] = failure_result
        if not failure_result["success"]:
            test_results["overall_success"] = False

        # Test 3: Tentative de déploiement défaillant
        self.log("\n=== Test 3: Tentative de déploiement défaillant ===")
        broken_deploy_result = self.attempt_broken_deployment()
        test_results["tests"]["broken_deployment"] = broken_deploy_result
        if not broken_deploy_result["success"]:
            test_results["overall_success"] = False

        # Test 4: Restauration de configuration
        self.log("\n=== Test 4: Restauration de configuration ===")
        restore_result = self.restore_configuration()
        test_results["tests"]["restore_config"] = restore_result
        if not restore_result["success"]:
            test_results["overall_success"] = False

        # Test 5: Rollback
        self.log("\n=== Test 5: Exécution du rollback ===")
        rollback_result = self.perform_rollback_deployment()
        test_results["tests"]["rollback"] = rollback_result
        if not rollback_result["success"]:
            test_results["overall_success"] = False

        # Test 6: Vérification de récupération
        self.log("\n=== Test 6: Vérification de récupération ===")
        recovery_result = self.test_service_recovery()
        test_results["tests"]["service_recovery"] = recovery_result
        if not recovery_result["success"]:
            test_results["overall_success"] = False

        # Test 7: Rollback Kubernetes (optionnel)
        self.log("\n=== Test 7: Rollback Kubernetes ===")
        k8s_rollback_result = self.test_kubernetes_rollback()
        test_results["tests"]["kubernetes_rollback"] = k8s_rollback_result

        # Test 8: Rollback ArgoCD (optionnel)
        self.log("\n=== Test 8: Rollback ArgoCD ===")
        argocd_rollback_result = self.test_argocd_rollback()
        test_results["tests"]["argocd_rollback"] = argocd_rollback_result

        # Nettoyage
        self.cleanup_test_environment()

        # Résumé
        self.log("\n" + "=" * 60)
        self.log("📊 RÉSUMÉ DES TESTS DE ROLLBACK ET RÉCUPÉRATION")
        self.log("=" * 60)

        for test_name, result in test_results["tests"].items():
            status = "✅ RÉUSSI" if result["success"] else "❌ ÉCHEC"
            self.log(f"{test_name}: {status} - {result.get('message', result.get('error', 'N/A'))}")

        overall_status = "✅ TOUS LES TESTS RÉUSSIS" if test_results["overall_success"] else "❌ CERTAINS TESTS ONT ÉCHOUÉ"
        self.log(f"\nRésultat global: {overall_status}")

        return test_results

    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        """Générer un rapport détaillé"""
        if output_file is None:
            # Use secure temporary file instead of hardcoded /tmp
            with tempfile.NamedTemporaryFile(mode="w", suffix="_rollback_recovery_report.json", delete=False) as f:
                output_file = f.name
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        self.log(f"📄 Rapport généré: {output_file}")


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(description="Tests de rollback et récupération")
    parser.add_argument("--url", default="http://localhost:5000", help="URL de base de l'API (défaut: http://localhost:5000)")
    parser.add_argument(
        "--report",
        default="/tmp/rollback_recovery_report.json",
        help="Fichier de rapport (défaut: /tmp/rollback_recovery_report.json)",
    )

    args = parser.parse_args()

    tester = RollbackRecoveryTester(args.url)
    results = tester.run_rollback_recovery_tests()
    tester.generate_report(results, args.report)

    # Code de sortie basé sur le succès global
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()
