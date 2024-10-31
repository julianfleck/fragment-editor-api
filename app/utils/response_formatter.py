from typing import Dict, Any, List, Union
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
    @staticmethod
    def format_expand_response(
        ai_response: Dict[str, Any],
        request_params: Dict[str, Any],
        original_content: Union[str, List[str]]
    ) -> Dict[str, Any]:
        try:
            is_fragments = isinstance(original_content, list)
            response_type = "fragments" if is_fragments else "cohesive"

            if is_fragments:
                fragments = []
                original_tokens = [count_tokens(f) for f in original_content]

                for i, fragment in enumerate(ai_response.get("fragments", [])):
                    lengths = []
                    for length_config in fragment.get("lengths", []):
                        versions = []
                        target_percentage = length_config["target_percentage"]
                        target_tokens = round(
                            original_tokens[i] * target_percentage / 100)

                        for version in length_config.get("versions", []):
                            final_tokens = count_tokens(version["text"])
                            versions.append({
                                "text": version["text"],
                                "final_tokens": final_tokens,
                                "final_percentage": round((final_tokens / original_tokens[i]) * 100, 1)
                            })

                        lengths.append({
                            "target_percentage": target_percentage,
                            "target_tokens": target_tokens,
                            "versions": versions
                        })

                    fragments.append({"lengths": lengths})

                response = {
                    "type": response_type,
                    "fragments": fragments
                }

            else:
                original_tokens = count_tokens(original_content)
                lengths = []

                for length_config in ai_response.get("lengths", []):
                    versions = []
                    target_percentage = length_config["target_percentage"]
                    target_tokens = round(
                        original_tokens * target_percentage / 100)

                    for version in length_config.get("versions", []):
                        final_tokens = count_tokens(version["text"])
                        versions.append({
                            "text": version["text"],
                            "final_tokens": final_tokens,
                            "final_percentage": round((final_tokens / original_tokens) * 100, 1)
                        })

                    lengths.append({
                        "target_percentage": target_percentage,
                        "target_tokens": target_tokens,
                        "versions": versions
                    })

                response = {
                    "type": response_type,
                    "lengths": lengths
                }

            # Add metadata
            response["metadata"] = {
                "mode": _determine_mode(request_params),
                "operation": "expand",
                "original_tokens": original_tokens,
                "versions_per_length": request_params.get('versions', DEFAULT_VERSIONS),
                "target_lengths": [
                    {
                        "target_percentage": length["target_percentage"],
                        "target_tokens": length["target_tokens"]
                    }
                    for length in (response["lengths"] if not is_fragments
                                   else response["fragments"][0]["lengths"])
                ],
                "step_size": request_params.get("steps_percentage", DEFAULT_STEP_SIZE),
                "start_percentage": request_params.get("start_percentage", DEFAULT_PERCENTAGE),
                "min_percentage": MIN_LENGTH_EXPANSION,
                "max_percentage": MAX_LENGTH_EXPANSION
            }

            return response

        except Exception as e:
            logger.error(f"Error formatting response: {e}", exc_info=True)
            return {
                "error": {
                    "code": "format_error",
                    "message": "Failed to format response",
                    "details": str(e)
                }
            }

    @staticmethod
    def format_compress_response(
        ai_response: Dict[str, Any],
        request_params: Dict[str, Any],
        original_content: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """Format compression response with metadata"""
        try:
            is_fragments = isinstance(original_content, list)
            response_type = "fragments" if is_fragments else "cohesive"

            if is_fragments:
                fragments = []
                original_tokens = [count_tokens(f) for f in original_content]

                for i, fragment in enumerate(ai_response.get("fragments", [])):
                    lengths = []
                    for length_config in fragment.get("lengths", []):
                        versions = []
                        target_percentage = length_config["target_percentage"]
                        target_tokens = round(
                            original_tokens[i] * target_percentage / 100)

                        for version in length_config.get("versions", []):
                            final_tokens = count_tokens(version["text"])
                            versions.append({
                                "text": version["text"],
                                "final_tokens": final_tokens,
                                "final_percentage": round((final_tokens / original_tokens[i]) * 100, 1)
                            })

                        lengths.append({
                            "target_percentage": target_percentage,
                            "target_tokens": target_tokens,
                            "versions": versions
                        })

                    fragments.append({"lengths": lengths})

                response = {
                    "type": response_type,
                    "fragments": fragments
                }

            else:
                original_tokens = count_tokens(original_content)
                lengths = []

                for length_config in ai_response.get("lengths", []):
                    versions = []
                    target_percentage = length_config["target_percentage"]
                    target_tokens = round(
                        original_tokens * target_percentage / 100)

                    for version in length_config.get("versions", []):
                        final_tokens = count_tokens(version["text"])
                        versions.append({
                            "text": version["text"],
                            "final_tokens": final_tokens,
                            "final_percentage": round((final_tokens / original_tokens) * 100, 1)
                        })

                    lengths.append({
                        "target_percentage": target_percentage,
                        "target_tokens": target_tokens,
                        "versions": versions
                    })

                response = {
                    "type": response_type,
                    "lengths": lengths
                }

            # Add metadata with compression-specific values
            response["metadata"] = {
                "mode": _determine_mode(request_params),
                "operation": "compress",
                "original_tokens": original_tokens,
                "versions_per_length": request_params.get('versions', DEFAULT_VERSIONS),
                "target_lengths": [
                    {
                        "target_percentage": length["target_percentage"],
                        "target_tokens": length["target_tokens"]
                    }
                    for length in (response["lengths"] if not is_fragments
                                   else response["fragments"][0]["lengths"])
                ],
                "step_size": request_params.get("steps_percentage", DEFAULT_STEP_SIZE),
                "start_percentage": request_params.get("start_percentage", DEFAULT_PERCENTAGE),
                "min_percentage": MIN_LENGTH_COMPRESSION,
                "max_percentage": MAX_LENGTH_COMPRESSION
            }

            return response

        except Exception as e:
            logger.error(f"Error formatting compression response: {
                         e}", exc_info=True)
            return {
                "error": {
                    "code": "format_error",
                    "message": "Failed to format compression response",
                    "details": str(e)
                }
            }

    @staticmethod
    def format_summarize_response():
        """Format summarization response with metadata"""
        # Similar implementation for summarize endpoint
        pass


def _determine_mode(params: Dict[str, Any]) -> str:
    """Determine operation mode from parameters"""
    if params.get("target_percentages"):
        return "custom"
    elif "steps_percentage" in params or "start_percentage" in params:
        return "staggered"
    return "fixed"


def _count_tokens(content: Union[str, List[str]]) -> Union[int, List[int]]:
    """Count tokens in content"""
    if isinstance(content, list):
        return [count_tokens(fragment) for fragment in content]
    return count_tokens(content)


def _get_target_percentages(params: Dict[str, Any], is_expansion: bool) -> List[int]:
    """Extract target percentages from parameters"""
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


def _count_fragment_versions(fragments: List[Dict[str, Any]]) -> List[int]:
    """Count versions per fragment"""
    return [len(fragment.get("versions", [])) for fragment in fragments]
