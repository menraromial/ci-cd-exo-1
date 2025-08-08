"""
Endpoint de santé pour l'application Flask
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint de vérification de santé de l'application
    Retourne un statut 200 avec un message de santé
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "version": "1.0.0",
            }
        ),
        200,
    )
