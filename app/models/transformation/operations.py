from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Iterable
from ..base.description import DescriptionMixin
from ..content import Context
from ..base.factories.style import create_style
from ..content.styles import Style
from .result import TransformationResult
from ..validation import ValidationError
from ..requests import TransformationRequest
import json
from app.services import get_ai_completion
from ..content.styles import StyleRegistry
import logging
from .content import TransformedContent
from ..validation.content import ContentValidationChain
from ..content.metrics import ContentMetrics
from ..base.factories.validation import create_validation_result
from ..base.factories.metadata import create_metadata
from ..base.factories.content import create_context
from ..validation.ai_response import AIResponseValidator
from ..metadata.core import ProcessingMetadata, ContentMetadata
from ..content.core import ContentType
from datetime import datetime, timezone
from ..metadata import Metadata
from ..validation import ValidationResult


@dataclass
class TransformationOperation(DescriptionMixin):
    """Base class for all transformation operations"""
    request: 'TransformationRequest'
    warnings: List[str] = field(default_factory=list)
    operation_name: str = field(init=False)
    style_name: str = field(default="default")
    _style: Optional[Style] = field(init=False, default=None)
    preserve_terms: Optional[List[str]] = None
    maintain_length: bool = True
    _style_registry: StyleRegistry = field(
        default_factory=StyleRegistry, init=False)

    def __post_init__(self):
        # Initialize style from request params or default
        style_name = self.request.params.get('style', self.style_name)
        self._style = create_style(style_name)

        if not self._style_registry.validate_style(self._style.name):
            raise ValueError(f"Style must be one of: {
                             self._style_registry.available_styles}")

        # Set preserve terms from request params
        if 'preserve_terms' in self.request.params:
            self.preserve_terms = self.request.params['preserve_terms']
            self.request.mark_param_processed('preserve_terms')

    @property
    def style(self) -> Style:
        """Get the Style instance"""
        if self._style is None:
            self._style = create_style(self.style_name)
        return self._style

    def execute(self) -> TransformationResult:
        """Execute transformation operation"""
        try:
            started_at = datetime.now(timezone.utc)

            # Get AI response
            response = self.get_ai_completion(
                self._get_prompt('system'),
                self.format_message(self._get_prompt('user'))
            )

            # Create processing metadata
            processing = ProcessingMetadata(
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                operation_type=self.operation_name,
                model_version=self.request.get_param('model_version', '1.0')
            )

            # Create content metadata
            content = " ".join(self.request.content_as_list)
            content_metadata = ContentMetadata(
                content_type=self.request.get_param(
                    'content_type', ContentType.TEXT),
                topics=self.request.get_param('topics', []),
                context=self.request.context or create_context(),
                word_count=len(content.split()),
                char_count=len(content)
            )

            # Combine into single Metadata instance
            metadata = Metadata(processing=processing,
                                content=content_metadata)

            # Extract transformed texts and metrics
            transformed_texts = self._extract_transformed_texts(response)
            metrics = self._extract_metrics(response)

            # Create validation result
            validation = ValidationResult(
                length_match=True,
                context_preserved=True,
                error_rate=0.0,
                preserved_terms=self.preserve_terms or [],
                coherence_score=metrics.context_coherence,
                style_adherence=metrics.style_adherence
            )
            # Create result with all required fields
            return TransformationResult(
                original=self.request.content_as_list,
                transformed=transformed_texts,
                context=self.request.context or create_context(),
                metrics=metrics,
                validation=validation,
                metadata=metadata,
                style=self.style,
                warnings=[{"code": "OPERATION_WARNING", "message": w}
                          for w in self.warnings]
            )

        except Exception as e:
            logging.error(f"Operation failed: {str(e)}", exc_info=True)
            raise ValidationError(
                code="operation_error",
                message=f"Operation failed: {str(e)}"
            )

    def validate_request(self) -> None:
        """Validate operation-specific request parameters"""
        self._validate_operation_specific()

    def _validate_operation_specific(self) -> None:
        """Override in subclasses to add specific validation"""
        pass

    def _get_target_ratio(self) -> float:
        """Override in subclasses to specify target ratio"""
        return 1.0

    def _get_tolerance(self) -> float:
        """Override in subclasses to specify tolerance"""
        return 0.2

    def _get_prompt(self, prompt_type: str) -> str:
        """Get operation-specific prompt"""
        from app.prompts import get_prompt
        return get_prompt(self.operation_name, prompt_type)

    def get_ai_completion(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Execute AI completion request"""
        # Get temperature
        temperature = self.request.get_param('temperature')

        # Get context and style
        context = self.request.context.to_dict() if self.request.context else None
        style = self.style.to_dict() if self.style else None

        # Call AI service
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            context=context,
            style=style
        )

        # Validate response structure
        AIResponseValidator.validate_response_structure(response)

        return response

    def format_message(self, template: str) -> str:
        """Format user message with common parameters"""
        original_tokens = sum(len(text.split())
                              for text in self.request.content_as_list)
        text = "\n".join(self.request.content_as_list)

        return template.format(
            text=text,
            texts=self.request.content_as_list,
            style=self.style.name,
            tone_str=self._format_tone(),
            aspects_str=self._format_aspects(),
            preserve_terms_str=self._format_preserve_terms(),
            target_percentage=self.request.get_param('target_percentage'),
            versions=self.request.get_param('versions', 1),
            versions_per_length=self.request.get_param('versions', 1),
            original_tokens=original_tokens,
            version_details=self._format_version_details()
        )

    def _format_tone(self) -> str:
        """Format tone parameter for prompt"""
        return f"\n- Use {self.request.params['tone']} tone" if 'tone' in self.request.params else ""

    def _format_aspects(self) -> str:
        """Format aspects parameter for prompt"""
        return f"\n- Consider these aspects: {', '.join(self.request.params['aspects'])}" if 'aspects' in self.request.params else ""

    def _format_preserve_terms(self) -> str:
        """Format preserve terms parameter for prompt"""
        return f"\n- Preserve these terms: {', '.join(self.preserve_terms)}" if self.preserve_terms else ""

    def add_warning(self, message: str) -> None:
        """Add a warning message"""
        self.warnings.append(message)

    def _extract_transformed_texts(self, data: Dict[str, Any]) -> List[str]:
        """Extract transformed texts from AI response data"""
        expected_count = len(self.request.content_as_list)
        return AIResponseValidator.validate_texts(data, expected_count)

    def _extract_metrics(self, data: Dict[str, Any]) -> ContentMetrics:
        """Extract metrics from AI response data"""
        raw_metrics = AIResponseValidator.validate_metrics(data)

        # Convert metrics to proper types
        return ContentMetrics(
            preserved_terms=self.preserve_terms or [],  # Use actual preserved terms list
            context_coherence=raw_metrics["context_coherence"],
            domain_adherence=raw_metrics["domain_adherence"],
            style_adherence=raw_metrics["style_adherence"]
        )

    def _format_version_details(self) -> str:
        """Format version details string"""
        # TODO: Add versions per length and return json instead of string
        versions = self.request.get_param('versions', 1)
        return f"Generate {versions} version{'s' if versions > 1 else ''}"
