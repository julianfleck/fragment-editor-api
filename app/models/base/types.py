from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .description import DescriptionMixin


@dataclass
class BaseResult(DescriptionMixin):
    """Base class for all result objects"""
    is_valid: bool = True
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
