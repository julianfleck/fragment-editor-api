from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_api_key
from app.utils.completion_helpers import (
    count_tokens, parse_ai_response,
    create_base_completion, process_versions,
    create_error_response, create_metadata,
    calculate_percentages, APIRequestError,
    format_target_lengths, create_format_strings
)
from app.config.ai_settings import DEFAULT_MODEL
from app.config.prompts_compression import (
    COMPRESS_SINGLE, COMPRESS_FIXED, COMPRESS_STAGGERED,
    COMPRESS_FRAGMENT, USER_MESSAGES
)
import logging

logger = logging.getLogger(__name__)
compress_bp = Blueprint('compress', __name__)


def create_completion(text: str, data: dict, mode: str = 'single') -> dict:
    """Create AI completion with appropriate prompt based on mode"""
    original_tokens = count_tokens(text)
    target_percentages = calculate_percentages(data, is_expansion=False)
    versions_count = len(target_percentages)

    # Get formatted targets from helper
    token_targets, targets_formatted = format_target_lengths(
        original_tokens, target_percentages)

    # Common parameters needed by all templates
    base_params = {
        'text': text,
        'tokens': original_tokens,
        'target_tokens': token_targets[0],
        # Add this for single version case
        'target_percentage': target_percentages[0],
        'targets_formatted': targets_formatted
    }

    # Set up prompt parameters based on mode
    if mode == 'fragment':
        system_prompt = COMPRESS_FRAGMENT
        fragments = text.split('\n---\n')
        format_strings = create_format_strings(
            num_fragments=len(fragments),
            num_versions=versions_count,
            mode='fragment'
        )

        msg_params = {
            **base_params,
            'target_percentages': target_percentages,
            'fragments': len(fragments),
            'fragment_format': format_strings['fragment_format']
        }
        msg_template = USER_MESSAGES['fragment']
    else:
        is_staggered = 'steps_percentage' in data or 'start_percentage' in data

        if versions_count == 1:
            system_prompt = COMPRESS_SINGLE
            msg_template = USER_MESSAGES['single']
            msg_params = base_params  # Use base params directly for single version
        else:
            system_prompt = COMPRESS_STAGGERED if is_staggered else COMPRESS_FIXED
            msg_template = USER_MESSAGES['fixed']
            format_strings = create_format_strings(
                num_fragments=1,
                num_versions=versions_count,
                mode='fixed'
            )

            msg_params = {
                **base_params,
                'target_tokens': token_targets,
                'percentages': target_percentages,
                'count': versions_count,
                'version_format': format_strings['version_format']
            }

    prompt = msg_template.format(**msg_params)
    return create_base_completion(text, system_prompt, prompt, DEFAULT_MODEL)


@compress_bp.route('/', methods=['POST'])
@require_api_key
def compress_text():
    """Handle text compression requests"""
    try:
        content = g.get_param('content', required=True)

        # Collect all parameters that affect versioning
        versioning_params = {
            'target_percentage': int(g.get_param('target_percentage', 50)),
            'steps_percentage': g.get_int_param('steps_percentage'),
            'start_percentage': g.get_int_param('start_percentage'),
            'versions': g.get_int_param('versions')
        }

        # Remove None values to ensure correct defaults
        versioning_params = {k: v for k,
                             v in versioning_params.items() if v is not None}

        logger.info(f"Processing compression request: {versioning_params}")

        target_percentages = calculate_percentages(
            versioning_params, is_expansion=False)

        if isinstance(content, list):
            # Fragment compression
            response = create_completion(
                "\n---\n".join(content), versioning_params, mode='fragment')
            result = parse_ai_response(response.choices[0].message.content)

            if 'error' in result:
                return create_error_response('ai_error', result['error']['message'],
                                             result['error'].get('response', ''))

            # Process fragments
            fragments = []
            original_tokens_list = [count_tokens(frag) for frag in content]

            for i, fragment in enumerate(content):
                versions = []
                original_tokens = original_tokens_list[i]
                start_idx = i * len(target_percentages)
                end_idx = start_idx + len(target_percentages)
                fragment_versions = result['versions'][start_idx:end_idx]

                if len(fragment_versions) < len(target_percentages):
                    logger.warning(f"Fragment {i} only got {
                                   len(fragment_versions)} versions instead of {len(target_percentages)}")

                for j, target in enumerate(target_percentages):
                    if j >= len(fragment_versions):
                        continue

                    compressed_text = fragment_versions[j]['text']
                    num_tokens = count_tokens(compressed_text)
                    final_percentage = (num_tokens / original_tokens) * 100

                    versions.append({
                        "text": compressed_text,
                        "target_percentage": target,
                        "final_percentage": final_percentage,
                        "num_tokens": num_tokens
                    })

                fragments.append({
                    "versions": versions,
                    "original_tokens": original_tokens
                })

            metadata = create_metadata("fragments", content, {
                'target_percentages': target_percentages,
                'target_percentage': versioning_params.get('target_percentage', 50),
                'mode': 'fragments',
                'steps_percentage': versioning_params.get('steps_percentage')
            }, {
                'versions_per_fragment': len(target_percentages),
                'final_versions': [len(fragment["versions"]) for fragment in fragments],
                'original_tokens_per_fragment': original_tokens_list
            })

            return jsonify({
                "type": "fragments",
                "fragments": fragments,
                "metadata": metadata
            }), 200

        else:
            # Single text compression
            response = create_completion(content, versioning_params)
            result = parse_ai_response(response.choices[0].message.content)

            if 'error' in result:
                return create_error_response('ai_error', result['error']['message'],
                                             result['error'].get('response', ''))

            original_tokens = count_tokens(content)
            versions = process_versions(
                result,
                original_tokens,
                target_percentages,
                is_expansion=False  # Explicitly mark as compression
            )

            metadata = create_metadata("cohesive", content, {
                'target_percentages': target_percentages,
                'target_percentage': versioning_params.get('target_percentage', 50),
                'mode': 'staggered' if 'steps_percentage' in versioning_params or 'start_percentage' in versioning_params else "fixed",
                'steps_percentage': versioning_params.get('steps_percentage')
            }, {
                'final_versions': len(versions),
                'original_tokens': original_tokens
            })

            return jsonify({
                "type": "cohesive",
                "versions": versions,
                "metadata": metadata
            }), 200

    except APIRequestError as e:
        return create_error_response('ai_error', e.message, status=e.status)
    except Exception as e:
        logger.error(f"Compression error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return create_error_response('internal_server_error', 'An unexpected error occurred', str(e))
