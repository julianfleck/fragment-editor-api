from dataclasses import dataclass, field
from typing import Optional, List
from ..base import DescriptionMixin
from ..content import Context
from ..content.styles import StyleRegistry
from .operations import TransformationOperation
from .result import TransformationResult
from ..base.factories.style import create_style
from ..content.styles import Style


@dataclass
class RephraseOperation(TransformationOperation, DescriptionMixin):
    """Operation for rephrasing text content"""
    style: Style = field(default_factory=create_style)
    preserve_terms: Optional[List[str]] = None
    maintain_length: bool = True
    _style_registry: StyleRegistry = field(
        default_factory=StyleRegistry, init=False)

    def __post_init__(self):
        if not self._style_registry.validate_style(self.style.name):
            raise ValueError(f"Style must be one of: {
                             self._style_registry.available_styles}")

    def validate_result(self, result: TransformationResult) -> None:
        """Validate rephrasing result"""
        if not result.original or not result.transformed:
            raise ValueError("Both original and transformed content required")

        if self.preserve_terms:
            for term in self.preserve_terms:
                if term not in result.transformed:
                    result.warnings.append(
                        f"Required term '{term}' not preserved in rephrasing")
                    result.error_rate += 0.1  # Increase error rate for each missing term

        # Update preserved terms in result
        result.metrics.preserved_terms = [term for term in self.preserve_terms or []
                                          if term in result.transformed]

    def execute(self, content: str, context: Context) -> TransformationResult:
        """Execute the rephrasing operation"""
        # This is just the interface - actual implementation will be in the service layer
        raise NotImplementedError(
            "Rephrase operation execution not implemented")
