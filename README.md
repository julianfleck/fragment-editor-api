## Overview

The Text Transformation API provides REST endpoints for transforming text through various operations including expansion, summarization, and chunking. This API is designed for developers who need to programmatically manipulate and transform text content while maintaining semantic meaning.

## Base URL

```
<https://api.metasphere.xyz/text/v1>
```

## Authentication

All requests must include an API key in the header:

```
Authorization: Bearer your-api-key
```

## Controllers

### Generate Controller

The Generate controller handles the creation of new texts and their automatic chunking.

### Create Text

Creates a new text document and optionally splits it into chunks.

**Endpoint:** `POST /generate/text`

**Request Body:**

```json
{
    "content": "string",
    "chunk_size": 500,  // Optional, number of characters per chunk
    "overlap": 50,      // Optional, number of overlapping characters between chunks
    "metadata": {       // Optional
        "title": "string",
        "author": "string",
        "tags": ["string"]
    }
}

```

**Response:** `200 OK`

```json
{
    "text_id": "t-abc123",
    "chunks": [
        {
            "id": "c-xyz789",
            "content": "string",
            "position": 1
        }
    ],
    "metadata": {
        "chunk_count": 3,
        "total_length": 1500
    }
}

```

### Summarize Controller

Handles text reduction operations with various summarization styles.

### Summarize Chunk

Creates a more concise version of a text chunk.

**Endpoint:** `POST /summarize/chunk`

**Request Body:**

```json
{
    "content": "string",
    "target_length": 200,   // Optional, default: 200 characters
    "aspects": [            // Optional
        "context",
        "implications",
        "examples",
        "technical_details",
        "counterarguments"
    ]
}
```

**Response:** `200 OK`

```json
{
    "content": "string",
    "metadata": {
        "original_length": 1000,
        "summary_length": 200,
        "compression_rate": 0.2,
        "aspects": ["context", "examples"],  // Only included if aspects were specified
        "target_length": 200
    }
}
```

### Summarize Batch

Summarizes multiple chunks in one request.

**Endpoint:** `POST /summarize/batch`

**Request Body:**

```json
{
    "chunk_ids": ["string"],
    "style": "key_points",
    "target_length": 200,
    // ... same optional parameters as single summarize
}

```

**Response:** `200 OK`

```json
{
    "chunks": [
        {
            "id": "string",
            "content": "string",
            "metadata": {
                "original_length": 1000,
                "summary_length": 200
            }
        }
    ]
}

```

### Expand Controller

Handles text expansion operations with various elaboration styles.

### Expand Text

Creates expanded versions of a text or text fragments.

**Endpoint:** `POST /expand`

**Request Body (Single Text):**
```json
{
    "content": "string",
    "style": "elaborate",     // Optional, default: elaborate
    "target_length": 200,     // Optional, default: 200
    "versions": 1,            // Optional, default: 1, max: 5
    "aspects": [              // Optional
        "context",
        "implications",
        "examples",
        "technical_details",
        "counterarguments"
    ],
    "tone": "academic"        // Optional: academic, conversational, technical
}
```

**Request Body (Multiple Fragments):**
```json
{
    "content": ["string", "string"],  // Array of text fragments
    // ... same optional parameters as single text
}
```

**Response (Single Text, versions=1):** `200 OK`
```json
{
    "type": "cohesive",
    "versions": [
        {
            "text": "expanded version"
        }
    ],
    "metadata": {
        "type": "cohesive",
        "original_tokens": 100,
        "target_tokens": 200,
        "versions_requested": 1
    }
}
```

**Response (Single Text, versions>1):** `200 OK`
```json
{
    "type": "cohesive",
    "versions": [
        {
            "text": "expanded version 1"
        },
        {
            "text": "expanded version 2"
        }
    ],
    "metadata": {
        "type": "cohesive",
        "original_tokens": 100,
        "target_tokens": 200,
        "versions_requested": 2
    }
}
```

**Response (Multiple Fragments):** `200 OK`
```json
{
    "type": "fragments",
    "fragments": [
        {
            "id": "f1",
            "original": "original fragment 1",
            "versions": [
                {
                    "text": "expanded version"
                }
            ]
        }
    ],
    "metadata": {
        "type": "fragments",
        "fragment_count": 2,
        "original_tokens": 200,
        "target_tokens": 200,
        "versions_requested": 1
    }
}
```

### Compress Controller

Handles text reduction operations with precise length control.

**Endpoint:** `POST /text/v1/compress`

#### Metadata Fields

The API returns metadata for both cohesive texts and fragments. These help track processing details and validate responses.

### Cohesive Text Metadata
```json
{
    "metadata": {
        "mode": "fixed|staggered",
        "original_text": "string",
        "original_tokens": number,
        "target_percentages": [number],
        "step_size": number,          // Only present in staggered mode
        "versions_requested": number,
        "final_versions": number
    }
}
```

### Fragments Metadata
```json
{
    "metadata": {
        "mode": "fragments",
        "fragment_count": number,
        "original_text": ["string"],
        "original_tokens": [number],
        "target_percentages": [number],
        "step_size": number,          // Only present in staggered mode
        "versions_per_fragment": number,
        "versions_requested": number,
        "final_versions": [number]    // Array of version counts per fragment
    }
}
```

#### Compression Scenarios

1. **Basic Single Compression**
```json
// Request
{
    "content": "The Text Transformation API offers a robust set of REST endpoints that enable developers to programmatically manipulate and transform text content.",
    "target_percentage": 50
}

// Response
{
    "type": "cohesive",
    "versions": [
        {
            "text": "The Text Transformation API provides REST endpoints for programmatic text manipulation.",
            "target_percentage": 50,
            "final_percentage": 49.1
        }
    ]
}
```

2. **Multiple Versions (Same Percentage)**
```json
// Request
{
    "content": "The Text Transformation API offers a robust set of REST endpoints that enable developers to programmatically manipulate and transform text content.",
    "target_percentage": 50,
    "versions": 3
}

// Response
{
    "type": "cohesive",
    "versions": [
        {
            "text": "The Text Transformation API provides REST endpoints for programmatic text manipulation.",
            "target_percentage": 50,
            "final_percentage": 49.1
        },
        {
            "text": "REST API endpoints enable developers to transform and manipulate text.",
            "target_percentage": 50,
            "final_percentage": 51.2
        },
        {
            "text": "API offers REST endpoints for text transformation and manipulation.",
            "target_percentage": 50,
            "final_percentage": 48.7
        }
    ]
}
```

3. **Staggered Compression (With Steps)**
```json
// Request
{
    "content": "The Text Transformation API offers a robust set of REST endpoints that enable developers to programmatically manipulate and transform text content.",
    "target_percentage": 30,
    "steps_percentage": 20
}

// Response
{
    "type": "cohesive",
    "versions": [
        {
            "text": "The Text Transformation API provides REST endpoints for programmatic text manipulation and transformation.",
            "target_percentage": 70,
            "final_percentage": 71.5
        },
        {
            "text": "The API offers REST endpoints for text manipulation.",
            "target_percentage": 50,
            "final_percentage": 48.9
        },
        {
            "text": "API endpoints for text operations.",
            "target_percentage": 30,
            "final_percentage": 31.2
        }
    ]
}
```

4. **Fragment Compression (Fixed)**
```json
// Request
{
    "content": [
        "The Text Transformation API offers a robust set of REST endpoints.",
        "These endpoints enable developers to programmatically manipulate text.",
        "Operations include expansion, summarization, and chunking."
    ],
    "target_percentage": 50,
    "versions": 2
}

// Response
{
    "type": "fragments",
    "fragments": [
        {
            "versions": [
                {
                    "text": "The API offers REST endpoints.",
                    "target_percentage": 50,
                    "final_percentage": 48.5
                },
                {
                    "text": "Text API provides endpoints.",
                    "target_percentage": 50,
                    "final_percentage": 51.2
                }
            ]
        },
        {
            "versions": [
                {
                    "text": "Endpoints enable text manipulation.",
                    "target_percentage": 50,
                    "final_percentage": 49.8
                },
                {
                    "text": "Developers can manipulate text.",
                    "target_percentage": 50,
                    "final_percentage": 51.5
                }
            ]
        },
        {
            "versions": [
                {
                    "text": "Operations: expansion and summarization.",
                    "target_percentage": 50,
                    "final_percentage": 48.9
                },
                {
                    "text": "Features include text operations.",
                    "target_percentage": 50,
                    "final_percentage": 51.1
                }
            ]
        }
    ]
}
```

5. **Fragment Compression (Staggered)**
```json
// Request
{
    "content": [
        "The Text Transformation API offers a robust set of REST endpoints.",
        "These endpoints enable developers to programmatically manipulate text.",
        "Operations include expansion, summarization, and chunking."
    ],
    "start_percentage": 80,
    "target_percentage": 40,
    "steps_percentage": 20
}

// Response
{
    "type": "fragments",
    "fragments": [
        {
            "versions": [
                {
                    "text": "The Text Transformation API offers a set of REST endpoints.",
                    "target_percentage": 80,
                    "final_percentage": 79.2
                },
                {
                    "text": "The Text API offers REST endpoints.",
                    "target_percentage": 60,
                    "final_percentage": 61.5
                },
                {
                    "text": "API provides endpoints.",
                    "target_percentage": 40,
                    "final_percentage": 41.2
                }
            ]
        },
        {
            "versions": [
                {
                    "text": "These endpoints enable developers to manipulate text programmatically.",
                    "target_percentage": 80,
                    "final_percentage": 81.5
                },
                {
                    "text": "Endpoints allow developers to manipulate text.",
                    "target_percentage": 60,
                    "final_percentage": 58.9
                },
                {
                    "text": "Endpoints for text manipulation.",
                    "target_percentage": 40,
                    "final_percentage": 41.5
                }
            ]
        },
        {
            "versions": [
                {
                    "text": "Operations include expansion and summarization operations.",
                    "target_percentage": 80,
                    "final_percentage": 78.9
                },
                {
                    "text": "Operations include expansion, summarization.",
                    "target_percentage": 60,
                    "final_percentage": 61.2
                },
                {
                    "text": "Operations: summarize, expand.",
                    "target_percentage": 40,
                    "final_percentage": 39.8
                }
            ]
        }
    ]
}
```

## Collections

### Texts Collection

Manages full text documents.

### Get Text

Retrieves a complete text document and its associated chunks.

**Endpoint:** `GET /texts/{text_id}`

**Response:** `200 OK`

```json
{
    "text": {
        "id": "string",
        "content": "string",
        "chunk_ids": ["string"],
        "metadata": {
            "created_at": "2024-10-30T12:00:00Z",
            "word_count": 1000,
            "language": "en"
        }
    }
}

```

### Chunks Collection

Manages individual text chunks.

### Get Chunk

Retrieves a specific text chunk and its transformation history.

**Endpoint:** `GET /chunks/{chunk_id}`

**Response:** `200 OK`

```json
{
    "chunk": {
        "id": "string",
        "content": "string",
        "text_id": "string",
        "position": 1,
        "transformations": [
            {
                "type": "summarize",
                "level": 1,
                "parent_id": "string",
                "timestamp": "2024-10-30T12:00:00Z"
            }
        ]
    }
}

```

## Error Responses

The API uses standard HTTP status codes and returns detailed error messages:

| Status Code | Description |
| --- | --- |
| 400 | Bad Request - Invalid parameters or malformed request |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |

**Error Response Format:**

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    }
}

```

## Rate Limiting

- **Standard Tier:**
    - 100 requests per minute per IP
    - 1000 requests per hour per API key
    - Batch operations count as multiple requests based on chunk count
- **Premium Tier:**
    - 500 requests per minute per IP
    - 5000 requests per hour per API key
    - Priority processing for batch operations

## Best Practices

1. **Chunking:**
    - Recommended chunk size: 300-500 characters
    - Use overlap for better context preservation
    - Respect natural text boundaries (paragraphs, sentences)
2. **Summarization:**
    - Start with larger chunks for better context
    - Use appropriate style based on content type
    - Preserve key terms when relevant
3. **Expansion:**
    - Provide clear focus aspects
    - Match tone to target audience
    - Consider using batch operations for related chunks

## Versioning

This documentation describes API v1. The API follows semantic versioning, and breaking changes will be announced at least 6 months in advance.