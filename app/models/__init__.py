from .base.description import DescriptionMixin
from .base.interfaces import (
    Serializable,
    Validatable,
    ValidationResultInterface,
    TransformationResultBase,
    TransformationOperation
)
from .content.types import Context
from .content.core import ContentType
from .content.metrics import ContentMetrics
from .content.summary import Summary
from .content.validation import ContentValidation
from .taxonomy.base import TaxonomyNode
from .taxonomy.relationships import SemanticRelationship
from .taxonomy.structure import (
    Section,
    StructuredContent,
    Fragment,
    Length,
    Version
)
from .validation.base import ValidationBase
from .validation.error import ValidationError
from .validation.result import ValidationResult
from .validation.rules import ValidationRules
from .transformation.operations import TransformationOperation
from .transformation.result import TransformationResult
from .transformation.expand import ExpansionOperation
from .transformation.compress import CompressionOperation
from .transformation.rephrase import RephraseOperation
from .requests.transformation import TransformationRequest
from .responses.transformation import TransformationResponse
from .metadata.core import Metadata, ProcessingMetadata, ContentMetadata

__all__ = [
    # Base
    'DescriptionMixin', 'Serializable', 'Validatable',
    'TransformationResultBase', 'TransformationOperation',

    # Content
    'Context', 'ContentType', 'ContentMetrics', 'Summary', 'ContentValidation',

    # Taxonomy
    'TaxonomyNode', 'Section', 'Fragment', 'Length', 'Version',
    'StructuredContent', 'SemanticRelationship',

    # Validation
    'ValidationBase', 'ValidationError', 'ValidationResult', 'ValidationRules', 'ValidationResultInterface',

    # Transformation
    'TransformationOperation', 'TransformationResult',
    'ExpansionOperation', 'CompressionOperation', 'RephraseOperation',

    # Request/Response
    'TransformationRequest', 'TransformationResponse',

    # Metadata
    'Metadata', 'ProcessingMetadata', 'ContentMetadata'
]

# Directory Structure:
# app/
#   models/
#     __init__.py
#     base/
#       __init__.py
#       description.py      # DescriptionMixin
#       interfaces.py       # Abstract base classes & protocols
#
#     content/
#       __init__.py
#       core.py            # Context, ContentType
#       metrics.py         # ContentMetrics
#       summary.py         # Summary
#       topics.py          # Topics
#       validation.py      # ContentValidation
#
#     metadata/
#       __init__.py
#       core.py           # Metadata
#
#   requests/
#     __init__.py
#     base.py           # BaseRequest
#     transformation.py # TransformationRequest
#     batch.py         # BatchRequest
#     chain.py         # ChainRequest
#
#     responses/
#       __init__.py
#       base.py           # BaseResponse
#       error.py          # ErrorResponse
#       transformation.py # TransformationResponse
#
#     taxonomy/
#       __init__.py
#       base.py          # TaxonomyNode
#       category.py      # Category
#       relationships.py # SemanticRelationship
#       structure.py     # Section, Chunk, Segment, Fragment, Version, Length
#       topic.py        # Topic
#
#     transformation/
#       operations.py    # TransformationOperation (base class)
#       compress.py     # CompressionOperation
#       expand.py       # ExpansionOperation
#       rephrase.py    # RephraseOperation
#       result.py      # TransformationResult

# app/models/
#   transformation/
#       __init__.py
#     operations.py    # TextOperation base class
#     implementations/ # Specific operation implementations
#       expand.py
#       compress.py
#       rephrase.py

#     validation/
#       __init__.py
#       base.py        # ValidationBase
#       error.py       # ValidationError
#       result.py      # ValidationResult
#       rules.py       # ValidationRules
