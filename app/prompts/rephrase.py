REPHRASE_BASE = """Generate alternative versions of text with different wording but identical meaning. Respond in JSON format:

1. Rephrasing requirements:
   - Use completely different sentence structure
   - Replace words with synonyms where possible
   - Keep technical terms unchanged (e.g. API, REST, endpoints)
   - Maintain exact same meaning and facts
   - Match original tone and formality level
   - Keep same information density
   - Never add or remove details

2. Examples of good rephrasing:
   Original: "The Text Transformation API offers a robust set of REST endpoints."
   Version 1: "A comprehensive collection of REST endpoints is provided by the Text Transformation API."
   Version 2: "The Text Transformation API delivers a powerful suite of REST endpoints."

3. Response format (JSON):
   {
     "fragments": [
       {
         "lengths": [
           {
             "versions": [
               {"text": "first rephrased version"},
               {"text": "second rephrased version"}
             ]
           }
         ]
       }
     ]
   }

4. If rephrasing impossible:
   {"error": "specific reason"}"""

USER_MESSAGES = {
    'base': """Create {versions} unique rephrased versions of this text.
Style: {style}

Original text:
{text}

Requirements:
- Use different sentence structures
- Replace words with synonyms where appropriate
- Keep technical terms unchanged
- Maintain exact meaning and tone{tone_str}{aspects_str}""",

    'fragment': """Create {versions} unique rephrased versions for each of these {fragment_count} fragments.
Style: {style}

Original fragments:
{text}

Requirements:
- Rephrase each fragment independently
- Use different sentence structures
- Replace words with synonyms where appropriate
- Keep technical terms unchanged
- Maintain exact meaning and tone{tone_str}{aspects_str}

Process each fragment separately - DO NOT combine or merge them."""
}
