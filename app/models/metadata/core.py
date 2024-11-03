from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from ..base.description import DescriptionMixin
from ..content.core import Context, ContentType
from ..taxonomy.topic import Topic


@dataclass
class ProcessingMetadata(DescriptionMixin):
    """Metadata about the processing operation itself"""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    processing_time: float = 0.0
    model_version: str = "1.0"
    operation_type: str = "transform"
    batch_id: Optional[str] = None

    def __post_init__(self):
        if self.completed_at and self.started_at > self.completed_at:
            raise ValueError("Start time cannot be after completion time")
        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")


@dataclass
class ContentMetadata(DescriptionMixin):
    """Metadata about the content being processed"""
    content_type: ContentType
    topics: List[Topic]
    context: Context
    word_count: int = 0
    char_count: int = 0
    language: str = "en"
    encoding: str = "utf-8"

    def __post_init__(self):
        if self.word_count < 0:
            raise ValueError("Word count cannot be negative")
        if self.char_count < 0:
            raise ValueError("Character count cannot be negative")


@dataclass
class Metadata(DescriptionMixin):
    """
    Complete metadata for a text transformation operation.
    Combines processing and content metadata with additional custom fields.
    Uses timezone-aware UTC timestamps.
    """
    processing: ProcessingMetadata
    content: ContentMetadata
    additional_info: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "2.0"

    def __post_init__(self):
        if not isinstance(self.processing, ProcessingMetadata):
            self.processing = ProcessingMetadata(**self.processing)
        if not isinstance(self.content, ContentMetadata):
            self.content = ContentMetadata(**self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "processing": self.processing.to_dict(),
            "content": self.content.to_dict(),
            "additional_info": self.additional_info,
            "tags": self.tags,
            "version": self.version
        }
