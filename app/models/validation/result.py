from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING
from ..base.description import DescriptionMixin
from ..base.interfaces import ValidationResultInterface

if TYPE_CHECKING:
    from ..transformation.result import TransformationResult


@dataclass
class ValidationResult(DescriptionMixin, ValidationResultInterface):
    """Validation results for a text transformation operation"""
    length_match: bool
    context_preserved: bool
    warnings: List[str] = field(default_factory=list)
    error_rate: float = 0.0
    preserved_terms: List[str] = field(default_factory=list)
    coherence_score: float = 1.0
    style_adherence: float = 1.0
    _validation_state: bool = field(default=True)

    def __post_init__(self):
        if not 0 <= self.error_rate <= 1:
            raise ValueError("Error rate must be between 0 and 1")
        if not 0 <= self.coherence_score <= 1:
            raise ValueError("Coherence score must be between 0 and 1")
        if not 0 <= self.style_adherence <= 1:
            raise ValueError("Style adherence must be between 0 and 1")

    @property
    def is_valid(self) -> bool:
        return (
            self._validation_state and
            self.length_match and
            self.context_preserved and
            self.error_rate < 0.1 and
            self.coherence_score > 0.8 and
            self.style_adherence > 0.8 and
            not self.warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation results to dictionary format"""
        return {
            "length_match": self.length_match,
            "context_preserved": self.context_preserved,
            "warnings": self.warnings,
            "error_rate": self.error_rate,
            "preserved_terms": self.preserved_terms,
            "coherence_score": self.coherence_score,
            "style_adherence": self.style_adherence,
            "is_valid": self.is_valid
        }

    def validate_transformation(self, result: 'TransformationResult') -> None:
        """
        Validate transformation results against quality thresholds
        Updates validation state based on content metrics and rules
        """
        # Validate metrics against thresholds
        if result.metrics.context_coherence < 0.8:
            self.warnings.append("Low context coherence score")
            self.error_rate += 0.2
            self.context_preserved = False

        if result.metrics.style_adherence < 0.8:
            self.warnings.append("Style adherence below threshold")
            self.error_rate += 0.2
            self.style_adherence = result.metrics.style_adherence

        # Check length constraints
        if hasattr(result, 'compression_ratio'):
            target_ratio = getattr(result, 'target_percentage', 100) / 100
            ratio_deviation = abs(result.compression_ratio - target_ratio)

            if ratio_deviation > 0.2:  # 20% deviation threshold
                self.warnings.append(
                    f"Length deviation of {
                        ratio_deviation:.2%} exceeds threshold"
                )
                self.error_rate += min(ratio_deviation, 0.3)
                self.length_match = False

        # Update preserved terms
        self.preserved_terms = result.metrics.preserved_terms

        # Update coherence score
        self.coherence_score = min(
            self.coherence_score,
            result.metrics.context_coherence
        )

        # Update internal validation state
        self._validation_state = (
            self.error_rate < 0.1 and
            self.coherence_score >= 0.8 and
            self.style_adherence >= 0.8 and
            self.context_preserved and
            self.length_match
        )
