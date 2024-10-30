"""
Compression prompts for different modes:
- Single: One compressed version
- Fixed: Multiple versions at same percentage
- Staggered: Multiple versions with decreasing percentages
"""

# System prompts with detailed rules
COMPRESS_SINGLE = """Generate a JSON response following these EXACT rules:

1. Response format MUST be:
   {
     "versions": [
       {
         "text": "your compressed text here"
       }
     ]
   }

2. Compression requirements:
   - Match target percentage exactly
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
   - Preserve technical accuracy

3. If compression impossible:
   {"error": "specific reason"}

IMPORTANT: Always wrap your response in the versions array, even for single compressions."""

COMPRESS_FIXED = """Generate a JSON response following these rules:

1. Response format:
   {"versions": [{"text": "version 1"}, {"text": "version 2"}]}

2. Each version must:
   - Match the target percentage exactly
   - Use different sentence structures
   - Keep core technical terms intact
   - Maintain complete sentences
   - Preserve technical accuracy

3. Variations between versions:
   - Use different synonyms
   - Restructure sentences
   - Vary which details to keep
   - Keep same technical meaning

4. If task cannot be completed:
   {"error": "specific reason"}"""

COMPRESS_STAGGERED = """Generate a JSON response following these rules:

1. Response format:
   {"versions": [{"text": "longest"}, {"text": "medium"}, {"text": "shortest"}]}

2. Each version must:
   - Match its target percentage exactly
   - Remove less important information gradually
   - Keep core technical terms
   - Maintain readability
   - Preserve technical accuracy

3. Progressive reduction:
   - Sort versions from longest to shortest
   - Remove details systematically
   - Keep core message intact
   - Maintain grammatical correctness

4. If task cannot be completed:
   {"error": "specific reason"}"""

# User messages with examples
USER_MESSAGES = {
    'single': """Generate ONE compressed version at {target}% length:
Original length: {tokens} tokens
Original text: {text}

Example:
Original: "The big brown cat sat lazily on the comfortable mat in the sunny corner."
{target}% compression: {{"versions": [{{"text": "The brown cat sat on the mat in the corner."}}]}}

IMPORTANT: 
- Target EXACTLY {target}% of original length
- Keep technical terms intact
- Remove less important details first""",

    'fixed': """Generate {count} DIFFERENT compressed versions at {target}% length:
Original length: {tokens} tokens
Original text: {text}

Example:
Original: "The big brown cat sat lazily on the comfortable mat in the sunny corner."
Two 50% versions:
{{
  "versions": [
    {{"text": "The brown cat sat on the mat in the corner."}},
    {{"text": "A cat rested on the mat near the window."}}
  ]
}}

IMPORTANT:
- Each version must be EXACTLY {target}% length
- Use different phrasing for each version
- Keep technical terms intact
- Maintain complete sentences""",

    'staggered': """Generate compressed versions at these exact percentages: {percentages}
Original length: {tokens} tokens
Original text: {text}

Example:
Original: "The big brown cat sat lazily on the comfortable mat in the sunny corner."
Staggered compression (75%, 50%, 25%):
{{
  "versions": [
    {{"text": "The brown cat sat lazily on the mat in the corner."}},
    {{"text": "The brown cat sat on the mat in the corner."}},
    {{"text": "The cat sat on the mat."}}
  ]
}}

IMPORTANT:
- Match each percentage EXACTLY
- Remove details gradually
- Keep technical terms intact
- Sort from longest to shortest""",

    'fragment': """Compress these {fragment_count} fragments independently:

{text}

Compression requirements:
{requirements}

Response format:
{{
  "fragments": [
    {{
      "versions": [
        {{"text": "compressed version 1"}},
        {{"text": "compressed version 2"}}
      ]
    }},
    {{
      "versions": [
        {{"text": "compressed version 1"}},
        {{"text": "compressed version 2"}}
      ]
    }}
  ]
}}

IMPORTANT: 
- Keep each fragment self-contained
- Keep technical terms intact
- Return exactly {fragment_count} fragments with {version_count} versions each""",

    'fragment_single': """- Generate ONE version at {target}% length""",

    'fragment_fixed': """- Generate {version_count} DIFFERENT versions at {target}% length""",

    'fragment_staggered': """- Generate versions at these percentages: {percentages}
- Remove details gradually
- Sort from longest to shortest"""
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
           // ... more versions for fragment 1
         ]
       },
       {
         "versions": [
           {"text": "fragment 2 version 1"},
           {"text": "fragment 2 version 2"}
           // ... more versions for fragment 2
         ]
       }
       // ... more fragments
     ]
   }

2. Compression requirements for EACH fragment:
   - Match target percentage exactly
   - Keep core technical terms intact
   - Remove adjectives and details first
   - Maintain complete sentences
   - Keep each fragment self-contained

3. If compression impossible:
   {"error": "specific reason"}"""
