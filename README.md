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
    "chunk_id": "string",
    "style": "key_points",  // One of: key_points, abstract, headline, tldr
    "target_length": 200,   // Desired length in characters
    "preserve_keywords": [   // Optional
        "string"
    ],
    "focus": {             // Optional
        "aspect": "argument",  // One of: argument, narrative, technical, action
        "perspective": "neutral" // One of: critical, neutral, supportive
    }
}

```

**Response:** `200 OK`

```json
{
    "chunk_id": "c-def456",
    "content": "string",
    "metadata": {
        "original_length": 1000,
        "summary_length": 200,
        "preservation_rate": 0.2
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

### Expand Chunk

Creates a more detailed version of a text chunk.

**Endpoint:** `POST /expand/chunk`

**Request Body:**

```json
{
    "chunk_id": "string",
    "style": "elaborate", // One of: elaborate, explain, example, detail
    "target_length": 1000,
    "aspects": [         // Optional
        "context",
        "implications",
        "examples",
        "technical_details",
        "counterarguments"
    ],
    "tone": "academic"   // One of: academic, conversational, technical
}

```

**Response:** `200 OK`

```json
{
    "chunk_id": "c-ghi789",
    "content": "string",
    "metadata": {
        "original_length": 500,
        "expanded_length": 1000,
        "expansion_rate": 2.0
    }
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