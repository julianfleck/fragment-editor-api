from dataclasses import dataclass
from typing import Optional
from ..base.description import DescriptionMixin
from ..content import Context
from .operations import TransformationOperation
from .result import TransformationResult


@dataclass
class CompressionOperation(TransformationOperation, DescriptionMixin):
    """Operation for compressing text content"""
    target_percentage: int = 80  # Default compression target of 80%
    min_tokens: Optional[int] = None
    max_tokens: Optional[int] = None

    def __post_init__(self):
        if self.target_percentage is None or not 0 < self.target_percentage < 100:
            raise ValueError("Compression target must be between 0% and 100%")
        if self.min_tokens is not None and self.min_tokens < 0:
            raise ValueError("Minimum tokens cannot be negative")
        if self.max_tokens is not None and self.max_tokens < 0:
            raise ValueError("Maximum tokens cannot be negative")
        if self.min_tokens and self.max_tokens and self.min_tokens > self.max_tokens:
            raise ValueError(
                "Minimum tokens cannot be greater than maximum tokens")

    def validate_result(self, result: TransformationResult) -> None:
        """Validate compression result"""
        if not result.original or not result.transformed:
            raise ValueError("Both original and transformed content required")

        # Validate compression ratio
        actual_ratio = len(result.transformed) / len(result.original)
        target_ratio = self.target_percentage / 100
        ratio_deviation = abs(actual_ratio - target_ratio)

        if ratio_deviation > target_ratio:
            result.validation.warnings.append(
                f"Compression ratio ({
                    actual_ratio:.2f}) differs significantly "
                f"from target ({target_ratio:.2f})"
            )
            # Cap at 0.5
            result.validation.error_rate += min(ratio_deviation, 0.5)

        # Check token limits if specified
        if self.min_tokens and len(result.transformed.split()) < self.min_tokens:
            result.validation.warnings.append(
                f"Output below minimum token count: {self.min_tokens}")
            result.validation.error_rate += 0.2

        if self.max_tokens and len(result.transformed.split()) > self.max_tokens:
            result.validation.warnings.append(
                f"Output exceeds maximum token count: {self.max_tokens}")
            result.validation.error_rate += 0.2

        # Update coherence score based on compression severity
        result.validation.coherence_score *= max(0.5,
                                                 1 - (ratio_deviation * 2))

    def execute(self, content: str, context: Context) -> TransformationResult:
        """Execute the compression operation"""
        # This is just the interface - actual implementation will be in the service layer
        raise NotImplementedError(
            "Compression operation execution not implemented")
