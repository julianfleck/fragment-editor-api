from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from .base import DescriptionMixin
from .content import Context, ContentType
from .taxonomy import Section


class SegmentationType(Enum):
    SEMANTIC = "semantic"      # Based on meaning
    STRUCTURAL = "structural"  # Based on document structure
    SYNTACTIC = "syntactic"    # Based on grammar/syntax
    LENGTH = "length"          # Based on size/tokens


@dataclass
class Segment(DescriptionMixin):
    """A categorized segment of content"""
    content: str
    segment_type: SegmentationType
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Context] = None


@dataclass
class Fragment(DescriptionMixin):
    """A smaller piece of complex content"""
    content: str
    fragment_id: str
    content_type: ContentType
    dependencies: List[str] = field(
        default_factory=list)  # IDs of related fragments
    context: Optional[Context] = None

    def __post_init__(self):
        if not self.fragment_id:
            raise ValueError("fragment_id is required")


@dataclass
class Chunk(Section):
    """
    A logical section of content, extending Section with chunking-specific attributes.
    Inherits hierarchical structure from Section.
    """
    chunk_size: int = field(default=1000)  # Size in tokens
    overlap: int = field(default=0)  # Overlap with adjacent chunks
    # Whether this chunk is at a natural boundary
    is_boundary: bool = field(default=False)

    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0:
            raise ValueError("overlap cannot be negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap cannot be larger than chunk_size")


@dataclass
class SegmentationResult(DescriptionMixin):
    """Results of a segmentation operation"""
    segments: List[Segment]
    segment_type: SegmentationType
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Context] = None

    def __post_init__(self):
        if not self.segments:
            raise ValueError("Must have at least one segment")
