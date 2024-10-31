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

2. Length and version requirements:
   - Generate versions for EACH target length
   - Make versions at same length unique
   - Match target token counts exactly
   - Vary the added details
   - Use different examples
   - Maintain consistent quality

3. Response format (JSON):
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

4. If expansion impossible:
   {"error": "specific reason"}"""

EXPAND_STAGGERED = """Generate progressively expanded versions of text and respond in JSON format:

1. Expansion strategy:
   - Start with essential elaborations
   - Add more detail with each length
   - Build upon previous lengths
   - Maintain narrative flow
   - Keep core message consistent

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

3. Response format (JSON):
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

4. If expansion impossible:
   {"error": "specific reason"}"""

EXPAND_FRAGMENT = """Generate expanded versions of multiple text fragments and respond in JSON format:

1. Expansion strategy:
   - Treat each fragment independently
   - Maintain fragment boundaries
   - Keep fragments self-contained
   - Never merge fragment content
   - Never simply repeat original text

2. Per-fragment requirements:
   - Generate versions for EACH target length
   - For each length:
     * Match target tokens exactly
     * Make versions unique
     * Keep expansions self-contained
     * Maintain fragment focus
     * Add relevant details
   - Maintain professional language

3. Response format (JSON):
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

4. If expansion impossible:
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
                    {"text": f"expanded version {v+1} at {length}%"}
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
