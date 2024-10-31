# Shared AI configuration and prompts

# Model settings
# DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_MODEL = "llama3-groq-70b-8192-tool-use-preview"
DEFAULT_TEMPERATURE = 0.7

# Valid options for API parameters
VALID_STYLES = {'elaborate', 'explain', 'example', 'detail'}
VALID_TONES = {'academic', 'conversational', 'technical'}
VALID_ASPECTS = {'context', 'examples', 'implications',
                 'technical_details', 'counterarguments'}

# Valid options for fragment styles
VALID_FRAGMENT_STYLES = {'bullet', 'narrative', 'outline'}

# Default number of versions to generate
DEFAULT_VERSIONS = 1
MAX_VERSIONS = 5

COMPRESS_PROMPT = """Generate a JSON response following these rules:

1. For single version compression:
   - Return {"versions": [{"text": "compressed version"}]}
   - Focus on reaching exact target percentage
   - Maintain core meaning while removing less essential details

2. For multiple fixed-length versions:
   - All versions must be same length but with different phrasing
   - Vary sentence structure and word choice significantly
   - Keep technical terms and core meaning intact

3. For staggered compression:
   - Each version must be progressively shorter
   - Remove less essential information gradually
   - Maintain readability at each step

4. Always ensure:
   - Valid JSON format
   - Complete sentences
   - Proper punctuation
   - Core meaning preserved

5. If task cannot be completed:
   - Return {"error": "specific reason"}"""

EXPAND_PROMPT = """Generate expanded versions of text fragments following these rules:
1. Each version should be a unique expansion targeting the specified token length
2. Keep the core meaning but add relevant details, examples, or context
3. Return JSON with format: {"versions": [{"text": "expanded version 1"}, {"text": "expanded version 2"}]}
4. Each version should be self-contained and coherent
5. If task cannot be completed, return {"error": "reason"}"""

COHESIVE_PROMPT = """Generate a JSON response following these rules:
1. Make text more cohesive while preserving meaning
2. Keep the same tone and style as the original
3. Match the input language (e.g. Spanish input = Spanish output)
4. Return JSON with format: {"text": "cohesive_text"}
5. Stay factual - avoid editorializing
6. Be systematic in improving flow
7. If task cannot be completed, return {"error": "reason"}"""

FRAGMENT_PROMPT = """Generate a JSON response following these rules:
1. Split text into complete, standalone fragments
2. Each fragment should be a complete thought
3. Match the input language (e.g. Spanish input = Spanish output)
4. Return JSON with format: {"fragments": [{"text": "fragment1"}, {"text": "fragment2"}]}
5. Keep original meaning and context
6. Be systematic in identifying natural break points
7. If task cannot be completed, return {"error": "reason"}"""

GENERATE_PROMPT = """Generate a JSON response following these rules:
1. Each version should be a unique generation targeting the specified token length
2. Keep the style and tone consistent with the request
3. Return JSON with format: {"versions": [{"text": "generated version 1"}, {"text": "generated version 2"}]}
4. Each version should be self-contained and coherent
5. If task cannot be completed, return {"error": "reason"}"""
