from datetime import datetime, UTC
from ....models.metadata import ContentMetadata, ProcessingMetadata, Metadata
from .content import create_content_type, create_context


def create_metadata() -> ContentMetadata:
    """Creates a default ContentMetadata instance"""
    return ContentMetadata(
        content_type=create_content_type(),
        topics=[],
        context=create_context(),
        word_count=0,
        char_count=0
    )


def create_processing_metadata() -> ProcessingMetadata:
    """Creates a default ProcessingMetadata instance"""
    return ProcessingMetadata(
        started_at=datetime.now(UTC),
        completed_at=None,
        processing_time=0.0,
        model_version="1.0",
        operation_type="transform",
        batch_id=None
    )
