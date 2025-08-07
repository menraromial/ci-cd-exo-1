"""
Endpoint de calcul pour l'application Flask
"""

from flask import Blueprint, jsonify, request

calculator_bp = Blueprint("calculator", __name__)


@calculator_bp.route("/calculate", methods=["POST"])
def calculate():
    """
    Endpoint de calcul simple
    Accepte des données JSON et effectue un calcul simple
    """
    try:
        # Validation de la présence des données JSON
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()

        # Validation des champs requis
        required_fields = ["operation", "a", "b"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        operation = data["operation"]
        a = data["a"]
        b = data["b"]

        # Validation des types numériques
        try:
            a = float(a)
            b = float(b)
        except (ValueError, TypeError):
            return jsonify({"error": "Values a and b must be numeric"}), 400

        # Calcul selon l'opération
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return jsonify({"error": "Division by zero is not allowed"}), 400
            result = a / b
        else:
            return (
                jsonify({"error": ("Unsupported operation. " "Use: add, subtract, multiply, divide")}),
                400,
            )

        return (
            jsonify({"result": result, "operation": operation, "a": a, "b": b}),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
