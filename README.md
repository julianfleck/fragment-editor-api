# Text Transformation API

A semantic text transformation API that helps developers manipulate text while preserving meaning and context. Unlike working directly with language models, this API handles prompt engineering, validation, and error handling, allowing developers to focus on their application logic. Whether you're building a content management system, text editor, or documentation tool, you can rely on standardized endpoints for intelligent text operations.

## Overview

The API provides a suite of text transformation operations that can be chained together for complex content processing. For example, you might fragment a long article into semantic chunks, expand each chunk with more detail, and then join them back together into a cohesive, longer text. Each operation preserves meaning and context while optimizing for the specific transformation needed.

## Key Concepts

### Text Processing Modes

The API handles text in two modes:

**Cohesive Text** (`/text/*`)
- Single, continuous text treated as one unit
- Maintains overall flow and context
- Preserves cross-sentence relationships
- Best for: Articles, paragraphs, descriptions
- Example: Blog posts, product descriptions, news articles

**Text Fragments** (`/fragments/*`)
- Batch processing of multiple text segments
- Each fragment processed independently
- Maintains individual context per fragment
- Best for: Parallel processing of related content
- Example: List items, sections, chapter summaries

Common workflows:
```
/text/fragment → /fragments/expand → /fragments/join    // Split, expand each part, recombine
/text/compress → /text/fragment → /fragments/expand     // Compress, split, then expand parts
/fragments/compress → /fragments/join → /text/expand    // Compress parts, join, expand whole
```

### Operations

1. **Text Length Transformation**
   - Semantic compression (20% - 90%)
   - Intelligent expansion (110% - 300%)
   - Multi-version generation
   - Staggered length variations

2. **Style Transformation**
   - Writing style adaptation
   - Tone adjustment
   - Aspect emphasis
   - Context preservation

3. **Fragment Operations**
   - Semantic segmentation (/text/fragment)
   - Context-aware joining (/fragments/join)
   - Batch processing (/fragments/*)
   - Parallel transformations

### Parameters

### Valid Parameters

The API accepts the following parameters across all endpoints:
- `content`: Text content to transform (required)
- `style`: Writing style control (`professional`, `technical`, `formal`, `casual`, `elaborate`, `explain`, `example`, `detail`)
- `tone`: Tone adjustment (`technical`, `conversational`, `academic`, `informal`, `friendly`, `strict`)
- `aspects`: Focus aspects for transformation (array of aspects)
- `versions`: Number of variations to generate (1-5)

Additional parameters for expand/compress operations:
- `target_percentage`: Target length as percentage of original
- `target_percentages`: Multiple target lengths
- `start_percentage`: Starting percentage for staggered operations
- `steps_percentage`: Step size for staggered operations

Any parameters not in this list will trigger a warning but won't prevent the operation.

#### Style Control

Style parameters can be used with any transformation operation to control the output:

**Writing Style** (`style`)
```json
{
    "style": "professional",  // Default
    "content": "Your text here"
}
```
- `professional`: Clear, business-appropriate language
- `technical`: Precise, terminology-focused
- `formal`: Academic, scholarly tone
- `casual`: Relaxed, approachable
- `elaborate`: Detailed and comprehensive
- `explain`: Focus on explanation and clarity
- `example`: Illustration through examples
- `detail`: Rich in specific details

**Tone** (`tone`)
```json
{
    "tone": "technical",  // Optional
    "content": "Your text here"
}
```
- `technical`: Precise and specialized
- `conversational`: Natural and flowing
- `academic`: Scholarly and researched
- `informal`: Casual and relaxed
- `friendly`: Warm and approachable
- `strict`: Direct and authoritative

**Focus Aspects** (`aspects`)
```json
{
    "aspects": ["context", "technical_details"],
    "content": "Your text here"
}
```
- `context`: Provide background information
- `examples`: Add illustrative instances
- `implications`: Explore consequences and effects
- `technical_details`: Include technical specifics
- `counterarguments`: Present opposing viewpoints

#### Length Control

**Fixed Length**
```json
{
    "target_percentage": 150,  // 150% of original
    "versions": 2  // Optional: Generate multiple versions (1-5)
}
```

**Multiple Targets**
```json
{
    "target_percentages": [75, 50, 25],  // Generate multiple lengths
    "versions": 1  // Optional: Versions per target
}
```

**Staggered Length**
```json
{
    "start_percentage": 80,
    "target_percentage": 30,
    "steps_percentage": 10  // Generate: 80%, 70%, 60%, 50%, 40%, 30%
}
```

# Endpoints

## Text Operations

### POST /text/compress
Compress cohesive text while preserving key information.

**Request:**
```json
{
    "content": "Your long text here",
    "target_percentage": 50,
    "style": "professional",
    "tone": "formal"
}
```

**Response:** `200 OK`
```json
{
    "type": "cohesive",
    "lengths": [
        {
            "target_percentage": 50,
            "target_tokens": 100,
            "versions": [
                {
                    "text": "Compressed version of your text",
                    "final_tokens": 98,
                    "final_percentage": 49.5
                }
            ]
        }
    ],
    "metadata": {
        "mode": "fixed",
        "operation": "compress",
        "original_tokens": 200,
        "versions_per_length": 1,
        "min_percentage": 20,
        "max_percentage": 90
    }
}
```

### POST /text/fragment
Split cohesive text into semantic chunks.

**Request:**
```json
{
    "content": "Your long text here",
    "min_length": 100,  // Minimum tokens per fragment
    "max_length": 300   // Maximum tokens per fragment
}
```

**Response:** `200 OK`
```json
{
    "type": "fragments",
    "fragments": [
        {
            "text": "First semantic chunk",
            "tokens": 150
        },
        {
            "text": "Second semantic chunk",
            "tokens": 200
        }
    ],
    "metadata": {
        "original_tokens": 350,
        "fragment_count": 2
    }
}
```

## Fragment Operations

### POST /fragments/expand
Expand multiple text fragments independently.

**Request:**
```json
{
    "content": [
        "First fragment",
        "Second fragment"
    ],
    "target_percentage": 150,
    "style": "creative"
}
```

**Response:** `200 OK`
```json
{
    "type": "fragments",
    "fragments": [
        {
            "lengths": [
                {
                    "target_percentage": 150,
                    "target_tokens": 15,
                    "versions": [
                        {
                            "text": "Expanded first fragment",
                            "final_tokens": 15,
                            "final_percentage": 150.0
                        }
                    ]
                }
            ]
        },
        {
            "lengths": [
                {
                    "target_percentage": 150,
                    "target_tokens": 15,
                    "versions": [
                        {
                            "text": "Expanded second fragment",
                            "final_tokens": 15,
                            "final_percentage": 150.0
                        }
                    ]
                }
            ]
        }
    ],
    "metadata": {
        "mode": "fragments",
        "operation": "expand",
        "original_tokens": [10, 10],
        "versions_per_length": 1,
        "min_percentage": 110,
        "max_percentage": 300
    }
}
```

### POST /fragments/join
Join multiple fragments into cohesive text while maintaining context and flow.

**Request:**
```json
{
    "content": [
        "First semantic chunk about AI",
        "Second chunk discussing applications",
        "Third chunk exploring implications"
    ],
    "style": "academic",
    "preserve_structure": true  // Optional: maintain clear section breaks
}
```

**Response:** `200 OK`
```json
{
    "type": "cohesive",
    "text": "A comprehensive analysis of AI reveals several key aspects. The technology finds applications across various sectors, from healthcare to finance. These developments carry significant implications for society and future technological progress.",
    "metadata": {
        "operation": "join",
        "original_fragments": 3,
        "original_tokens": [8, 7, 9],
        "final_tokens": 28
    }
}
```

### POST /compress
Simplified compression endpoint that automatically handles both cohesive text and fragments.

**Request (Cohesive Text):**
```json
{
    "content": "Your long text here",
    "target_percentage": 50,
    "style": "professional"
}
```

**Request (Multiple Fragments):**
```json
{
    "content": [
        "First piece of text",
        "Second piece of text"
    ],
    "target_percentage": 50,
    "style": "professional"
}
```

**Response:** `200 OK`
```json
{
    "type": "cohesive",  // or "fragments"
    "lengths": [
        {
            "target_percentage": 50,
            "target_tokens": 100,
            "versions": [
                {
                    "text": "Compressed version of your text",
                    "final_tokens": 98,
                    "final_percentage": 49.5
                }
            ]
        }
    ],
    "metadata": {
        "mode": "fixed",
        "operation": "compress",
        "original_tokens": 200,
        "versions_per_length": 1,
        "min_percentage": 20,
        "max_percentage": 90
    }
}
```

### POST /expand
Simplified expansion endpoint that automatically handles both cohesive text and fragments.

**Request (Cohesive Text):**
```json
{
    "content": "Short text to expand",
    "target_percentage": 150,
    "style": "creative",
    "aspects": ["visual_details", "examples"]
}
```

**Request (Multiple Fragments):**
```json
{
    "content": [
        "First short text",
        "Second short text"
    ],
    "target_percentage": 150,
    "style": "creative"
}
```

**Response:** `200 OK`
```json
{
    "type": "cohesive",  // or "fragments"
    "lengths": [
        {
            "target_percentage": 150,
            "target_tokens": 150,
            "versions": [
                {
                    "text": "Expanded version with more detail and examples...",
                    "final_tokens": 152,
                    "final_percentage": 152.0
                }
            ]
        }
    ],
    "metadata": {
        "mode": "fixed",
        "operation": "expand",
        "original_tokens": 100,
        "versions_per_length": 1,
        "min_percentage": 110,
        "max_percentage": 300
    }
}
```

Note: These endpoints automatically detect the input type and handle both cohesive text and fragments. For more control over the processing mode, use the specific `/text/*` or `/fragments/*` endpoints.

## Error Handling and Validation

### Parameter Validation

The API validates all request parameters and provides structured warnings for unsupported parameters while still processing valid ones:

```json
{
    "content": "Your text here",
    "target_percentage": 150,
    "style": "professional",
    "unsupported_param": "test"  // This will trigger a warning
}
```

**Response with Warning:**
```json
{
    "type": "cohesive",
    "lengths": [
        // ... normal response content ...
    ],
    "metadata": {
        "mode": "fixed",
        "operation": "expand",
        "warnings": [
            {
                "field": "unsupported_param",
                "code": "validation_warning",
                "message": "Unsupported parameter(s): unsupported_param"
            }
        ]
    }
}
```

### Valid Parameters

The API accepts the following parameters:
- `content`: Text content to transform (required)
- `target_percentage`: Target length as percentage of original
- `target_percentages`: Multiple target lengths
- `start_percentage`: Starting percentage for staggered operations
- `steps_percentage`: Step size for staggered operations
- `versions`: Number of variations to generate
- `style`: Writing style control
- `tone`: Tone adjustment
- `aspects`: Focus aspects for transformation
- `fragment_style`: Style for fragment operations

Any parameters not in this list will trigger a warning but won't prevent the operation.

### Response Validation

Since the API relies on AI models for text transformation, the quality and accuracy of responses can vary. To help developers handle this uncertainty, every response includes detailed validation information:

```json
{
    "metadata": {
        "validation": {
            "fragments": {
                "expected": 2,
                "received": 2,
                "passed": true
            },
            "lengths": {
                "expected": [140, 160, 180, 200],
                "passed": true,
                "tolerance": 0.2
            }
        },
        "warnings": [
            {
                "key": "1.0.1", // Fragment.Length.Version
                "code": "target_deviation",
                "message": "Fragment 2, length 1, version 1: Target was 140%, but achieved 100.0%"
            }
        ]
    }
}
```

The validation structure helps you:
1. Verify that all content was processed
2. Check if length targets were met
3. Identify specific problematic generations
4. Make informed decisions about retrying or accepting suboptimal results

#### Validation Components

**Fragment Processing**
- Tracks if all input fragments were successfully handled
- Useful for batch operations to ensure completeness
- `passed` indicates if the entire batch succeeded

**Length Validation**
- Verifies if target lengths were achieved within tolerance
- Particularly important for staggered operations with multiple targets
- Default tolerance of 20% balances precision with model capabilities

**Warning System**
- Structured warnings with:
  - `field`: Parameter identifier for validation warnings (param.[name])
  - `key`: Location identifier for processing warnings (fragment.length.version)
  - `code`: Type of warning for programmatic handling
  - `message`: Human-readable description
  
**Common Warning Codes**
- `validation_warning`: Parameter or input validation issues
- `fragment_missing`: Missing or invalid fragment
- `length_missing`: Missing length configuration
- `version_missing`: Missing version in length
- `target_deviation`: Generated length outside tolerance
- `fragment_error`: Error processing fragment
- `length_error`: Error processing length
- `version_error`: Error processing version

#### Common Scenarios

1. **Length Deviation**
   ```python
   # Check if any generations were significantly off-target
   if response.metadata.warnings:
       problematic = [w for w in response.metadata.warnings if "Target was" in w.message]
       if problematic:
           # Consider regenerating or using alternate versions
   ```

2. **Batch Processing**
   ```python
   # Verify all fragments were processed
   if response.metadata.validation.fragments.passed:
       # Safe to proceed with next operation
   else:
       # Handle missing fragments
   ```

3. **Staggered Operations**
   ```python
   # Check if all length variations were generated
   if response.metadata.validation.lengths.passed:
       # All target percentages achieved
   else:
       # Some length targets missing
   ```


### Error Responses

The API uses standard HTTP status codes and returns detailed error messages:

#### Validation Errors (400)
```json
{
    "error": {
        "code": "validation_error",
        "message": "Target percentage must be between 20 and 90 for compression",
        "details": {
            "param": "target_percentage",
            "received": 15,
            "allowed_range": [20, 90]
        }
    }
}
```

#### Content Errors (422)
```json
{
    "error": {
        "code": "content_error",
        "message": "Content too short for fragmentation",
        "details": {
            "min_required_tokens": 100,
            "received_tokens": 45
        }
    }
}
```

#### Rate Limit Errors (429)
```json
{
    "error": {
        "code": "rate_limit_exceeded",
        "message": "Too many requests",
        "details": {
            "retry_after": 60,
            "limit": "60 requests per hour"
        }
    }
}
```

### Common Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| `validation_error` | Invalid parameters | Out-of-range values, invalid combinations |
| `content_error` | Content issues | Text too short/long, invalid format |
| `operation_error` | Operation failed | Incompatible operation for content type |
| `format_error` | Response formatting failed | Internal parsing issues |
| `rate_limit_exceeded` | Too many requests | Exceeded API quota |

## Best Practices

### Content Length
- Keep individual texts under 2000 tokens
- Use fragmentation for longer content
- Consider context overlap for better coherence

### Operation Chaining
```python
# Example: Expand article while maintaining readability
original = "Long article text..."

# 1. Fragment into semantic chunks
fragments = api.text.fragment(original, max_length=300)

# 2. Expand each fragment independently
expanded = api.fragments.expand(fragments, target_percentage=150)

# 3. Join with proper transitions
final = api.fragments.join(expanded, style="professional")
```

### Parameter Selection
- Start with default style parameters
- Use aspects for fine-tuning focus
- Test multiple target percentages for optimal length

## Rate Limits

| Tier | Requests/Hour | Max Tokens/Request | Versions/Request |
|------|---------------|-------------------|------------------|
| Free | 60 | 2000 | 2 |
| Pro | 1000 | 5000 | 5 |
| Enterprise | Custom | Custom | Custom |

## Versioning

This API follows semantic versioning (MAJOR.MINOR.PATCH):
- Current version: v1
- Breaking changes trigger MAJOR version bump
- New features increment MINOR version
- Bug fixes increment PATCH version

All endpoints are versioned in the URL:
```
https://api.textransform.dev/v1/text/compress
```

Changes and deprecations are announced through:
- GitHub releases
- API response headers
- Email notifications (for registered users)

