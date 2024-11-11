from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class ErrorResponse:
    """API error response model"""
    error_code: str = field()  # Required field
    message: str = field()     # Required field
    status: int = field(default=500)  # HTTP status code, defaults to 500
    details: Optional[Dict[str, Any]] = field(default=None)
    warnings: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        response: Dict[str, Any] = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status": self.status
            }
        }

        # Add optional fields only if they exist
        if self.details is not None:
            response["error"]["details"] = self.details

        if self.warnings:
            response["warnings"] = self.warnings

        return response
