from flask import Blueprint, g
from app.middleware.auth import require_api_key
from app.utils.completion_helpers import (
    count_tokens, parse_ai_response,
    create_base_completion, process_versions,
    create_error_response, create_metadata,
    calculate_percentages, APIRequestError,
    format_target_lengths, create_format_strings
)
from app.config.ai_settings import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_VERSIONS,
    MAX_VERSIONS
)
from app.config.prompts_expansion import (
    EXPAND_SINGLE, EXPAND_FIXED, EXPAND_FRAGMENT, USER_MESSAGES
)
import logging

logger = logging.getLogger(__name__)
expand_bp = Blueprint('expand', __name__)


def create_completion(text: str, data: dict, mode: str = 'single') -> dict:
    """Create AI completion with appropriate prompt based on mode"""
    original_tokens = count_tokens(text)
    target_percentages = calculate_percentages(data, is_expansion=True)
    versions_count = len(target_percentages)

    # Get formatted targets from helper
    token_targets, targets_formatted = format_target_lengths(
        original_tokens, target_percentages)

    # Common style parameters
    style = data.get('style', 'elaborate')
    tone_str = f", tone: {data['tone']}" if data.get('tone') else ""
    aspects_str = f", focusing on: {
        ', '.join(data['aspects'])}" if data.get('aspects') else ""

    # Set up prompt parameters based on mode
    if mode == 'fragment':
        system_prompt = EXPAND_FRAGMENT
        fragments = text if isinstance(text, list) else text.split('\n---\n')
        format_strings = create_format_strings(
            num_fragments=len(fragments),
            num_versions=len(target_percentages),
            mode='fragment'
        )

        msg_params = {
            'text': '\n'.join(f'Fragment {i+1}:\n{fragment.strip()}\n'
                              for i, fragment in enumerate(fragments)),
            'target_tokens': token_targets,
            'target_percentages': target_percentages,
            'fragments': len(fragments),
            'style': style,
            'tone_str': tone_str,
            'aspects_str': aspects_str,
            'targets_formatted': targets_formatted,
            'fragment_format': format_strings['fragment_format']
        }
        msg_template = USER_MESSAGES['fragment']
    else:
        if versions_count == 1:
            system_prompt = EXPAND_SINGLE
            msg_template = USER_MESSAGES['single']
            msg_params = {
                'text': text,
                'tokens': original_tokens,
                'target_tokens': token_targets[0],
                'target_percentage': target_percentages[0],
                'style': style,
                'tone_str': tone_str,
                'aspects_str': aspects_str
            }
        else:
            system_prompt = EXPAND_FIXED
            msg_template = USER_MESSAGES['fixed']
            format_strings = create_format_strings(
                num_fragments=1,
                num_versions=versions_count,
                mode='fixed'
            )

            msg_params = {
                'text': text,
                'tokens': original_tokens,
                'token_targets': token_targets,
                'percentages': target_percentages,
                'count': versions_count,
                'targets_formatted': targets_formatted,
                'style': style,
                'tone_str': tone_str,
                'aspects_str': aspects_str,
                'version_format': format_strings['version_format']
            }

    prompt = msg_template.format(**msg_params)
    return create_base_completion(text, system_prompt, prompt, DEFAULT_MODEL)


@expand_bp.route('/', methods=['POST'])
@require_api_key
def expand_text():
    """Handle text expansion requests"""
    try:
        content = g.get_param('content', required=True)
        style = g.get_param('style', 'elaborate')

        # Calculate original tokens
        original_tokens = count_tokens(
            content) if not isinstance(content, list) else None
        original_tokens_list = [count_tokens(frag) for frag in content] if isinstance(
            content, list) else None

        # Collect all parameters that affect versioning
        versioning_params = {
            'target_percentage': int(g.get_param('target_percentage', 120)),
            'steps_percentage': g.get_int_param('steps_percentage'),
            'start_percentage': g.get_int_param('start_percentage'),
            'versions': g.get_int_param('versions')
        }

        # Remove None values to ensure correct defaults
        versioning_params = {k: v for k,
                             v in versioning_params.items() if v is not None}

        # Calculate target percentages for all modes
        target_percentages = calculate_percentages(
            versioning_params, is_expansion=True)

        data = {
            **versioning_params,
            'target_percentages': target_percentages,
            'style': style,
            'tone': g.get_param('tone'),
            'aspects': g.get_list_param('aspects', [])
        }

        logger.info(f"Processing expansion request: {data}")

        if isinstance(content, list):
            # Fragment expansion
            response = create_completion(
                "\n---\n".join(content), data, mode='fragment')
            result = parse_ai_response(response.choices[0].message.content)

            if 'error' in result:
                return create_error_response('ai_error', result['error'])

            # Process fragments using helper
            fragments = []
            for i, (fragment, version) in enumerate(zip(content, result['versions'])):
                expanded_text = version['text']
                num_tokens = count_tokens(expanded_text)
                final_percentage = (num_tokens / original_tokens_list[i]) * 100

                fragments.append({
                    "id": f"f{i+1}",
                    "original": fragment,
                    "versions": [{
                        "text": expanded_text,
                        "num_tokens": num_tokens,
                        # Use first target for fragments
                        "target_percentage": target_percentages[0],
                        "final_percentage": final_percentage
                    }]
                })

            metadata = create_metadata("fragments", content, {
                'target_percentage': target_percentages[0],
                'target_percentages': target_percentages,
                'style': style,
                'tone': g.get_param('tone'),
                'aspects': g.get_list_param('aspects', []),
                'mode': 'fragments'
            }, {
                'versions_per_fragment': 1,
                'final_versions': [len(f["versions"]) for f in fragments],
                'original_tokens_list': original_tokens_list
            })

            return {
                "type": "fragments",
                "fragments": fragments,
                "metadata": metadata
            }, 200

        else:
            # Single text expansion
            response = create_completion(content, data)
            result = parse_ai_response(response.choices[0].message.content)

            if 'error' in result:
                return create_error_response('ai_error', result['error'])

            # Process versions using helper
            versions_data = process_versions(
                result,
                original_tokens,
                target_percentages,
                is_expansion=True
            )

            metadata = create_metadata("cohesive", content, {
                'target_percentage': target_percentages[0],
                'target_percentages': target_percentages,
                'style': style,
                'tone': g.get_param('tone'),
                'aspects': g.get_list_param('aspects', []),
                'mode': 'staggered' if 'steps_percentage' in data or 'start_percentage' in data else 'fixed'
            }, {
                'final_versions': len(versions_data),
                'original_tokens': original_tokens
            })

            return {
                "type": "cohesive",
                "versions": versions_data,
                "metadata": metadata
            }, 200

    except APIRequestError as e:
        return create_error_response('ai_error', e.message, status=e.status)
    except Exception as e:
        logger.error(f"Expansion error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return create_error_response('expansion_failed', 'Failed to generate expanded text', str(e))
