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
                    {"text": f"generated text for version {
                        i+1} at {config['target_percentage']}%"}
                    for i in range(config["versions_per_length"])
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

    def __init__(self, content: Union[str, List[str]], params: dict, warnings: Optional[List[str]] = None):
        self.content = content
        self.params = params
        self.warnings = warnings or []
        self.is_fragments = isinstance(content, list)

        # Determine if this is expansion or compression based on target
        self.is_expansion = self._should_expand()
        self.base_operation = 'expand' if self.is_expansion else 'compress'

        # Calculate targets and set up operation
        self.required_operation = self._determine_operation()
        self.target_percentages = self._calculate_target_percentages()

        # Validate final percentages
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
        from app.prompts.compress import (
            COMPRESS_BASE,
            COMPRESS_STAGGERED,
            COMPRESS_FRAGMENT
        )
        from app.prompts.expand import (
            EXPAND_BASE,
            EXPAND_STAGGERED,
            EXPAND_FRAGMENT
        )

        operation, mode = self.required_operation.split('_')

        if operation == 'EXPAND':
            if mode == self.FRAGMENT:
                return EXPAND_FRAGMENT
            elif mode == self.STAGGERED:
                return EXPAND_STAGGERED
            return EXPAND_BASE
        else:  # COMPRESS
            if mode == self.FRAGMENT:
                return COMPRESS_FRAGMENT
            elif mode == self.STAGGERED:
                return COMPRESS_STAGGERED
            return COMPRESS_BASE

    def get_user_message(self) -> str:
        """Get the appropriate user message template based on operation type"""
        from app.prompts.compress import USER_MESSAGES as COMPRESS_MESSAGES
        from app.prompts.expand import USER_MESSAGES as EXPAND_MESSAGES

        operation = 'expand' if self.is_expansion else 'compress'
        messages = EXPAND_MESSAGES if self.is_expansion else COMPRESS_MESSAGES
        mode = self._get_mode()

        # Get template and format with parameters
        template = messages[mode]

        # Format version details using local function
        version_details = format_version_details(
            self.content,
            self.target_percentages,
            self.is_fragments
        )

        # Format tone and aspects strings
        tone_str = f"\n- Maintain {self.params['tone']
                                   } tone" if 'tone' in self.params else ''
        aspects_str = f"\n- Focus on: {
            ', '.join(self.params['aspects'])}" if 'aspects' in self.params else ''

        # Get token counts
        if self.is_fragments:
            original_tokens = [count_tokens(f) for f in self.content]
        else:
            original_tokens = count_tokens(self.content)

        # Format template with all parameters
        return template.format(
            versions_per_length=self.params.get('versions', DEFAULT_VERSIONS),
            style=self.params.get('style', 'professional'),
            text=self.content,
            original_tokens=original_tokens,
            version_details=version_details,
            tone_str=tone_str,
            aspects_str=aspects_str,
            fragment_count=len(self.content) if self.is_fragments else 1
        )

    def parse_ai_response(self, response: dict) -> dict:
        """Parse and validate AI response structure"""
        try:
            warnings = []  # Track warnings for metadata

            # Validate basic structure
            if self.is_fragments:
                if 'fragments' not in response:
                    raise ValueError("Missing 'fragments' key in response")

                # Handle fragment count mismatch
                expected_fragments = len(self.content)
                actual_fragments = len(response['fragments'])

                if actual_fragments != expected_fragments:
                    if actual_fragments > expected_fragments:
                        warnings.append(f"Truncated response from {actual_fragments} to {
                                        expected_fragments} fragments")
                        response['fragments'] = response['fragments'][:expected_fragments]
                    else:
                        warnings.append(f"Incomplete response: expected {
                                        expected_fragments} fragments, got {actual_fragments}")

                # Validate each fragment
                for i, fragment in enumerate(response['fragments']):
                    if 'lengths' not in fragment:
                        raise ValueError(
                            f"Missing 'lengths' key in fragment {i+1}")

                    # Validate lengths match target configurations
                    if len(fragment['lengths']) < len(self.target_percentages):
                        warnings.append(
                            f"Fragment {i+1} has fewer lengths than expected")
                    fragment['lengths'] = fragment['lengths'][:len(
                        self.target_percentages)]

                    # Validate each length configuration
                    for j, length_config in enumerate(fragment['lengths']):
                        if 'versions' not in length_config:
                            raise ValueError(f"Missing 'versions' key in length config {
                                             j+1} of fragment {i+1}")

                        # Truncate versions if needed
                        if len(length_config['versions']) > MAX_VERSIONS:
                            warnings.append(f"Truncated excess versions in fragment {
                                            i+1}, length {j+1}")
                        length_config['versions'] = length_config['versions'][:MAX_VERSIONS]

                        # Validate each version
                        for k, version in enumerate(length_config['versions']):
                            self._validate_version(version, i, j, k)

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

        except ValueError as e:
            logger.error(f"Failed to validate response structure: {str(e)}")
            raise APIRequestError(f"Invalid response structure: {
                                  str(e)}", status=400)

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
        tolerance = 0.9
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
