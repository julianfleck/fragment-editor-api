from flask import Blueprint, g, jsonify, current_app
from app.middleware.auth import require_api_key
from app.utils.text_transform import TransformationRequest
from app.services.groq import get_ai_completion
from app.exceptions import APIRequestError
from app.utils.request_helpers import get_param, get_int_param, get_list_param
import logging
from app.utils.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)
compress_bp = Blueprint('compress', __name__)


@compress_bp.route('/', methods=['POST'])
@require_api_key
def compress_text():
    """
    Compress text to target length(s).

    - Single target: Compresses to specified percentage
    - Multiple targets: Creates versions at different lengths
    - Fragments: Compresses multiple text fragments independently
    """
    try:
        # Log incoming request
        logger.info("Compression request received")
        logger.debug(f"Request params: {g.params}")

        # Get required content parameter
        content = get_param('content', required=True)
        logger.info(f"Content to compress: {content[:100]}..." if len(
            str(content)) > 100 else content)

        # Collect parameters
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

        # Remove None values and log
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Compression parameters: {params}")

        # Create transformation request with compression operation
        transform = TransformationRequest(
            content=content,
            operation='compress',
            params=params
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

        # Format response with metadata
        formatted_response = ResponseFormatter.format_compress_response(
            ai_response=result,
            request_params=params,
            original_content=content
        )

        logger.info("Compression completed successfully")
        logger.debug(f"Formatted response: {formatted_response}")

        return jsonify(formatted_response), 200

    except APIRequestError as e:
        logger.error(f"API Request Error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'compression_error',
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
        logger.error(f"Unexpected error in compress endpoint", exc_info=True)
        return jsonify({
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'details': str(e) if current_app.debug else None,
                'status': 500
            }
        }), 500


@compress_bp.route('/examples', methods=['GET'])
def get_compress_examples():
    """Return example requests for the compress endpoint"""
    return jsonify({
        "single_compression": {
            "content": "The quick brown fox jumps over the lazy dog while the sun sets in the west, casting long shadows across the verdant meadow.",
            "target_percentage": 50,  # Keep 50% of the original text
            "style": "concise"
        },
        "multiple_versions": {
            "content": "The quick brown fox jumps over the lazy dog while the sun sets in the west, casting long shadows across the verdant meadow.",
            "target_percentage": 50,  # Keep 50% of the original text
            "versions": 3,
            "style": "professional"
        },
        "staggered_compression": {
            "content": "The quick brown fox jumps over the lazy dog while the sun sets in the west, casting long shadows across the verdant meadow.",
            "start_percentage": 80,    # Start by keeping 80%
            "target_percentage": 30,   # End by keeping 30%
            "steps_percentage": 10,    # Reduce by 10% each step
            "style": "technical"
        },
        "fragment_compression": {
            "content": [
                "The quick brown fox jumps over the lazy dog.",
                "The sun sets in the west, casting long shadows."
            ],
            "target_percentage": 50,  # Keep 50% of each fragment
            "versions": 2,
            "style": "creative"
        },
        "custom_compression": {
            "content": "The quick brown fox jumps over the lazy dog while the sun sets in the west, casting long shadows across the verdant meadow.",
            # Keep 75%, 50%, and 25% of original
            "target_percentages": [75, 50, 25],
            "style": "professional",
            "tone": "formal",
            "aspects": ["key actions", "main subjects"]
        }
    }), 200
