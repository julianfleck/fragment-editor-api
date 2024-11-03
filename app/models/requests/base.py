from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..base.description import DescriptionMixin
from ..content import Context


@dataclass
class BaseRequest(DescriptionMixin):
    """Base class for all API requests"""
    operation: str
    context: Optional[Context] = None
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Base validation for all requests"""
        if not self.operation:
            raise ValueError("Operation type is required")
