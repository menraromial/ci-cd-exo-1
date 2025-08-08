#!/usr/bin/env python3
"""
Script de validation simple pour la configuration de production
Version simplifiée sans dépendances externes complexes
"""

import os
import sys
from pathlib import Path


def validate_basic_files():
    """Valider que les fichiers de base existent"""
    required_files = [
        "Dockerfile",
        "requirements.txt",
        "app/main.py",
        "app/api/health.py",
        "app/api/hello.py",
        "app/api/calculator.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False

    print("✅ All required files present")
    return True


def validate_dockerfile():
    """Valider le Dockerfile"""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False

    content = dockerfile_path.read_text()

    # Vérifications de base
    checks = [
        ("FROM python:", "Base image specified"),
        ("WORKDIR", "Working directory set"),
        ("COPY requirements.txt", "Requirements copied"),
        ("RUN pip install", "Dependencies installed"),
        ("EXPOSE", "Port exposed"),
        ("CMD", "Command specified"),
    ]

    passed = 0
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"⚠️  {description} - not found")

    return passed >= 4  # Au moins 4 vérifications doivent passer


def validate_app_structure():
    """Valider la structure de l'application"""
    app_dir = Path("app")
    if not app_dir.exists():
        print("❌ App directory not found")
        return False

    api_dir = app_dir / "api"
    if not api_dir.exists():
        print("❌ API directory not found")
        return False

    # Vérifier les modules principaux
    modules = ["health.py", "hello.py", "calculator.py"]
    missing_modules = []

    for module in modules:
        if not (api_dir / module).exists():
            missing_modules.append(module)

    if missing_modules:
        print(f"⚠️  Missing API modules: {', '.join(missing_modules)}")
    else:
        print("✅ All API modules present")

    return len(missing_modules) == 0


def main():
    """Fonction principale"""
    print("🚀 Starting Simple Production Validation...")
    print("=" * 50)

    validations = [
        ("Basic Files", validate_basic_files),
        ("Dockerfile", validate_dockerfile),
        ("App Structure", validate_app_structure),
    ]

    passed = 0
    total = len(validations)

    for name, validation_func in validations:
        print(f"\n📋 Validating {name}...")
        if validation_func():
            passed += 1
        else:
            print(f"❌ {name} validation failed")

    print("\n" + "=" * 50)
    print(f"📊 VALIDATION SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED! Ready for production.")
        return 0
    elif passed >= total * 0.8:  # 80% ou plus
        print("⚠️  MOSTLY READY: Some minor issues to address.")
        return 0
    else:
        print("❌ VALIDATION FAILED: Critical issues must be fixed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
