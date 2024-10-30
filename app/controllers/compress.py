from flask import Blueprint, request, jsonify, current_app
from app.middleware.auth import require_api_key
from app.utils.ai_helpers import groq_client, calculate_max_tokens, parse_ai_response, count_tokens
from app.config.ai_settings import DEFAULT_MODEL
from app.config.prompts_compression import (
    COMPRESS_SINGLE, COMPRESS_FIXED, COMPRESS_STAGGERED, COMPRESS_FRAGMENT, USER_MESSAGES
)
import logging

logger = logging.getLogger(__name__)
compress_bp = Blueprint('compress', __name__)


def calculate_percentages(data: dict) -> list:
    """Calculate target percentages based on request parameters"""
    target = int(data.get('target_percentage', 50))

    # Case 1: Fixed percentage (single or multiple versions)
    if 'steps_percentage' not in data and 'start_percentage' not in data:
        return [target] * int(data.get('versions', 1))

    # Case 2: Staggered with explicit start
    if 'start_percentage' in data:
        start = int(data['start_percentage'])
    else:
        start = 100  # Default start at 100%

    step = int(data.get('steps_percentage', 20))

    # Calculate versions needed
    percentages = []
    current = start
    while current >= target:
        percentages.append(current)
        current -= step

    return percentages


def create_completion(text: str, data: dict, mode: str = 'single') -> dict:
    """Create AI completion with appropriate prompt based on mode"""

    # Calculate target percentages
    target_percentages = calculate_percentages(data)

    if mode == 'fragment':
        system_prompt = COMPRESS_FRAGMENT
        fragments = text.split('\n---\n')

        msg_params = {
            'fragment_count': len(fragments),
            'version_count': len(target_percentages),
            'text': '\n'.join(f'Fragment {i+1}:\n{fragment.strip()}\n'
                              for i, fragment in enumerate(fragments)),
            'requirements': f"Generate {len(target_percentages)} versions at these percentages: {', '.join(map(str, target_percentages))}%",
            'target': data.get('target_percentage', 50)
        }
        msg_template = USER_MESSAGES['fragment']
    else:
        # Select appropriate system prompt based on versions
        if len(target_percentages) == 1:
            system_prompt = COMPRESS_SINGLE
            msg_template = USER_MESSAGES['single']
            msg_params = {
                'text': text,
                'tokens': count_tokens(text),
                'target': data.get('target_percentage', 50)
            }
        elif 'steps_percentage' in data or 'start_percentage' in data:
            system_prompt = COMPRESS_STAGGERED
            msg_template = USER_MESSAGES['staggered']
            msg_params = {
                'text': text,
                'tokens': count_tokens(text),
                'percentages': ', '.join(map(str, target_percentages))
            }
        else:
            system_prompt = COMPRESS_FIXED
            msg_template = USER_MESSAGES['fixed']
            msg_params = {
                'text': text,
                'tokens': count_tokens(text),
                'target': data.get('target_percentage', 50),
                # Add count for fixed versions
                'count': len(target_percentages)
            }

    # Format user message
    prompt = msg_template.format(**msg_params)

    # Log request details
    logger.info(f"Mode: {mode}")
    logger.info(f"System prompt: {system_prompt}")
    logger.info(f"User prompt: {prompt}")

    # Make AI request
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model=DEFAULT_MODEL,
        temperature=0.7,
        max_tokens=calculate_max_tokens(text, multiplier=2)
    )

    logger.info("=== AI RESPONSE START ===")
    logger.info(response.choices[0].message.content)
    logger.info("=== AI RESPONSE END ===")

    return response


@compress_bp.route('/', methods=['POST'])
@require_api_key
def compress_text():
    """Handle text compression requests"""
    try:
        data = request.get_json()
        content = data.get('content')

        logger.info(f"Processing compression request: {data}")

        if not content:
            return jsonify({
                'error': {
                    'code': 'missing_field',
                    'message': 'Missing content field',
                    'status': 400
                }
            }), 400

        # Calculate target percentages first
        target_percentages = calculate_percentages(data)

        if isinstance(content, list):
            # Fragment compression
            response = create_completion(
                "\n---\n".join(content),
                data=data,
                mode='fragment'
            )

            result = parse_ai_response(response.choices[0].message.content)
            if 'error' in result:
                return jsonify({
                    'error': {
                        'code': 'ai_error',
                        'message': result['error']['message'],
                        'details': result['error'].get('response', ''),
                        'status': 500
                    }
                }), 500

            # Process fragments
            fragments = []
            original_tokens_list = [count_tokens(frag) for frag in content]

            for i, fragment in enumerate(content):
                versions = []
                original_tokens = original_tokens_list[i]

                # Get this fragment's versions
                start_idx = i * len(target_percentages)
                end_idx = start_idx + len(target_percentages)

                for j, version in enumerate(result['versions'][start_idx:end_idx]):
                    compressed_text = version['text']
                    num_tokens = count_tokens(compressed_text)
                    final_percentage = (num_tokens / original_tokens) * 100

                    # Skip if this is effectively the original text (100%)
                    if abs(final_percentage - 100.0) < 0.1:
                        continue

                    versions.append({
                        "text": compressed_text,
                        "target_percentage": target_percentages[j],
                        "final_percentage": final_percentage,
                        "num_tokens": num_tokens
                    })

                fragments.append({
                    "versions": versions,
                    "original_tokens": original_tokens
                })

            return jsonify({
                "type": "fragments",
                "fragments": fragments,
                "metadata": {
                    "mode": "fragments",
                    "fragment_count": len(content),
                    "original_text": content,
                    "original_tokens": original_tokens_list,
                    "target_percentages": target_percentages,
                    "step_size": data.get('steps_percentage'),
                    "versions_per_fragment": len(target_percentages)
                }
            }), 200

        else:
            # Single text compression
            response = create_completion(content, data)
            result = parse_ai_response(response.choices[0].message.content)

            if 'error' in result:
                return jsonify({
                    'error': {
                        'code': 'ai_error',
                        'message': result['error']['message'],
                        'details': result['error'].get('response', ''),
                        'status': 500
                    }
                }), 500

            # Calculate original tokens
            original_tokens = count_tokens(content)

            # Process versions - filter out 100% versions
            versions = []
            for i, version in enumerate(result['versions']):
                compressed_text = version['text']
                num_tokens = count_tokens(compressed_text)
                final_percentage = (num_tokens / original_tokens) * 100

                # Skip if this is effectively the original text (100%)
                if abs(final_percentage - 100.0) < 0.1:
                    continue

                versions.append({
                    "text": compressed_text,
                    "target_percentage": target_percentages[i],
                    "final_percentage": final_percentage,
                    "num_tokens": num_tokens
                })

            # Also filter target_percentages to match actual versions
            target_percentages = target_percentages[len(
                target_percentages)-len(versions):]

            return jsonify({
                "type": "cohesive",
                "versions": versions,
                "metadata": {
                    "mode": "staggered" if 'steps_percentage' in data or 'start_percentage' in data else "fixed",
                    "original_text": content,
                    "original_tokens": original_tokens,
                    "target_percentages": target_percentages,
                    "step_size": data.get('steps_percentage')
                }
            }), 200

    except Exception as e:
        logger.error(f"Compression error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'details': str(e),
                'status': 500
            }
        }), 500
