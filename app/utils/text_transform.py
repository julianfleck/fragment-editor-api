from typing import List, Dict, Union, Optional, Tuple, Any
from dataclasses import dataclass
import json
import logging
from app.exceptions import APIRequestError
from app.utils.ai_helpers import count_tokens
from app.config.text_transform import (
    DEFAULT_PERCENTAGE,
    MIN_LENGTH_EXPANSION, MAX_LENGTH_EXPANSION, DEFAULT_LENGTH_EXPANSION,
    MIN_LENGTH_COMPRESSION, MAX_LENGTH_COMPRESSION, DEFAULT_LENGTH_COMPRESSION,
    DEFAULT_STEP_SIZE, MIN_STEP_SIZE, MAX_STEP_SIZE,
    MAX_VERSIONS, DEFAULT_VERSIONS,
    MODES
)
from app.utils.request_validator import RequestValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    code: str
    message: str


def format_version_details(
    content: Union[str, List[str]],
    target_configs: List[Dict[str, Any]],
    is_fragments: bool
) -> str:
    """
    Format version details for prompt templates.
    Works for both expansion and compression operations.
    """
    def create_length_structure(tokens: int, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "target_percentage": config["target_percentage"],
                "target_tokens": round(tokens * config["target_percentage"] / 100),
                "versions": [
                    {"text": f"generated text for version {i+1} ({config['target_percentage']}% of original length, approx. {
                        round(tokens * config['target_percentage'] / 100)} tokens)"}
                    for i in range(config.get("versions_per_length", config.get("versions", 1)))
                ]
            }
            for config in configs
        ]

    if is_fragments:
        original_tokens = [count_tokens(f) for f in content]
        structure = {
            "fragments": [
                {
                    "lengths": create_length_structure(tokens, target_configs)
                }
                for tokens in original_tokens
            ]
        }
    else:
        original_tokens = count_tokens(content)
        structure = {
            "lengths": create_length_structure(original_tokens, target_configs)
        }

    return json.dumps(structure, indent=2)


class TransformationRequest:
    """Handles text transformation request logic and prompt generation"""

    # Operation types
    SINGLE = 'SINGLE'
    FIXED = 'FIXED'
    STAGGERED = 'STAGGERED'
    FRAGMENT = 'FRAGMENT'

    def __init__(self, content: Union[str, List[str]], params: dict, warnings: Optional[List[str]] = None, operation: str = 'expand'):
        self.content = content
        self.params = params
        self.warnings = warnings or []
        self.is_fragments = isinstance(content, list)
        self.operation = operation

        match operation:
            case 'rephrase':
                self._init_rephrase()
            case 'expand' | 'compress':
                self._init_transform()
            case _:
                raise APIRequestError(f"Unknown operation: {
                                      operation}", status=400)

    def _init_rephrase(self):
        """Initialize for rephrase operation"""
        self.is_expansion = False
        self.base_operation = 'rephrase'
        self.required_operation = 'REPHRASE'
        self.target_percentages = [{
            'target_percentage': 100,
            'versions_per_length': self.params.get('versions', DEFAULT_VERSIONS)
        }]

    def _init_transform(self):
        """Initialize for expand/compress operations"""
        self.is_expansion = self._should_expand()
        self.base_operation = 'expand' if self.is_expansion else 'compress'
        self.required_operation = self._determine_operation()
        self.target_percentages = self._calculate_target_percentages()
        if error := self._validate_percentages():
            raise APIRequestError(message=error.message, status=400)

    def _should_expand(self) -> bool:
        """Determine if this should be an expansion based on target percentage"""
        target = self.params.get('target_percentage')
        if not target:
            targets = self.params.get('target_percentages', [])
            if targets:
                return max(targets) > 100
            return self.operation == 'expand'
        return target > 100

    def _validate_params(self) -> Optional[ValidationError]:
        """Deprecated - validation now handled by RequestValidator"""
        return None

    def _determine_operation(self) -> str:
        """Determine the specific operation type"""
        if self.is_fragments:
            base_type = self.FRAGMENT
        else:
            # Check if staggered operation is requested
            has_steps = 'steps_percentage' in self.params
            has_start = 'start_percentage' in self.params
            has_multiple_targets = len(
                self.params.get('target_percentages', [])) > 1

            if has_steps or has_start or has_multiple_targets:
                base_type = self.STAGGERED
            elif self.params.get('versions', 1) > 1:
                if self.params.get('target_percentage'):
                    base_type = self.FIXED
                else:
                    base_type = self.STAGGERED
            else:
                base_type = self.SINGLE

        return f"{self.base_operation.upper()}_{base_type}"

    def _calculate_staggered_percentages(self, start: Optional[int], target: int,
                                         step: Optional[int], versions: Optional[int]) -> List[int]:
        """Calculate percentages for staggered operations"""
        if start is not None:
            # Calculate from start to target
            current = start
            percentages = [start] if start != 100 else []

            if self.is_expansion:
                while current < target:
                    current += (step or 20)
                    if current != 100 and current < target:
                        percentages.append(round(current))
                percentages.append(target)
            else:
                while current > target:
                    current -= (step or 20)
                    if current != 100 and current > target:
                        percentages.append(round(current))
                percentages.append(target)

            return percentages

        # No start specified, calculate based on versions
        versions = versions or 3
        if self.is_expansion:
            step = step or (target - 100) / versions
            return [round(100 + (i * step)) for i in range(1, versions + 1)]
        else:
            step = step or (100 - target) / versions
            percentages = [round(100 - (i * step))
                           for i in range(1, versions + 1)]
            return [p for p in percentages if p != 100]

    def _calculate_target_percentages(self) -> List[Dict[str, Any]]:
        """
        Calculate target lengths with their respective version counts.
        Returns a list of length configurations, each with:
        {
            "target_percentage": int,
            "versions_per_length": int
        }
        """
        if 'target_percentages' in self.params:
            # Explicit list of percentages becomes individual lengths
            return [{"target_percentage": p, "versions_per_length": 1}
                    for p in self.params['target_percentages']]

        elif 'steps_percentage' in self.params:
            step = max(self.params['steps_percentage'], MIN_STEP_SIZE)
            target = self.params['target_percentage']
            versions_per_length = min(
                self.params.get('versions', DEFAULT_VERSIONS), MAX_VERSIONS)

            # Calculate start percentage based on operation type
            if self.is_expansion:
                start = self.params.get('start_percentage',
                                        min(DEFAULT_PERCENTAGE + step, target))
            else:
                start = self.params.get('start_percentage',
                                        max(DEFAULT_PERCENTAGE - step, target))

            # Generate length configurations
            if self.is_expansion:
                return [
                    {"target_percentage": p, "versions_per_length": versions_per_length}
                    for p in range(start, target + step, step)
                ]
            else:
                return [
                    {"target_percentage": p, "versions_per_length": versions_per_length}
                    for p in range(start, target - step, -step)
                ]

        else:
            # Single target with possible multiple versions
            target = self.params.get('target_percentage',
                                     DEFAULT_LENGTH_EXPANSION if self.is_expansion else DEFAULT_LENGTH_COMPRESSION)
            versions = min(self.params.get(
                'versions', DEFAULT_VERSIONS), MAX_VERSIONS)
            return [{"target_percentage": target, "versions_per_length": versions}]

    def _validate_percentages(self) -> Optional[ValidationError]:
        """Validate calculated target percentages"""
        if not self.target_percentages:
            return ValidationError(
                'invalid_targets',
                'No valid target percentages could be calculated'
            )

        # Extract just the percentage values from the target configs
        percentages = [config["target_percentage"]
                       for config in self.target_percentages]

        # Validate versions per length
        for config in self.target_percentages:
            if not 1 <= config["versions_per_length"] <= MAX_VERSIONS:
                return ValidationError(
                    'invalid_versions',
                    f'Version count must be between 1 and {MAX_VERSIONS}'
                )

        return None

    def get_system_prompt(self) -> str:
        """Get the appropriate system prompt based on operation type"""
        from app.prompts.compress import COMPRESS_BASE, COMPRESS_STAGGERED, COMPRESS_FRAGMENT
        from app.prompts.expand import EXPAND_BASE, EXPAND_STAGGERED, EXPAND_FRAGMENT
        from app.prompts.rephrase import REPHRASE_BASE

        match self.operation:
            case 'rephrase':
                return REPHRASE_BASE
            case 'expand' | 'compress':
                operation, mode = self.required_operation.split('_')
                if mode == self.FRAGMENT:
                    return EXPAND_FRAGMENT if self.is_expansion else COMPRESS_FRAGMENT
                elif mode in [self.STAGGERED, self.FIXED]:
                    return EXPAND_STAGGERED if self.is_expansion else COMPRESS_STAGGERED
                else:
                    return EXPAND_BASE if self.is_expansion else COMPRESS_BASE

    def get_user_message(self) -> str:
        """Get the appropriate user message template based on operation type"""
        from app.prompts.compress import USER_MESSAGES as COMPRESS_MESSAGES
        from app.prompts.expand import USER_MESSAGES as EXPAND_MESSAGES
        from app.prompts.rephrase import USER_MESSAGES as REPHRASE_MESSAGES

        # Format common parameters
        text = self.content if not self.is_fragments else "\n".join(
            f"Fragment {i+1}: {f}" for i, f in enumerate(self.content))
        style = self.params.get('style', 'professional')
        tone_str = f"\n- Use {self.params['tone']
                              } tone" if 'tone' in self.params else ""
        aspects_str = f"\n- Consider these aspects: {
            ', '.join(self.params['aspects'])}" if 'aspects' in self.params else ""

        match self.operation:
            case 'rephrase':
                template_key = 'fragment' if self.is_fragments else 'base'
                return REPHRASE_MESSAGES[template_key].format(
                    text=text,
                    style=style,
                    versions=self.params.get('versions', DEFAULT_VERSIONS),
                    fragment_count=len(
                        self.content) if self.is_fragments else 1,
                    tone_str=tone_str,
                    aspects_str=aspects_str
                )
            case 'expand' | 'compress':
                messages = EXPAND_MESSAGES if self.is_expansion else COMPRESS_MESSAGES
                template_key = 'fragment' if self.is_fragments else self._get_mode()
                original_tokens = count_tokens(
                    self.content[0] if self.is_fragments else self.content)

                return messages[template_key].format(
                    text=text,
                    style=style,
                    tone_str=tone_str,
                    aspects_str=aspects_str,
                    original_tokens=original_tokens,
                    versions_per_length=self.params.get(
                        'versions', DEFAULT_VERSIONS),
                    fragment_count=len(
                        self.content) if self.is_fragments else 1,
                    version_details=format_version_details(
                        self.content,
                        self.target_percentages,
                        self.is_fragments
                    )
                )

    def parse_ai_response(self, response: dict) -> dict:
        """Parse and validate AI response structure"""
        try:
            warnings = []  # Track warnings for metadata

            # Validate basic structure
            if self.is_fragments:
                if 'fragments' not in response:
                    response['fragments'] = []
                    warnings.append(
                        "Response missing 'fragments' key - reconstructing structure")

                expected_fragments = len(self.content)
                actual_fragments = len(response.get('fragments', []))
                processed_fragments = []

                for i in range(expected_fragments):
                    try:
                        # Handle missing fragment
                        if i >= actual_fragments:
                            warnings.append(
                                f"Fragment {i+1} missing from response - using original")
                            processed_fragments.append(
                                self._create_placeholder_fragment(i))
                            continue

                        fragment = response['fragments'][i]
                        if 'lengths' not in fragment:
                            warnings.append(
                                f"Fragment {i+1} missing lengths - using original")
                            processed_fragments.append(
                                self._create_placeholder_fragment(i))
                            continue

                        # Handle missing or insufficient lengths
                        expected_lengths = len(self.target_percentages)
                        actual_lengths = len(fragment['lengths'])

                        if actual_lengths < expected_lengths:
                            warnings.append(f"Fragment {
                                            i+1} has fewer lengths than expected ({actual_lengths}/{expected_lengths})")
                            # Pad with placeholder lengths
                            fragment['lengths'].extend([
                                self._create_placeholder_length(
                                    self.target_percentages[j]['target_percentage'],
                                    i
                                )
                                for j in range(actual_lengths, expected_lengths)
                            ])

                        # Handle missing versions
                        for j, length_config in enumerate(fragment['lengths']):
                            if 'versions' not in length_config:
                                warnings.append(
                                    f"Fragment {i+1}, length {j+1} missing versions - using original")
                                length_config['versions'] = [
                                    {'text': self.content[i]}]
                                continue

                            expected_versions = self.params.get(
                                'versions', DEFAULT_VERSIONS)
                            actual_versions = len(length_config['versions'])

                            if actual_versions < expected_versions:
                                warnings.append(f"Fragment {
                                                i+1}, length {j+1} has fewer versions than expected ({actual_versions}/{expected_versions})")
                                # Pad with original text for missing versions
                                length_config['versions'].extend([
                                    {'text': self.content[i]}
                                    for _ in range(actual_versions, expected_versions)
                                ])

                        processed_fragments.append(fragment)

                    except Exception as e:
                        logger.warning(f"Error processing fragment {
                                       i+1}: {str(e)}")
                        warnings.append(f"Error processing fragment {
                                        i+1} - using original")
                        processed_fragments.append(
                            self._create_placeholder_fragment(i))

                response['fragments'] = processed_fragments

                # Add warnings to metadata
                if warnings:
                    if 'metadata' not in response:
                        response['metadata'] = {}
                    response['metadata']['warnings'] = warnings

                return response

            else:
                # Non-fragment validation
                if 'lengths' not in response:
                    raise ValueError("Missing 'lengths' key in response")

                if len(response['lengths']) < len(self.target_percentages):
                    raise ValueError(f"Expected at least {len(
                        self.target_percentages)} lengths, got {len(response['lengths'])}")
                response['lengths'] = response['lengths'][:len(
                    self.target_percentages)]

                # Validate each length configuration
                for i, length_config in enumerate(response['lengths']):
                    if 'versions' not in length_config:
                        raise ValueError(
                            f"Missing 'versions' key in length config {i+1}")
                    length_config['versions'] = length_config['versions'][:MAX_VERSIONS]
                    for j, version in enumerate(length_config['versions']):
                        self._validate_version(version, None, i, j)

                # Add warnings to metadata if any exist
                if warnings:
                    if 'metadata' not in response:
                        response['metadata'] = {}
                    response['metadata']['warnings'] = warnings

                return response

        except Exception as e:
            logger.error(f"Failed to validate response structure: {str(e)}")
            raise APIRequestError(f"Invalid response structure: {
                                  str(e)}", status=400)

    def _create_placeholder_fragment(self, fragment_index: int) -> dict:
        """Create a placeholder fragment using original text"""
        return {
            'lengths': [
                {
                    'target_percentage': config['target_percentage'],
                    'versions': [
                        {'text': self.content[fragment_index]}
                        for _ in range(self.params.get('versions', DEFAULT_VERSIONS))
                    ]
                }
                for config in self.target_percentages
            ]
        }

    def _create_placeholder_length(self, target_percentage: int, fragment_index: int) -> dict:
        """Create a placeholder length configuration using original text"""
        return {
            'target_percentage': target_percentage,
            'versions': [
                {'text': self.content[fragment_index]}
                for _ in range(self.params.get('versions', DEFAULT_VERSIONS))
            ]
        }

    def _validate_version(self, version: dict, fragment_idx: Optional[int], length_idx: int, version_idx: int) -> None:
        """Validate a single version"""
        if 'text' not in version:
            raise ValueError(f"Missing 'text' in version {
                             version_idx+1} of length {length_idx+1}")

        # Skip token validation for rephrase operation
        if self.operation == 'rephrase':
            return

        # Original validation logic for expand/compress
        original_tokens = count_tokens(
            self.content[fragment_idx] if fragment_idx is not None else self.content
        )
        target_percentage = self.target_percentages[length_idx]['target_percentage']
        target_tokens = round(original_tokens * target_percentage / 100)
        actual_tokens = count_tokens(version['text'])

        # Increased tolerance to 2.0 (100% deviation allowed)
        tolerance = 2.0
        if abs(actual_tokens - target_tokens) > (target_tokens * tolerance):
            raise ValueError(
                f"Version {version_idx+1} of length {length_idx +
                                                     1} token count ({actual_tokens}) "
                f"differs significantly from target ({target_tokens})"
            )

    def _strip_metadata(self, response: dict) -> dict:
        """Remove everything except text field from response"""
        if self.is_fragments:
            return {
                'fragments': [
                    {
                        'versions': [
                            {'text': v['text']} for v in fragment['versions']
                        ]
                    } for fragment in response['fragments']
                ]
            }
        else:
            return {
                'versions': [
                    {'text': v['text']} for v in response['versions']
                ]
            }

    def _get_mode(self) -> str:
        """
        Determine expansion mode based on content and parameters:
        - 'fragment' for list of content items
        - 'staggered' for multiple increasing percentages
        - 'base' for single content with one percentage
        """
        if self.is_fragments:
            return 'fragment'
        elif len(self.target_percentages) > 1:
            return 'staggered'
        else:
            return 'base'

    def _validate_parameters(self) -> None:
        """Deprecated - validation now handled by RequestValidator"""
        pass
