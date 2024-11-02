from flask import Blueprint, jsonify, request, current_app
from app.middleware.auth import require_api_key
from app.utils.text_transform import TransformationRequest
from app.services.groq import get_ai_completion
from app.exceptions import APIRequestError
from app.utils.request_helpers import get_param, get_int_param, get_list_param
from app.utils.response_formatter import ResponseFormatter
from app.utils.request_validator import RequestValidator
import logging

logger = logging.getLogger(__name__)
rephrase_bp = Blueprint('rephrase', __name__)


@rephrase_bp.route('/', methods=['POST'])
@require_api_key
def rephrase_text():
    """
    Generate alternative versions of text while preserving meaning.
    Handles both single texts and multiple fragments.
    """
    try:
        # Get raw request data for validation
        raw_data = request.get_json()
        content = raw_data.get('content')

        # Validate request
        error, warnings = RequestValidator.validate_request(content, raw_data)
        if error:
            raise error

        # Get filtered params
        params = {
            'versions': get_int_param('versions', 1),
            'style': get_param('style', 'professional'),
            'tone': get_param('tone'),
            'aspects': get_list_param('aspects')
        }
        params = {k: v for k, v in params.items() if v is not None}

        # Create transformation request
        transform = TransformationRequest(
            content=content,
            params=params,
            warnings=warnings,
            operation='rephrase'  # New operation type
        )

        # Get prompts
        system_prompt = transform.get_system_prompt()
        user_message = transform.get_user_message()

        # Get AI completion
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_message=user_message
        )

        if "error" in response:
            logger.error(f"AI service returned error: {response['error']}")
            return jsonify(response), 500

        # Parse and validate response
        result = transform.parse_ai_response(response)

        # Format response
        formatted_response = ResponseFormatter.format_response(
            ai_response=result,
            request_params=params,
            original_content=content,
            operation='rephrase',
            validation_warnings=warnings
        )

        return jsonify(formatted_response), 200

    except APIRequestError as e:
        logger.error(f"API Request Error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'rephrase_error',
                'message': str(e),
                'status': e.status
            }
        }), e.status
    except ValueError as e:
        logger.error(f"Validation Error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'validation_error',
                'message': str(e),
                'status': 400
            }
        }), 400
    except Exception as e:
        logger.error("Unexpected error in rephrase endpoint", exc_info=True)
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'details': str(e) if current_app.debug else None,
                'status': 500
            }
        }), 500


@rephrase_bp.route('/examples', methods=['GET'])
def get_rephrase_examples():
    """Return example requests for the rephrase endpoint"""
    return jsonify({
        "single_rephrase": {
            "content": "The quick brown fox jumps over the lazy dog.",
            "versions": 3,
            "style": "creative"
        },
        "fragment_rephrase": {
            "content": [
                "The quick brown fox jumps.",
                "The lazy dog sleeps."
            ],
            "versions": 2,
            "style": "professional",
            "tone": "formal"
        },
        "styled_rephrase": {
            "content": "The quick brown fox jumps over the lazy dog.",
            "versions": 2,
            "style": "technical",
            "aspects": ["action_focus", "subject_emphasis"]
        }
    }), 200
