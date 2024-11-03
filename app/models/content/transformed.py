from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any
from ..base import DescriptionMixin
from .core import Context
from .metrics import ContentMetrics


@dataclass
class TransformedContent(DescriptionMixin):
    """
    Content after transformation, with context preservation metrics.
    Uses timezone-aware UTC timestamps.
    """
    original: str
    transformed: str
    context: Context
    metrics: ContentMetrics
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.original:
            raise ValueError("Original content cannot be empty")
        if not self.transformed:
            raise ValueError("Transformed content cannot be empty")

    @property
    def is_valid(self) -> bool:
        """Check if transformation is valid"""
        return self.metrics.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "text": self.transformed,
            "context_metrics": {
                "preserved_terms": self.metrics.preserved_terms,
                "context_coherence": self.metrics.context_coherence,
                "domain_adherence": self.metrics.domain_adherence,
                "style_adherence": self.metrics.style_adherence
            },
            "created_at": self.created_at.isoformat()
        }
