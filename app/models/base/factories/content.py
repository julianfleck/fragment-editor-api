from typing import List
from ....models.content import (
    Context, ContentMetrics, ContentType,
    Summary, ContentValidation
)


def create_context() -> Context:
    """Creates a default Context instance"""
    return Context(
        domain="general",
        style="neutral",
        tone="neutral"
    )


def create_content_metrics() -> ContentMetrics:
    """Creates a default ContentMetrics instance"""
    return ContentMetrics(
        preserved_terms=[],
        context_coherence=0.0,
        domain_adherence=0.0,
        style_adherence=0.0,
        formality_score=0.0,
        complexity_score=0.0
    )


def create_content_type() -> ContentType:
    """Creates a default ContentType instance"""
    return ContentType(
        primary="text",
        subtype="plain",
        format="raw"
    )


def create_content_validation() -> ContentValidation:
    """Creates a default ContentValidation instance"""
    return ContentValidation(
        is_coherent=False,
        is_complete=False,
        readability_score=0.0,
        grammar_score=0.0,
        context_match=0.0,
        issues=[]
    )


def create_summary() -> Summary:
    """Creates a default Summary instance"""
    return Summary(
        short="",
        medium="",
        long="",
        key_points=[],
        context=create_context()
    )
