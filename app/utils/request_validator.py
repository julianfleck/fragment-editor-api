from typing import Dict, Any, Optional, Union, List
import logging
from app.exceptions import ValidationError
from app.config.text_transform import (
    DEFAULT_PERCENTAGE,
    MIN_LENGTH_EXPANSION, MAX_LENGTH_EXPANSION,
    MIN_LENGTH_COMPRESSION, MAX_LENGTH_COMPRESSION,
    MIN_STEP_SIZE, MAX_STEP_SIZE,
    MAX_VERSIONS, DEFAULT_VERSIONS,
    VALID_FRAGMENT_STYLES
)
from app.config.endpoint_params import VALID_STYLES, VALID_TONES, VALID_ASPECTS

logger = logging.getLogger(__name__)

VALID_PARAMS = {
    'target_percentage', 'target_percentages', 'start_percentage',
    'steps_percentage', 'versions', 'style', 'tone', 'aspects',
    'fragment_style', 'content'
}


class RequestValidator:
    @staticmethod
    def validate_request(content: Union[str, List[str]], params: Dict[str, Any]) -> tuple[Optional[ValidationError], Optional[List[str]]]:
        """Main validation entry point for text transformation requests"""
        # Check for unknown parameters
        warnings = []
        unknown_params = set(params.keys()) - VALID_PARAMS
        if unknown_params:
            warnings.extend([
                {
                    "field": f"{param}",
                    "code": "validation_warning",
                    "message": f"Unsupported parameter: {param}"
                }
                for param in unknown_params
            ])
            logger.info(f"Generated warnings: {warnings}")

        # Determine operation type (expansion/compression)
        is_expansion = RequestValidator._is_expansion(params)

        # Basic parameter validation
        if error := RequestValidator._validate_basic_params(params):
            return error, warnings if warnings else None

        # Style validation
        if error := RequestValidator._validate_style_params(params):
            return error, warnings if warnings else None

        # Length validation
        if error := RequestValidator._validate_length_params(params, is_expansion):
            return error, warnings if warnings else None

        # Fragment validation if applicable
        if isinstance(content, list):
            if error := RequestValidator._validate_fragment_params(params):
                return error, warnings if warnings else None

        return None, warnings if warnings else None

    @staticmethod
    def _is_expansion(params: Dict[str, Any]) -> bool:
        """Determine if request is for expansion"""
        target = params.get('target_percentage')
        if not target:
            targets = params.get('target_percentages', [])
            return any(t > 100 for t in targets) if targets else False
        return target > 100

    @staticmethod
    def _validate_basic_params(params: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate basic request parameters"""
        if 'target_percentage' in params and 'target_percentages' in params:
            return ValidationError(
                code='invalid_params',
                message='Cannot specify both target_percentage and target_percentages',
                field='target_percentage'
            )

        versions = params.get('versions')
        if versions is not None:
            if not isinstance(versions, int):
                return ValidationError(
                    code='invalid_versions',
                    message='Versions must be an integer',
                    field='versions'
                )
            if versions < 1 or versions > MAX_VERSIONS:
                return ValidationError(
                    code='invalid_versions',
                    message=f'Number of versions must be between 1 and {
                        MAX_VERSIONS}',
                    field='versions'
                )

        return None

    @staticmethod
    def _validate_style_params(params: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate style-related parameters"""
        if 'style' in params and params['style'] not in VALID_STYLES:
            return ValidationError(
                code='invalid_style',
                message=f'Invalid style. Must be one of: {
                    ", ".join(VALID_STYLES)}',
                field='style'
            )

        if 'tone' in params and params['tone'] not in VALID_TONES:
            return ValidationError(
                code='invalid_tone',
                message=f'Invalid tone. Must be one of: {
                    ", ".join(VALID_TONES)}',
                field='tone'
            )

        if 'aspects' in params:
            invalid_aspects = set(params['aspects']) - VALID_ASPECTS
            if invalid_aspects:
                return ValidationError(
                    code='invalid_aspects',
                    message=f'Invalid aspects: {", ".join(invalid_aspects)}. Valid aspects are: {
                        ", ".join(VALID_ASPECTS)}',
                    field='aspects'
                )

        return None

    @staticmethod
    def _validate_length_params(params: Dict[str, Any], is_expansion: bool) -> Optional[ValidationError]:
        """Validate length-related parameters"""
        target = params.get('target_percentage')
        start = params.get('start_percentage')
        step = params.get('steps_percentage')

        # Validate step size
        if step is not None:
            if step < MIN_STEP_SIZE:
                return ValidationError(
                    code='invalid_step',
                    message=f'Step size cannot be less than {MIN_STEP_SIZE}%',
                    field='steps_percentage'
                )
            if step > MAX_STEP_SIZE:
                return ValidationError(
                    code='invalid_step',
                    message=f'Step size cannot exceed {MAX_STEP_SIZE}%',
                    field='steps_percentage'
                )

        # Validate expansion/compression specific parameters
        if is_expansion:
            if target and target <= DEFAULT_PERCENTAGE:
                return ValidationError(
                    code='invalid_expansion',
                    message='Expansion target must be greater than 100%',
                    field='target_percentage'
                )
            if target and target > MAX_LENGTH_EXPANSION:
                return ValidationError(
                    code='invalid_expansion',
                    message=f'Expansion target cannot exceed {
                        MAX_LENGTH_EXPANSION}%',
                    field='target_percentage'
                )
            if target and target < MIN_LENGTH_EXPANSION:
                return ValidationError(
                    code='invalid_expansion',
                    message=f'Expansion target must be at least {
                        MIN_LENGTH_EXPANSION}%',
                    field='target_percentage'
                )
            if start and target and start >= target:
                return ValidationError(
                    code='invalid_range',
                    message='Start percentage must be less than target for expansion',
                    field='start_percentage'
                )
        else:
            if target and target >= DEFAULT_PERCENTAGE:
                return ValidationError(
                    code='invalid_compression',
                    message='Compression target must be less than 100%',
                    field='target_percentage'
                )
            if target and target > MAX_LENGTH_COMPRESSION:
                return ValidationError(
                    code='invalid_compression',
                    message=f'Compression target cannot exceed {
                        MAX_LENGTH_COMPRESSION}%',
                    field='target_percentage'
                )
            if target and target < MIN_LENGTH_COMPRESSION:
                return ValidationError(
                    code='invalid_compression',
                    message=f'Compression target cannot be less than {
                        MIN_LENGTH_COMPRESSION}%',
                    field='target_percentage'
                )
            if start and target and start <= target:
                return ValidationError(
                    code='invalid_range',
                    message='Start percentage must be greater than target for compression',
                    field='start_percentage'
                )

        return None

    @staticmethod
    def _validate_fragment_params(params: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate fragment-specific parameters"""
        if 'fragment_style' in params and params['fragment_style'] not in VALID_FRAGMENT_STYLES:
            return ValidationError(
                code='invalid_fragment_style',
                message=f'Invalid fragment style. Must be one of: {
                    ", ".join(VALID_FRAGMENT_STYLES)}',
                field='fragment_style'
            )

        return None
