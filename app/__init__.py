from flask import Flask, jsonify, request, g
from flask_cors import CORS
from app.config import config_by_name
from app.utils.request_helpers import init_request_helpers
import logging
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    app = Flask(__name__)

    # Load config
    app.config.from_object(config_by_name[config_name])

    # Remove existing handlers to avoid duplicates
    logging.getLogger().handlers.clear()
    app.logger.handlers.clear()

    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configure single console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    # Configure Flask logger to use same handler
    app.logger.setLevel(logging.INFO)

    # Initialize CORS
    CORS(app)

    # Initialize request helpers
    init_request_helpers(app)

    # Global request logging
    @app.before_request
    def log_request_info():
        logger.debug('Headers: %s', dict(request.headers))
        logger.debug('Body: %s', request.get_data())
        logger.debug('Query Params: %s', dict(request.args))
        logger.debug('Route: %s %s', request.method, request.path)

    # Handle parameter validation errors
    @app.errorhandler(ValueError)
    def handle_validation_error(e):
        return jsonify({
            'error': {
                'code': 'invalid_parameters',
                'message': str(e)
            }
        }), 400

    # Enforce JSON for all POST/PUT/PATCH requests
    @app.before_request
    def require_json():
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Allow requests with query parameters
            if request.args:
                return None

            # For requests without query parameters, require JSON
            if not request.is_json:
                return jsonify({
                    'error': {
                        'code': 'invalid_content_type',
                        'message': 'Content-Type must be application/json when not using query parameters'
                    }
                }), 415

            # Try to parse JSON body
            try:
                _ = request.get_json()
            except Exception:
                return jsonify({
                    'error': {
                        'code': 'invalid_json',
                        'message': 'Invalid JSON in request body'
                    }
                }), 400

    # Global error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception('An error occurred: %s', str(e))

        # Handle HTTP exceptions
        if isinstance(e, HTTPException):
            response = {
                'error': {
                    'code': e.name.lower().replace(' ', '_'),
                    'message': e.description,
                    'status': e.code
                }
            }
            return jsonify(response), e.code

        # Handle other exceptions
        response = {
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'details': str(e) if app.debug else None,
                'status': 500
            }
        }
        return jsonify(response), 500

    # Register blueprints
    from app.controllers.generate import generate_bp
    from app.controllers.compress import compress_bp
    from app.controllers.expand import expand_bp

    logger.debug("Registering blueprints...")
    app.register_blueprint(generate_bp, url_prefix='/text/v1/generate')
    app.register_blueprint(compress_bp, url_prefix='/text/v1/compress')
    app.register_blueprint(expand_bp, url_prefix='/text/v1/expand')

    # Log all registered routes
    logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"{rule.endpoint}: {
                     rule.rule} [{', '.join(rule.methods)}]")

    @app.route('/')
    def welcome():
        return jsonify({
            "api": {
                "name": app.config['API_TITLE'],
                "version": app.config['API_VERSION'],
                "status": "operational"
            },
            "endpoints": {
                "generate": {
                    "url": "/text/v1/generate",
                    "methods": ["POST"],
                    "description": "Generate and chunk text content"
                },
                "compress": {
                    "url": "/text/v1/compress",
                    "methods": ["POST"],
                    "description": "Create concise versions of text"
                },
                "expand": {
                    "url": "/text/v1/expand",
                    "methods": ["POST"],
                    "description": "Expand and elaborate on text"
                }
            },
            "documentation": "https://api.metasphere.xyz/docs",
            "contact": {
                "support": "support@metasphere.xyz",
                "issues": "https://github.com/yourusername/repo/issues"
            }
        })

    return app
