"""
Tests pour l'endpoint de métriques Prometheus
"""

import pytest
from app.main import create_app


class TestMetricsEndpoint:
    """Tests pour l'endpoint /metrics"""

    @pytest.fixture
    def app(self):
        """Créer une instance de l'application pour les tests"""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Créer un client de test"""
        return app.test_client()

    def test_metrics_endpoint_success(self, client):
        """Test que l'endpoint /metrics retourne un statut 200"""
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Test que l'endpoint /metrics retourne le bon content-type"""
        response = client.get('/metrics')
        assert 'text/plain' in response.content_type

    def test_metrics_contains_prometheus_metrics(self, client):
        """Test que l'endpoint /metrics contient des métriques Prometheus"""
        response = client.get('/metrics')
        data = response.get_data(as_text=True)
        
        # Vérifier la présence de métriques de base
        assert 'flask_requests_total' in data
        assert 'flask_request_duration_seconds' in data
        assert 'system_cpu_usage_percent' in data
        assert 'system_memory_usage_percent' in data
        assert 'flask_app_info' in data

    def test_metrics_format(self, client):
        """Test que les métriques sont au format Prometheus"""
        response = client.get('/metrics')
        data = response.get_data(as_text=True)
        
        # Vérifier le format des métriques
        lines = data.strip().split('\n')
        metric_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        
        # Au moins quelques métriques doivent être présentes
        assert len(metric_lines) > 0
        
        # Vérifier le format de base (nom_métrique valeur)
        for line in metric_lines[:5]:  # Vérifier les 5 premières
            if line.strip():
                parts = line.split()
                assert len(parts) >= 2  # Au minimum nom et valeur

    def test_metrics_after_request(self, client):
        """Test que les métriques sont mises à jour après une requête"""
        # Faire une requête sur un autre endpoint
        client.get('/health')
        
        # Vérifier que les métriques incluent cette requête
        response = client.get('/metrics')
        data = response.get_data(as_text=True)
        
        # Vérifier que les compteurs de requêtes sont présents
        assert 'flask_requests_total' in data
        assert 'method="GET"' in data

    def test_metrics_method_not_allowed(self, client):
        """Test que seul GET est autorisé sur /metrics"""
        response = client.post('/metrics')
        assert response.status_code == 405

    def test_metrics_system_info(self, client):
        """Test que les informations système sont incluses"""
        response = client.get('/metrics')
        data = response.get_data(as_text=True)
        
        # Vérifier la présence d'informations système
        assert 'system_cpu_usage_percent' in data
        assert 'system_memory_usage_percent' in data
        assert 'system_disk_usage_percent' in data

    def test_metrics_app_info(self, client):
        """Test que les informations d'application sont incluses"""
        response = client.get('/metrics')
        data = response.get_data(as_text=True)
        
        # Vérifier la présence d'informations d'application
        assert 'flask_app_info' in data
        assert 'version=' in data
        assert 'python_version=' in data