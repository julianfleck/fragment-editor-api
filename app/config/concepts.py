from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import inspect


class DescriptionMixin:
    """Mixin class to provide description access methods"""

    @classmethod
    def get_description(cls) -> str:
        """Get the class's docstring description"""
        return inspect.getdoc(cls) or ""

    @classmethod
    def get_field_descriptions(cls) -> Dict[str, str]:
        """Get descriptions of all fields from their type hints' docstrings"""
        return {
            name: inspect.getdoc(hint) or ""
            for name, hint in cls.__annotations__.items()
        }


@dataclass
class Summary(DescriptionMixin):
    """
    A list of summaries of text content at different compression levels.
    Summaries are ordered from short to long and must be unique from each other.
    Used for preview generation, content adaptation, and quick scanning of content.
    """
    short: str  # 1-2 sentences maximum
    medium: str  # roughly 1/3 of original text length
    long: str   # roughly 2/3 of original text, excluding redundancy

    def __post_init__(self):
        if len({self.short, self.medium, self.long}) != 3:
            raise ValueError("All summaries must be unique")


@dataclass
class ContentType(DescriptionMixin):
    """
    Identifies the semantic type and format of content being processed.
    Used to optimize transformation strategies and maintain appropriate style.
    Content type should factor in both the structure and source of the content
    (e.g., if from a newspaper, likely a news article).

    Valid combinations are defined in VALID_TYPES to ensure consistent categorization.
    """
    primary: str
    subtype: str
    format: str

    VALID_TYPES = {
        "article": ["news", "blog", "academic", "technical"],
        "documentation": ["api", "user", "technical", "reference"],
        "specification": ["rfc", "standard", "proposal"]
    }


@dataclass
class Topics(DescriptionMixin):
    """
    Key subjects and themes extracted from the text. Used for:
    - Contextual preservation during transformation
    - Metadata enrichment
    - Content categorization

    Limited to a primary topic and maximum 6 related topics to maintain focus
    and relevance. Topics should be specific enough to be meaningful but
    general enough to be useful for categorization.
    """
    primary: str
    related: List[str]

    def __post_init__(self):
        if len(self.related) > 6:
            raise ValueError("Maximum 6 related topics allowed")


@dataclass
class Section(DescriptionMixin):
    """
    A semantic text chunk that maintains coherent meaning. Guidelines:
    - Optimal size: 3-5 sentences
    - Short texts (~400 chars): ~4 sections
    - Medium texts (~800 chars): ~8 sections
    - Preserves headlines and document structure

    Sections should be semantically coherent units that can be summarized
    distinctly from adjacent sections. Headlines are preserved and associated
    with their relevant content.
    """
    content: str
    heading: Optional[str] = None
    level: int = 0
    tokens: int = 0

    def __post_init__(self):
        self.tokens = len(self.content.split())


@dataclass
class Taxonomy(DescriptionMixin):
    """
    Classification hierarchy for content organization:

    Hypernyms: Broader categories that the text belongs to
    (e.g., "technology" for AI content). Used for:
    - Context preservation
    - Style adaptation
    - Content classification

    Hyponyms: Specific subcategories within the text's domain
    (e.g., "neural networks" for AI content). Used for:
    - Detail preservation
    - Technical accuracy
    - Specialized transformations

    Both limited to 5-7 highly relevant terms.
    """
    hypernyms: List[str]
    hyponyms: List[str]

    def __post_init__(self):
        if len(self.hypernyms) > 7 or len(self.hyponyms) > 7:
            raise ValueError("Maximum 7 terms per category")


@dataclass
class Metadata(DescriptionMixin):
    """
    Structured information about the text content including:
    - Content type and format
    - Topics and categories
    - Processing history and timestamps
    - Source attribution

    Used for operation optimization, content tracking, and maintaining
    processing history. Essential for validation and quality control
    of transformations.
    """
    content_type: ContentType
    topics: Topics
    taxonomy: Taxonomy
    created_at: datetime
    processed_at: datetime
    version: str
    source: Optional[str] = None


@dataclass
class ValidationResult(DescriptionMixin):
    """
    Quality assurance data for text transformations:
    - Length accuracy compared to target
    - Semantic preservation verification
    - Processing warnings and issues
    - Transformation accuracy metrics

    Used to ensure transformations meet quality standards and
    maintain semantic integrity. Error rate should typically
    be below 0.1 for acceptable results.
    """
    length_match: bool
    context_preserved: bool
    warnings: List[str]
    error_rate: float

    @property
    def is_valid(self) -> bool:
        return (self.length_match and
                self.context_preserved and
                not self.warnings and
                self.error_rate < 0.1)


@dataclass
class TransformationResult(DescriptionMixin):
    """
    Complete result of a text transformation operation including:
    - Transformed content
    - Length metrics
    - Metadata and taxonomy
    - Validation results
    - Optional section breakdown
    - Optional summaries
    """
    content: str
    original_length: int
    final_length: int
    metadata: Metadata
    validation: ValidationResult
    sections: Optional[List[Section]] = None
    summaries: Optional[Summary] = None

    @property
    def compression_ratio(self) -> float:
        return self.final_length / self.original_length
