from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.exceptions import APIRequestError, ValidationError, AuthenticationError
import logging

logger = logging.getLogger(__name__)


def init_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        response = {
            "error": {
                "code": e.code,
                "message": e.message,
                "field": e.field,
                "status": 400
            }
        }
        return jsonify(response), 400

    @app.errorhandler(AuthenticationError)
    def handle_auth_error(e):
        response = {
            "error": {
                "code": e.code,
                "message": e.message,
                "status": e.status
            }
        }
        return jsonify(response), e.status

    @app.errorhandler(APIRequestError)
    def handle_api_error(e):
        response = {
            "error": {
                "code": "api_error",
                "message": e.message,
                "details": e.details,
                "status": e.status
            }
        }
        return jsonify(response), e.status

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        response = {
            "error": {
                "code": e.name.lower().replace(' ', '_'),
                "message": e.description,
                "status": e.code
            }
        }
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        logger.exception('An unexpected error occurred: %s', str(e))
        response = {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": str(e) if app.debug else None,
                "status": 500
            }
        }
        return jsonify(response), 500
