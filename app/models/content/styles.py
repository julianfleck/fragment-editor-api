from dataclasses import dataclass, field
from typing import Set, Dict, Any
from ..base.description import DescriptionMixin


@dataclass
class Style(DescriptionMixin):
    """Represents a content style with its characteristics"""
    name: str
    formality: float  # 0-1 scale (casual to formal)
    complexity: float  # 0-1 scale (simple to complex)
    tone: str
    characteristics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0 <= self.formality <= 1:
            raise ValueError("Formality must be between 0 and 1")
        if not 0 <= self.complexity <= 1:
            raise ValueError("Complexity must be between 0 and 1")


@dataclass
class StyleRegistry(DescriptionMixin):
    """Registry of available content styles"""
    styles: Dict[str, Style] = field(default_factory=lambda: {
        "formal": Style(
            name="formal",
            formality=0.9,
            complexity=0.7,
            tone="professional",
            characteristics={
                "vocabulary": "advanced",
                "sentence_structure": "complex",
                "academic": True
            }
        ),
        "casual": Style(
            name="casual",
            formality=0.2,
            complexity=0.3,
            tone="conversational",
            characteristics={
                "vocabulary": "simple",
                "sentence_structure": "relaxed",
                "colloquial": True
            }
        ),
        "technical": Style(
            name="technical",
            formality=0.8,
            complexity=0.9,
            tone="precise",
            characteristics={
                "vocabulary": "technical",
                "sentence_structure": "structured",
                "domain_specific": True
            }
        ),
        "simple": Style(
            name="simple",
            formality=0.4,
            complexity=0.2,
            tone="clear",
            characteristics={
                "vocabulary": "basic",
                "sentence_structure": "simple",
                "accessible": True
            }
        ),
        "elaborate": Style(
            name="elaborate",
            formality=0.7,
            complexity=0.8,
            tone="descriptive",
            characteristics={
                "vocabulary": "rich",
                "sentence_structure": "varied",
                "descriptive": True
            }
        )
    })

    @property
    def available_styles(self) -> Set[str]:
        return set(self.styles.keys())

    def get_style(self, name: str) -> Style:
        if name not in self.styles:
            raise ValueError(f"Style '{name}' not found. Available styles: {
                             self.available_styles}")
        return self.styles[name]

    def validate_style(self, name: str) -> bool:
        return name in self.styles
