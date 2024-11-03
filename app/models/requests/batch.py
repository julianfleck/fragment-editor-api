from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .base import BaseRequest
from ..content import Context


@dataclass
class BatchRequest(BaseRequest):
    """Request model for batch text operations"""
    contents: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Context] = None
    batch_id: Optional[str] = None
    parallel: bool = True

    def __post_init__(self):
        if not self.contents:
            raise ValueError("Batch contents cannot be empty")
        if not all(self.contents):
            raise ValueError("All batch items must contain content")
        if len(self.contents) > 100:  # Example limit
            raise ValueError("Batch size exceeds maximum limit of 100")
