from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ParamConfig:
    required: bool
    type: type
    default: Any = None
    min_value: Any = None
    max_value: Any = None
    allowed_values: List[Any] = None


# Shared parameters across ALL endpoints
SHARED_PARAMS = {
    'style': ParamConfig(
        required=False,
        type=str,
        default='professional',
        allowed_values=['professional', 'casual', 'technical', 'formal']
    ),
    'tone': ParamConfig(
        required=False,
        type=str,
        allowed_values=['formal', 'informal', 'friendly', 'strict']
    ),
    'aspects': ParamConfig(
        required=False,
        type=list,
        default=[]
    ),
    'versions': ParamConfig(
        required=False,
        type=int,
        default=1,
        min_value=1,
        max_value=5
    )
}

# Operation-specific parameters
ENDPOINT_PARAMS = {
    'rephrase': {
        **SHARED_PARAMS  # Only uses shared parameters
    },
    'expand': {
        **SHARED_PARAMS,
        'target_percentage': ParamConfig(
            required=False,
            type=int,
            default=150,
            min_value=110,
            max_value=300
        ),
        'target_percentages': ParamConfig(
            required=False,
            type=list
        ),
        'start_percentage': ParamConfig(
            required=False,
            type=int,
            min_value=100,
            max_value=300
        ),
        'steps_percentage': ParamConfig(
            required=False,
            type=int,
            min_value=10,
            max_value=50
        )
    },
    'compress': {
        **SHARED_PARAMS,
        'target_percentage': ParamConfig(
            required=False,
            type=int,
            default=50,
            min_value=10,
            max_value=90
        ),
        'target_percentages': ParamConfig(
            required=False,
            type=list
        ),
        'start_percentage': ParamConfig(
            required=False,
            type=int,
            min_value=10,
            max_value=100
        ),
        'steps_percentage': ParamConfig(
            required=False,
            type=int,
            min_value=10,
            max_value=50
        )
    }
}


def validate_params(operation: str, params: Dict[str, Any]) -> List[Dict[str, str]]:
    """Validate parameters for a specific operation"""
    warnings = []
    operation_params = ENDPOINT_PARAMS.get(operation, {})

    # Check for unknown parameters
    unknown_params = set(params.keys()) - set(operation_params.keys())
    if unknown_params:
        warnings.append({
            "code": "unknown_params",
            "message": f"Unknown parameters: {', '.join(unknown_params)}"
        })

    # Validate known parameters
    for param_name, config in operation_params.items():
        if param_name not in params:
            if config.required:
                warnings.append({
                    "code": "missing_required",
                    "message": f"Missing required parameter: {param_name}"
                })
            continue

        value = params[param_name]

        # Type validation
        if not isinstance(value, config.type):
            warnings.append({
                "code": "invalid_type",
                "message": f"Parameter {param_name} should be of type {config.type.__name__}"
            })
            continue

        # Range validation
        if config.min_value is not None and value < config.min_value:
            warnings.append({
                "code": "below_min",
                "message": f"Parameter {param_name} below minimum value of {config.min_value}"
            })

        if config.max_value is not None and value > config.max_value:
            warnings.append({
                "code": "above_max",
                "message": f"Parameter {param_name} above maximum value of {config.max_value}"
            })

        # Allowed values validation
        if config.allowed_values and value not in config.allowed_values:
            warnings.append({
                "code": "invalid_value",
                "message": f"Invalid value for {param_name}. Allowed values: {config.allowed_values}"
            })

    return warnings
