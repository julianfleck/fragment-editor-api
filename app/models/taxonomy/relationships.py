from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..base.description import DescriptionMixin


@dataclass
class SemanticRelationship(DescriptionMixin):
    """Represents semantic relationships between taxonomy nodes"""
    source: str
    target: str
    relationship_type: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    bidirectional: bool = False

    def __post_init__(self):
        if not self.source:
            raise ValueError("Source cannot be empty")
        if not self.target:
            raise ValueError("Target cannot be empty")
        if not self.relationship_type:
            raise ValueError("Relationship type cannot be empty")
        if not 0 <= self.weight <= 1:
            raise ValueError("Weight must be between 0 and 1")
