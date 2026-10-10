from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service readiness."""
    return (
        jsonify({
            "status": "ok",
            "service": "truthlens-api",
        }),
        200,
    )
