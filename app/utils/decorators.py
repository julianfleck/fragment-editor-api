from functools import wraps
from flask import request, abort
from .versioning import validate_version, get_version_headers


def versioned_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract version from URL (e.g., /v1/text/compress)
        version = request.path.split('/')[1]

        if not version.startswith('v'):
            abort(404, "API version must be specified")

        if not validate_version(version):
            abort(404, f"API version {version} not supported")

        # Get the response from the route handler
        response = f(*args, **kwargs)

        # Add version headers
        if hasattr(response, 'headers'):
            response.headers.update(get_version_headers(version))

        return response

    return decorated_function
