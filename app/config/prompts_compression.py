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
   - Match target percentage exactly
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
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
    'single': """Compress this text to exactly {target}% of its original length ({tokens} tokens):

{text}

Response format:
{{
  "versions": [
    {{"text": "compressed version"}}  // target: {target}%
  ]
}}

IMPORTANT:
- Keep technical terms intact
- Match target percentage exactly
- Never return the original text unchanged""",

    'fixed': """Generate {count} different {target}% versions of this text ({tokens} tokens):

{text}

Response format:
{{
  "versions": [
    {{"text": "version 1"}},  // target: {target}%
    {{"text": "version 2"}},  // target: {target}%
    // ... exactly {count} versions
  ]
}}

IMPORTANT:
- Keep technical terms intact
- Match target percentage exactly
- Make each version unique
- Never return the original text unchanged""",

    'staggered': """Generate progressively shorter versions of this text ({tokens} tokens):

{text}

Target percentages: {percentages}%

Response format:
{{
  "versions": [
    {{"text": "longest version"}},   // matches first percentage
    {{"text": "medium version"}},    // matches middle percentage
    {{"text": "shortest version"}}   // matches final percentage
  ]
}}

IMPORTANT:
- Keep technical terms intact
- Match each target percentage exactly
- Each version MUST be shorter than the previous
- Never return the original text unchanged""",

    'fragment': """Compress these {fragment_count} fragments independently:

{text}

Compression requirements:
- Generate EXACTLY {version_count} versions per fragment
- Target percentages: {requirements}
- Each version must be shorter than the previous one
- Never return the original text unchanged

Response format:
{{
  "fragments": [
    {{
      "versions": [
        {{"text": "compressed version 1"}},  // {target_percentages[0]}%
        {{"text": "compressed version 2"}},  // {target_percentages[1]}%
        ...  // up to {version_count} versions
      ]
    }},
    // EXACTLY {fragment_count} fragments
  ]
}}

IMPORTANT: 
- Keep each fragment self-contained
- Keep technical terms intact
- Return EXACTLY {fragment_count} fragments with {version_count} versions each
- Each version MUST be shorter than the previous one
- Never return the original text unchanged"""
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
