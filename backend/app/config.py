import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root or parent if present
backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Config:
    """Base application configuration."""

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") in ("1", "true", "True")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-truthlens-do-not-use-in-production")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))

    # CORS configuration: default Next.js frontend is on localhost:3000
    cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

    # Database configuration for future persistence (Supabase / Postgres / SQLite)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini Configuration (explicitly required; no implicit model fallback)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")

    # Placeholders for future integrations
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key-truthlens"


class ProductionConfig(Config):
    DEBUG = False
    # Never inherit the development SECRET_KEY fallback
    SECRET_KEY = os.getenv("SECRET_KEY", None)
    # Never inherit an implicit model fallback
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", None)


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
