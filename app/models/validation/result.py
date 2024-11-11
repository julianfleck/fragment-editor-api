from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING, Optional
from ..base.description import DescriptionMixin
from ..base.interfaces import ValidationResultInterface

if TYPE_CHECKING:
    from ..transformation.result import TransformationResult


@dataclass
class ValidationResult(DescriptionMixin, ValidationResultInterface):
    """Validation results for a text transformation operation"""
    length_match: bool = True
    context_preserved: bool = True
    _warnings: List[Dict[str, Any]] = field(default_factory=list)
    error_rate: float = 0.0
    preserved_terms: List[str] = field(default_factory=list)
    coherence_score: float = 1.0
    style_adherence: float = 1.0

    @property
    def warnings(self) -> List[str]:
        """Get validation warnings as list of strings"""
        return [w["message"] for w in self._warnings]

    def extend_warnings(self, new_warnings: List[Dict[str, Any]] | List[str]) -> None:
        """Extend warnings list with new warnings, handling both structured and string formats"""
        for warning in new_warnings:
            if isinstance(warning, str):
                self._warnings.append({
                    "code": "GENERAL_WARNING",
                    "message": warning,
                    "details": {}
                })
            else:
                self._warnings.append(warning)

    @property
    def is_valid(self) -> bool:
        """Computed validation state based on actual metrics"""
        return (
            self.error_rate < 0.3 and
            self.coherence_score >= 0.8 and
            self.style_adherence >= 0.8 and
            self.context_preserved and
            self.length_match
        )

    def add_warning(self, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning with structured data"""
        self._warnings.append({
            "code": code,
            "message": message,
            "details": details or {}
        })

    def validate_transformation(self, result: 'TransformationResult') -> None:
        """Validate transformation results against quality thresholds"""
        # Validate metrics against thresholds
        if result.metrics.context_coherence < 0.8:
            self.add_warning(
                "LOW_COHERENCE",
                "Low context coherence score",
                {"score": result.metrics.context_coherence}
            )
            self.error_rate += 0.2
            self.context_preserved = False

        if result.metrics.style_adherence < 0.8:
            self.add_warning(
                "LOW_STYLE_ADHERENCE",
                "Style adherence below threshold",
                {"score": result.metrics.style_adherence}
            )
            self.error_rate += 0.2
            self.style_adherence = result.metrics.style_adherence

        # Check length constraints
        if hasattr(result, 'compression_ratio'):
            target_ratio = getattr(result, 'target_percentage', 100) / 100
            ratio_deviation = abs(result.compression_ratio - target_ratio)

            if ratio_deviation > 0.2:  # 20% deviation threshold
                self.add_warning(
                    "LENGTH_DEVIATION",
                    f"Length deviation of {
                        ratio_deviation:.2%} exceeds threshold",
                    {"deviation": ratio_deviation}
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "is_valid": self.is_valid,
            "length_match": self.length_match,
            "context_preserved": self.context_preserved,
            "warnings": self._warnings,
            "error_rate": self.error_rate,
            "preserved_terms": self.preserved_terms,
            "coherence_score": self.coherence_score,
            "style_adherence": self.style_adherence
        }
