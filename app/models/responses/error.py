from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .base import BaseResponse


@dataclass
class ErrorResponse(BaseResponse):
    """API error response"""
    error_code: str = field(default="unknown_error")
    message: str = field(default="An unknown error occurred")
    details: Optional[Dict[str, Any]] = field(default=None, repr=False)
    type: str = field(default="error")
    status: int = field(default=400)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "type": self.type,
            "status": self.status,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "error": {
                "code": self.error_code,
                "message": self.message,
                **({"details": self.details} if self.details else {})
            }
        }

    def __getattribute__(self, name: str) -> Any:
        # Skip details field in general attribute access
        if name == "details" and not name.startswith('_'):
            return super().__getattribute__("_details")
        return super().__getattribute__(name)
