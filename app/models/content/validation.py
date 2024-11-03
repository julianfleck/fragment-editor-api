from dataclasses import dataclass
from typing import List, Dict, Any
from ..base.description import DescriptionMixin
from .core import Context


@dataclass
class ContentValidation(DescriptionMixin):
    """
    Content-specific validation results.
    Focuses on semantic and contextual validity.
    """
    is_coherent: bool
    is_complete: bool
    readability_score: float  # 0-1 score
    grammar_score: float      # 0-1 score
    context_match: float      # 0-1 score
    issues: List[Dict[str, Any]]

    def __post_init__(self):
        scores = [self.readability_score,
                  self.grammar_score, self.context_match]
        for score in scores:
            if not 0 <= score <= 1:
                raise ValueError("All scores must be between 0 and 1")

    @property
    def is_valid(self) -> bool:
        return (
            self.is_coherent and
            self.is_complete and
            self.readability_score >= 0.7 and
            self.grammar_score >= 0.8 and
            self.context_match >= 0.8 and
            not any(issue.get('severity') == 'error' for issue in self.issues)
        )
