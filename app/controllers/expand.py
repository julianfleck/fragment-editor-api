from flask import Blueprint, g, jsonify, current_app, request
from app.middleware.auth import require_api_key
import logging

# Core model imports
from app.models.validation import ValidationError
from app.models.transformation import ExpansionOperation
from app.models.requests import TransformationRequest
from app.models.responses import ErrorResponse

logger = logging.getLogger(__name__)
expand_bp = Blueprint('expand', __name__)


@expand_bp.route('/', methods=['POST'])
@require_api_key
def expand_text():
    try:
        # Create request model
        transform_request = TransformationRequest.from_flask_request(request)

        # Execute operation
        operation = ExpansionOperation(transform_request)
        result = operation.execute()

        # Convert to response
        response = result.to_response()
        return jsonify(response.to_dict()), 200

    except ValidationError as e:
        warnings = [{"message": str(w)} for w in getattr(e, 'warnings', [])]
        error_response = ErrorResponse(
            error_code=e.code,
            message=e.message,
            warnings=warnings
        )
        return jsonify(error_response.to_dict()), 400


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
