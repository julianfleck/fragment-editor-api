"""
Expansion prompts for different modes:
- Single: One expanded version
- Fixed: Multiple versions at same percentage
- Fragment: Multiple fragments with independent expansion
"""

# System prompts with detailed rules
EXPAND_SINGLE = """Generate a JSON response with a single expanded version of text:

1. Response format MUST be:
   {
     "versions": [
       {"text": "expanded version"}
     ]
   }

2. Expansion requirements:
   - Add relevant details and examples
   - Preserve original meaning and tone
   - Maintain professional language
   - Never simply repeat the original text
   - Never change the core message

3. If expansion impossible:
   {"error": "specific reason"}
"""

EXPAND_FIXED = """Generate a JSON response with multiple expanded versions of text:

1. Response format MUST be:
   {
     "versions": [
       {"text": "version 1"},
       {"text": "version 2"}
       // EXACTLY the requested number of versions
     ]
   }

2. Expansion requirements:
   - Match target percentage exactly
   - Add relevant details and examples
   - Preserve original meaning and tone
   - Maintain professional language
   - Each version should be unique
   - Each version MUST be longer than the previous
   - Never simply repeat the original text

3. If expansion impossible:
   {"error": "specific reason"}
"""

EXPAND_FRAGMENT = """Generate a JSON response with multiple expanded versions of text fragments:

1. Response format MUST be:
   {
     "fragments": [
       {
         "versions": [
           {"text": "fragment 1 version 1"},
           {"text": "fragment 1 version 2"}
         ]
       }
     ]
   }

2. Expansion requirements for EACH fragment:
   - Generate EXACTLY the requested number of versions
   - Each version MUST match its target percentage
   - Keep fragments independent and self-contained
   - Preserve original meaning and context
   - Add relevant details and examples
   - Maintain professional language
   - Never simply repeat the original text

3. If expansion impossible:
   {"error": "specific reason"}
"""

# User messages with examples
USER_MESSAGES = {
    'single': """Expand this text from {tokens} to {target_tokens} tokens ({target_percentage}% of original).
Style: {style}

{text}

Response format:
{{
  "versions": [
    {{"text": "expanded version"}}  // target: {target_tokens} tokens ({target_percentage}%)
  ]
}}

IMPORTANT:
- Target exactly {target_tokens} tokens
- Preserve original meaning
- Add relevant details{tone_str}{aspects_str}""",

    'fixed': """Generate {count} unique expanded versions.
Style: {style}

Original text ({tokens} tokens):
{text}

Target lengths:
{targets_formatted}

Response format:
{{
  "versions": [
    {version_format}
  ]
}}

IMPORTANT:
- Match token counts exactly
- Each version MUST be longer than the previous
- Make each version unique
- Preserve original meaning{tone_str}{aspects_str}""",

    'fragment': """Expand these fragments independently.
Style: {style}

Original fragments:
{text}

Target lengths:
{targets_formatted}

Response format:
{{
  "fragments": [
    {fragment_format}
  ]
}}

IMPORTANT:
- Target exact token counts shown above for each version
- Keep fragments independent
- Preserve original meaning
- Add relevant details{tone_str}{aspects_str}"""
}
