from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_api_key
from app.utils.text_processing import chunk_text
from app.utils.ai_helpers import groq_client, calculate_max_tokens, count_tokens, parse_ai_response
from app.config.ai_settings import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_VERSIONS,
    MAX_VERSIONS,
    VALID_FRAGMENT_STYLES,
    GENERATE_PROMPT
)

generate_bp = Blueprint('generate', __name__)


@generate_bp.route('/text', methods=['POST'])
@require_api_key
def create_text():
    try:
        content = g.get_param('content', required=True)
        target_length = int(g.get_param('target_length', 200))
        style = g.get_param('style', 'elaborate')
        versions = min(
            int(g.get_param('versions', DEFAULT_VERSIONS)), MAX_VERSIONS)

        if style not in VALID_FRAGMENT_STYLES:
            return jsonify({
                'error': {
                    'code': 'invalid_style',
                    'message': f'Style must be one of: {", ".join(VALID_FRAGMENT_STYLES)}'
                }
            }), 400

        # Common completion creation function
        def create_completion(text, prompt_suffix=""):
            return groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": GENERATE_PROMPT},
                    {"role": "user", "content": f"Generate {versions} new versions of this text in {
                        style} style, targeting {target_length} tokens{prompt_suffix}: {text}"}
                ],
                model=DEFAULT_MODEL,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=calculate_max_tokens(text, multiplier=2)
            )

        # Handle single string
        if isinstance(content, str):
            completion = create_completion(content)
            result = parse_ai_response(completion.choices[0].message.content)
            if "error" in result:
                return jsonify({"error": result["error"]}), 400

            return jsonify({
                "type": "cohesive",
                "versions": result["versions"],
                "metadata": {
                    "type": "cohesive",
                    "original_tokens": count_tokens(content),
                    "target_tokens": target_length,
                    "versions_requested": versions,
                    # For debugging
                    "raw_response": completion.choices[0].message.content
                }
            }), 200

        # Handle list of fragments
        if isinstance(content, list):
            fragments = []
            for idx, fragment in enumerate(content):
                completion = create_completion(
                    fragment, f" for fragment {idx+1}")
                result = parse_ai_response(
                    completion.choices[0].message.content)
                if "error" in result:
                    return jsonify({"error": result["error"]}), 400

                fragments.append({
                    "id": f"f{idx+1}",
                    "original": fragment,
                    "versions": result["versions"],
                    # For debugging
                    "raw_response": completion.choices[0].message.content
                })

            return jsonify({
                "type": "fragments",
                "fragments": fragments,
                "metadata": {
                    "type": "fragments",
                    "fragment_count": len(fragments),
                    "original_tokens": count_tokens(' '.join(content)),
                    "target_tokens": target_length,
                    "versions_requested": versions
                }
            }), 200

        return jsonify({
            "error": {
                "code": "invalid_content",
                "message": "Content must be either a string or an array of strings"
            }
        }), 400

    except Exception as e:
        return jsonify({
            "error": {
                "code": "generation_failed",
                "message": "Failed to generate text",
                "details": str(e)
            }
        }), 500
