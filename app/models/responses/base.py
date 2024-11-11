from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from ..base.description import DescriptionMixin
from ..requests.base import BaseRequest


@dataclass
class BaseResponse(DescriptionMixin):
    """Base class for all API responses"""
    type: str = field(default="base")
    status: int = field(default=200)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request: Optional[BaseRequest] = None

    def __post_init__(self):
        self._check_unused_parameters()

    def _check_unused_parameters(self) -> None:
        """Add warnings for unused parameters"""
        if self.request:
            for param in self.request.unprocessed_params:
                self.add_warning(f"Unused parameter in request: {param}")

    def add_warning(self, message: str) -> None:
        """Add a warning message"""
        self.warnings.append({"message": message})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "type": self.type,
            "status": self.status,
            "warnings": self.warnings,
            "metadata": self.metadata
        }
