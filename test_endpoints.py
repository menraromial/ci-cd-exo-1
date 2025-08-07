#!/usr/bin/env python3
"""
Script d'exemples de requêtes pour tester tous les endpoints de l'API
Peut être utilisé pour des tests manuels ou automatisés
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional


class APITester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "User-Agent": "API-Tester/1.0"})

    def make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200
    ) -> Dict[str, Any]:
        """Faire une requête et afficher le résultat"""
        url = f"{self.base_url}{endpoint}"

        print(f"\n{'='*60}")
        print(f"🔗 {method.upper()} {url}")

        if data:
            print(f"📤 Données envoyées:")
            print(json.dumps(data, indent=2))

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            print(f"📊 Status Code: {response.status_code}")
            print(f"⏱️  Temps de réponse: {response.elapsed.total_seconds():.3f}s")

            # Afficher les headers importants
            important_headers = ["content-type", "content-length", "server"]
            for header in important_headers:
                if header in response.headers:
                    print(f"📋 {header.title()}: {response.headers[header]}")

            # Afficher le contenu de la réponse
            try:
                response_data = response.json()
                print(f"📥 Réponse JSON:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"📥 Réponse texte:")
                print(response.text)

            # Vérifier le status code attendu
            if response.status_code == expected_status:
                print(f"✅ Status code correct ({expected_status})")
            else:
                print(f"⚠️  Status code inattendu (attendu: {expected_status}, reçu: {response.status_code})")

            return {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response_data if "response_data" in locals() else response.text,
                "headers": dict(response.headers),
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de requête: {e}")
            return {"error": str(e), "status_code": None, "response_time": None, "data": None, "headers": None}

    def test_health_endpoint(self):
        """Tester l'endpoint de santé"""
        print(f"\n🏥 TEST DE L'ENDPOINT DE SANTÉ")
        return self.make_request("GET", "/health")

    def test_hello_endpoint(self):
        """Tester l'endpoint hello"""
        print(f"\n👋 TEST DE L'ENDPOINT HELLO")
        return self.make_request("GET", "/api/hello")

    def test_calculator_operations(self):
        """Tester toutes les opérations de la calculatrice"""
        print(f"\n🧮 TESTS DES OPÉRATIONS DE CALCULATRICE")

        operations = [
            # Opérations valides
            {"operation": "add", "a": 10, "b": 5, "expected": 15, "status": 200},
            {"operation": "subtract", "a": 10, "b": 3, "expected": 7, "status": 200},
            {"operation": "multiply", "a": 4, "b": 7, "expected": 28, "status": 200},
            {"operation": "divide", "a": 20, "b": 4, "expected": 5, "status": 200},
            # Cas avec nombres décimaux
            {"operation": "add", "a": 3.14, "b": 2.86, "expected": 6.0, "status": 200},
            {"operation": "divide", "a": 22, "b": 7, "expected": 3.142857142857143, "status": 200},
            # Cas d'erreur - division par zéro
            {"operation": "divide", "a": 10, "b": 0, "expected": None, "status": 400},
            # Cas d'erreur - opération invalide
            {"operation": "power", "a": 2, "b": 3, "expected": None, "status": 400},
            # Cas d'erreur - paramètres manquants
            {"operation": "add", "a": 5, "expected": None, "status": 400},
        ]

        results = []
        for i, op in enumerate(operations, 1):
            print(f"\n--- Test {i}: {op['operation']} ---")

            # Préparer les données (exclure les champs de test)
            data = {k: v for k, v in op.items() if k not in ["expected", "status"]}

            result = self.make_request("POST", "/api/calculate", data, op["status"])
            results.append(result)

            # Vérifier le résultat si c'est une opération valide
            if op["status"] == 200 and result.get("data") and "result" in result["data"]:
                actual_result = result["data"]["result"]
                expected_result = op["expected"]

                if abs(actual_result - expected_result) < 0.0001:  # Tolérance pour les flottants
                    print(f"✅ Résultat correct: {actual_result}")
                else:
                    print(f"❌ Résultat incorrect: attendu {expected_result}, reçu {actual_result}")

        return results

    def test_error_cases(self):
        """Tester les cas d'erreur"""
        print(f"\n🚨 TESTS DES CAS D'ERREUR")

        error_tests = [
            # Endpoint inexistant
            {"method": "GET", "endpoint": "/api/nonexistent", "status": 404},
            # Méthode HTTP incorrecte
            {"method": "POST", "endpoint": "/health", "status": 405},
            # Données JSON malformées pour calculate
            {"method": "POST", "endpoint": "/api/calculate", "data": {"invalid": "data"}, "status": 400},
        ]

        results = []
        for i, test in enumerate(error_tests, 1):
            print(f"\n--- Test d'erreur {i} ---")
            result = self.make_request(test["method"], test["endpoint"], test.get("data"), test["status"])
            results.append(result)

        return results

    def performance_test(self, num_requests: int = 10):
        """Test de performance basique"""
        print(f"\n⚡ TEST DE PERFORMANCE ({num_requests} requêtes)")

        response_times = []
        successful_requests = 0

        for i in range(num_requests):
            print(f"Requête {i+1}/{num_requests}...", end=" ")
            result = self.make_request("GET", "/health")

            if result.get("response_time"):
                response_times.append(result["response_time"])
                successful_requests += 1
                print(f"✅ {result['response_time']:.3f}s")
            else:
                print("❌ Échec")

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            print(f"\n📊 Statistiques de performance:")
            print(f"   Requêtes réussies: {successful_requests}/{num_requests}")
            print(f"   Temps moyen: {avg_time:.3f}s")
            print(f"   Temps minimum: {min_time:.3f}s")
            print(f"   Temps maximum: {max_time:.3f}s")

            return {
                "successful_requests": successful_requests,
                "total_requests": num_requests,
                "avg_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
            }

        return None

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS COMPLETS DE L'API")
        print(f"🎯 URL de base: {self.base_url}")
        print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Vérifier que l'API est accessible
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ API non accessible (status: {response.status_code})")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Impossible de se connecter à l'API: {e}")
            return False

        print("✅ API accessible, démarrage des tests...")

        # Exécuter tous les tests
        results = {
            "health": self.test_health_endpoint(),
            "hello": self.test_hello_endpoint(),
            "calculator": self.test_calculator_operations(),
            "errors": self.test_error_cases(),
            "performance": self.performance_test(),
        }

        print(f"\n{'='*60}")
        print("🎉 TESTS TERMINÉS")
        print(f"📊 Résumé disponible dans la variable 'results'")

        return results


def main():
    """Fonction principale pour exécution en ligne de commande"""
    import argparse

    parser = argparse.ArgumentParser(description="Tester les endpoints de l'API")
    parser.add_argument("--url", default="http://localhost:5000", help="URL de base de l'API (défaut: http://localhost:5000)")
    parser.add_argument(
        "--endpoint",
        choices=["health", "hello", "calculator", "errors", "performance", "all"],
        default="all",
        help="Endpoint spécifique à tester (défaut: all)",
    )
    parser.add_argument(
        "--performance-requests", type=int, default=10, help="Nombre de requêtes pour le test de performance (défaut: 10)"
    )

    args = parser.parse_args()

    tester = APITester(args.url)

    if args.endpoint == "health":
        tester.test_health_endpoint()
    elif args.endpoint == "hello":
        tester.test_hello_endpoint()
    elif args.endpoint == "calculator":
        tester.test_calculator_operations()
    elif args.endpoint == "errors":
        tester.test_error_cases()
    elif args.endpoint == "performance":
        tester.performance_test(args.performance_requests)
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()
