"""
Expansion prompts defining strategies and templates for text expansion operations.
System prompts focus on expansion strategies while user messages handle specific requirements.
"""

from typing import List, Tuple, Dict, Any
import json


# Core expansion strategies for different operation modes
EXPAND_BASE = """Generate expanded versions of text following these rules and respond in JSON format:

1. Expansion strategy:
   - Add relevant details and examples
   - Elaborate on key concepts
   - Use specific examples
   - Add supporting evidence
   - Include relevant context
   - Maintain professional language
   - Never simply repeat the original text
   - Never contradict original meaning
   - Never add incorrect information
   - Keep technical terms unchanged
   - Match original tone and formality level
   - Never append "version X" or generic phrases
   - Each version must be unique and substantive
   - Stay within exact token count targets

2. Examples of good expansion:
   Original: "The API offers REST endpoints."
   Version 1: "The API provides a comprehensive set of REST endpoints that enable seamless integration with third-party systems."
   Version 2: "Developers can leverage the API's collection of REST endpoints, which support various authentication methods and data formats."

   Original: "testing the text expansion api"
   Version 1: "evaluating the functionality and performance of the text expansion api system"
   Version 2: "conducting tests to verify the text expansion api's capabilities and response times"
   Version 3: "running validation checks on the text expansion api's core features"

3. Length and version requirements:
   - Generate versions for EACH target length
   - Make versions at same length unique
   - Match target token counts exactly
   - Vary the added details
   - Use different examples
   - Maintain consistent quality

4. Response format (JSON):
   {
     "lengths": [
       {
         "target_percentage": <percentage>,
         "target_tokens": <token_count>,
         "versions": [
           {"text": "unique version at this length"},
           {"text": "another version at same length"}
         ]
       }
       // Additional lengths as requested
     ]
   }

5. If expansion impossible:
   {"error": "specific reason"}"""

EXPAND_STAGGERED = """Generate progressively expanded versions of text and respond in JSON format:

1. Expansion strategy:
   - Start with essential elaborations
   - Add more detail with each length
   - Build upon previous lengths
   - Maintain narrative flow
   - Keep core message consistent
   - Never append "version X" or generic phrases
   - Each version must expand with relevant content
   - Stay within exact token count targets

2. Progressive expansion technique:
   - Each length MUST be longer than previous
   - For each length:
     * Match target tokens exactly
     * Make versions unique
     * Build on previous content:
       - Start with core elaborations
       - Add supporting details
       - Include examples and context
       - Expand depth and breadth
   - Never simply repeat previous versions

3. Progressive expansion examples:
   Original: "The API offers REST endpoints."
   120%: "The API provides REST endpoints for integration"
   140%: "The API provides REST endpoints for integration with authentication support"
   160%: "The API provides REST endpoints for integration with authentication support and data validation"

   Original: "testing the text expansion api"
   120%: "validating the text expansion api's core functions"
   140%: "validating the text expansion api's core functions and response times"
   160%: "validating the text expansion api's core functions, response times, and error handling"

4. Length and version requirements:
   - Generate versions for EACH target length
   - Make versions at same length unique
   - Match target token counts exactly
   - Vary the added details
   - Use different examples
   - Maintain consistent quality

5. Response format (JSON):
   {
     "lengths": [
       {
         "target_percentage": <percentage>,
         "target_tokens": <token_count>,
         "versions": [
           {"text": "unique version at this length"},
           {"text": "another version at same length"}
         ]
       }
       // Additional lengths with increasing targets
     ]
   }

6. If expansion impossible:
   {"error": "specific reason"}"""

EXPAND_FRAGMENT = """Generate expanded versions of multiple text fragments and respond in JSON format:

1. Expansion strategy:
   - Treat each fragment independently
   - Maintain fragment boundaries
   - Keep fragments self-contained
   - Never merge fragment content
   - Never simply repeat original text
   - Keep technical terms unchanged
   - Match original tone and formality level

2. Examples of good fragment expansion:
   Original Fragment 1: "The API uses OAuth."
   Version 1: "The API implements OAuth authentication to ensure secure access control and user authorization."
   Version 2: "Security is handled through the API's OAuth implementation, providing robust token-based authentication."

   Original Fragment 2: "Data is returned in JSON."
   Version 1: "All API responses are formatted in JSON, enabling straightforward parsing and integration."
   Version 2: "The system returns data in JSON format, which supports nested objects and arrays."

3. Per-fragment requirements:
   - Generate versions for EACH target length
   - For each length:
     * Match target tokens exactly
     * Make versions unique
     * Keep expansions self-contained
     * Maintain fragment focus
     * Add relevant details
   - Maintain professional language

4. Response format (JSON):
   {
     "fragments": [
       {
         "lengths": [
           {
             "target_percentage": <percentage>,
             "target_tokens": <token_count>,
             "versions": [
               {"text": "unique version at this length"},
               {"text": "another version at same length"}
             ]
           }
           // Additional lengths as requested
         ]
       }
       // One entry per input fragment
     ]
   }

5. If expansion impossible:
   {"error": "specific reason"}"""

# User message templates with explicit requirements
USER_MESSAGES = {
    'base': """Expand this text to create {versions_per_length} version(s) at each target length.
Style: {style}

Original text ({original_tokens} tokens):
{text}

Target lengths and versions:
{version_details}

IMPORTANT:
- Match token counts exactly
- Make versions at same length unique
- Preserve original meaning{tone_str}{aspects_str}""",

    'staggered': """Create {versions_per_length} version(s) at each progressive length.
Style: {style}

Original text ({original_tokens} tokens):
{text}

Progressive lengths and versions:
{version_details}

IMPORTANT:
- Match token counts exactly
- Each length must build upon previous ones
- Make versions at same length unique
- Preserve original meaning{tone_str}{aspects_str}""",

    'fragment': """Expand these {fragment_count} text fragments.
Style: {style}

Original fragments:
{text}

Target lengths and versions per fragment:
{version_details}

IMPORTANT:
- Match token counts exactly
- Make versions at same length unique
- Keep fragments independent
- Preserve original meaning{tone_str}{aspects_str}"""
}

# Helper functions for formatting version details


def format_version_details(
    original_tokens: int | List[int],
    target_lengths: List[int],
    versions_per_length: int,
    mode: str = 'base'
) -> str:
    """Format example structure showing required lengths and versions"""
    def create_length_structure(tokens: int) -> List[Dict[str, Any]]:
        return [
            {
                "target_percentage": length,
                "target_tokens": round(tokens * length / 100),
                "versions": [
                    {"text": f"expanded version {
                        v+1} ({length}% of original length, approx. {round(tokens * length / 100)} tokens)"}
                    for v in range(versions_per_length)
                ]
            }
            for length in target_lengths
        ]

    if mode == 'fragment':
        structure = {
            "fragments": [
                {
                    "lengths": create_length_structure(tokens)
                }
                for i, tokens in enumerate(original_tokens)
            ]
        }
    else:
        structure = {
            "lengths": create_length_structure(original_tokens)
        }

    return json.dumps(structure, indent=2)
