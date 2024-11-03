from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..base.description import DescriptionMixin
from ..content.types import Context


@dataclass
class TaxonomyNode(DescriptionMixin):
    """Base class for all taxonomy-related nodes"""
    name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Context] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty")
        if self.description and len(self.description) > 500:
            raise ValueError("Description must be 500 characters or less")
