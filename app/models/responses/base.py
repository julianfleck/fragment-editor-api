from dataclasses import dataclass, field
from typing import Dict, Any, List
from ..base.description import DescriptionMixin


@dataclass
class BaseResponse(DescriptionMixin):
    """Base class for all API responses"""
    type: str = field(default="base")
    status: int = field(default=200)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "type": self.type,
            "status": self.status,
            "warnings": self.warnings,
            "metadata": self.metadata
        }
