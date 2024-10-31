from functools import wraps
from flask import request, jsonify


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': {
                    'code': 'unauthorized',
                    'message': 'No Authorization header',
                    'status': 401
                }
            }), 401

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({
                    'error': {
                        'code': 'invalid_auth',
                        'message': 'Invalid authorization scheme',
                        'status': 401
                    }
                }), 401

            if not token:
                return jsonify({
                    'error': {
                        'code': 'invalid_auth',
                        'message': 'Invalid token',
                        'status': 401
                    }
                }), 401

        except ValueError:
            return jsonify({
                'error': {
                    'code': 'invalid_auth',
                    'message': 'Invalid authorization header format',
                    'status': 401
                }
            }), 401

        return f(*args, **kwargs)
    return decorated_function
