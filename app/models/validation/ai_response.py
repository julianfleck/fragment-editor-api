from dataclasses import dataclass
from typing import Dict, Any, List
from .base import ValidationBase
from ..validation import ValidationError
import logging

logger = logging.getLogger(__name__)


class AIResponseValidator:
    """Validates AI response data"""

    @classmethod
    def validate_texts(cls, response: Dict[str, Any], expected_count: int = 1) -> List[str]:
        """Validate and extract transformed texts from AI response"""
        logger.debug(f"Validating response for {expected_count} texts")
        texts = []

        # Handle fragments format (multiple input texts)
        if "fragments" in response:
            for fragment in response["fragments"]:
                if fragment.get("lengths") and fragment["lengths"][0].get("versions"):
                    texts.append(fragment["lengths"][0]
                                 ["versions"][0].get("text", ""))

        # Handle single text format (lengths at root level)
        elif "lengths" in response and response["lengths"]:
            texts = [response["lengths"][0]["versions"][0].get("text", "")]

        # Handle direct versions format (fallback)
        elif "versions" in response:
            texts = [v.get("text", "") for v in response["versions"]]

        if not texts:
            raise ValidationError(
                code="NO_TEXTS_FOUND",
                message="No valid texts found in response"
            )

        # Handle mismatched counts
        if len(texts) < expected_count:
            logger.warning(f"Found fewer texts than expected ({
                           len(texts)}/{expected_count})")
            texts.extend([""] * (expected_count - len(texts)))
        elif len(texts) > expected_count:
            logger.warning(f"Found more texts than expected ({
                           len(texts)}/{expected_count})")
            texts = texts[:expected_count]

        return texts

    @classmethod
    def validate_metrics(cls, response: Dict[str, Any]) -> Dict[str, float]:
        """Extract and validate transformation metrics"""
        metrics = {
            "preserved_terms": 1.0,
            "context_coherence": 1.0,
            "domain_adherence": 1.0,
            "style_adherence": 1.0
        }

        # Handle different response formats
        if "lengths" in response and response["lengths"]:
            source = response["lengths"][0]
        elif "fragments" in response and response["fragments"]:
            source = response["fragments"][0].get("lengths", [{}])[0]
        else:
            source = response

        # Extract metrics if present
        if "metrics" in source:
            for key in metrics:
                if key in source["metrics"]:
                    value = float(source["metrics"][key])
                    # Clamp between 0 and 1
                    metrics[key] = max(0.0, min(1.0, value))

        return metrics

    @classmethod
    def validate_response_structure(cls, response: Dict[str, Any]) -> None:
        """Validate overall response structure"""
        valid_root_keys = {"lengths", "fragments",
                           "versions", "metrics", "error"}

        if not any(key in response for key in valid_root_keys):
            raise ValidationError(
                code="INVALID_STRUCTURE",
                message=f"Response must contain one of: {
                    ', '.join(valid_root_keys)}"
            )

        # Check for error response
        if "error" in response:
            raise ValidationError(
                code=response["error"].get("code", "UNKNOWN_ERROR"),
                message=response["error"].get(
                    "message", "Unknown error occurred")
            )
