from dataclasses import dataclass
from .operations import TransformationOperation
from ..validation import ValidationError


@dataclass
class ExpansionOperation(TransformationOperation):
    """Operation for expanding text content"""

    def __post_init__(self):
        self.operation_name = 'expand'
        super().__post_init__()

    def _validate_operation_specific(self) -> None:
        # Validation already handled by TransformationRequest
        pass

    def _get_target_ratio(self) -> float:
        target_percentage = self.request.get_param('target_percentage', 120)
        return target_percentage / 100

    def _get_tolerance(self) -> float:
        return 0.2  # 20% tolerance for expansion
