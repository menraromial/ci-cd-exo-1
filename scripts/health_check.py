#!/usr/bin/env python3
"""
Script de vérification de santé pour la validation
"""

import sys
import os
import importlib.util
from pathlib import Path


def check_app_imports():
    """Vérifier que l'application peut être importée"""
    try:
        # Ajouter le répertoire app au path
        app_path = Path(__file__).parent.parent / "app"
        sys.path.insert(0, str(app_path))

        # Essayer d'importer les modules principaux
        from main import create_app
        from api.health import health_bp
        from api.hello import hello_bp
        from api.calculator import calculator_bp

        print("✅ All application modules imported successfully")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_app_creation():
    """Vérifier que l'application peut être créée"""
    try:
        # Ajouter le répertoire app au path
        app_path = Path(__file__).parent.parent / "app"
        sys.path.insert(0, str(app_path))

        from main import create_app

        app = create_app()

        print("✅ Flask application created successfully")
        print(f"   - Debug mode: {app.config.get('DEBUG', False)}")
        print(f"   - Host: {app.config.get('HOST', 'not set')}")
        print(f"   - Port: {app.config.get('PORT', 'not set')}")

        return True

    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False


def check_endpoints():
    """Vérifier que les endpoints sont enregistrés"""
    try:
        # Ajouter le répertoire app au path
        app_path = Path(__file__).parent.parent / "app"
        sys.path.insert(0, str(app_path))

        from main import create_app

        app = create_app()

        # Vérifier les routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")

        expected_endpoints = ["/health", "/api/hello", "/api/calculate", "/metrics"]
        found_endpoints = []

        for endpoint in expected_endpoints:
            if any(endpoint in route for route in routes):
                found_endpoints.append(endpoint)
                print(f"✅ Endpoint found: {endpoint}")
            else:
                print(f"❌ Endpoint missing: {endpoint}")

        return len(found_endpoints) == len(expected_endpoints)

    except Exception as e:
        print(f"❌ Endpoint check error: {e}")
        return False


def main():
    """Fonction principale"""
    print("🏥 Starting Application Health Check...")
    print("=" * 40)

    checks = [("Import Check", check_app_imports), ("App Creation", check_app_creation), ("Endpoints Check", check_endpoints)]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n📋 {name}...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} failed")

    print("\n" + "=" * 40)
    print(f"📊 HEALTH CHECK SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 APPLICATION HEALTHY!")
        return 0
    else:
        print("❌ APPLICATION HEALTH ISSUES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
