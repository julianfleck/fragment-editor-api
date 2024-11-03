from dataclasses import dataclass
from typing import Dict, Any
from ..base.description import DescriptionMixin
from ..content import Context


@dataclass
class Version(DescriptionMixin):
    """Single version of transformed text with metrics"""
    text: str
    final_tokens: int
    final_percentage: float
    context: Context
    metrics: Dict[str, float]

    def __post_init__(self):
        if not self.text:
            raise ValueError("Text cannot be empty")
        if self.final_tokens <= 0:
            raise ValueError("Token count must be positive")
        if not 0 < self.final_percentage <= 200:  # Allow up to 200% expansion
            raise ValueError("Percentage must be between 0 and 200")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "text": self.text,
            "final_tokens": self.final_tokens,
            "final_percentage": self.final_percentage,
            "metrics": self.metrics
        }
