import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Ensure backend root is on Python module search path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app import create_app
from app.schemas.content_analysis import (
    ClaimAnalysis,
    ContentAnalysis,
    EntityAnalysis,
    LanguageInfo,
    SuspiciousSignal,
    UrlTarget,
)
from app.schemas.evidence import FailureCategory, GroundingAnalysis, RetrievalStatus
from app.schemas.investigation import InvestigationResult


@pytest.fixture(autouse=True)
def disable_tavily_for_api_tests(monkeypatch):
    """Ensure Tavily is not active during API unit tests."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as test_client:
        yield test_client


MOCK_GROUNDING = GroundingAnalysis(
    retrieval_status=RetrievalStatus.FAILED,
    failure_category=FailureCategory.PROVIDER_ERROR,
    is_grounded=False,
)

MOCK_ANALYSIS = ContentAnalysis(
    normalized_text="Congratulations! You've won ₹50,000. Pay ₹499 to claim your reward at https://sbi-reward-claim.example",
    language=LanguageInfo(code="en", name="English", confidence=0.99),
    claims=[
        ClaimAnalysis(
            id="cl-1",
            statement="The recipient has won ₹50,000.",
            category="benefit_claim",
            claim_type="factual",
            importance="high",
            confidence=0.98,
        ),
        ClaimAnalysis(
            id="cl-2",
            statement="An advance processing fee of ₹499 is required.",
            category="payment_instruction",
            claim_type="behavioral_instruction",
            importance="high",
            confidence=0.95,
        ),
        ClaimAnalysis(
            id="cl-3",
            statement="The reward must be claimed within 2 hours.",
            category="urgency_constraint",
            claim_type="behavioral_instruction",
            importance="medium",
            confidence=0.92,
        ),
    ],
    entities=[
        EntityAnalysis(
            name="State Bank of India",
            type="financial_institution",
            context="Target referenced brand",
            confidence=0.95,
        )
    ],
    urls=[
        UrlTarget(
            url="https://sbi-reward-claim.example",
            domain="sbi-reward-claim.example",
            context="Prize redemption destination",
        )
    ],
    suspicious_signals=[
        SuspiciousSignal(
            type="advance_payment_request",
            description="Demands upfront fee transfer prior to releasing funds",
            confidence=0.98,
            evidence="Pay ₹499 to claim your reward",
        ),
        SuspiciousSignal(
            type="urgency",
            description="Imposes coercive time limit to act",
            confidence=0.94,
            evidence="within 2 hours",
        ),
    ],
)


def test_health_check(client):
    """GET /api/health returns ok status and service identity."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "status": "ok",
        "service": "truthlens-api",
    }


def test_investigate_valid_text(client):
    """POST /api/investigate returns valid InvestigationResult with Gemini content analysis."""
    payload = {
        "input_type": "text",
        "content": "Congratulations! You've won ₹50,000. Pay ₹499 to claim your reward at https://sbi-reward-claim.example",
    }
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS), \
         patch("app.services.investigation_service.ground_claims", return_value=MOCK_GROUNDING):
        response = client.post(
            "/api/investigate",
            data=json.dumps(payload),
            content_type="application/json",
        )
    assert response.status_code == 200
    data = response.get_json()

    # Validate schema conforms to InvestigationResult Pydantic model
    validated = InvestigationResult.model_validate(data)
    assert validated.development_mode is True
    assert validated.truth_assessment_status.value == "NOT_ASSESSED"
    assert validated.truth_status is None
    assert len(validated.claims) == 3
    assert len(validated.scam_signals) >= 2
    assert validated.url_analysis is not None
    assert validated.url_analysis.domain == "sbi-reward-claim.example"

    # Check camelCase serialization matching frontend TypeScript types
    assert "claimNumber" in data["claims"][0]
    assert "truthStatus" in data["claims"][0]
    assert data["claims"][0]["truthStatus"] is None
    assert data["claims"][0]["truthAssessmentStatus"] == "NOT_ASSESSED"
    assert "evidenceRefIds" in data["claims"][0]
    assert "isSimulatedDemo" in data["evidence"][0]
    assert "developmentMode" in data or "development_mode" in data


def test_investigate_frontend_aliases(client):
    """POST /api/investigate accepts frontend aliases (inputMode, text)."""
    payload = {
        "inputMode": "text",
        "text": "Special grant awarded. Send processing fee immediately.",
    }
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS), \
         patch("app.services.investigation_service.ground_claims", return_value=MOCK_GROUNDING):
        response = client.post(
            "/api/investigate",
            data=json.dumps(payload),
            content_type="application/json",
        )
    assert response.status_code == 200
    data = response.get_json()
    assert data["inputMode"] == "text"


def test_investigate_url_input(client):
    """POST /api/investigate handles URL input mode."""
    payload = {
        "input_type": "url",
        "content": "https://sbi-reward-claim.example",
    }
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS), \
         patch("app.services.investigation_service.ground_claims", return_value=MOCK_GROUNDING):
        response = client.post(
            "/api/investigate",
            data=json.dumps(payload),
            content_type="application/json",
        )
    assert response.status_code == 200
    data = response.get_json()
    assert data["inputMode"] == "url"
    assert data["urlAnalysis"] is not None


def test_investigate_empty_content(client):
    """POST /api/investigate rejects empty or whitespace content with 422."""
    payload = {
        "input_type": "text",
        "content": "   ",
    }
    response = client.post(
        "/api/investigate",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["error"] == "Unprocessable Entity"
    assert "validation failed" in data["message"]


def test_investigate_missing_content(client):
    """POST /api/investigate rejects missing content field with 422."""
    payload = {
        "input_type": "text",
    }
    response = client.post(
        "/api/investigate",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["error"] == "Unprocessable Entity"


def test_investigate_unsupported_input_type(client):
    """POST /api/investigate rejects invalid input types with 422."""
    payload = {
        "input_type": "unsupported_hologram",
        "content": "Sample content",
    }
    response = client.post(
        "/api/investigate",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["error"] == "Unprocessable Entity"


def test_investigate_invalid_json(client):
    """POST /api/investigate rejects non-JSON body with 400."""
    response = client.post(
        "/api/investigate",
        data="not-valid-json",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Bad Request"


def test_404_not_found(client):
    """Unknown route returns JSON 404 envelope."""
    response = client.get("/api/unknown_endpoint")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Not Found"


# --- Production Deployment Safety & Configuration Tests ---

def test_production_config_missing_secret_key_fails_safely():
    """In production, missing SECRET_KEY raises a clear configuration error."""
    import os
    with patch.dict(os.environ, {"SECRET_KEY": "", "GEMINI_MODEL": "gemini-2.5-flash"}, clear=False):
        with pytest.raises(ValueError) as exc_info:
            create_app("production")
        assert "SECRET_KEY must be explicitly configured" in str(exc_info.value)


def test_production_config_dev_secret_key_fails_safely():
    """In production, using the development fallback SECRET_KEY raises a security error."""
    import os
    with patch.dict(os.environ, {
        "SECRET_KEY": "dev-secret-key-truthlens-do-not-use-in-production",
        "GEMINI_MODEL": "gemini-2.5-flash"
    }, clear=False):
        with pytest.raises(ValueError) as exc_info:
            create_app("production")
        assert "cannot use the development fallback key" in str(exc_info.value)


def test_production_config_missing_gemini_model_fails_safely():
    """In production, GEMINI_MODEL must be explicitly configured without implicit fallback."""
    import os
    with patch.dict(os.environ, {
        "SECRET_KEY": "production-secure-key-12345",
        "GEMINI_MODEL": ""
    }, clear=False):
        with pytest.raises(ValueError) as exc_info:
            create_app("production")
        assert "GEMINI_MODEL must be explicitly configured" in str(exc_info.value)


def test_production_config_wildcard_cors_forbidden():
    """In production, arbitrary wildcard origin '*' is strictly rejected."""
    import os
    with patch.dict(os.environ, {
        "SECRET_KEY": "production-secure-key-12345",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "CORS_ORIGINS": "*"
    }, clear=False):
        with pytest.raises(ValueError) as exc_info:
            create_app("production")
        assert "Wildcard origin '*' is forbidden" in str(exc_info.value)


def test_production_config_valid_environment_succeeds():
    """In production with valid SECRET_KEY, explicit GEMINI_MODEL, and explicit Vercel CORS, app creates cleanly."""
    import os
    with patch.dict(os.environ, {
        "SECRET_KEY": "production-secure-key-12345",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "CORS_ORIGINS": "https://truthlens.vercel.app,http://localhost:3000"
    }, clear=False):
        prod_app = create_app("production")
        assert prod_app is not None
        assert prod_app.config["SECRET_KEY"] == "production-secure-key-12345"
        assert prod_app.config["GEMINI_MODEL"] == "gemini-2.5-flash"
        assert prod_app.config["CORS_ORIGINS"] == ["https://truthlens.vercel.app", "http://localhost:3000"]


def test_development_config_default_model_is_gemini_2_5_flash():
    """In development, default GEMINI_MODEL is gemini-2.5-flash when unset."""
    import os
    with patch.dict(os.environ, {}, clear=False):
        env_copy = {k: v for k, v in os.environ.items() if k != "GEMINI_MODEL"}
        with patch.dict(os.environ, env_copy, clear=True):
            dev_app = create_app("development")
            assert dev_app.config["GEMINI_MODEL"] == "gemini-2.5-flash"


def test_development_config_model_override():
    """In development, GEMINI_MODEL environment variable overrides the default."""
    import os
    with patch.dict(os.environ, {"GEMINI_MODEL": "custom-gemini-model"}, clear=False):
        dev_app = create_app("development")
        assert dev_app.config["GEMINI_MODEL"] == "custom-gemini-model"

