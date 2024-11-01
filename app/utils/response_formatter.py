from typing import Dict, Any, List, Union, Optional
import logging
from app.utils.ai_helpers import count_tokens
from app.config.text_transform import (
    DEFAULT_PERCENTAGE,
    MIN_LENGTH_EXPANSION, MAX_LENGTH_EXPANSION, DEFAULT_LENGTH_EXPANSION,
    MIN_LENGTH_COMPRESSION, MAX_LENGTH_COMPRESSION, DEFAULT_LENGTH_COMPRESSION,
    DEFAULT_STEP_SIZE, MIN_STEP_SIZE, MAX_STEP_SIZE,
    MAX_VERSIONS, DEFAULT_VERSIONS,
    MODES
)

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Handles formatting of API responses for text transformations"""

    @staticmethod
    def format_response(
        ai_response: Dict[str, Any],
        request_params: Dict[str, Any],
        original_content: Union[str, List[str]],
        operation: str,
        validation_warnings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Unified formatter for both expansion and compression responses.
        Handles both fragment and cohesive text processing.
        """
        try:
            is_fragments = isinstance(original_content, list)
            content_list = original_content if is_fragments else [
                original_content]
            warnings = []

            # Convert input to unified format if needed
            if not is_fragments and 'lengths' in ai_response:
                ai_response = {'fragments': [
                    {'lengths': ai_response['lengths']}]}

            processed_fragments = []
            original_tokens = [count_tokens(text) for text in content_list]

            # Get target percentages based on mode
            target_percentages = ResponseFormatter._get_target_percentages(
                request_params, operation)

            validation = {
                "fragments": {
                    "expected": len(content_list),
                    "received": 0,
                    "passed": False
                },
                "lengths": {
                    "expected": target_percentages,
                    "passed": False,
                    "tolerance": 0.2
                }
            }

            # Process each fragment
            for i, original_text in enumerate(content_list):
                try:
                    fragment = (ai_response.get('fragments', []) or [])[
                        i] if ai_response else None
                    if not fragment or 'lengths' not in fragment:
                        warnings.append({
                            "key": f"{i}",
                            "message": f"Fragment {i+1} missing or invalid - using original"
                        })
                        processed_fragments.append(
                            ResponseFormatter._create_placeholder_fragment(original_text, request_params))
                        continue

                    lengths = []

                    # Use calculated target percentages instead of just the target
                    for j, target_percentage in enumerate(target_percentages):
                        try:
                            length_config = fragment['lengths'][j] if j < len(
                                fragment['lengths']) else None
                            if not length_config:
                                warnings.append({
                                    "key": f"{i}.{j}",
                                    "message": f"Fragment {i+1} length {j+1} missing - using original"
                                })
                                lengths.append(ResponseFormatter._create_placeholder_length(
                                    target_percentage, original_text, request_params))
                                continue

                            versions = []
                            target_tokens = round(
                                original_tokens[i] * target_percentage / 100)

                            # Process versions
                            for k, version in enumerate(length_config.get('versions', [])):
                                try:
                                    if not version or 'text' not in version:
                                        warnings.append({
                                            "key": f"{i}.{j}.{k}",
                                            "message": f"Fragment {i+1} length {j+1} version {k+1} missing - using original"
                                        })
                                        version = {'text': original_text}

                                    final_tokens = count_tokens(
                                        version['text'])
                                    final_percentage = round(
                                        (final_tokens / original_tokens[i]) * 100, 1)

                                    # Check if version is within tolerance
                                    deviation = abs(
                                        final_percentage - target_percentage) / target_percentage
                                    if deviation > validation['lengths']['tolerance']:
                                        warnings.append({
                                            "key": f"{i}.{j}.{k}",
                                            "message": f"Fragment {i+1}, length {j+1}, version {k+1}: Target was {target_percentage}%, but achieved {final_percentage}%"
                                        })

                                    versions.append({
                                        'text': version['text'],
                                        'final_tokens': final_tokens,
                                        'final_percentage': final_percentage
                                    })

                                except Exception as e:
                                    logger.warning(
                                        f"Error processing version: {str(e)}")
                                    warnings.append({
                                        "key": f"{i}.{j}.{k}",
                                        "message": f"Error processing fragment {i+1} length {j+1} version {k+1}"
                                    })

                            lengths.append({
                                'target_percentage': target_percentage,
                                'target_tokens': target_tokens,
                                'versions': versions
                            })

                        except Exception as e:
                            logger.warning(
                                f"Error processing length: {str(e)}")
                            warnings.append({
                                "key": f"{i}.{j}",
                                "message": f"Error processing fragment {i+1} length {j+1}"
                            })

                    processed_fragments.append({'lengths': lengths})

                except Exception as e:
                    logger.warning(f"Error processing fragment: {str(e)}")
                    warnings.append({
                        "key": f"{i}",
                        "message": f"Error processing fragment {i+1}"
                    })

            # Update processed counts
            validation["fragments"]["received"] = len(processed_fragments)
            validation["fragments"]["passed"] = (
                validation["fragments"]["received"] == validation["fragments"]["expected"]
            )

            # Check if all lengths were processed
            if processed_fragments:
                validation["lengths"]["passed"] = all(
                    len(fragment["lengths"]) == len(target_percentages)
                    for fragment in processed_fragments
                )

            response = {
                'type': 'fragments' if is_fragments else 'cohesive',
                'fragments': processed_fragments,
                'metadata': {
                    'mode': ResponseFormatter._determine_mode(request_params),
                    'operation': operation,
                    'validation': validation,
                    'step_size': request_params.get('steps_percentage'),
                    'start_percentage': request_params.get('start_percentage'),
                    'warnings': warnings if warnings else None
                }
            }

            return response

        except Exception as e:
            logger.error(f"Error formatting response: {e}", exc_info=True)
            return {
                'error': {
                    'code': 'format_error',
                    'message': f'Failed to format {operation} response',
                    'details': str(e)
                }
            }

    @staticmethod
    def _create_placeholder_fragment(original_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete placeholder fragment with all required lengths"""
        target_percentages = ResponseFormatter._get_target_percentages(
            params, 'expand')  # Default to expand
        return {
            'lengths': [
                ResponseFormatter._create_placeholder_length(
                    percentage, original_text, params)
                for percentage in target_percentages
            ]
        }

    @staticmethod
    def _create_placeholder_length(target_percentage: int, original_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a placeholder length with original text for all versions"""
        original_tokens = count_tokens(original_text)
        return {
            'target_percentage': target_percentage,
            'target_tokens': round(original_tokens * target_percentage / 100),
            'versions': [
                {
                    'text': original_text,
                    'final_tokens': original_tokens,
                    'final_percentage': 100.0
                }
                for _ in range(params.get('versions', DEFAULT_VERSIONS))
            ]
        }

    @staticmethod
    def _determine_mode(params: Dict[str, Any]) -> str:
        """Determine operation mode from parameters"""
        if params.get("target_percentages"):
            return "custom"
        elif "steps_percentage" in params or "start_percentage" in params:
            return "staggered"
        return "fixed"

    @staticmethod
    def _get_target_percentages(params: Dict[str, Any], operation: str) -> List[int]:
        """Extract target percentages from parameters based on mode"""
        is_expansion = operation == 'expand'

        if "target_percentages" in params:
            return params["target_percentages"]
        elif "steps_percentage" in params:
            start = params.get("start_percentage", DEFAULT_PERCENTAGE)
            target = params["target_percentage"]
            step = params["steps_percentage"]

            if is_expansion:
                return list(range(start, target + step, step))
            else:
                return list(range(start, target - step, -step))
        else:
            return [params.get("target_percentage",
                               DEFAULT_LENGTH_EXPANSION if is_expansion else DEFAULT_LENGTH_COMPRESSION)]
