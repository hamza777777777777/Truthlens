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

    is_production = config_name == "production" or app.config.get("FLASK_ENV") == "production" or os.getenv("FLASK_ENV") == "production"

    # Synchronize runtime environment overrides with app.config
    if os.getenv("SECRET_KEY") is not None:
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    elif is_production:
        app.config["SECRET_KEY"] = None

    if os.getenv("GEMINI_MODEL") is not None:
        app.config["GEMINI_MODEL"] = os.getenv("GEMINI_MODEL")
    elif is_production:
        app.config["GEMINI_MODEL"] = None

    if os.getenv("CORS_ORIGINS") is not None:
        raw_cors = os.getenv("CORS_ORIGINS", "")
        app.config["CORS_ORIGINS"] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    if is_production:
        # Enforce explicit production SECRET_KEY without fallback
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key or str(secret_key).strip() == "dev-secret-key-truthlens-do-not-use-in-production":
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: SECRET_KEY must be explicitly configured "
                "in production environment and cannot use the development fallback key."
            )

        # Enforce explicit GEMINI_MODEL without implicit fallback
        gemini_model = app.config.get("GEMINI_MODEL")
        if not gemini_model or not str(gemini_model).strip():
            raise ValueError(
                "CRITICAL CONFIGURATION ERROR: GEMINI_MODEL must be explicitly configured in production. "
                "Implicit model fallbacks are forbidden."
            )

        # Disallow wildcard origin '*' in production
        cors_origins = app.config.get("CORS_ORIGINS", [])
        if "*" in cors_origins:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Wildcard origin '*' is forbidden in production CORS_ORIGINS. "
                "Specify explicit trusted origins (e.g. Vercel deployment URL)."
            )

    # Configure CORS for Next.js frontend (local development or deployed Vercel domain)
    cors_allowed = app.config.get("CORS_ORIGINS", ["http://localhost:3000"])
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_allowed if cors_allowed else []}},
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
