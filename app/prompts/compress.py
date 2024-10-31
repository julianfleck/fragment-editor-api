"""
Compression prompts defining strategies and templates for text compression operations.
System prompts focus on compression strategies while user messages handle specific requirements.
"""

from typing import List, Tuple, Dict, Any
import json

# Core compression strategies for different operation modes
COMPRESS_BASE = """Generate compressed versions of text following these rules and respond in JSON format:

1. Compression strategy:
   - Preserve core meaning and key points
   - Remove redundant information
   - Simplify complex phrases
   - Use concise language
   - Maintain readability
   - Never add new information
   - Never change original meaning
   - Keep essential context

2. Length and version requirements:
   - Generate versions for EACH target length
   - Make versions at same length unique
   - Match target token counts exactly
   - Vary compression approach
   - Maintain quality and clarity

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

4. If compression impossible:
   {"error": "specific reason"}"""

COMPRESS_STAGGERED = """Generate progressively compressed versions of text and respond in JSON format:

1. Compression strategy:
   - Start with light compression
   - Increase compression gradually
   - Maintain core message
   - Preserve essential details
   - Keep narrative coherence

2. Progressive compression technique:
   - Each length MUST be shorter than previous
   - For each length:
     * Match target tokens exactly
     * Make versions unique
     * Progressive information reduction:
       - Remove less important details first
       - Keep core message intact
       - Maintain readability
       - Preserve key context
   - Never simply truncate text

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
       // Additional lengths with decreasing targets
     ]
   }

4. If compression impossible:
   {"error": "specific reason"}"""

COMPRESS_FRAGMENT = """Generate compressed versions of multiple text fragments and respond in JSON format:

1. Compression strategy:
   - Treat each fragment independently
   - Maintain fragment boundaries
   - Keep fragments self-contained
   - Never merge fragment content
   - Preserve essential meaning

2. Per-fragment requirements:
   - Generate versions for EACH target length
   - For each length:
     * Match target tokens exactly
     * Make versions unique
     * Keep core message intact
     * Maintain fragment focus
     * Remove non-essential details
   - Keep language clear and concise

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

4. If compression impossible:
   {"error": "specific reason"}"""

# User message templates with explicit requirements
USER_MESSAGES = {
    'base': """Compress this text to create {versions_per_length} version(s) at each target length.
Style: {style}

Original text ({original_tokens} tokens):
{text}

Target lengths and versions:
{version_details}

IMPORTANT:
- Match token counts exactly
- Make versions at same length unique
- Preserve core meaning{tone_str}{aspects_str}""",

    'staggered': """Create {versions_per_length} version(s) at each progressive compression length.
Style: {style}

Original text ({original_tokens} tokens):
{text}

Progressive lengths and versions:
{version_details}

IMPORTANT:
- Match token counts exactly
- Each length must be more compressed than previous
- Make versions at same length unique
- Preserve core meaning{tone_str}{aspects_str}""",

    'fragment': """Compress these {fragment_count} text fragments.
Style: {style}

Original fragments:
{text}

Target lengths and versions per fragment:
{version_details}

IMPORTANT:
- Match token counts exactly
- Make versions at same length unique
- Keep fragments independent
- Preserve core meaning{tone_str}{aspects_str}"""
}

# Reuse the format_version_details function from expand.py
