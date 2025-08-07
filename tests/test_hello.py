"""
Tests unitaires pour l'endpoint /api/hello
"""

import pytest


class TestHelloEndpoint:
    """Tests pour l'endpoint de bienvenue"""

    def test_hello_endpoint_success(self, client):
        """Test que l'endpoint /api/hello retourne un statut 200 avec le bon message"""
        response = client.get('/api/hello')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data is not None
        assert 'message' in data
        assert 'version' in data
        
        assert data['message'] == 'Hello World!'
        assert data['version'] == '1.0.0'

    def test_hello_endpoint_method_not_allowed(self, client):
        """Test que seule la méthode GET est autorisée"""
        # Test POST
        response = client.post('/api/hello')
        assert response.status_code == 405
        
        # Test PUT
        response = client.put('/api/hello')
        assert response.status_code == 405
        
        # Test DELETE
        response = client.delete('/api/hello')
        assert response.status_code == 405

    def test_hello_endpoint_response_structure(self, client):
        """Test la structure complète de la réponse"""
        response = client.get('/api/hello')
        data = response.get_json()
        
        # Vérifier que seuls les champs attendus sont présents
        expected_keys = {'message', 'version'}
        actual_keys = set(data.keys())
        assert actual_keys == expected_keys
        
        # Vérifier les types des valeurs
        assert isinstance(data['message'], str)
        assert isinstance(data['version'], str)

    def test_hello_endpoint_multiple_calls(self, client):
        """Test que l'endpoint est stable sur plusieurs appels"""
        responses = []
        for _ in range(5):
            response = client.get('/api/hello')
            responses.append(response)
        
        # Tous les appels doivent réussir avec la même réponse
        for response in responses:
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Hello World!'
            assert data['version'] == '1.0.0'

    def test_hello_endpoint_without_prefix(self, client):
        """Test que l'endpoint n'est pas accessible sans le préfixe /api"""
        response = client.get('/hello')
        assert response.status_code == 404

    def test_hello_endpoint_case_sensitivity(self, client):
        """Test que l'endpoint est sensible à la casse"""
        # Test avec différentes variations de casse
        variations = ['/api/Hello', '/api/HELLO', '/API/hello', '/Api/Hello']
        
        for variation in variations:
            response = client.get(variation)
            assert response.status_code == 404