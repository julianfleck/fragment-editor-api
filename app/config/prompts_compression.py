"""
Compression prompts for different modes:
- Single: One compressed version
- Fixed: Multiple versions at same percentage
- Staggered: Multiple versions with decreasing percentages
"""

# System prompts with detailed rules
COMPRESS_SINGLE = """Generate a JSON response with a single compressed version of text:

1. Response format MUST be:
   {
     "versions": [
       {"text": "compressed version"}
     ]
   }

2. Compression requirements:
   - Remove approximately half of the words/tokens
   - Keep core technical terms intact
   - Remove adjectives, adverbs, and non-essential details first
   - Maintain complete sentences and readability
   - Never just reorder or rephrase the original text
   - Never return the original text unchanged

3. If compression impossible:
   {"error": "specific reason"}
"""

COMPRESS_FIXED = """Generate a JSON response with multiple compressed versions of text:

1. Response format MUST be:
   {
     "versions": [
       {"text": "version 1"},
       {"text": "version 2"}
       // EXACTLY the requested number of versions
     ]
   }

2. Compression requirements:
   - Match target percentage exactly
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
   - Each version should be unique
   - Never return the original text unchanged

3. If compression impossible:
   {"error": "specific reason"}
"""

COMPRESS_STAGGERED = """Generate a JSON response with progressively shorter versions of text:

1. Response format MUST be:
   {
     "versions": [
       {"text": "longest version"},
       {"text": "medium version"},
       {"text": "shortest version"}
     ]
   }

2. Compression requirements:
   - Match each target percentage exactly
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
   - Each version MUST be shorter than the previous
   - Never return the original text unchanged

3. If compression impossible:
   {"error": "specific reason"}
"""

# User messages with examples
USER_MESSAGES = {
    'single': """Compress this text from {tokens} to {target_tokens} tokens ({target_percentage}% of original).

{text}

Response format:
{{
  "versions": [
    {{"text": "compressed version"}}  // target: {target_tokens} tokens ({target_percentage}%)
  ]
}}

IMPORTANT:
- Target exactly {target_tokens} tokens
- Keep technical terms intact
- Focus on removing adjectives and non-essential details
- Don't just reorder words""",

    'fixed': """Generate {count} unique compressed versions.

Original text ({tokens} tokens):
{text}

Target lengths:
{targets_formatted}

Response format:
{{
  "versions": [
    // Generate exactly {count} versions with these targets:
    {{"text": "version"}},  // target: {target_tokens} tokens ({target_percentage}%)
    // ... and so on for each target in decreasing length
  ]
}}

IMPORTANT:
- Match token counts exactly
- Each version MUST be shorter than the previous one
- Keep technical terms intact
- Make each version unique""",

    'fragment': """Compress these fragments independently.

Original fragments:
{text}

Target per fragment: {target_tokens} tokens ({target_percentage}% of original)

Response format:
{{
  "versions": [
    {{"text": "compressed fragment 1"}},  // target: {target_tokens} tokens ({target_percentage}%)
    {{"text": "compressed fragment 2"}},  // target: {target_tokens} tokens ({target_percentage}%)
    // ... one version per fragment
  ]
}}

IMPORTANT:
- Target exactly {target_tokens} tokens per fragment
- Keep fragments independent
- Keep technical terms intact
- Make each version unique"""
}

# Fragment-specific prompts
COMPRESS_FRAGMENT = """Generate a JSON response compressing multiple text fragments:

1. Response format MUST be:
   {
     "fragments": [
       {
         "versions": [
           {"text": "fragment 1 version 1"},
           {"text": "fragment 1 version 2"}
           // EXACTLY the requested number of versions
         ]
       },
       // EXACTLY one entry per input fragment
     ]
   }

2. Compression requirements for EACH fragment:
   - Generate EXACTLY the requested number of versions
   - Each version MUST match its target percentage
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
   - Keep each fragment self-contained
   - Each version should be shorter than the previous one
   - Never return the original text unchanged

3. If compression impossible:
   {"error": "specific reason"}"""
