from typing import List, Dict, Union, Optional, Tuple
import json
import time
import logging
from app.config.ai_settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from app.config.prompts_compression import (
    COMPRESS_SINGLE, COMPRESS_FIXED, COMPRESS_STAGGERED,
    COMPRESS_FRAGMENT, USER_MESSAGES as COMPRESS_MESSAGES
)
from app.config.prompts_expansion import (
    EXPAND_SINGLE, EXPAND_FIXED, EXPAND_FRAGMENT,
    USER_MESSAGES as EXPAND_MESSAGES
)
from app.utils.ai_helpers import groq_client, count_tokens, calculate_max_tokens, clean_generated_text
from app.exceptions import APIRequestError

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text input"""
    return clean_generated_text(text)


def sort_versions_by_length(versions: List[Dict], reverse: bool = False) -> List[Dict]:
    """Sort versions by token count"""
    return sorted(versions, key=lambda x: count_tokens(x['text']), reverse=reverse)


def parse_ai_response(response_text: str) -> dict:
    """Parse AI response and ensure it's valid JSON with sorted versions"""
    logger.debug(f"Parsing AI response: {response_text}")

    try:
        # Find and parse JSON content
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            result = json.loads(json_str)
            logger.debug(f"Parsed JSON: {result}")

            # Handle different response formats and sort versions
            if 'fragments' in result:
                versions = []
                for fragment in result['fragments']:
                    versions.extend(fragment['versions'])
                return {'versions': sort_versions_by_length(versions)}
            elif 'versions' in result:
                result['versions'] = sort_versions_by_length(
                    result['versions'])
                return result
            elif 'error' in result:
                return result
            else:
                return {"error": {"code": "invalid_format", "message": "Response missing required fields"}}

        return {"error": {"code": "invalid_response_format", "message": "AI response was not in expected format"}}
    except Exception as e:
        logger.error(f"Response parsing error: {str(e)}")
        return {"error": {"code": "parsing_error", "message": f"Failed to process response: {str(e)}"}}


def process_versions(
    result: dict,
    original_tokens: int,
    target_percentages: List[int],
    is_expansion: bool = False
) -> List[Dict]:
    """Process and match sorted versions to target percentages"""
    if 'error' in result:
        return []

    # Sort versions - ascending for compression, descending for expansion
    sorted_versions = sort_versions_by_length(
        result['versions'], reverse=is_expansion)

    # Sort target percentages the same way
    sorted_targets = sorted(target_percentages, reverse=is_expansion)
    processed_versions = []

    # Match versions to targets based on order
    for target, version in zip(sorted_targets, sorted_versions):
        processed_text = version['text']
        num_tokens = count_tokens(processed_text)
        final_percentage = (num_tokens / original_tokens) * 100

        version_data = {
            "text": processed_text,
            "target_percentage": target,
            "final_percentage": final_percentage,
            "num_tokens": num_tokens
        }

        # Validate and add validation info if needed
        validation = validate_version(
            processed_text, original_tokens, target, is_expansion)
        if not validation["is_valid"]:
            version_data["validation"] = validation

        processed_versions.append(version_data)

    return processed_versions


def normalize_percentage(percentage: int, is_expansion: bool = False) -> int:
    """Normalize percentage for compression/expansion

    For expansion: 120% or 20% both mean expand by 20%
    For compression: percentage is used as-is (e.g., 80% means compress to 80%)
    """
    if is_expansion and percentage <= 100:
        return 100 + percentage
    return percentage


def validate_version(
    text: str,
    original_tokens: int,
    target_percentage: int,
    is_expansion: bool = False,
    tolerance: float = 0.50
) -> dict:
    """Validate if version meets target criteria and return validation details"""
    num_tokens = count_tokens(text)
    final_percentage = (num_tokens / original_tokens) * 100
    target = normalize_percentage(target_percentage, is_expansion)

    # Calculate acceptable ranges
    min_acceptable = target * (1 - tolerance)
    max_acceptable = target * (1 + tolerance)

    validation = {
        "is_valid": True,
        "reason": None,
        "target_range": {
            "min": min_acceptable,
            "target": target,
            "max": max_acceptable
        }
    }

    # Check for same text cases
    if not is_expansion and abs(final_percentage - 100.0) < 1.0:
        validation.update({
            "is_valid": False,
            "reason": "text_unchanged"
        })
    # Check for expansion/compression specific cases
    elif is_expansion and final_percentage <= 102:
        validation.update({
            "is_valid": False,
            "reason": "insufficient_expansion"
        })
    elif not is_expansion and final_percentage >= 98:
        validation.update({
            "is_valid": False,
            "reason": "insufficient_compression"
        })
    # Check if within target range
    elif not (min_acceptable <= final_percentage <= max_acceptable):
        validation.update({
            "is_valid": False,
            "reason": "outside_target_range"
        })

    return validation


def create_base_completion(
    text: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    multiplier: int = 2,
    max_retries: int = 3,
    initial_retry_delay: float = 1.0
) -> dict:
    """Create an AI completion with standard error handling and logging"""
    logger.info(f"System prompt: {system_prompt}")
    logger.info(f"User prompt: {user_prompt}")

    retry_delay = initial_retry_delay
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=temperature,
                max_tokens=calculate_max_tokens(text, multiplier=multiplier)
            )

            logger.info("=== AI RESPONSE START ===")
            logger.info(response.choices[0].message.content)
            logger.info("=== AI RESPONSE END ===")

            return response

        except InternalServerError as e:
            logger.warning(f"Groq server error (attempt {
                           attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise APIRequestError(
                    "Groq service is currently unavailable. Please try again later.",
                    status=503
                )
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded (attempt {
                           attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise APIRequestError(
                    "Rate limit exceeded. Please try again later.",
                    status=429
                )
            time.sleep(retry_delay)
            retry_delay *= 2

        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}")
            raise APIRequestError(f"Unexpected error: {str(e)}")


def create_error_response(code: str, message: str, details: str = None, status: int = 500) -> Tuple[dict, int]:
    """Create standardized error response"""
    error_response = {
        'error': {
            'code': code,
            'message': message,
            'status': status
        }
    }
    if details:
        error_response['error']['details'] = details

    return error_response, status


def create_metadata(
    content_type: str,
    original_text: Union[str, List[str]],
    params: dict,
    result_data: dict
) -> dict:
    """Create standardized metadata for API responses"""
    base_metadata = {
        "type": content_type,
        "mode": params.get('mode', 'fixed'),
        "original_text": original_text,
        "original_tokens": count_tokens(original_text) if isinstance(original_text, str)
        else [count_tokens(t) for t in original_text],
        "target_percentages": params.get('target_percentages', [params.get('target_percentage', 120)]),
        "style": params.get('style'),
        "tone": params.get('tone'),
        "aspects": params.get('aspects', []),
        "versions_requested": params.get('versions', 1),
        "final_versions": result_data.get('final_versions')
    }

    # Add step_size only for staggered mode
    if params.get('mode') == 'staggered' and 'steps_percentage' in params:
        base_metadata["step_size"] = params['steps_percentage']

    if content_type == "fragments":
        base_metadata.update({
            "fragment_count": len(original_text),
            "versions_per_fragment": result_data.get('versions_per_fragment'),
            "final_versions": result_data.get('final_versions', [])
        })

    return base_metadata


def calculate_percentages(data: dict, is_expansion: bool = False) -> list:
    """Calculate target percentages based on request parameters"""
    target = data.get('target_percentage')
    start = data.get('start_percentage')
    step = data.get('steps_percentage')
    versions = data.get('versions')

    # Case: start + target + steps -> calculate intermediate steps
    if start and target and step:
        current = start
        percentages = [start]

        if is_expansion:
            while current < target:
                current += step
                if current < target:
                    percentages.append(round(current))
            percentages.append(target)
        else:
            while current > target:
                current -= step
                if current > target:
                    percentages.append(round(current))
            percentages.append(target)

        return percentages

    # Case: versions + target -> multiple versions at target length
    if versions and target and not step and not start:
        # Return array with 'versions' number of targets
        return [target] * versions

    # Case: target + steps -> calculate versions
    elif target and step and not versions and not start:
        current = 100  # Always start at 100%
        percentages = []
        if is_expansion:
            while current < target:  # Go up to target for expansion
                percentages.append(current)
                current += step
            percentages.append(target)  # Include final target
        else:
            while current > target:  # Go down to target for compression
                percentages.append(current)
                current -= step
            percentages.append(target)  # Include final target

    # Case: target only -> single version
    elif target and not step and not versions and not start:
        percentages = [target]

    # Case: start + target -> calculate steps
    elif start and target and not step and not versions:
        total_diff = abs(target - start)
        suggested_step = 20  # Default step size
        num_steps = total_diff / suggested_step
        step = total_diff / round(num_steps)
        current = start
        percentages = [start]
        while (is_expansion and current < target) or (not is_expansion and current > target):
            current = current + step if is_expansion else current - step
            percentages.append(round(current))
        percentages[-1] = target  # Ensure we hit target exactly

    # Case: all parameters -> validate & prioritize
    elif start and target and versions and step:
        # Calculate how many steps we need
        needed_steps = abs(target - start) / step
        if abs(needed_steps - versions) > 0.1:  # Allow small rounding differences
            # If mismatch, ignore target and use start + versions + step
            if is_expansion:
                percentages = [start + (step * i) for i in range(versions)]
            else:
                percentages = [start - (step * i) for i in range(versions)]
        else:
            # If values match up, use them as is
            percentages = [start + (step * i) if is_expansion else start - (step * i)
                           for i in range(versions)]

    else:
        # Default case: single version with default target
        percentages = [120 if is_expansion else 50]

    # Round all percentages
    percentages = [round(p) for p in percentages]

    # Sort appropriately (ascending for expansion, descending for compression)
    return sorted(percentages, reverse=not is_expansion)


def format_target_lengths(original_tokens: int, target_percentages: list) -> tuple:
    """Format target lengths showing both tokens and percentages

    Returns:
        tuple: (token_targets, targets_formatted)
    """
    # Calculate target tokens for each percentage
    token_targets = [round((p / 100) * original_tokens)
                     for p in target_percentages]

    # Create formatted target string
    targets_formatted = '\n'.join([
        f"Version {i+1}: {t} tokens ({p}% of original)"
        for i, (p, t) in enumerate(zip(target_percentages, token_targets))
    ])

    return token_targets, targets_formatted


def create_format_strings(num_fragments: int, num_versions: int, mode: str = 'fragment') -> dict:
    """Create format strings for JSON response templates

    Args:
        num_fragments: Number of fragments (1 for single text)
        num_versions: Number of versions per fragment/text
        mode: 'fragment' or 'fixed'

    Returns:
        dict with format strings for versions and fragments
    """
    # Create version format for a single fragment/text
    version_format = ',\n        '.join([
        f'{{"text": "version {i+1}"}}'
        for i in range(num_versions)
    ])

    if mode == 'fragment':
        # Create fragment format with nested versions
        fragment_format = ',\n    '.join([
            f'{{\n      "versions": [\n        {
                version_format}\n      ]\n    }}'
            for _ in range(num_fragments)
        ])
        return {
            'version_format': version_format,
            'fragment_format': fragment_format
        }
    else:
        # For fixed/single mode, just return version format
        return {
            'version_format': version_format
        }


def create_completion(text: str, data: dict, mode: str = 'single') -> dict:
    """Create AI completion with appropriate prompt based on mode"""
    is_expansion = data.get('is_expansion', False)
    target_percentages = calculate_percentages(data, is_expansion=is_expansion)
    versions_count = len(target_percentages)

    # Common parameters for all modes
    style = data.get('style', 'elaborate')
    tone_str = f", tone: {data['tone']}" if data.get('tone') else ""
    aspects_str = f", focusing on: {
        ', '.join(data['aspects'])}" if data.get('aspects') else ""

    if mode == 'fragment':
        # Handle fragments mode
        fragments = text if isinstance(text, list) else text.split('\n---\n')
        fragments_tokens = [count_tokens(f) for f in fragments]

        # Calculate target tokens for each fragment and percentage
        fragment_targets = []
        for fragment_tokens in fragments_tokens:
            fragment_targets.append([
                round((p / 100) * fragment_tokens)
                for p in target_percentages
            ])

        # Format targets for prompt
        targets_formatted = '\n'.join([
            f"Fragment {i+1}: " + ', '.join([
                f"{t} tokens ({p}%)"
                for t, p in zip(fragment_target, target_percentages)
            ])
            for i, fragment_target in enumerate(fragment_targets)
        ])

        msg_params = {
            'text': '\n'.join(f'Fragment {i+1}:\n{fragment.strip()}\n'
                              for i, fragment in enumerate(fragments)),
            'target_tokens': fragment_targets,
            'target_percentages': target_percentages,
            'fragments': len(fragments),
            'style': style,
            'tone_str': tone_str,
            'aspects_str': aspects_str,
            'targets_formatted': targets_formatted
        }
        system_prompt = EXPAND_FRAGMENT if is_expansion else COMPRESS_FRAGMENT
        msg_template = EXPAND_MESSAGES['fragment'] if is_expansion else COMPRESS_MESSAGES['fragment']

    else:
        # Handle single text mode (fixed or staggered)
        original_tokens = count_tokens(text)
        token_targets = [round((p / 100) * original_tokens)
                         for p in target_percentages]

        # Format targets for multi-version prompts
        targets_formatted = '\n'.join([
            f"Version {i+1}: {t} tokens ({p}% of original)"
            for i, (p, t) in enumerate(zip(target_percentages, token_targets))
        ])

        if versions_count > 1:
            # Multiple versions requested (fixed or staggered)
            system_prompt = EXPAND_FIXED if is_expansion else COMPRESS_FIXED
            msg_template = EXPAND_MESSAGES['fixed'] if is_expansion else COMPRESS_MESSAGES['fixed']
            msg_params = {
                'text': text,
                'tokens': original_tokens,
                'token_targets': token_targets,
                'percentages': target_percentages,
                'count': versions_count,
                'targets_formatted': targets_formatted,
                'style': style,
                'tone_str': tone_str,
                'aspects_str': aspects_str
            }
        else:
            # Single version
            system_prompt = EXPAND_SINGLE if is_expansion else COMPRESS_SINGLE
            msg_template = EXPAND_MESSAGES['single'] if is_expansion else COMPRESS_MESSAGES['single']
            msg_params = {
                'text': text,
                'tokens': original_tokens,
                'target_tokens': token_targets[0],
                'target_percentage': target_percentages[0],
                'style': style,
                'tone_str': tone_str,
                'aspects_str': aspects_str
            }

    # Create the prompt and get completion
    prompt = msg_template.format(**msg_params)
    return create_base_completion(
        text=text,
        system_prompt=system_prompt,
        user_prompt=prompt,
        model=DEFAULT_MODEL,
        multiplier=3 if is_expansion else 2
    )
