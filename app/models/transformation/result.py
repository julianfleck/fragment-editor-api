from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from ..base.description import DescriptionMixin
from ..content import Context, ContentMetrics
from ..metadata import Metadata
from ..content.styles import Style
from ..base.factories import create_style, create_metadata
from ..responses.transformation import TransformationResponse

if TYPE_CHECKING:
    from ..validation.result import ValidationResult


@dataclass
class TransformationResult(DescriptionMixin):
    """Result of a text transformation operation with flexible response structure"""
    # Core transformation data
    original: List[str]
    transformed: List[str]
    metrics: ContentMetrics
    context: Optional[Context] = None
    validation: Optional[ValidationResult] = None
    style: Style = field(default_factory=create_style)
    metadata: Metadata = field(default_factory=create_metadata)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    target_percentage: Optional[float] = None

    def __post_init__(self):
        if not self.original:
            raise ValueError("Original content cannot be empty")
        if not self.transformed:
            raise ValueError("Transformed content cannot be empty")
        if not isinstance(self.metrics, ContentMetrics):
            raise ValueError("Metrics must be a ContentMetrics instance")

    @property
    def compression_ratio(self) -> float:
        """Calculate actual compression/expansion ratio"""
        return self.final_length / self.original_length

    @property
    def original_length(self) -> int:
        return len(" ".join(self.original).split())

    @property
    def final_length(self) -> int:
        return len(" ".join(self.transformed).split())

    def to_response(self) -> TransformationResponse:
        """Convert to API response with minimal nesting"""
        response = TransformationResponse(
            status=200,
            metadata=self.metadata.to_dict()
        )

        # Single text - flattest structure
        if len(self.transformed) == 1:
            response.fragments = [{
                "text": self.transformed[0],
                "metrics": self.metrics.to_dict()
            }]
            if self.target_percentage:
                response.fragments[0]["target_percentage"] = self.target_percentage
                response.fragments[0]["final_percentage"] = self.compression_ratio * 100

        # Multiple texts
        else:
            response.fragments = [
                {
                    "text": text,
                    "metrics": self.metrics.to_dict(),
                    "final_percentage": self.compression_ratio * 100
                }
                for text in self.transformed
            ]

        if self.validation:
            response.validation = self.validation

        return response

    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary format"""
        result = {
            "text": self.transformed[0] if len(self.transformed) == 1 else None,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata.to_dict(),
            "warnings": [w["message"] for w in self.warnings]
        }

        if len(self.transformed) > 1:
            result["versions"] = [{"text": t} for t in self.transformed]
        if self.target_percentage:
            result["target_percentage"] = self.target_percentage
            result["final_percentage"] = self.compression_ratio * 100
        if self.validation:
            result["validation"] = self.validation.to_dict()
        if self.context:
            result["context"] = self.context.to_dict()

        return {k: v for k, v in result.items() if v is not None}
