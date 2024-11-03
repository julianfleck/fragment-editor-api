from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from ..validation import ValidationBase, ValidationError


@dataclass
class RequestError(ValidationBase):
    """Represents a request validation error"""
    code: str = field(default="")
    message: str = field(default="")
    param: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.code:
            raise ValueError("Error code is required")
        if not self.message:
            raise ValueError("Error message is required")

    @classmethod
    def from_validation_error(cls, error: 'ValidationError', param: Optional[str] = None) -> 'RequestError':
        """Create from ValidationError"""
        return cls(
            code=error.code,
            message=error.message,
            param=param or error.target,
            details=error.details,
            suggestions=error.suggestions
        )

    def to_response(self) -> Dict[str, Any]:
        """Convert to API error response format"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "param": self.param,
                **({"details": self.details} if self.details else {}),
                **({"suggestions": self.suggestions} if self.suggestions else {})
            }
        }
