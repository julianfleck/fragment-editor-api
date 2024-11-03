from ....models.requests.transformation import TransformationRequest
from ....models.responses.transformation import TransformationResponse
from ....models.responses.base import BaseResponse
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


def create_transformation_response() -> TransformationResponse:
    """Creates a default TransformationResponse instance"""
    return TransformationResponse(
        status=200,
        fragments=[],
        validation=None,
        type="transformation",
        metadata=create_processing_metadata().to_dict()
    )


def create_base_response() -> BaseResponse:
    """Creates a default BaseResponse instance"""
    return BaseResponse(
        status=200,
        type="base",
        metadata=create_processing_metadata().to_dict()
    )
