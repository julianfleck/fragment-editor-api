from dataclasses import dataclass
from typing import List
from ..base.description import DescriptionMixin


@dataclass
class ContentMetrics(DescriptionMixin):
    """Content transformation and preservation metrics"""
    preserved_terms: List[str]
    context_coherence: float  # 0-1 score
    domain_adherence: float  # 0-1 score
    style_adherence: float   # 0-1 score
    formality_score: float   # Add formality score
    complexity_score: float  # Add complexity score

    def __post_init__(self):
        scores = [
            self.context_coherence,
            self.domain_adherence,
            self.style_adherence,
            self.formality_score,
            self.complexity_score
        ]
        for score in scores:
            if not 0 <= score <= 1:
                raise ValueError("All scores must be between 0 and 1")

    @property
    def is_valid(self) -> bool:
        """Check if metrics meet quality thresholds"""
        return all(score >= 0.8 for score in [
            self.context_coherence,
            self.domain_adherence,
            self.style_adherence,
            self.formality_score,
            self.complexity_score
        ])
