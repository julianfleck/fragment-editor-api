from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .base import ValidationBase


@dataclass
class ValidationError(ValidationBase):
    """Represents a validation error with context"""
    code: str = field(default="")
    message: str = field(default="")
    target: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.code:
            raise ValueError("Error code is required")
        if not self.message:
            raise ValueError("Error message is required")
