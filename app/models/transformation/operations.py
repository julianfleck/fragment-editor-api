from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..base.description import DescriptionMixin
from ..content import Context
from .result import TransformationResult


@dataclass
class TransformationOperation(ABC, DescriptionMixin):
    """
    Base abstract class for all transformation operations.
    Defines the interface that all text transformation operations must implement.
    """
    name: str
    description: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Initialize empty dict if metadata is None
        if self.metadata is None:
            self.metadata = {}

    @abstractmethod
    def validate_input(self, content: str, context: Context) -> None:
        """Validate operation input parameters before execution"""
        if not content:
            raise ValueError("Content cannot be empty")
        if not context:
            raise ValueError("Context is required")

    @abstractmethod
    def execute(self, content: str, context: Context) -> TransformationResult:
        """
        Execute the transformation operation with validation

        Args:
            content: The text content to transform
            context: The context containing style and requirements

        Returns:
            TransformationResult containing the transformed text and metrics
        """
        # Pre-execution validation
        self.validate_input(content, context)

        # Execute transformation
        result = self._transform(content, context)

        # Post-transformation validation chain:
        # 1. Basic result validation (from TransformationResult.__post_init__)
        # 2. Operation-specific validation
        # 3. Style and context validation
        try:
            # Operation-specific validation
            self.validate_result(result)

            # Style and context validation
            result.validation.validate_transformation(result)

            # Update internal validation state based on all validations
            result.validation._validation_state = (
                result.validation._validation_state and
                result.metrics.is_valid and
                result.is_valid
            )
        except ValueError as e:
            result.validation.warnings.append(str(e))
            result.validation._validation_state = False

        return result

    @abstractmethod
    def _transform(self, content: str, context: Context) -> TransformationResult:
        """Internal transformation implementation"""
        pass

    @abstractmethod
    def validate_result(self, result: TransformationResult) -> None:
        """Validate operation-specific transformation results"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Return operation-specific metadata"""
        return {
            "name": self.name,
            "description": self.description,
            **(self.metadata or {})
        }
