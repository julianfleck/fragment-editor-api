from dataclasses import dataclass
from typing import Optional
from ..base.description import DescriptionMixin
from .types import Context
from .styles import Style


@dataclass
class ContentType(DescriptionMixin):
    """Content type and format identifier"""
    primary: str
    subtype: str
    format: str
    context: Optional[Context] = None

    # Add common content type constants
    TEXT = "text"
    ARTICLE = "article"
    DOCUMENTATION = "documentation"
    SPECIFICATION = "specification"

    VALID_TYPES = {
        TEXT: ["plain", "markdown"],
        ARTICLE: ["news", "blog", "academic", "technical"],
        DOCUMENTATION: ["api", "user", "technical", "reference"],
        SPECIFICATION: ["rfc", "standard", "proposal"]
    }

    def __post_init__(self):
        if self.primary not in self.VALID_TYPES:
            raise ValueError(f"Invalid primary type: {self.primary}")
        if self.subtype not in self.VALID_TYPES[self.primary]:
            raise ValueError(f"Invalid subtype for {
                             self.primary}: {self.subtype}")
