from dataclasses import dataclass, field
from typing import Set, List, Optional
from .base import TaxonomyNode


@dataclass
class Category(TaxonomyNode):
    """Represents a content category with hierarchical structure"""
    parent: Optional['Category'] = None
    children: List['Category'] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    weight: float = 1.0  # For weighted categorization

    def __post_init__(self):
        super().__post_init__()
        if not 0 <= self.weight <= 1:
            raise ValueError("Weight must be between 0 and 1")
        if self.parent and self in self.parent.children:
            raise ValueError(
                "Circular reference detected in category hierarchy")
