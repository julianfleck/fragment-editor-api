# Todo

-   context param for all endpoints: allow passing in a context object

-   segmentation endpoint
-   fragmentation endpoint
-   chunking endpoint
-   difference between segmentation, fragmentation, chunking:
    -   Segmentation is used for categorizing data based on characteristics
    -   Fragmentation is used for breaking down complex data into smaller, more manageable pieces
    -   Chunking is used for organizing data into logical sections
-   batch endpoint
    -   pass in a list of operations to perform
    -   return one response object with all results
-   vs chain endpoint
    -   pass in a list of operations to perform
    -   returns a single response object

## Endpoints

-   [ ] /segment
-   [ ] /fragment
-   [ ] /chunk

-   [ ] /batch
-   [ ] /chain

---

# Model refactoring

-   [x] move all models to app/models/
-   [ ] add **init** methods to all models
-   [ ] add **post_init** methods to all models

# Proposed New Flow
## Request Models

```python
@dataclass
class TransformationRequest:
    """Base request model for all text transformations"""
    content: Union[str, List[str]]
    operation: str  # 'expand', 'compress', 'rephrase'
    params: Dict[str, Any]
    context: Optional[Context] = None
    
    def __post_init__(self):
        self.is_fragments = isinstance(self.content, list)
        self.validate()
    
    def validate(self) -> None:
        """Validate request parameters"""
        if error := RequestValidator.validate_request(self.content, self.params):
            raise ValidationError(error.code, error.message)
```

## Operation Models

```python
@dataclass
class TextOperation:
    """Base class for text operations"""
    request: TransformationRequest
    warnings: List[Dict[str, str]] = field(default_factory=list)
    
    @abstractmethod
    def execute(self) -> TransformationResult:
        """Execute the text operation"""
        pass

@dataclass
class ExpansionOperation(TextOperation):
    """Handles text expansion logic"""
    def execute(self) -> TransformationResult:
        system_prompt = self.get_system_prompt()
        user_message = self.get_user_message()
        response = get_ai_completion(system_prompt, user_message)
        return self.parse_ai_response(response)

@dataclass
class CompressionOperation(TextOperation):
    """Handles text compression logic"""
    def execute(self) -> TransformationResult:
        # Similar to ExpansionOperation
        pass

@dataclass 
class RephraseOperation(TextOperation):
    """Handles text rephrasing logic"""
    def execute(self) -> TransformationResult:
        # Similar pattern
        pass
```

### Response Models

```python
@dataclass
class TransformationResult:
    """Result of a text transformation operation"""
    fragments: List[Fragment]
    metadata: Metadata
    validation: ValidationResult
    warnings: List[Dict[str, str]] = field(default_factory=list)
    
    def to_response(self) -> TransformationResponse:
        """Convert to API response format"""
        return TransformationResponse(
            fragments=self.fragments,
            metadata={
                **self.metadata.to_dict(),
                'validation': self.validation.to_dict(),
                'warnings': self.warnings
            },
            type='fragments' if len(self.fragments) > 1 else 'cohesive'
        )
```

## Controller Refactor Example

```python
@expand_bp.route('/', methods=['POST'])
@require_api_key
def expand_text():
    try:
        # Create request model
        request = TransformationRequest(
            content=g.get_param('content', required=True),
            operation='expand',
            params=g.params
        )
        
        # Execute operation
        operation = ExpansionOperation(request)
        result = operation.execute()
        
        # Convert to response
        response = result.to_response()
        return jsonify(response.to_dict()), 200
        
    except ValidationError as e:
        return jsonify({
            'error': {
                'code': e.code,
                'message': e.message,
                'status': 400
            }
        }), 400
```


Key Benefits
Better Separation of Concerns
Clear model boundaries
Validation logic in models
Operation-specific logic isolated
Type Safety
Dataclass validation
Clear interfaces between components
Better error handling
Code Reuse
Common validation logic
Shared response formatting
Consistent error handling

## 3. API Response Models

-   Create dedicated response models for each endpoint (`expand`, `rephrase`, etc.)
-   Move response formatting logic from controllers to response models
-   Add response serialization validation
-   Reference:

```82:89:app/controllers/expand.py
        # Format response with collected warnings
        formatted_response = ResponseFormatter.format_response(
            ai_response=result,
            request_params=params,
            original_content=content,
            operation='expand',  # Specify operation type
            validation_warnings=transform.warnings
        )
```

## 4. Model Dependencies

-   Review and possibly refactor circular dependencies between models
-   Create proper model interfaces/protocols
-   Add factory methods for complex model creation
-   Reference:

```1:15:app/models/__init__.py
from .base import DescriptionMixin
from .content import (
    Context, ContentValidation, Summary,
    ContentType, Topics, ContentMetrics,
    TransformedContent
)
from .validation import ValidationResult, ValidationError
from .metadata import Metadata
from .transformation import (
    Version, Length, Fragment,
    TransformationResult
)
from .taxonomy import Section, Taxonomy
from .responses import TransformationResponse
    # Base
```

## 5. Configuration Integration

-   Move validation constants from `ContentValidation` to configuration
-   Create model-specific configuration classes
-   Add environment-based model behavior
-   Reference:

```24:49:app/models/content.py
@dataclass
class ContentValidation(DescriptionMixin):
    """
    Validation rules for content-related attributes.
    Single source of truth for valid values across the application.
    """
    VALID_DOMAINS: List[str] = field(default_factory=lambda: [
        "technical", "academic", "marketing", "legal",
        "creative", "business", "educational"
    ])

    VALID_TONES: List[str] = field(default_factory=lambda: [
        "technical", "conversational", "academic",
        "informal", "friendly", "strict", "professional",
        "formal", "casual", "authoritative"
    ])

    VALID_STYLES: List[str] = field(default_factory=lambda: [
        "professional", "casual", "technical", "formal",
        "elaborate", "explain", "example", "detail"
    ])

    VALID_ASPECTS: List[str] = field(default_factory=lambda: [
        "context", "examples", "implications",
        "technical_details", "counterarguments"
    ])
```

## 6. Controller Integration

-   Update controllers to use new model structure
-   Add proper error handling for model validation
-   Implement model-based response formatting
-   Reference:

```41:57:app/controllers/rephrase.py
        # Create transformation request
        transform = TransformationRequest(
            content=content,
            params=params,
            warnings=warnings,
            operation='rephrase'  # New operation type
        )

        # Get prompts
        system_prompt = transform.get_system_prompt()
        user_message = transform.get_user_message()

        # Get AI completion
        response = get_ai_completion(
            system_prompt=system_prompt,
            user_message=user_message
        )
```

## 7. Testing & Documentation

-   Add property-based tests for models
-   Add serialization/deserialization tests
-   Update API documentation to reflect model changes
-   Add model usage examples

## 8. Cleanup

-   Remove deprecated code in `utils/text_transform.py`
-   Consolidate duplicate validation logic
-   Remove unused model fields
-   Add proper deprecation warnings

## 9. New Features

-   Add versioning to models
-   Add model migration utilities
-   Add model validation events/hooks
-   Add model state tracking

## 10. Performance

-   Add lazy loading for heavy models
-   Add caching for validation results
-   Optimize model serialization
-   Add bulk operation support

`__post_init__` methods in Python dataclasses are special methods that run automatically after the regular `__init__` initialization. They're useful for:

1. Validation of instance attributes
2. Derived/computed fields
3. Complex initialization logic
4. Cross-field validation

Here are examples from your codebase:

1. Topics validation:

```180:182:app/models/content.py
    def __post_init__(self):
        if len(self.related) > 6:
            raise ValueError("Maximum 6 related topics allowed")
```

Checks maximum number of related topics.

2. ContentType validation:

```159:165:app/models/content.py
    def __post_init__(self):
        if self.primary not in self.VALID_TYPES:
            raise ValueError(f"Invalid primary type. Must be one of: {
                             list(self.VALID_TYPES.keys())}")
        if self.subtype not in self.VALID_TYPES[self.primary]:
            raise ValueError(f"Invalid subtype for {self.primary}. Must be one of: {
                             self.VALID_TYPES[self.primary]}")
```

Validates primary type and subtype against allowed values.

3. Context validation:

```80:87:app/models/content.py
    def __post_init__(self):
        if self.domain not in ContentValidation.VALID_DOMAINS:
            raise ValueError(f"Invalid domain. Must be one of: {
                             ContentValidation.VALID_DOMAINS}")

        if self.tone not in ContentValidation.VALID_TONES:
            raise ValueError(f"Invalid tone. Must be one of: {
                             ContentValidation.VALID_TONES}")
```

Validates domain and tone against ContentValidation rules.

4. Metadata initialization:

```23:25:app/models/metadata.py
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}
```

Ensures additional_info is never None.

Key benefits of using `__post_init__`:

1. Runs after all fields are set
2. Can access all instance attributes
3. Can modify instance state
4. Better separation of concerns
5. Cleaner validation logic

Example of a good `__post_init__` pattern:

```python
@dataclass
class TransformationConfig(DescriptionMixin):
    """Configuration for text transformation operations"""
    target_percentage: int
    max_tokens: int
    min_tokens: int = 100

    def __post_init__(self):
        # Validate ranges
        if not (0 < self.target_percentage <= 200):
            raise ValueError("Target percentage must be between 0 and 200")

        # Ensure consistent state
        if self.min_tokens > self.max_tokens:
            self.min_tokens = self.max_tokens

        # Compute derived values
        self.target_tokens = int(self.max_tokens * self.target_percentage / 100)
```

Best practices:

1. Keep validation logic in `__post_init__`
2. Use for cross-field validation
3. Initialize computed fields
4. Handle defaults properly
5. Raise clear validation errors
