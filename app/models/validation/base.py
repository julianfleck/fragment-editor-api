from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ..base.description import DescriptionMixin


@dataclass
class ValidationBase(DescriptionMixin, Exception):
    """Base class for all validation-related models"""
    is_valid: bool = True
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.is_valid = False
        self.errors.append({
            "code": code,
            "message": message,
            **({"details": details} if details else {})
        })

    def add_warning(self, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.warnings.append({
            "code": code,
            "message": message,
            **({"details": details} if details else {})
        })
