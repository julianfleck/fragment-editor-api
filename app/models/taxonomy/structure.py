from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from .base import TaxonomyNode
from ..content.core import Context


class StructureType(Enum):
    SECTION = "section"      # Logical document sections
    CHUNK = "chunk"         # Length-based chunks
    SEGMENT = "segment"     # Purpose-based segments
    FRAGMENT = "fragment"   # Semantic completeness units


@dataclass
class Version(TaxonomyNode):
    """Single version of transformed text with metrics"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    text: str = ""
    final_tokens: int = 0
    final_percentage: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    # Optional fields
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if not self.text:
            raise ValueError("Text cannot be empty")
        if self.final_tokens <= 0:
            raise ValueError("Token count must be positive")
        if not 0 < self.final_percentage <= 200:
            raise ValueError("Percentage must be between 0 and 200")
        super().__post_init__()


@dataclass
class Length(TaxonomyNode):
    """Length-based transformation target with results"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    target_percentage: int = 0
    target_tokens: int = 0
    # Optional fields
    versions: List[Version] = field(default_factory=list)
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if not 0 < self.target_percentage <= 200:
            raise ValueError("Target percentage must be between 0 and 200")
        if self.target_tokens <= 0:
            raise ValueError("Target tokens must be positive")
        super().__post_init__()


@dataclass
class Section(TaxonomyNode):
    """Represents a logical section of content with its own context and metadata"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    content: str = ""
    # Optional fields
    level: int = 0
    parent: Optional['Section'] = None
    children: List['Section'] = field(default_factory=list)
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if self.level < 0:
            raise ValueError("Section level cannot be negative")
        if not self.content:
            raise ValueError("Section content cannot be empty")
        if self.parent and self.level <= self.parent.level:
            raise ValueError(
                "Child section must have higher level than parent")
        super().__post_init__()


@dataclass
class Chunk(Section):
    """A length-based segment of content, extending Section with chunking attributes"""
    # Optional fields specific to Chunk
    chunk_size: int = 0
    overlap: int = 0
    is_boundary: bool = False

    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.overlap < 0:
            raise ValueError("Overlap cannot be negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("Overlap cannot be larger than chunk size")
        super().__post_init__()


@dataclass
class Segment(TaxonomyNode):
    """A purpose-specific segment of content"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    content: str = ""
    # Optional fields
    segment_type: StructureType = StructureType.SECTION
    category: str = ""
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if not self.content:
            raise ValueError("Segment content cannot be empty")
        if not self.category:
            raise ValueError("Segment category cannot be empty")
        super().__post_init__()


@dataclass
class Fragment(TaxonomyNode):
    """A piece of content that maintains semantic completeness"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    content: str = ""
    fragment_id: str = ""
    # Optional fields
    lengths: List[Length] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if not self.content:
            raise ValueError("Fragment content cannot be empty")
        if not self.fragment_id:
            raise ValueError("Fragment ID is required")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("Fragment dependencies must be unique")
        super().__post_init__()


@dataclass
class StructuredContent(TaxonomyNode):
    """Container for structured content results"""
    # Required fields first (both from parent and this class)
    name: str = ""  # From TaxonomyNode
    structure_type: StructureType = StructureType.SECTION
    # Optional fields
    elements: List[Union[Section, Chunk, Segment, Fragment]
                   ] = field(default_factory=list)
    description: str = ""  # From TaxonomyNode
    metadata: Dict[str, Any] = field(default_factory=dict)  # From TaxonomyNode
    context: Optional[Context] = None  # From TaxonomyNode

    def __post_init__(self):
        if not self.elements:
            raise ValueError("Must have at least one structural element")

        expected_type = {
            StructureType.SECTION: Section,
            StructureType.CHUNK: Chunk,
            StructureType.SEGMENT: Segment,
            StructureType.FRAGMENT: Fragment
        }[self.structure_type]

        if not all(isinstance(e, expected_type) for e in self.elements):
            raise ValueError(f"All elements must be of type {
                             expected_type.__name__}")
        super().__post_init__()
