import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure backend directory is in python search path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.schemas.content_analysis import (
    ClaimAnalysis,
    ContentAnalysis,
    EntityAnalysis,
    LanguageInfo,
    SuspiciousSignal,
    UrlTarget,
)
from app.schemas.investigation import InvestigationRequest, InvestigationResult
from app.services.gemini_service import (
    GeminiAuthError,
    GeminiConfigError,
    GeminiProviderError,
    GeminiRateLimitError,
    GeminiSchemaError,
    analyze_content,
)
from app.services.investigation_service import investigate
from google.genai import errors, types
from google.genai.types import BlockedReason, FinishReason


MOCK_VALID_GEMINI_OUTPUT = {
    "normalized_text": "Congratulations! You've won ₹50,000. Pay ₹499 to claim your reward within 2 hours at https://sbi-reward-claim.example",
    "language": {
        "code": "en",
        "name": "English",
        "confidence": 0.99,
    },
    "claims": [
        {
            "id": "claim-1",
            "statement": "The recipient has won ₹50,000.",
            "category": "benefit_claim",
            "claim_type": "factual",
            "importance": "high",
            "confidence": 0.98,
        },
        {
            "id": "claim-2",
            "statement": "The recipient must pay ₹499 to receive the reward.",
            "category": "payment_instruction",
            "claim_type": "behavioral_instruction",
            "importance": "high",
            "confidence": 0.95,
        },
        {
            "id": "claim-3",
            "statement": "The reward must be claimed within 2 hours.",
            "category": "urgency_constraint",
            "claim_type": "behavioral_instruction",
            "importance": "medium",
            "confidence": 0.92,
        },
        {
            "id": "claim-4",
            "statement": "The provided URL is associated with the reward claim.",
            "category": "link_context",
            "claim_type": "contextual",
            "importance": "medium",
            "confidence": 0.90,
        },
    ],
    "entities": [
        {
            "name": "SBI",
            "type": "financial_institution",
            "context": "Referenced in hostname as the purported banking entity",
            "confidence": 0.94,
        }
    ],
    "urls": [
        {
            "url": "https://sbi-reward-claim.example",
            "domain": "sbi-reward-claim.example",
            "context": "Supplied destination for claiming the monetary reward",
        }
    ],
    "suspicious_signals": [
        {
            "type": "advance_payment_request",
            "description": "Demands payment of ₹499 upfront before receiving prize.",
            "confidence": 0.98,
            "evidence": "Pay ₹499 to claim your reward",
        },
        {
            "type": "urgency",
            "description": "Imposes a short 2-hour deadline to induce hasty action.",
            "confidence": 0.95,
            "evidence": "within 2 hours",
        },
        {
            "type": "reward_lure",
            "description": "Promises unsolicited ₹50,000 windfall.",
            "confidence": 0.96,
            "evidence": "You've won ₹50,000",
        },
    ],
}


def _create_mock_client(response_text: str):
    """Create a mock google-genai client returning specified response text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


# 1. Valid structured Gemini response
def test_valid_structured_gemini_response():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("Sample message", client=mock_client)
        assert isinstance(analysis, ContentAnalysis)
        assert analysis.normalized_text.startswith("Congratulations!")
        assert analysis.language.code == "en"
        assert len(analysis.claims) == 4
        assert len(analysis.entities) == 1
        assert len(analysis.urls) == 1
        assert len(analysis.suspicious_signals) == 3


# 2. Multiple claim extraction
def test_multiple_claim_extraction():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("Sample message", client=mock_client)
        statements = [c.statement for c in analysis.claims]
        assert "The recipient has won ₹50,000." in statements
        assert "The recipient must pay ₹499 to receive the reward." in statements
        assert analysis.claims[0].claim_type == "factual"
        assert analysis.claims[1].claim_type == "behavioral_instruction"


# 3. Entity extraction
def test_entity_extraction():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("Sample message", client=mock_client)
        assert len(analysis.entities) == 1
        assert analysis.entities[0].name == "SBI"
        assert analysis.entities[0].type == "financial_institution"
        assert analysis.entities[0].confidence >= 0.9


# 4. URL extraction
def test_url_extraction():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("Sample message", client=mock_client)
        assert len(analysis.urls) == 1
        assert analysis.urls[0].url == "https://sbi-reward-claim.example"
        assert analysis.urls[0].domain == "sbi-reward-claim.example"


# 5. Suspicious signal extraction
def test_suspicious_signal_extraction():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("Sample message", client=mock_client)
        types_found = [s.type for s in analysis.suspicious_signals]
        assert "advance_payment_request" in types_found
        assert "urgency" in types_found
        assert "reward_lure" in types_found
        assert all(s.evidence for s in analysis.suspicious_signals)


# 6. Language detection
def test_language_detection():
    hindi_output = dict(MOCK_VALID_GEMINI_OUTPUT)
    hindi_output["language"] = {"code": "hi", "name": "Hindi", "confidence": 0.97}
    mock_client = _create_mock_client(json.dumps(hindi_output))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        analysis = analyze_content("बधाई हो!", client=mock_client)
        assert analysis.language.code == "hi"
        assert analysis.language.name == "Hindi"
        assert analysis.language.confidence == 0.97


# 7. Invalid structured response
def test_invalid_structured_response():
    mock_client = _create_mock_client("invalid non-json text response")
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError):
            analyze_content("Sample message", client=mock_client)


# 8. Gemini provider error
def test_gemini_provider_error():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = errors.ServerError(503, "Service unavailable", None)
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiProviderError):
            analyze_content("Sample message", client=mock_client)


# 9. Missing API key
def test_missing_api_key():
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": ""}):
        with pytest.raises(GeminiConfigError) as exc_info:
            analyze_content("Sample message", client=None)
        assert "GEMINI_API_KEY" in str(exc_info.value)


# 10. Missing model configuration
def test_missing_model_configuration():
    mock_client = MagicMock()
    with patch.dict(os.environ, {"GEMINI_MODEL": "", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiConfigError) as exc_info:
            analyze_content("Sample message", client=mock_client)
        assert "GEMINI_MODEL" in str(exc_info.value)


# 11. Investigation pipeline integration with mock Gemini
def test_investigate_pipeline_integration():
    mock_client = _create_mock_client(json.dumps(MOCK_VALID_GEMINI_OUTPUT))
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(
            input_type="text",
            content="Congratulations! You've won ₹50,000. Pay ₹499.",
        )
        result = investigate(request, gemini_client=mock_client)

        assert isinstance(result, InvestigationResult)
        assert result.development_mode is True
        assert len(result.claims) == 4
        assert result.claims[0].statement == "The recipient has won ₹50,000."
        assert len(result.scam_signals) >= 3
        assert result.url_analysis is not None
        assert result.url_analysis.domain == "sbi-reward-claim.example"
        assert result.metrics.claims_detected == 4
        assert result.metrics.threat_signals_found >= 3


# 12. Edge Case: response.candidates == None
def test_response_candidates_none():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(candidates=None)
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some prompt", client=mock_client)
        assert "no output candidates" in str(exc_info.value)


# 13. Edge Case: response.candidates == []
def test_response_candidates_empty_list():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(candidates=[])
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some prompt", client=mock_client)
        assert "no output candidates" in str(exc_info.value)


# 14. Edge Case: candidate.finish_reason == FinishReason.SAFETY
def test_response_finish_reason_safety():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.SAFETY,
                content=None,
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Harmful content", client=mock_client)
        assert "safety filters" in str(exc_info.value)


# 15. Edge Case: other non-STOP finish reasons (MAX_TOKENS, RECITATION, PROHIBITED_CONTENT)
@pytest.mark.parametrize(
    "finish_reason,expected_snippet",
    [
        (FinishReason.MAX_TOKENS, "MAX_TOKENS limit"),
        (FinishReason.RECITATION, "RECITATION policy"),
        (FinishReason.PROHIBITED_CONTENT, "prohibited content"),
        (FinishReason.SPII, "sensitive personally identifiable information"),
        (FinishReason.BLOCKLIST, "content blocklist"),
    ],
)
def test_response_non_stop_finish_reasons(finish_reason, expected_snippet):
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=finish_reason,
                content=None,
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some content", client=mock_client)
        assert expected_snippet in str(exc_info.value)


# 16. Edge Case: prompt_feedback.block_reason when present
def test_response_prompt_feedback_block_reason():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        prompt_feedback=types.GenerateContentResponsePromptFeedback(
            block_reason=BlockedReason.SAFETY
        ),
        candidates=[],
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Blocked prompt", client=mock_client)
        assert "blocked prompt processing" in str(exc_info.value)


# 17. Edge Case: candidate with no usable text/parts
def test_response_candidate_no_content():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.STOP,
                content=None,
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some prompt", client=mock_client)
        assert "no content parts" in str(exc_info.value)


def test_response_candidate_empty_parts():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.STOP,
                content=types.Content(parts=[]),
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some prompt", client=mock_client)
        assert "no content parts" in str(exc_info.value)


def test_response_candidate_blank_text_parts():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.STOP,
                content=types.Content(parts=[types.Part.from_text(text="   ")]),
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        with pytest.raises(GeminiSchemaError) as exc_info:
            analyze_content("Some prompt", client=mock_client)
        assert "no usable text parts" in str(exc_info.value)


# 18. Normal FinishReason.STOP response
def test_response_normal_stop_finish_reason():
    mock_client = MagicMock()
    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.STOP,
                content=types.Content(
                    parts=[types.Part.from_text(text=json.dumps(MOCK_VALID_GEMINI_OUTPUT))]
                ),
            )
        ]
    )
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        result = analyze_content("Some prompt", client=mock_client)
        assert isinstance(result, ContentAnalysis)
        assert len(result.claims) == 4
        assert result.claims[0].statement == "The recipient has won ₹50,000."


# 19. Requirement 2 verification: response.text is NEVER accessed if candidate is invalid
def test_response_text_never_accessed_when_candidate_invalid():
    """Ensure response.text is guarded and never accessed if finish_reason is non-STOP or parts are missing."""
    mock_response = MagicMock()
    # If response.text is accessed, raise AssertionError to fail the test immediately
    type(mock_response).text = property(
        lambda self: (_ for _ in ()).throw(AssertionError("CRITICAL: response.text was accessed prematurely!"))
    )
    # Set invalid candidate
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = FinishReason.SAFETY
    mock_response.candidates = [mock_candidate]
    mock_response.prompt_feedback = None

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_API_KEY": "mock-key"}):
        # Must raise GeminiSchemaError, NOT AssertionError
        with pytest.raises(GeminiSchemaError):
            analyze_content("Prompt", client=mock_client)
