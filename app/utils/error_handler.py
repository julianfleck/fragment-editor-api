from flask import jsonify
from werkzeug.exceptions import HTTPException

def init_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Handle HTTP exceptions
        if isinstance(e, HTTPException):
            response = {
                "error": {
                    "code": e.name.lower().replace(' ', '_'),
                    "message": e.description,
                    "status": e.code
                }
            }
            return jsonify(response), e.code
            
        # Handle other exceptions
        response = {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": str(e) if app.debug else None,
                "status": 500
            }
        }
        return jsonify(response), 500

    @app.route('/')
    def welcome():
        return jsonify({
            "message": "Welcome to the Text Transform API",
            "version": app.config['API_VERSION'],
            "documentation": "https://api.metasphere.xyz/docs",
            "endpoints": {
                "generate": "/text/v1/generate",
                "summarize": "/text/v1/summarize",
                "expand": "/text/v1/expand"
            },
            "status": "operational"
        }) 