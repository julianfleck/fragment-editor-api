from typing import List
from ....models.taxonomy.structure import (
    Fragment, Length, Section, StructuredContent,
    StructureType, Version
)
from ....models.taxonomy import Topic
from .content import create_content_type


def create_fragment() -> Fragment:
    """Creates a default Fragment instance"""
    return Fragment(
        name="",
        content="",
        fragment_id="",
        lengths=[create_length()],
        dependencies=[]
    )


def create_length() -> Length:
    """Creates a default Length instance"""
    return Length(
        name="",
        target_percentage=100,
        target_tokens=1,
        versions=[]
    )


def create_section() -> Section:
    """Creates a default Section instance"""
    return Section(
        name="",
        content="",
        level=0,
        children=[]
    )


def create_structured_content() -> StructuredContent:
    """Creates a default StructuredContent instance"""
    return StructuredContent(
        name="",
        structure_type=StructureType.SECTION,
        elements=[]
    )


def create_topic() -> Topic:
    """Creates a default Topic instance"""
    return Topic(
        name="",
        confidence=0.0,
        relevance=0.0,
        related=[],
        metadata={}
    )


def create_version() -> Version:
    """Creates a default Version instance"""
    return Version(
        name="",
        text="",
        final_tokens=1,
        final_percentage=100.0,
        metrics={}
    )
