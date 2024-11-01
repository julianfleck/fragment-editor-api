from functools import wraps
from flask import request, jsonify, current_app
from app.exceptions import AuthenticationError


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError(
                code='unauthorized',
                message='No Authorization header'
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                raise AuthenticationError(
                    code='invalid_auth',
                    message='Invalid authorization scheme'
                )

            if token not in current_app.config['API_KEYS']:
                raise AuthenticationError(
                    code='invalid_auth',
                    message='Invalid API key'
                )

        except ValueError:
            raise AuthenticationError(
                code='invalid_auth',
                message='Invalid authorization header format'
            )

        return f(*args, **kwargs)
    return decorated_function
