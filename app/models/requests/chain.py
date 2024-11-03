from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .base import BaseRequest
from ..content import Context


@dataclass
class ChainOperation:
    """Single operation in a transformation chain"""
    operation: str
    params: Dict[str, Any]


@dataclass
class ChainRequest(BaseRequest):
    """Request model for chained text operations"""
    content: str = field(default="")
    operations: List[ChainOperation] = field(default_factory=list)
    context: Optional[Context] = None

    def __post_init__(self):
        if not self.content:
            raise ValueError("Content cannot be empty")
        if not self.operations:
            raise ValueError("Operations chain cannot be empty")
        if len(self.operations) > 5:  # Example limit
            raise ValueError("Chain length exceeds maximum limit of 5")

        # Validate operation sequence
        self._validate_operation_sequence()

    def _validate_operation_sequence(self) -> None:
        """Validate that operation sequence is valid"""
        valid_sequences = {
            'expand': ['rephrase'],
            'compress': ['rephrase'],
            'rephrase': ['expand', 'compress']
        }

        for i, op in enumerate(self.operations[:-1]):
            next_op = self.operations[i + 1]
            if next_op.operation not in valid_sequences.get(op.operation, []):
                raise ValueError(
                    f"Invalid operation sequence: {op.operation} -> {next_op.operation}")
