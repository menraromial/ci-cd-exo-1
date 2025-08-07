#!/usr/bin/env python3
"""
Script de validation complète de la configuration de production
"""

import os
import sys
import json
import yaml
import subprocess
import requests
from pathlib import Path


class ProductionValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message):
        self.success_count += 1
        print(f"✅ SUCCESS: {message}")

    def validate_docker_image(self):
        """Valider l'image Docker"""
        print("\n🐳 Validating Docker Image...")
        self.total_checks += 4

        try:
            # Vérifier que l'image peut être construite
            result = subprocess.run(
                ["docker", "build", "-t", "python-cicd-test", "."], capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                self.log_success("Docker image builds successfully")
            else:
                self.log_error(f"Docker build failed: {result.stderr}")

            # Vérifier la taille de l'image
            result = subprocess.run(
                ["docker", "images", "--format", "table {{.Size}}", "python-cicd-test"], capture_output=True, text=True
            )
            if result.returncode == 0:
                size_line = result.stdout.strip().split("\n")[-1]
                if "MB" in size_line:
                    size_mb = float(size_line.replace("MB", "").strip())
                    if size_mb < 200:
                        self.log_success(f"Docker image size is optimized: {size_mb}MB")
                    else:
                        self.log_warning(f"Docker image size could be optimized: {size_mb}MB")
                else:
                    self.log_warning(f"Docker image size: {size_line}")

            # Vérifier les vulnérabilités avec Trivy si disponible
            trivy_result = subprocess.run(["which", "trivy"], capture_output=True)
            if trivy_result.returncode == 0:
                result = subprocess.run(
                    ["trivy", "image", "--severity", "HIGH,CRITICAL", "--exit-code", "1", "python-cicd-test"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    self.log_success("No high/critical vulnerabilities found")
                else:
                    self.log_error("High/critical vulnerabilities found in image")
            else:
                self.log_warning("Trivy not available for vulnerability scanning")

            # Vérifier que l'image utilise un utilisateur non-root
            result = subprocess.run(
                ["docker", "run", "--rm", "python-cicd-test", "whoami"], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and "appuser" in result.stdout:
                self.log_success("Image runs as non-root user")
            else:
                self.log_error("Image may be running as root user")

        except subprocess.TimeoutExpired:
            self.log_error("Docker operations timed out")
        except Exception as e:
            self.log_error(f"Docker validation failed: {str(e)}")

    def validate_helm_charts(self):
        """Valider les Helm charts"""
        print("\n⎈ Validating Helm Charts...")
        self.total_checks += 5

        chart_path = Path("gitops-example/helm-chart")

        # Vérifier que les fichiers Helm existent
        required_files = [
            "Chart.yaml",
            "values.yaml",
            "values-development.yaml",
            "values-staging.yaml",
            "values-production.yaml",
        ]

        for file in required_files:
            if (chart_path / file).exists():
                self.log_success(f"Helm file exists: {file}")
            else:
                self.log_error(f"Missing Helm file: {file}")

        # Valider la syntaxe YAML
        try:
            for values_file in ["values.yaml", "values-production.yaml"]:
                with open(chart_path / values_file, "r") as f:
                    yaml.safe_load(f)
                self.log_success(f"Valid YAML syntax: {values_file}")
        except Exception as e:
            self.log_error(f"Invalid YAML syntax: {str(e)}")

        # Vérifier la configuration des ressources
        try:
            with open(chart_path / "values-production.yaml", "r") as f:
                prod_values = yaml.safe_load(f)

            resources = prod_values.get("resources", {})
            if resources.get("limits") and resources.get("requests"):
                self.log_success("Resource limits and requests are configured")
            else:
                self.log_error("Missing resource limits or requests")

            # Vérifier l'autoscaling
            autoscaling = prod_values.get("autoscaling", {})
            if autoscaling.get("enabled") and autoscaling.get("minReplicas", 0) >= 2:
                self.log_success("Autoscaling properly configured for production")
            else:
                self.log_warning("Autoscaling not optimally configured")

        except Exception as e:
            self.log_error(f"Failed to validate Helm values: {str(e)}")

    def validate_monitoring_config(self):
        """Valider la configuration de monitoring"""
        print("\n📊 Validating Monitoring Configuration...")
        self.total_checks += 3

        # Vérifier que les métriques sont configurées
        metrics_file = Path("app/api/metrics.py")
        if metrics_file.exists():
            self.log_success("Metrics endpoint exists")

            # Vérifier le contenu du fichier de métriques
            with open(metrics_file, "r") as f:
                content = f.read()
                if "prometheus_client" in content and "REQUEST_COUNT" in content:
                    self.log_success("Prometheus metrics properly configured")
                else:
                    self.log_error("Prometheus metrics not properly configured")
        else:
            self.log_error("Metrics endpoint missing")

        # Vérifier ServiceMonitor
        servicemonitor_file = Path("gitops-example/helm-chart/templates/servicemonitor.yaml")
        if servicemonitor_file.exists():
            self.log_success("ServiceMonitor template exists")
        else:
            self.log_error("ServiceMonitor template missing")

    def validate_security_config(self):
        """Valider la configuration de sécurité"""
        print("\n🔒 Validating Security Configuration...")
        self.total_checks += 4

        # Vérifier les GitHub Actions workflows
        workflows_path = Path(".github/workflows")
        if workflows_path.exists():
            workflow_files = list(workflows_path.glob("*.yml"))
            if len(workflow_files) >= 2:
                self.log_success(f"GitHub Actions workflows configured: {len(workflow_files)} files")
            else:
                self.log_error("Missing GitHub Actions workflows")

            # Vérifier la configuration de sécurité dans les workflows
            for workflow_file in workflow_files:
                with open(workflow_file, "r") as f:
                    content = f.read()
                    if "permissions:" in content:
                        self.log_success(f"Security permissions configured in {workflow_file.name}")
                    else:
                        self.log_warning(f"Missing permissions configuration in {workflow_file.name}")
        else:
            self.log_error("GitHub Actions workflows directory missing")

        # Vérifier la configuration de sécurité Kubernetes
        try:
            with open("gitops-example/helm-chart/values-production.yaml", "r") as f:
                prod_values = yaml.safe_load(f)

            security_context = prod_values.get("securityContext", {})
            if security_context.get("runAsNonRoot") and security_context.get("readOnlyRootFilesystem"):
                self.log_success("Kubernetes security context properly configured")
            else:
                self.log_error("Kubernetes security context not properly configured")

        except Exception as e:
            self.log_error(f"Failed to validate security configuration: {str(e)}")

    def validate_application_health(self):
        """Valider la santé de l'application (si elle tourne)"""
        print("\n🏥 Validating Application Health...")
        self.total_checks += 2

        try:
            # Essayer de démarrer l'application localement pour tester
            env = os.environ.copy()
            env["PYTHONPATH"] = "app"

            # Test simple d'import
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from app.main import create_app; app = create_app(); print('App created successfully')",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )

            if result.returncode == 0:
                self.log_success("Application can be imported and created successfully")
            else:
                self.log_error(f"Application import failed: {result.stderr}")

            # Vérifier que les endpoints sont définis
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from app.main import create_app; app = create_app(); print([rule.rule for rule in app.url_map.iter_rules()])",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )

            if result.returncode == 0 and "/health" in result.stdout:
                self.log_success("Health endpoint is configured")
            else:
                self.log_error("Health endpoint not found")

        except subprocess.TimeoutExpired:
            self.log_error("Application health check timed out")
        except Exception as e:
            self.log_error(f"Application health validation failed: {str(e)}")

    def generate_report(self):
        """Générer le rapport final"""
        print("\n" + "=" * 60)
        print("🎯 VALIDATION REPORT")
        print("=" * 60)

        success_rate = (self.success_count / self.total_checks) * 100 if self.total_checks > 0 else 0

        print(f"✅ Successful checks: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.errors:
            print("\n🚨 ERRORS TO FIX:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS TO CONSIDER:")
            for warning in self.warnings:
                print(f"  • {warning}")

        print("\n" + "=" * 60)

        if len(self.errors) == 0 and success_rate >= 80:
            print("🎉 PRODUCTION READY! Configuration validation passed.")
            return 0
        elif len(self.errors) == 0:
            print("⚠️  MOSTLY READY: Some optimizations recommended.")
            return 0
        else:
            print("❌ NOT READY: Critical issues must be fixed before production.")
            return 1

    def run_all_validations(self):
        """Exécuter toutes les validations"""
        print("🚀 Starting Production Configuration Validation...")

        self.validate_docker_image()
        self.validate_helm_charts()
        self.validate_monitoring_config()
        self.validate_security_config()
        self.validate_application_health()

        return self.generate_report()


if __name__ == "__main__":
    validator = ProductionValidator()
    exit_code = validator.run_all_validations()
    sys.exit(exit_code)
