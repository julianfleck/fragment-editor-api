from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from .base import ValidationBase
from .error import ValidationError


@dataclass
class RequestValidationError(ValidationError):
    """Specific validation errors for requests"""
    EMPTY_CONTENT = ("EMPTY_CONTENT", "Content cannot be empty")
    INVALID_FRAGMENTS = ("INVALID_FRAGMENTS",
                         "All fragments must contain content")
    INVALID_EXPANSION = ("INVALID_EXPANSION",
                         "Expansion target must be between 100% and 200%")
    INVALID_COMPRESSION = ("INVALID_COMPRESSION",
                           "Compression target must be between 0% and 100%")
    MISSING_STYLE = ("MISSING_STYLE", "Style is required for rephrasing")

    @classmethod
    def create(cls, error_type: tuple[str, str], details: Optional[Dict[str, Any]] = None) -> 'RequestValidationError':
        return cls(
            code=error_type[0],
            message=error_type[1],
            details=details or {}
        )
