from dataclasses import dataclass
from typing import Optional
from ..base.description import DescriptionMixin
from ..content import Context
from .operations import TransformationOperation
from .result import TransformationResult


@dataclass
class ExpansionOperation(TransformationOperation, DescriptionMixin):
    """Operation for expanding text content"""
    target_percentage: int = 120  # Default expansion target of 120%
    min_tokens: Optional[int] = None
    max_tokens: Optional[int] = None

    def __post_init__(self):
        if not self.target_percentage:
            raise ValueError("Expansion target percentage is required")
        if not 100 < self.target_percentage <= 200:
            raise ValueError("Expansion target must be between 100% and 200%")
        if self.min_tokens is not None and self.min_tokens < 0:
            raise ValueError("Minimum tokens cannot be negative")
        if self.max_tokens is not None and self.max_tokens < 0:
            raise ValueError("Maximum tokens cannot be negative")
        if self.min_tokens and self.max_tokens and self.min_tokens > self.max_tokens:
            raise ValueError(
                "Minimum tokens cannot be greater than maximum tokens")

    def validate_result(self, result: TransformationResult) -> None:
        """Validate expansion result"""
        if not result.original or not result.transformed:
            raise ValueError("Both original and transformed content required")

        # Validate expansion ratio
        actual_ratio = len(result.transformed) / len(result.original)
        target_ratio = self.target_percentage / 100
        ratio_deviation = abs(actual_ratio - target_ratio)

        if ratio_deviation > (target_ratio - 1):  # More lenient for expansion
            result.validation.warnings.append(
                f"Expansion ratio ({actual_ratio:.2f}) differs significantly "
                f"from target ({target_ratio:.2f})"
            )
            # Less penalty for expansion
            result.validation.error_rate += min(ratio_deviation / 2, 0.4)

        # Check token limits if specified
        if self.min_tokens and len(result.transformed.split()) < self.min_tokens:
            result.validation.warnings.append(
                f"Output below minimum token count: {self.min_tokens}")
            result.validation.error_rate += 0.2

        if self.max_tokens and len(result.transformed.split()) > self.max_tokens:
            result.validation.warnings.append(
                f"Output exceeds maximum token count: {self.max_tokens}")
            result.validation.error_rate += 0.2

        # Update coherence score based on expansion quality
        # More lenient for expansion
        result.validation.coherence_score *= max(
            0.6, 1 - (ratio_deviation * 1.5))

    def execute(self, content: str, context: Context) -> TransformationResult:
        """Execute the expansion operation"""
        # This is just the interface - actual implementation will be in the service layer
        raise NotImplementedError(
            "Expansion operation execution not implemented")
