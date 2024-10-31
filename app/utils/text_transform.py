from typing import List, Dict, Union, Optional, Tuple, Any
from dataclasses import dataclass
import json
import logging
from app.exceptions import APIRequestError
from app.prompts.expand import (
    USER_MESSAGES,
    EXPAND_BASE,
    EXPAND_STAGGERED,
    EXPAND_FRAGMENT,
    format_version_details
)
from app.utils.ai_helpers import count_tokens
from app.config.text_transform import (
    DEFAULT_PERCENTAGE,
    MIN_LENGTH, MAX_LENGTH, DEFAULT_LENGTH,
    DEFAULT_STEP_SIZE, MIN_STEP_SIZE, MAX_STEP_SIZE,
    MAX_VERSIONS, DEFAULT_VERSIONS,
    MODES
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    code: str
    message: str


class TransformationRequest:
    """Handles text transformation request logic and prompt generation"""

    # Operation types
    SINGLE = 'SINGLE'
    FIXED = 'FIXED'
    STAGGERED = 'STAGGERED'
    FRAGMENT = 'FRAGMENT'

    def __init__(self, content: Union[str, List[str]], operation: str, params: dict):
        self.content = content
        self.params = params
        self.is_fragments = isinstance(content, list)

        # Determine if this is expansion or compression based on target
        self.is_expansion = self._should_expand()
        self.base_operation = 'expand' if self.is_expansion else 'compress'

        # Validate parameters before proceeding
        if error := self._validate_params():
            raise APIRequestError(error.message, status=400)

        # Determine the specific operation type and calculate targets
        self.required_operation = self._determine_operation()
        self.target_percentages = self._calculate_target_percentages()

        # Validate final percentages
        if error := self._validate_percentages():
            raise APIRequestError(error.message, status=400)

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
        """Validate input parameters"""
        target = self.params.get('target_percentage')
        start = self.params.get('start_percentage')
        step = self.params.get('steps_percentage')
        versions = self.params.get('versions')
        targets = self.params.get('target_percentages', [])

        # Check for conflicting parameters
        if targets and target:
            return ValidationError(
                'invalid_params',
                'Cannot specify both target_percentage and target_percentages'
            )

        # Validate versions
        if versions is not None and versions < 1:
            return ValidationError(
                'invalid_versions',
                'Number of versions must be at least 1'
            )

        # Validate step size
        if step is not None and step <= 0:
            return ValidationError(
                'invalid_step',
                'Step size must be greater than 0'
            )

        # Validate start/target combination
        if start and target:
            if self.is_expansion and start >= target:
                return ValidationError(
                    'invalid_range',
                    'Start percentage must be less than target for expansion'
                )
            if not self.is_expansion and start <= target:
                return ValidationError(
                    'invalid_range',
                    'Start percentage must be greater than target for compression'
                )

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
                self.params.get('versions', 1), MAX_VERSIONS)

            # Calculate start percentage
            start = (self.params.get(
                'start_percentage', DEFAULT_PERCENTAGE + step))

            # Generate length configurations
            return [
                {"target_percentage": p, "versions_per_length": versions_per_length}
                for p in range(start, target + step, step)
            ]

        else:
            # Single target with possible multiple versions
            target = self.params.get('target_percentage', DEFAULT_LENGTH)
            versions = min(self.params.get('versions', 1), MAX_VERSIONS)
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

        if self.is_expansion:
            if any(p <= DEFAULT_PERCENTAGE for p in percentages):
                return ValidationError(
                    'invalid_expansion',
                    'Expansion targets must be greater than 100%'
                )
            if any(p > MAX_LENGTH for p in percentages):
                return ValidationError(
                    'invalid_expansion',
                    f'Expansion targets cannot exceed {MAX_LENGTH}%'
                )
        else:
            if any(p >= DEFAULT_PERCENTAGE for p in percentages):
                return ValidationError(
                    'invalid_compression',
                    'Compression targets must be less than 100%'
                )
            if any(p < MIN_LENGTH for p in percentages):
                return ValidationError(
                    'invalid_compression',
                    f'Compression targets cannot be less than {MIN_LENGTH}%'
                )

        # Validate versions per length
        for config in self.target_percentages:
            if not 1 <= config["versions_per_length"] <= MAX_VERSIONS:
                return ValidationError(
                    'invalid_versions',
                    f'Version count must be between 1 and {MAX_VERSIONS}'
                )

        return None

    def get_system_prompt(self) -> str:
        """
        Select appropriate system prompt based on content type and parameters.
        - EXPAND_STAGGERED for multiple increasing percentages
        - EXPAND_FRAGMENT for list of content items
        - EXPAND_BASE for single content with one percentage
        """
        mode = self._get_mode()
        if mode == 'staggered':
            return EXPAND_STAGGERED
        elif mode == 'fragment':
            return EXPAND_FRAGMENT
        else:
            return EXPAND_BASE

    def get_user_message(self) -> str:
        """
        Generate user message with format and targets.
        Handles both single content and fragments.
        Includes style, tone, and aspect parameters if provided.
        """
        mode = self._get_mode()

        # Calculate tokens for content
        if self.is_fragments:
            original_tokens = [count_tokens(fragment)
                               for fragment in self.content]
            # Create target pairs (tokens, percentage) for each fragment
            targets = [
                [(round(tokens * config["target_percentage"] / 100), config["target_percentage"])
                 for config in self.target_percentages]
                for tokens in original_tokens
            ]
            total_tokens = sum(original_tokens)
        else:
            original_tokens = count_tokens(self.content)
            targets = [(round(original_tokens * config["target_percentage"] / 100),
                       config["target_percentage"])
                       for config in self.target_percentages]
            total_tokens = original_tokens

        # Get versions per length from the first target config (they should all be the same)
        versions_per_length = self.target_percentages[0]["versions_per_length"]

        # Prepare message parameters
        message_params = {
            'style': self.params.get('style', 'professional'),
            'text': self.content,
            'original_tokens': total_tokens,
            'versions_per_length': versions_per_length,
            'version_count': len(self.target_percentages),
            'version_details': format_version_details(
                original_tokens,
                [config["target_percentage"]
                    for config in self.target_percentages],
                versions_per_length,
                mode=mode
            ),
            'tone_str': f"\n- Use {self.params.get('tone', 'neutral')} tone" if 'tone' in self.params else '',
            'aspects_str': f"\n- Focus on {', '.join(self.params['aspects'])}" if 'aspects' in self.params else ''
        }

        # Add fragment count for fragment mode
        if self.is_fragments:
            message_params['fragment_count'] = len(self.content)

        return USER_MESSAGES[mode].format(**message_params)

    def parse_ai_response(self, response: dict) -> dict:
        """Parse and validate AI response"""
        try:
            # Validate basic structure
            if self.is_fragments:
                if 'fragments' not in response:
                    raise ValueError("Missing 'fragments' key in response")
                if len(response['fragments']) != len(self.content):
                    raise ValueError(f"Expected {len(self.content)} fragments, got {
                                     len(response['fragments'])}")

                # Validate each fragment
                for i, fragment in enumerate(response['fragments']):
                    if 'lengths' not in fragment:
                        raise ValueError(
                            f"Missing 'lengths' key in fragment {i+1}")

                    # Validate lengths match target configurations
                    if len(fragment['lengths']) != len(self.target_percentages):
                        raise ValueError(
                            f"Wrong number of lengths in fragment {i+1}")

                    # Validate each length configuration
                    for j, length_config in enumerate(fragment['lengths']):
                        if 'versions' not in length_config:
                            raise ValueError(f"Missing 'versions' key in length config {
                                             j+1} of fragment {i+1}")

                        expected_versions = self.target_percentages[j]['versions_per_length']
                        if len(length_config['versions']) != expected_versions:
                            raise ValueError(
                                f"Expected {
                                    expected_versions} versions for length {j+1} "
                                f"in fragment {
                                    i+1}, got {len(length_config['versions'])}"
                            )

                        # Validate each version
                        for k, version in enumerate(length_config['versions']):
                            self._validate_version(version, i, j, k)

            else:
                if 'lengths' not in response:
                    raise ValueError("Missing 'lengths' key in response")
                if len(response['lengths']) != len(self.target_percentages):
                    raise ValueError(
                        f"Expected {len(self.target_percentages)} lengths, got {
                            len(response['lengths'])}"
                    )

                # Validate each length configuration
                for i, length_config in enumerate(response['lengths']):
                    if 'versions' not in length_config:
                        raise ValueError(
                            f"Missing 'versions' key in length config {i+1}")

                    expected_versions = self.target_percentages[i]['versions_per_length']
                    if len(length_config['versions']) != expected_versions:
                        raise ValueError(
                            f"Expected {
                                expected_versions} versions for length {i+1}, "
                            f"got {len(length_config['versions'])}"
                        )

                    # Validate each version
                    for j, version in enumerate(length_config['versions']):
                        self._validate_version(version, None, i, j)

            return response

        except ValueError as e:
            raise APIRequestError(str(e), status=400)

    def _validate_version(self, version: dict, fragment_idx: Optional[int], length_idx: int, version_idx: int) -> None:
        """Validate a single version"""
        if 'text' not in version:
            raise ValueError(f"Missing 'text' in version {
                             version_idx+1} of length {length_idx+1}")

        # Calculate expected token count
        original_tokens = count_tokens(
            self.content[fragment_idx] if fragment_idx is not None else self.content
        )
        target_percentage = self.target_percentages[length_idx]['target_percentage']
        target_tokens = round(original_tokens * target_percentage / 100)
        actual_tokens = count_tokens(version['text'])

        # Allow small deviation (e.g., 5%)
        tolerance = 0.8
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
        """Validate expansion parameters"""
        # Validate target percentage
        if 'target_percentage' in self.params:
            target = self.params['target_percentage']
            if target <= 100:
                raise APIRequestError(
                    code="expansion_error",
                    message="Expansion targets must be greater than 100%"
                )
            if target > 300:
                raise APIRequestError(
                    code="expansion_error",
                    message="Expansion targets cannot exceed 300%"
                )

        # Validate staggered parameters
        if 'steps_percentage' in self.params:
            step = self.params['steps_percentage']
            start = self.params.get('start_percentage', 100)
            target = self.params['target_percentage']

            if step < 10:
                raise APIRequestError(
                    code="expansion_error",
                    message="Step percentage must be at least 10%"
                )
            if start <= 100:
                raise APIRequestError(
                    code="expansion_error",
                    message="Start percentage must be greater than 100%"
                )
            if target <= start:
                raise APIRequestError(
                    code="expansion_error",
                    message="Target percentage must be greater than start percentage for expansion"
                )

        # Validate version count
        if 'versions' in self.params:
            versions = self.params['versions']
            if not isinstance(versions, int) or not 1 <= versions <= 5:
                raise APIRequestError(
                    code="expansion_error",
                    message="Version count must be between 1 and 5"
                )
