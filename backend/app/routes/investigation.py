import logging
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.schemas.investigation import InvestigationRequest
from app.services.gemini_service import GeminiServiceError
from app.services.investigation_service import investigate

logger = logging.getLogger("truthlens.routes.investigation")

investigation_bp = Blueprint("investigation", __name__)


@investigation_bp.route("/investigate", methods=["POST"])
def run_investigation():
    """Execute a content investigation through the service layer.

    Accepts:
      {
        "input_type": "text" | "image" | "url",
        "content": "message text or url",
        "image_url": "optional url",
        "metadata": {}
      }

    Returns:
      Serialized InvestigationResult matching the TypeScript frontend contract.
    """
    data = request.get_json(silent=True)
    if data is None:
        return (
            jsonify({
                "error": "Bad Request",
                "detail": "Request body must be valid application/json",
            }),
            400,
        )

    # Allow frontend parameter aliases (e.g. inputMode -> input_type, text -> content)
    normalized_data = dict(data)
    if "inputMode" in normalized_data and "input_type" not in normalized_data:
        normalized_data["input_type"] = normalized_data["inputMode"]
    if "text" in normalized_data and "content" not in normalized_data:
        normalized_data["content"] = normalized_data["text"]

    try:
        validated_request = InvestigationRequest(**normalized_data)
    except ValidationError as err:
        errors = [
            {
                "field": ".".join(str(loc) for loc in e.get("loc", [])),
                "message": e.get("msg", ""),
                "type": e.get("type", ""),
            }
            for e in err.errors()
        ]
        return (
            jsonify({
                "error": "Unprocessable Entity",
                "message": "Investigation request payload validation failed",
                "details": errors,
            }),
            422,
        )
    except Exception as err:
        return (
            jsonify({
                "error": "Bad Request",
                "message": str(err),
            }),
            400,
        )

    # Pass to service layer
    try:
        result = investigate(validated_request)
    except GeminiServiceError as err:
        logger.error(f"[{err.category}] {err.message}")
        return (
            jsonify({
                "error": err.category,
                "message": err.message,
            }),
            err.status_code,
        )
    except Exception as err:
        logger.error(f"[INTERNAL_ERROR] Investigation failed: {err.__class__.__name__}")
        return (
            jsonify({
                "error": "Internal Server Error",
                "message": "Investigation processing encountered an error.",
            }),
            500,
        )

    # Return serialized model with camelCase keys matching frontend TypeScript types
    return jsonify(result.model_dump(by_alias=True)), 200
