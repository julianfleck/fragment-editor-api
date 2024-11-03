from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .base import TaxonomyNode


@dataclass
class Topic(TaxonomyNode):
    """
    Key subject or theme extracted from text. Used for:
    - Contextual preservation during transformation
    - Metadata enrichment
    - Content categorization
    """
    primary: str = field(default="")
    related: List[str] = field(default_factory=list)
    confidence: float = field(default=0.0)
    relevance: float = field(default=0.0)

    def __post_init__(self):
        super().__post_init__()
        if not self.primary:
            raise ValueError("Primary topic cannot be empty")
        if len(self.related) > 6:
            raise ValueError("Maximum 6 related topics allowed")
        if self.primary in self.related:
            raise ValueError("Primary topic cannot be in related topics")
        if len(set(self.related)) != len(self.related):
            raise ValueError("Related topics must be unique")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("Confidence scores must be between 0 and 1")
