#!/usr/bin/env python3
"""
Script de tests end-to-end pour l'API Flask
Valide tous les endpoints et scénarios d'utilisation
"""

import os
import sys
import time
import json
import requests
from typing import Dict, Any, List, Tuple


class E2ETestRunner:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:5000")
        self.session = requests.Session()
        self.test_results = []

    def wait_for_api(self, max_retries: int = 30, delay: int = 2) -> bool:
        """Attendre que l'API soit disponible"""
        print(f"🔄 Attente de l'API sur {self.base_url}...")

        for attempt in range(max_retries):
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ API disponible après {attempt + 1} tentatives")
                    return True
            except requests.exceptions.RequestException:
                pass

            if attempt < max_retries - 1:
                print(f"⏳ Tentative {attempt + 1}/{max_retries}, nouvelle tentative dans {delay}s...")
                time.sleep(delay)

        print(f"❌ API non disponible après {max_retries} tentatives")
        return False

    def run_test(self, test_name: str, test_func) -> bool:
        """Exécuter un test et enregistrer le résultat"""
        print(f"\n🧪 Test: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name} - RÉUSSI")
            self.test_results.append({"name": test_name, "status": "PASS", "error": None})
            return True
        except Exception as e:
            print(f"❌ {test_name} - ÉCHEC: {str(e)}")
            self.test_results.append({"name": test_name, "status": "FAIL", "error": str(e)})
            return False

    def test_health_endpoint(self):
        """Test de l'endpoint /health"""
        response = self.session.get(f"{self.base_url}/health")
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert "status" in data, "Champ 'status' manquant dans la réponse"
        assert data["status"] == "healthy", f"Status attendu: 'healthy', reçu: {data['status']}"
        assert "timestamp" in data, "Champ 'timestamp' manquant dans la réponse"
        assert "version" in data, "Champ 'version' manquant dans la réponse"

    def test_hello_endpoint(self):
        """Test de l'endpoint /api/hello"""
        response = self.session.get(f"{self.base_url}/api/hello")
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert "message" in data, "Champ 'message' manquant dans la réponse"
        assert "version" in data, "Champ 'version' manquant dans la réponse"
        assert data["message"] == "Hello World!", f"Message attendu: 'Hello World!', reçu: {data['message']}"

    def test_calculator_add(self):
        """Test de l'endpoint /api/calculate - addition"""
        payload = {"operation": "add", "a": 5, "b": 3}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert "result" in data, "Champ 'result' manquant dans la réponse"
        assert data["result"] == 8, f"Résultat attendu: 8, reçu: {data['result']}"
        assert data["operation"] == "add", f"Opération attendue: 'add', reçue: {data['operation']}"

    def test_calculator_subtract(self):
        """Test de l'endpoint /api/calculate - soustraction"""
        payload = {"operation": "subtract", "a": 10, "b": 4}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert data["result"] == 6, f"Résultat attendu: 6, reçu: {data['result']}"
        assert data["operation"] == "subtract", f"Opération attendue: 'subtract', reçue: {data['operation']}"

    def test_calculator_multiply(self):
        """Test de l'endpoint /api/calculate - multiplication"""
        payload = {"operation": "multiply", "a": 7, "b": 6}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert data["result"] == 42, f"Résultat attendu: 42, reçu: {data['result']}"
        assert data["operation"] == "multiply", f"Opération attendue: 'multiply', reçue: {data['operation']}"

    def test_calculator_divide(self):
        """Test de l'endpoint /api/calculate - division"""
        payload = {"operation": "divide", "a": 15, "b": 3}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 200, f"Status code attendu: 200, reçu: {response.status_code}"

        data = response.json()
        assert data["result"] == 5, f"Résultat attendu: 5, reçu: {data['result']}"
        assert data["operation"] == "divide", f"Opération attendue: 'divide', reçue: {data['operation']}"

    def test_calculator_divide_by_zero(self):
        """Test de l'endpoint /api/calculate - division par zéro"""
        payload = {"operation": "divide", "a": 10, "b": 0}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 400, f"Status code attendu: 400, reçu: {response.status_code}"

        data = response.json()
        assert "error" in data, "Champ 'error' manquant dans la réponse d'erreur"

    def test_calculator_invalid_operation(self):
        """Test de l'endpoint /api/calculate - opération invalide"""
        payload = {"operation": "invalid", "a": 5, "b": 3}
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 400, f"Status code attendu: 400, reçu: {response.status_code}"

        data = response.json()
        assert "error" in data, "Champ 'error' manquant dans la réponse d'erreur"

    def test_calculator_missing_parameters(self):
        """Test de l'endpoint /api/calculate - paramètres manquants"""
        payload = {"operation": "add", "a": 5}  # 'b' manquant
        response = self.session.post(f"{self.base_url}/api/calculate", json=payload)
        assert response.status_code == 400, f"Status code attendu: 400, reçu: {response.status_code}"

        data = response.json()
        assert "error" in data, "Champ 'error' manquant dans la réponse d'erreur"

    def test_nonexistent_endpoint(self):
        """Test d'un endpoint inexistant"""
        response = self.session.get(f"{self.base_url}/api/nonexistent")
        assert response.status_code == 404, f"Status code attendu: 404, reçu: {response.status_code}"

    def run_all_tests(self) -> bool:
        """Exécuter tous les tests"""
        print("🚀 Démarrage des tests end-to-end")
        print(f"🎯 URL de base: {self.base_url}")

        # Attendre que l'API soit disponible
        if not self.wait_for_api():
            return False

        # Liste des tests à exécuter
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Hello Endpoint", self.test_hello_endpoint),
            ("Calculator Add", self.test_calculator_add),
            ("Calculator Subtract", self.test_calculator_subtract),
            ("Calculator Multiply", self.test_calculator_multiply),
            ("Calculator Divide", self.test_calculator_divide),
            ("Calculator Divide by Zero", self.test_calculator_divide_by_zero),
            ("Calculator Invalid Operation", self.test_calculator_invalid_operation),
            ("Calculator Missing Parameters", self.test_calculator_missing_parameters),
            ("Nonexistent Endpoint", self.test_nonexistent_endpoint),
        ]

        # Exécuter tous les tests
        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1

        # Afficher le résumé
        print(f"\n📊 Résumé des tests:")
        print(f"✅ Tests réussis: {passed}/{total}")
        print(f"❌ Tests échoués: {total - passed}/{total}")

        if passed == total:
            print("🎉 Tous les tests sont passés avec succès!")
            return True
        else:
            print("💥 Certains tests ont échoué")
            return False

    def generate_report(self, output_file: str = "/tmp/e2e_test_report.json"):
        """Générer un rapport de test en JSON"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["status"] == "PASS"]),
            "failed_tests": len([r for r in self.test_results if r["status"] == "FAIL"]),
            "results": self.test_results,
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Rapport généré: {output_file}")


def main():
    """Fonction principale"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:5000")

    runner = E2ETestRunner(base_url)
    success = runner.run_all_tests()
    runner.generate_report()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
