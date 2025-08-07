#!/usr/bin/env python3
"""
Application Flask principale pour le pipeline CI/CD Python
"""

import os
import time
from flask import Flask, request, g
from api.health import health_bp
from api.hello import hello_bp
from api.calculator import calculator_bp
from api.metrics import metrics_bp, init_metrics, record_request_metrics


def create_app():
    """Factory function pour créer l'application Flask"""
    app = Flask(__name__)

    # Configuration de base
    app.config["DEBUG"] = os.getenv("DEBUG", "false").lower() == "true"
    app.config["HOST"] = os.getenv("HOST", "0.0.0.0")
    app.config["PORT"] = int(os.getenv("PORT", 5000))
    app.config["VERSION"] = os.getenv("VERSION", "1.0.0")
    app.config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")

    # Initialize metrics
    init_metrics(app)

    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            endpoint = request.endpoint or 'unknown'
            method = request.method
            record_request_metrics(response, g.start_time, endpoint, method)
        return response

    # Enregistrement des blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(hello_bp, url_prefix="/api")
    app.register_blueprint(calculator_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
