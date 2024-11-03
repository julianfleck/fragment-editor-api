from dataclasses import dataclass, field
from typing import List, Dict, Any
from ..base.description import DescriptionMixin
from .styles import StyleRegistry


@dataclass
class Context(DescriptionMixin):
    """Contextual information for content processing"""
    domain: str
    style: str
    tone: str
    aspects: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def default() -> 'Context':
        """Create a default Context instance"""
        return Context(
            domain="general",
            style="neutral",
            tone="neutral"
        )

    # Move validation to a separate method that can be called after style resolution
    def validate(self, valid_domains: List[str], valid_tones: List[str], valid_aspects: List[str]) -> None:
        style_registry = StyleRegistry()
        if not style_registry.validate_style(self.style):
            raise ValueError(f"Invalid style: {self.style}. Available styles: {
                             style_registry.available_styles}")
        if self.domain not in valid_domains:
            raise ValueError(f"Invalid domain: {self.domain}")
        if self.tone not in valid_tones:
            raise ValueError(f"Invalid tone: {self.tone}")
        for aspect in self.aspects:
            if aspect not in valid_aspects:
                raise ValueError(f"Invalid aspect: {aspect}")
