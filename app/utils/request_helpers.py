from flask import request, g
import logging

logger = logging.getLogger(__name__)


def init_request_helpers(app):
    @app.before_request
    def init_request_context():
        # Initialize request context
        g.debug = app.debug
        g.params = {}

        # Merge query params and JSON body
        if request.args:
            g.params.update(request.args.to_dict())
        if request.is_json and request.get_json():
            g.params.update(request.get_json())

        logger.debug(f"Initialized request context with params: {g.params}")


def get_param(name: str, default=None, required=False):
    """Get parameter from request context"""
    value = g.params.get(name, default)
    if required and value is None:
        raise ValueError(f"Missing required parameter: {name}")
    return value


def get_int_param(name: str, default=None):
    """Get integer parameter from request context"""
    value = g.params.get(name, default)
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid integer value for parameter: {name}")
    return None


def get_list_param(name: str, default=None):
    """Get list parameter from request context"""
    value = g.params.get(name, default)
    if value is not None:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [x.strip() for x in value.split(',')]
        raise ValueError(f"Invalid list value for parameter: {name}")
    return None
