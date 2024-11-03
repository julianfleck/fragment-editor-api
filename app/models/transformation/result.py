from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from ..base.description import DescriptionMixin
from ..content import Context, ContentMetrics
from ..metadata import ContentMetadata, Metadata
from ..taxonomy.structure import Fragment, Length, Version
from ..base.interfaces import TransformationResultBase
from ..content.styles import Style
from ..base.factories import (
    create_context,
    create_content_metrics,
    create_validation_result,
    create_metadata,
    create_style
)

if TYPE_CHECKING:
    from ..validation.result import ValidationResult


@dataclass
class TransformationResult(DescriptionMixin, TransformationResultBase):
    """Complete result of a text transformation operation"""
    original: str = ""
    transformed: str = ""
    context: Context = field(default_factory=create_context)
    metrics: ContentMetrics = field(default_factory=create_content_metrics)
    metadata: ContentMetadata = field(default_factory=create_metadata)
    validation: ValidationResult = field(
        default_factory=create_validation_result)
    sections: Optional[List[Fragment]] = None
    style: Style = field(default_factory=create_style)
    warnings: List[str] = field(default_factory=list)
    error_rate: float = 0.0
    coherence_score: float = 1.0

    def __post_init__(self):
        if not self.original:
            raise ValueError("Original content cannot be empty")
        if not self.transformed:
            raise ValueError("Transformed content cannot be empty")
        if not 0 <= self.validation.style_adherence <= 1:
            raise ValueError("Style adherence must be between 0 and 1")
        if not 0 <= self.error_rate <= 1:
            raise ValueError("Error rate must be between 0 and 1")
        if not 0 <= self.coherence_score <= 1:
            raise ValueError("Coherence score must be between 0 and 1")

    @property
    def compression_ratio(self) -> float:
        """Calculate actual compression/expansion ratio"""
        return len(self.transformed) / len(self.original)

    @property
    def is_valid(self) -> bool:
        """Check if transformation is valid using stricter criteria"""
        return (
            self.metrics.is_valid and
            self.validation.style_adherence >= 0.8 and
            self.validation.error_rate < 0.1 and
            self.validation.coherence_score > 0.8 and
            not self.validation.warnings  # Consider warnings as validation criteria
        )

    def to_dict(self) -> Dict[str, Any]:
        """Enhanced to_dict with more comprehensive metrics"""
        base_dict = super().to_dict()
        base_dict.update({
            "style_metrics": {
                "adherence": self.validation.style_adherence,
                "target_style": self.style
            },
            "compression_ratio": self.compression_ratio,
            "metrics": self.metrics.to_dict()
        })
        return base_dict

    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "fragments": [
                {
                    "lengths": [
                        {
                            "target_percentage": length.target_percentage,
                            "target_tokens": length.target_tokens,
                            "versions": [
                                version.to_dict() for version in length.versions
                            ]
                        }
                        for length in fragment.lengths
                    ]
                }
                for fragment in (self.sections or [Fragment(lengths=[
                    Length(
                        target_percentage=int(self.compression_ratio * 100),
                        target_tokens=len(self.transformed.split()),
                        versions=[Version(
                            text=self.transformed,
                            final_tokens=len(self.transformed.split()),
                            final_percentage=self.compression_ratio * 100,
                            context=self.context,
                            metrics=self.metrics.to_dict()
                        )]
                    )
                ], context=self.context)])
            ],
            "metadata": self.metadata.to_dict(),
            "validation": self.validation.to_dict()
        }
