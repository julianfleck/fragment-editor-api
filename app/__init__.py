from flask import Flask, jsonify, request, g
from flask_cors import CORS
from app.config import config_by_name
from app.utils.request_helpers import init_request_helpers
from app.utils.versioning import get_version_headers, SUPPORTED_VERSIONS, LATEST_VERSION
import logging
from werkzeug.exceptions import HTTPException
from app.exceptions import APIRequestError

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

    # Initialize CORS with specific configuration
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Initialize request helpers
    init_request_helpers(app)

    # Initialize error handlers
    from app.utils.error_handler import init_error_handlers
    init_error_handlers(app)

    # Global request logging
    @app.before_request
    def log_request_info():
        logger.debug('Headers: %s', dict(request.headers))
        logger.debug('Body: %s', request.get_data())
        logger.debug('Query Params: %s', dict(request.args))
        logger.debug('Route: %s %s', request.method, request.path)

    # Enforce JSON for all POST/PUT/PATCH requests
    @app.before_request
    def require_json():
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.args:
                return None

            if not request.is_json:
                raise APIRequestError(
                    message='Content-Type must be application/json when not using query parameters',
                    status=415
                )

            try:
                _ = request.get_json()
            except Exception:
                raise APIRequestError(
                    message='Invalid JSON in request body',
                    status=400
                )

    # Version handling middleware
    @app.before_request
    def handle_version():
        if request.path == '/':
            return None

        parts = request.path.split('/')
        if len(parts) < 3 or not parts[2].startswith('v'):
            raise APIRequestError(
                message='API version must be specified',
                details={'supported_versions': SUPPORTED_VERSIONS},
                status=400
            )

        version = parts[2]
        if version not in SUPPORTED_VERSIONS:
            raise APIRequestError(
                message=f'API version {version} not supported',
                details={
                    'latest_version': LATEST_VERSION,
                    'supported_versions': SUPPORTED_VERSIONS
                },
                status=400
            )

        g.api_version = version

    @app.after_request
    def add_version_headers(response):
        # Add version headers to all responses except root
        if request.path != '/':
            version_headers = get_version_headers(
                getattr(g, 'api_version', None))
            response.headers.update(version_headers)
        return response

    # Register blueprints with versioned URLs
    from app.controllers.generate import generate_bp
    from app.controllers.compress import compress_bp
    from app.controllers.expand import expand_bp

    logger.debug("Registering blueprints...")
    # Note: version is now part of the URL prefix
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
                "version": LATEST_VERSION,
                "status": "operational",
                "supported_versions": SUPPORTED_VERSIONS
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
