"""
Tests unitaires pour l'endpoint /health
"""

import pytest
import json
from datetime import datetime


class TestHealthEndpoint:
    """Tests pour l'endpoint de santé"""

    def test_health_endpoint_success(self, client):
        """Test que l'endpoint /health retourne un statut 200 avec les bonnes données"""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data is not None
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        
        assert data['status'] == 'healthy'
        assert data['version'] == '1.0.0'

    def test_health_endpoint_timestamp_format(self, client):
        """Test que le timestamp est au format ISO 8601"""
        response = client.get('/health')
        data = response.get_json()
        
        timestamp = data['timestamp']
        assert timestamp.endswith('Z')  # Format UTC
        
        # Vérifier que le timestamp peut être parsé
        try:
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            assert isinstance(parsed_time, datetime)
        except ValueError:
            pytest.fail("Timestamp format is not valid ISO 8601")

    def test_health_endpoint_method_not_allowed(self, client):
        """Test que seule la méthode GET est autorisée"""
        # Test POST
        response = client.post('/health')
        assert response.status_code == 405
        
        # Test PUT
        response = client.put('/health')
        assert response.status_code == 405
        
        # Test DELETE
        response = client.delete('/health')
        assert response.status_code == 405

    def test_health_endpoint_multiple_calls(self, client):
        """Test que l'endpoint est stable sur plusieurs appels"""
        responses = []
        for _ in range(5):
            response = client.get('/health')
            responses.append(response)
        
        # Tous les appels doivent réussir
        for response in responses:
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['version'] == '1.0.0'

    def test_health_endpoint_response_structure(self, client):
        """Test la structure complète de la réponse"""
        response = client.get('/health')
        data = response.get_json()
        
        # Vérifier que seuls les champs attendus sont présents
        expected_keys = {'status', 'timestamp', 'version'}
        actual_keys = set(data.keys())
        assert actual_keys == expected_keys
        
        # Vérifier les types des valeurs
        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['version'], str)