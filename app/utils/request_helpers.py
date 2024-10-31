from flask import request, g
from typing import Optional, List, Any


def get_param(param_name: str, default: Any = None, required: bool = False) -> Any:
    """Get a parameter from request, optionally requiring it"""
    value = request.json.get(param_name, default)
    if required and value is None:
        raise ValueError(f"Missing required parameter: {param_name}")
    return value


def get_list_param(param_name: str, default: List = None) -> List:
    """Get a list parameter from request, return empty list if not present"""
    value = request.json.get(param_name)
    if value is None:
        return default if default is not None else []
    if not isinstance(value, list):
        return [value]
    return value


def get_int_param(param_name: str, default: int = None) -> Optional[int]:
    """Get an integer parameter from request, return None if not present or not valid"""
    value = request.json.get(param_name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def init_request_helpers(app):
    """Initialize request helpers"""
    @app.before_request
    def setup_request():
        """Set up request context with helpers"""
        g.get_param = get_param
        g.get_list_param = get_list_param
        g.get_int_param = get_int_param
