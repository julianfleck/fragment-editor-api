from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from app.config.text_transform import (
    DEFAULT_PERCENTAGE,
    MIN_LENGTH_EXPANSION, MAX_LENGTH_EXPANSION,
    MIN_LENGTH_COMPRESSION, MAX_LENGTH_COMPRESSION,
    MIN_STEP_SIZE, MAX_STEP_SIZE,
    MAX_VERSIONS, DEFAULT_VERSIONS,
    VALID_STYLES, VALID_TONES, VALID_ASPECTS,
    VALID_FRAGMENT_STYLES
)


@dataclass
class ValidationError:
    code: str
    message: str


class RequestValidator:
    @staticmethod
    def validate_request(content: Union[str, List[str]], params: Dict[str, Any]) -> Optional[ValidationError]:
        """Main validation entry point for text transformation requests"""

        # Determine operation type (expansion/compression)
        is_expansion = RequestValidator._is_expansion(params)

        # Basic parameter validation
        if error := RequestValidator._validate_basic_params(params):
            return error

        # Style validation
        if error := RequestValidator._validate_style_params(params):
            return error

        # Length validation
        if error := RequestValidator._validate_length_params(params, is_expansion):
            return error

        # Fragment validation if applicable
        if isinstance(content, list):
            if error := RequestValidator._validate_fragment_params(params):
                return error

        return None

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
        # Check for conflicting parameters
        if 'target_percentage' in params and 'target_percentages' in params:
            return ValidationError(
                'invalid_params',
                'Cannot specify both target_percentage and target_percentages'
            )

        # Validate versions
        versions = params.get('versions')
        if versions is not None:
            if not isinstance(versions, int):
                return ValidationError(
                    'invalid_versions',
                    'Versions must be an integer'
                )
            if versions < 1:
                return ValidationError(
                    'invalid_versions',
                    'Number of versions must be at least 1'
                )
            if versions > MAX_VERSIONS:
                return ValidationError(
                    'invalid_versions',
                    f'Number of versions cannot exceed {MAX_VERSIONS}'
                )

        return None

    @staticmethod
    def _validate_style_params(params: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate style-related parameters"""
        if 'style' in params and params['style'] not in VALID_STYLES:
            return ValidationError(
                'invalid_style',
                f'Invalid style. Must be one of: {", ".join(VALID_STYLES)}'
            )

        if 'tone' in params and params['tone'] not in VALID_TONES:
            return ValidationError(
                'invalid_tone',
                f'Invalid tone. Must be one of: {", ".join(VALID_TONES)}'
            )

        if 'aspects' in params:
            invalid_aspects = set(params['aspects']) - VALID_ASPECTS
            if invalid_aspects:
                return ValidationError(
                    'invalid_aspects',
                    f'Invalid aspects: {", ".join(invalid_aspects)}. Valid aspects are: {
                        ", ".join(VALID_ASPECTS)}'
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
                    'invalid_step',
                    f'Step size cannot be less than {MIN_STEP_SIZE}%'
                )
            if step > MAX_STEP_SIZE:
                return ValidationError(
                    'invalid_step',
                    f'Step size cannot exceed {MAX_STEP_SIZE}%'
                )

        # Validate expansion/compression specific parameters
        if is_expansion:
            if target and target <= DEFAULT_PERCENTAGE:
                return ValidationError(
                    'invalid_expansion',
                    'Expansion target must be greater than 100%'
                )
            if target and target > MAX_LENGTH_EXPANSION:
                return ValidationError(
                    'invalid_expansion',
                    f'Expansion target cannot exceed {MAX_LENGTH_EXPANSION}%'
                )
            if target and target < MIN_LENGTH_EXPANSION:
                return ValidationError(
                    'invalid_expansion',
                    f'Expansion target must be at least {
                        MIN_LENGTH_EXPANSION}%'
                )
            if start and target and start >= target:
                return ValidationError(
                    'invalid_range',
                    'Start percentage must be less than target for expansion'
                )
        else:
            if target and target >= DEFAULT_PERCENTAGE:
                return ValidationError(
                    'invalid_compression',
                    'Compression target must be less than 100%'
                )
            if target and target > MAX_LENGTH_COMPRESSION:
                return ValidationError(
                    'invalid_compression',
                    f'Compression target cannot exceed {
                        MAX_LENGTH_COMPRESSION}%'
                )
            if target and target < MIN_LENGTH_COMPRESSION:
                return ValidationError(
                    'invalid_compression',
                    f'Compression target cannot be less than {
                        MIN_LENGTH_COMPRESSION}%'
                )
            if start and target and start <= target:
                return ValidationError(
                    'invalid_range',
                    'Start percentage must be greater than target for compression'
                )

        return None

    @staticmethod
    def _validate_fragment_params(params: Dict[str, Any]) -> Optional[ValidationError]:
        """Validate fragment-specific parameters"""
        if 'fragment_style' in params and params['fragment_style'] not in VALID_FRAGMENT_STYLES:
            return ValidationError(
                'invalid_fragment_style',
                f'Invalid fragment style. Must be one of: {
                    ", ".join(VALID_FRAGMENT_STYLES)}'
            )

        return None
