from dataclasses import dataclass
from typing import Optional
from ..base.description import DescriptionMixin
from .core import Context


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
    key_points: list[str]
    context: Optional[Context] = None

    def __post_init__(self):
        if len({self.short, self.medium, self.long}) != 3:
            raise ValueError("All summaries must be unique")

        if not self.key_points:
            raise ValueError("Must include at least one key point")
        # Validate relative lengths
        if len(self.medium) <= len(self.short):
            raise ValueError(
                "Medium summary must be longer than short summary")
        if len(self.long) <= len(self.medium):
            raise ValueError("Long summary must be longer than medium summary")
