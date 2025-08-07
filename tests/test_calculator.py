"""
Tests unitaires pour l'endpoint /api/calculate
"""

import pytest
import json


class TestCalculatorEndpoint:
    """Tests pour l'endpoint de calcul"""

    def test_calculate_addition_success(self, client):
        """Test de l'addition avec des nombres entiers"""
        data = {
            'operation': 'add',
            'a': 5,
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 8
        assert result['operation'] == 'add'
        assert result['a'] == 5
        assert result['b'] == 3

    def test_calculate_subtraction_success(self, client):
        """Test de la soustraction"""
        data = {
            'operation': 'subtract',
            'a': 10,
            'b': 4
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 6
        assert result['operation'] == 'subtract'

    def test_calculate_multiplication_success(self, client):
        """Test de la multiplication"""
        data = {
            'operation': 'multiply',
            'a': 7,
            'b': 6
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 42
        assert result['operation'] == 'multiply'

    def test_calculate_division_success(self, client):
        """Test de la division"""
        data = {
            'operation': 'divide',
            'a': 15,
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 5.0
        assert result['operation'] == 'divide'

    def test_calculate_division_by_zero(self, client):
        """Test de la division par zéro"""
        data = {
            'operation': 'divide',
            'a': 10,
            'b': 0
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Division by zero' in result['error']

    def test_calculate_with_floats(self, client):
        """Test avec des nombres décimaux"""
        data = {
            'operation': 'add',
            'a': 2.5,
            'b': 3.7
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert abs(result['result'] - 6.2) < 0.0001  # Gestion de la précision flottante

    def test_calculate_with_negative_numbers(self, client):
        """Test avec des nombres négatifs"""
        data = {
            'operation': 'multiply',
            'a': -5,
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == -15

    def test_calculate_invalid_operation(self, client):
        """Test avec une opération invalide"""
        data = {
            'operation': 'power',
            'a': 2,
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Unsupported operation' in result['error']

    def test_calculate_missing_operation(self, client):
        """Test avec le champ operation manquant"""
        data = {
            'a': 5,
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Missing required field: operation' in result['error']

    def test_calculate_missing_a(self, client):
        """Test avec le champ a manquant"""
        data = {
            'operation': 'add',
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Missing required field: a' in result['error']

    def test_calculate_missing_b(self, client):
        """Test avec le champ b manquant"""
        data = {
            'operation': 'add',
            'a': 5
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Missing required field: b' in result['error']

    def test_calculate_invalid_number_a(self, client):
        """Test avec une valeur non numérique pour a"""
        data = {
            'operation': 'add',
            'a': 'not_a_number',
            'b': 3
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'must be numeric' in result['error']

    def test_calculate_invalid_number_b(self, client):
        """Test avec une valeur non numérique pour b"""
        data = {
            'operation': 'add',
            'a': 5,
            'b': 'not_a_number'
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'must be numeric' in result['error']

    def test_calculate_string_numbers(self, client):
        """Test avec des nombres sous forme de chaînes (doit fonctionner)"""
        data = {
            'operation': 'add',
            'a': '5',
            'b': '3'
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 8

    def test_calculate_no_json_content_type(self, client):
        """Test sans Content-Type application/json"""
        data = {
            'operation': 'add',
            'a': 5,
            'b': 3
        }
        response = client.post('/api/calculate', data=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Content-Type must be application/json' in result['error']

    def test_calculate_empty_json(self, client):
        """Test avec un JSON vide"""
        response = client.post('/api/calculate',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
        assert 'Missing required field' in result['error']

    def test_calculate_method_not_allowed(self, client):
        """Test que seule la méthode POST est autorisée"""
        # Test GET
        response = client.get('/api/calculate')
        assert response.status_code == 405
        
        # Test PUT
        response = client.put('/api/calculate')
        assert response.status_code == 405
        
        # Test DELETE
        response = client.delete('/api/calculate')
        assert response.status_code == 405

    def test_calculate_large_numbers(self, client):
        """Test avec de très grands nombres"""
        data = {
            'operation': 'multiply',
            'a': 999999999,
            'b': 999999999
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        expected = 999999999 * 999999999
        # Gestion de la précision pour les très grands nombres
        assert abs(result['result'] - expected) / expected < 0.0001

    def test_calculate_zero_values(self, client):
        """Test avec des valeurs zéro"""
        data = {
            'operation': 'add',
            'a': 0,
            'b': 0
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['result'] == 0

    def test_calculate_response_structure(self, client):
        """Test la structure de la réponse de succès"""
        data = {
            'operation': 'add',
            'a': 1,
            'b': 2
        }
        response = client.post('/api/calculate',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        
        # Vérifier que tous les champs attendus sont présents
        expected_keys = {'result', 'operation', 'a', 'b'}
        actual_keys = set(result.keys())
        assert actual_keys == expected_keys