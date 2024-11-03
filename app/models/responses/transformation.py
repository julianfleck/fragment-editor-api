from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from .base import BaseResponse
from ..metadata import Metadata
from ..taxonomy.structure import Fragment, Length, Version
from ..base.factories import create_validation_result, create_fragment

if TYPE_CHECKING:
    from ..transformation.result import TransformationResult
    from ..validation.result import ValidationResult


@dataclass
class TransformationResponse(BaseResponse):
    """API response for text transformation operations"""
    fragments: List[Fragment] = field(default_factory=list)
    validation: Optional[ValidationResult] = None
    type: str = field(default="transformation")

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        return {
            **base_dict,
            "fragments": [f.to_dict() for f in self.fragments],
            "validation": self.validation.to_dict() if self.validation else None
        }

    @classmethod
    def from_result(cls, result: TransformationResult) -> TransformationResponse:
        """Create response from transformation result"""
        # Create ValidationResult using factory with result metrics
        validation = create_validation_result()
        validation.style_adherence = result.metrics.style_adherence
        validation.error_rate = 1.0 - result.metrics.style_adherence
        validation.coherence_score = result.metrics.context_coherence
        validation.preserved_terms = result.metrics.preserved_terms

        # Create Fragment using factory
        fragment = create_fragment()
        fragment.lengths = [Length(
            target_percentage=100,
            target_tokens=len(result.transformed.split()),
            versions=[Version(
                text=result.transformed,
                final_tokens=len(result.transformed.split()),
                final_percentage=100.0,
                context=result.context,
                metrics=result.metrics.to_dict()
            )]
        )]

        return cls(
            fragments=[fragment],
            validation=validation,
            metadata={"style_adherence": result.metrics.style_adherence}
        )
