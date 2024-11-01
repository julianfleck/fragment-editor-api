from flask import Blueprint, g, jsonify, current_app, request
from app.middleware.auth import require_api_key
from app.utils.text_transform import TransformationRequest
from app.services.groq import get_ai_completion
from app.exceptions import APIRequestError
# Import helpers directly
from app.utils.request_helpers import get_param, get_int_param, get_list_param
import logging
from app.utils.response_formatter import ResponseFormatter
from app.utils.request_validator import RequestValidator

logger = logging.getLogger(__name__)
expand_bp = Blueprint('expand', __name__)


@expand_bp.route('/', methods=['POST'])
@require_api_key
def expand_text():
    """
    Expand text to target length(s).

    - Single target: Expands to specified percentage
    - Multiple targets: Creates versions at different lengths
    - Fragments: Expands multiple text fragments independently
    """
    try:
        # Get raw request data for validation first
        raw_data = request.get_json()
        content = raw_data.get('content')

        # Validate the raw request
        error, warnings = RequestValidator.validate_request(content, raw_data)
        if error:
            raise error

        # Now get filtered params for processing
        params = {
            'target_percentage': get_int_param('target_percentage'),
            'target_percentages': get_list_param('target_percentages'),
            'versions': get_int_param('versions'),
            'start_percentage': get_int_param('start_percentage'),
            'steps_percentage': get_int_param('steps_percentage'),
            'style': get_param('style', 'professional'),
            'tone': get_param('tone'),
            'aspects': get_list_param('aspects')
        }
        params = {k: v for k, v in params.items() if v is not None}

        # Create transformation request with validated params
        transform = TransformationRequest(
            content=content,
            params=params,
            warnings=warnings  # Pass through any warnings
        )

        # Get and log prompts
        system_prompt = transform.get_system_prompt()
        user_message = transform.get_user_message()

        logger.info("Generated prompts:")
        logger.info(f"System prompt:\n{system_prompt}")
        logger.info(f"User message:\n{user_message}")

        # Get AI completion
        logger.info("Requesting AI completion...")
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_message=user_message
        )

        if "error" in response:
            logger.error(f"AI service returned error: {response['error']}")
            return jsonify(response), 500

        logger.info("Successfully received AI response")
        logger.debug(f"Raw AI response: {response}")

        # Parse and validate response
        logger.info("Parsing and validating response...")
        result = transform.parse_ai_response(response)

        # Format response with collected warnings
        formatted_response = ResponseFormatter.format_response(
            ai_response=result,
            request_params=params,
            original_content=content,
            operation='expand',  # Specify operation type
            validation_warnings=transform.warnings
        )

        logger.info("Expansion completed successfully")
        logger.debug(f"Formatted response: {formatted_response}")

        return jsonify(formatted_response), 200

    except APIRequestError as e:
        logger.error(f"API Request Error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'expansion_error',
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
        logger.error(f"Unexpected error in expand endpoint", exc_info=True)
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'details': str(e) if current_app.debug else None,
                'status': 500
            }
        }), 500


@expand_bp.route('/examples', methods=['GET'])
def get_expand_examples():
    """Return example requests for the expand endpoint"""
    return jsonify({
        "single_expansion": {
            "content": "The cat sat on the mat.",
            "target_percentage": 150,  # Expand to 150% of original length
            "style": "creative"
        },
        "multiple_versions": {
            "content": "The cat sat on the mat.",
            "target_percentage": 150,  # Expand to 150% of original length
            "versions": 3,  # Generate 3 unique versions at 150%
            "style": "professional"
        },
        "staggered_expansion": {
            "content": "The cat sat on the mat.",
            "start_percentage": 120,    # Start at 120% of original
            "target_percentage": 200,   # End at 200% of original
            "steps_percentage": 20,     # Increase by 20% each step
            "style": "academic"
        },
        "fragment_expansion": {
            "content": [
                "The cat sat on the mat.",
                "The dog chased the ball."
            ],
            "target_percentage": 150,  # Expand each fragment to 150%
            "versions": 2,  # Generate 2 versions per fragment
            "style": "creative"
        },
        "custom_expansion": {
            "content": "The cat sat on the mat.",
            # Generate versions at 150%, 200%, and 250%
            "target_percentages": [150, 200, 250],
            "style": "professional",
            "tone": "humorous",
            "aspects": ["visual details", "character motivation"]
        }
    }), 200
