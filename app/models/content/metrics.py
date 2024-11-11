from dataclasses import dataclass
from typing import List, Optional
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

    def __init__(self, preserved_terms: Optional[List[str]] = None,
                 context_coherence: float = 1.0,
                 domain_adherence: float = 1.0,
                 style_adherence: float = 1.0,
                 formality_score: float = 0.5,
                 complexity_score: float = 0.5):
        self.preserved_terms = preserved_terms or []
        self.context_coherence = context_coherence
        self.domain_adherence = domain_adherence
        self.style_adherence = style_adherence
        self.formality_score = formality_score
        self.complexity_score = complexity_score
