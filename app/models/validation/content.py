from dataclasses import dataclass
from typing import List, Dict, Any
from ..content import ContentMetrics
from .base import ValidationBase
from ..transformation.content import TransformedContent


@dataclass
class ContentValidationChain:
    """Handles the complete validation chain for content transformations"""

    @staticmethod
    def validate_transformation(content: TransformedContent) -> ValidationBase:
        validation = ValidationBase()

        # Content validation
        if not content.original or not content.transformed:
            validation.add_error("EMPTY_CONTENT", "Content cannot be empty")
            return validation

        # Metrics validation
        metrics = content.metrics
        if metrics.context_coherence < 0.8:
            validation.add_warning(
                "LOW_COHERENCE",
                "Context coherence below threshold",
                {"score": metrics.context_coherence}
            )

        if metrics.style_adherence < 0.8:
            validation.add_warning(
                "LOW_STYLE_ADHERENCE",
                "Style adherence below threshold",
                {"score": metrics.style_adherence}
            )

        return validation
