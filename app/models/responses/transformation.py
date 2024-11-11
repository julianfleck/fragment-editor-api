from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from .base import BaseResponse
from ..metadata import Metadata
from ..taxonomy.structure import Fragment, Length, Version
from ..validation.result import ValidationResult
from ..base.factories.validation import create_validation_result
from ..base.factories.taxonomy import create_fragment

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
        """Convert to API response format with minimal nesting"""
        base_dict = super().to_dict()
        response = {**base_dict}

        # Single text transformation
        if len(self.fragments) == 1 and len(self.fragments[0].lengths) == 1:
            length = self.fragments[0].lengths[0]

            # Single version - simplest case
            if len(length.versions) == 1:
                version = length.versions[0]
                response.update({
                    "text": version.text,
                    "metrics": version.metrics
                })
            # Multiple versions
            else:
                response["versions"] = [v.to_dict() for v in length.versions]

        # Multiple lengths (expand/compress)
        elif len(self.fragments) == 1 and len(self.fragments[0].lengths) > 1:
            response["lengths"] = [
                {
                    "target_percentage": l.target_percentage,
                    "text": l.versions[0].text if l.versions else "",
                    "metrics": l.versions[0].metrics if l.versions else {}
                }
                for l in self.fragments[0].lengths
            ]

        # Multiple fragments
        else:
            response["fragments"] = [
                {
                    "text": f.lengths[0].versions[0].text,
                    "metrics": f.lengths[0].versions[0].metrics
                }
                for f in self.fragments
            ]

        if self.validation:
            response["validation"] = self.validation.to_dict()

        return response

    @classmethod
    def from_result(cls, result: TransformationResult) -> TransformationResponse:
        """Create response from transformation result"""
        # Create validation result using factory with result metrics
        validation = create_validation_result()
        validation.style_adherence = result.metrics.style_adherence
        validation.error_rate = 1.0 - result.metrics.style_adherence
        validation.coherence_score = result.metrics.context_coherence
        validation.preserved_terms = result.metrics.preserved_terms

        # Single text transformation - flattest structure
        if len(result.transformed) == 1:
            fragment = create_fragment()
            fragment.lengths = [Length(
                target_percentage=100,
                target_tokens=len(result.transformed[0].split()),
                versions=[Version(
                    text=result.transformed[0],
                    final_tokens=len(result.transformed[0].split()),
                    final_percentage=100.0,
                    context=result.context,
                    metrics=result.metrics.to_dict()
                )]
            )]
            fragments = [fragment]

        # Multiple fragments - keep fragment structure
        else:
            fragments = []
            for original, transformed in zip(result.original, result.transformed):
                fragment = create_fragment()
                fragment.lengths = [Length(
                    target_percentage=100,
                    target_tokens=len(transformed.split()),
                    versions=[Version(
                        text=transformed,
                        final_tokens=len(transformed.split()),
                        final_percentage=100.0,
                        context=result.context,
                        metrics=result.metrics.to_dict()
                    )]
                )]
                fragments.append(fragment)

        return cls(
            fragments=fragments,
            validation=validation,
            metadata={"style_adherence": result.metrics.style_adherence}
        )
