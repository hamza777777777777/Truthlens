import os
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import config_by_name
from app.routes.health import health_bp
from app.routes.investigation import investigation_bp


def create_app(config_name: str = None) -> Flask:
    """Application factory for TruthLens AI Flask backend."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_cls = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_cls)

    # Configure CORS for Next.js development server
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["http://localhost:3000"])}},
        supports_credentials=True,
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Register Blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(investigation_bp, url_prefix="/api")

    # Global JSON error handlers
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "error": "Not Found",
                "message": "The requested API endpoint does not exist",
            }),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify({
                "error": "Method Not Allowed",
                "message": "The HTTP method is not supported for this endpoint",
            }),
            405,
        )

    @app.errorhandler(500)
    def internal_error(error):
        return (
            jsonify({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred processing the request",
            }),
            500,
        )

    return app
