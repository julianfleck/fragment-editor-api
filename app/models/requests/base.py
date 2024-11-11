from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from ..base.description import DescriptionMixin
from ..content import Context
from abc import ABC, abstractmethod


@dataclass
class BaseRequest(DescriptionMixin, ABC):
    """Base class for all API requests"""
    operation: str
    context: Optional[Context] = None
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _processed_params: List[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._processed_params = []

    def mark_param_processed(self, param: str) -> None:
        """Mark a parameter as processed"""
        if param in self.get_params() and param not in self._processed_params:
            self._processed_params.append(param)

    @property
    def unprocessed_params(self) -> List[str]:
        """Get list of unprocessed parameters"""
        return [p for p in self.get_params() if p not in self._processed_params]

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Get all request parameters"""
        pass

    def validate(self) -> None:
        """Base validation for all requests"""
        if not self.operation:
            raise ValueError("Operation type is required")
