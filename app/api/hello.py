"""
Endpoint de bienvenue pour l'application Flask
"""

from flask import Blueprint, jsonify

hello_bp = Blueprint("hello", __name__)


@hello_bp.route("/hello", methods=["GET"])
def hello():
    """
    Endpoint de bienvenue
    Retourne un message JSON de bienvenue
    """
    return jsonify({"message": "Hello World!", "version": "1.0.0"}), 200
