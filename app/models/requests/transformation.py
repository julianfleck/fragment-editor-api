from dataclasses import dataclass, field
from typing import Union, List, Dict, Any, Optional
from ..base.description import DescriptionMixin
from ..content import Context
from ..validation import RequestValidationError


@dataclass
class TransformationRequest(DescriptionMixin):
    """Base request model for all text transformations"""
    content: Union[str, List[str]]
    operation: str  # 'expand', 'compress', 'rephrase'
    params: Dict[str, Any]
    context: Optional[Context] = None

    def __post_init__(self):
        self.is_fragments = isinstance(self.content, list)
        self.validate()

    def validate(self) -> None:
        """Validate request parameters"""
        if not self.content:
            raise RequestValidationError.create(
                RequestValidationError.EMPTY_CONTENT)

        if isinstance(self.content, list) and not all(self.content):
            raise RequestValidationError.create(
                RequestValidationError.INVALID_FRAGMENTS)

        # Operation-specific validation
        if self.operation == 'expand':
            if not 100 < self.params.get('target_percentage', 0) <= 200:
                raise RequestValidationError.create(
                    RequestValidationError.INVALID_EXPANSION)
        elif self.operation == 'compress':
            if not 0 < self.params.get('target_percentage', 0) < 100:
                raise RequestValidationError.create(
                    RequestValidationError.INVALID_COMPRESSION)
        elif self.operation == 'rephrase':
            if not self.params.get('style'):
                raise RequestValidationError.create(
                    RequestValidationError.MISSING_STYLE)
