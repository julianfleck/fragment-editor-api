from typing import Set, Dict, Any
from ....models.validation import ValidationResult, ValidationRules


def create_validation_result() -> ValidationResult:
    """Creates a default ValidationResult instance"""
    return ValidationResult(
        length_match=True,
        context_preserved=True,
        _warnings=[],
        error_rate=0.0,
        preserved_terms=[],
        coherence_score=1.0,
        style_adherence=1.0
    )


def create_validation_rules() -> ValidationRules:
    """Creates a default ValidationRules instance"""
    return ValidationRules(
        min_length=1,
        max_length=100000,
        min_coherence=0.8,
        max_error_rate=0.1,
        required_fields=set(),
        forbidden_terms=set(),
        custom_rules={}
    )
