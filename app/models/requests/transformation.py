from dataclasses import dataclass, field
from typing import Union, List, Dict, Any, Optional
from ..base.description import DescriptionMixin
from ..content import Context
from ..validation import RequestValidationError, ValidationError
from ..requests.base import BaseRequest


@dataclass
class TransformationRequest(BaseRequest):
    """Base request model for all text transformations"""
    operation: str = 'transform'  # 'expand', 'compress', 'rephrase'
    content: Union[str, List[str]] = field(default_factory=list)
    context: Optional[Context] = None
    params: Dict[str, Any] = field(default_factory=dict)
    is_fragments: bool = field(default=True, init=False)
    _processed_params: List[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        super().__post_init__()
        self.validate()

    def get_params(self) -> Dict[str, Any]:
        return self.params

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get parameter and mark it as processed"""
        value = self.params.get(key, default)
        self.mark_param_processed(key)
        return value

    def mark_param_processed(self, param: str) -> None:
        """Mark a parameter as processed"""
        if param in self.params and param not in self._processed_params:
            self._processed_params.append(param)

    @property
    def unprocessed_params(self) -> List[str]:
        """Get list of unprocessed parameters"""
        return [p for p in self.params if p not in self._processed_params]

    @property
    def content_as_list(self) -> List[str]:
        """Get content as list, converting if necessary"""
        if isinstance(self.content, str):
            return [self.content]
        return self.content

    def validate(self) -> None:
        """Validate request parameters"""
        if not self.content:
            raise RequestValidationError.create(
                RequestValidationError.EMPTY_CONTENT)

        # Only validate fragments if content is a list
        if isinstance(self.content, list):
            if not all(isinstance(item, str) for item in self.content):
                raise RequestValidationError.create(
                    RequestValidationError.INVALID_FRAGMENTS)
            if not all(self.content):
                raise RequestValidationError.create(
                    RequestValidationError.INVALID_FRAGMENTS)

        # Operation-specific validation
        self._validate_operation()

    def _validate_operation(self) -> None:
        """Validate operation-specific parameters"""
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

        # Validate temperature if present
        if 'temperature' in self.params:
            temp = self.params['temperature']
            if not isinstance(temp, (int, float)) or not 0 <= temp <= 0.9:
                raise ValidationError.invalid_temperature()

    @classmethod
    def from_flask_request(cls, request_obj) -> 'TransformationRequest':
        """Create from Flask request object"""
        raw_data = request_obj.get_json()
        content = raw_data.get('content')

        # Get all params from request
        params = {
            k: v for k, v in raw_data.items()
            if k not in ['content', 'operation']
        }

        return cls(
            content=content,
            operation=raw_data.get('operation', 'transform'),
            params=params
        )
