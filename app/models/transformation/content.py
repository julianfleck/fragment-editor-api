from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, List
from ..base import DescriptionMixin
from ..content import Context, ContentMetrics


@dataclass
class TransformedContent(DescriptionMixin):
    """
    Content after transformation, with context preservation metrics.
    Uses timezone-aware UTC timestamps.
    """
    original: List[str]  # Changed from str to List[str] to match TransformationResult
    transformed: List[str]
    context: Context
    metrics: ContentMetrics
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.original:
            raise ValueError("Original content cannot be empty")
        if not self.transformed:
            raise ValueError("Transformed content cannot be empty")
        if not all(isinstance(item, str) for item in self.original):
            raise ValueError("All original items must be strings")
        if not all(isinstance(item, str) for item in self.transformed):
            raise ValueError("All transformed items must be strings")

    @property
    def is_valid(self) -> bool:
        """Check if transformation is valid"""
        return self.metrics.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "texts": self.transformed,
            "context_metrics": {
                "preserved_terms": self.metrics.preserved_terms,
                "context_coherence": self.metrics.context_coherence,
                "domain_adherence": self.metrics.domain_adherence,
                "style_adherence": self.metrics.style_adherence
            },
            "created_at": self.created_at.isoformat()
        }
