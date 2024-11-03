from dataclasses import dataclass, field
from typing import Dict, Any, List, Set
from .base import ValidationBase


@dataclass
class ValidationRules(ValidationBase):
    """Defines validation rules and thresholds"""
    min_length: int = 1
    max_length: int = 100000
    min_coherence: float = 0.8
    max_error_rate: float = 0.1
    required_fields: Set[str] = field(default_factory=set)
    forbidden_terms: Set[str] = field(default_factory=set)
    custom_rules: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.min_length < 0:
            raise ValueError("Minimum length cannot be negative")
        if self.max_length <= self.min_length:
            raise ValueError(
                "Maximum length must be greater than minimum length")
        if not 0 <= self.min_coherence <= 1:
            raise ValueError("Minimum coherence must be between 0 and 1")
        if not 0 <= self.max_error_rate <= 1:
            raise ValueError("Maximum error rate must be between 0 and 1")


@dataclass
class ContentValidation:
    """Content validation constants"""
    VALID_DOMAINS = ["general", "technical", "academic", "business"]
    VALID_TONES = ["formal", "casual", "technical", "conversational"]
    VALID_ASPECTS = ["clarity", "conciseness", "accuracy", "engagement"]
