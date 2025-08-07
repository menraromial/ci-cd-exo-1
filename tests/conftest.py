"""
Configuration pytest pour les tests de l'application Flask
"""

import pytest
import sys
import os

# Ajouter le répertoire app au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import create_app


@pytest.fixture
def app():
    """Fixture pour créer l'application Flask en mode test"""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Fixture pour créer un client de test Flask"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Fixture pour créer un runner de commandes CLI"""
    return app.test_cli_runner()