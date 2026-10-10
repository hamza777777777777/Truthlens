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
from app.schemas.investigation import InvestigationResult


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as test_client:
        yield test_client


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
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS):
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
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS):
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
    with patch("app.services.investigation_service.analyze_content", return_value=MOCK_ANALYSIS):
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
