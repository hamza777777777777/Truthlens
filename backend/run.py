import os
import sys
from pathlib import Path

# Ensure backend root is on Python module search path
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", True)

    print(f"[*] Starting TruthLens AI Flask Backend on http://{host}:{port}")
    print(f"[*] Environment: {app.config.get('FLASK_ENV', 'development')} (debug={debug})")
    print(f"[*] CORS Allowed Origins: {app.config.get('CORS_ORIGINS')}")
    print("[*] Health Check: http://127.0.0.1:5000/api/health")
    print("[*] Investigation Endpoint: http://127.0.0.1:5000/api/investigate")

    app.run(host=host, port=port, debug=debug)
