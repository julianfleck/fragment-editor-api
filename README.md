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
- `creative`: More expressive and varied language
- `technical`: Precise, terminology-focused
- `academic`: Formal, scholarly
- `conversational`: Casual, approachable

**Tone** (`tone`)
```json
{
    "tone": "neutral",  // Default
    "content": "Your text here"
}
```
- `neutral`: Balanced and objective
- `formal`: Professional and serious
- `casual`: Relaxed and friendly
- `humorous`: Light and playful
- `authoritative`: Confident and expert

**Focus Aspects** (`aspects`)
```json
{
    "aspects": ["visual_details", "technical_terms"],
    "content": "Your text here"
}
```
- `visual_details`: Enhance descriptive elements
- `technical_terms`: Include domain-specific vocabulary
- `examples`: Add illustrative instances
- `context`: Provide background information
- `implications`: Explore consequences and effects

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

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

### Validation Errors (400)
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

### Content Errors (422)
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

### Rate Limit Errors (429)
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

## Common Error Codes

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