from dataclasses import dataclass, field
from typing import List, Optional
from ..base import DescriptionMixin
from ..content import Context
from ..taxonomy.structure import Length
from ..content.core import ContentType


@dataclass
class Fragment(DescriptionMixin):
    """Processed text fragment with transformation results"""
    lengths: List[Length]
    context: Optional[Context] = None
    fragment_id: Optional[str] = None
    content_type: Optional[ContentType] = None
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.lengths:
            raise ValueError("Fragment must have at least one length target")
