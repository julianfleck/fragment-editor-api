from typing import Dict, Any, List, Optional
from ....models.requests.transformation import TransformationRequest
from ....models.base.interfaces import Serializable
from .content import create_context
from .metadata import create_processing_metadata


def create_transformation_request() -> TransformationRequest:
    """Creates a default TransformationRequest instance"""
    return TransformationRequest(
        content="",
        operation="transform",
        params={},
        context=create_context()
    )


def create_base_response(status: int = 200,
                         type: str = "base",
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Creates a base response dictionary"""
    return {
        "status": status,
        "type": type,
        "metadata": metadata or create_processing_metadata().to_dict()
    }
