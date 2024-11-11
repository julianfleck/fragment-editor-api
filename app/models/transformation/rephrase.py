from dataclasses import dataclass
from .operations import TransformationOperation
from ..validation import ValidationError


@dataclass
class RephraseOperation(TransformationOperation):
    """Operation for rephrasing text content"""

    def __post_init__(self):
        self.operation_name = 'rephrase'
        super().__post_init__()

    def _validate_operation_specific(self) -> None:
        # Validation already handled by TransformationRequest
        pass

    def _get_target_ratio(self) -> float:
        return 1.0  # Rephrase maintains original length

    def _get_tolerance(self) -> float:
        return 0.2  # 20% tolerance for rephrasing
