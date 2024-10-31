import os
import groq
import tiktoken
import json
import logging

logger = logging.getLogger(__name__)

# Initialize Groq client (shared instance)
groq_client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

# Initialize tokenizer for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string"""
    return len(tokenizer.encode(text))


def calculate_max_tokens(text: str, multiplier: int = 2) -> int:
    """Calculate max tokens based on input text length
    Args:
        text: Input text
        multiplier: Token multiplier (2x for summaries, 3x for expansions)
    """
    base_tokens = count_tokens(text)
    # Add buffer for JSON structure and metadata
    json_overhead = 500  # tokens for JSON structure, IDs, etc.
    # Minimum 1000 tokens
    return max(base_tokens * multiplier + json_overhead, 1000)


def clean_generated_text(text: str) -> str:
    """Clean up AI generated text by removing prefixes and formatting"""
    text = text.replace('\n', ' ').strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    return text


def parse_ai_response(response_text: str) -> dict:
    """Parse AI response and ensure it's valid JSON"""
    logger.debug(f"Parsing AI response: {response_text}")

    try:
        # Try to find JSON-like content
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            result = json.loads(json_str)
            logger.debug(f"Parsed JSON: {result}")

            # Handle different response formats
            if 'fragments' in result:
                # Convert fragment format to flat versions for processing
                versions = []
                for fragment in result['fragments']:
                    versions.extend(fragment['versions'])
                return {'versions': versions}
            elif 'versions' in result:
                return result
            elif 'error' in result:
                return result
            else:
                return {
                    "error": {
                        "code": "invalid_format",
                        "message": "Response missing required fields",
                        "response": response_text,
                        "parsed": result
                    }
                }

        return {
            "error": {
                "code": "invalid_response_format",
                "message": "AI response was not in expected format",
                "response": response_text
            }
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            "error": {
                "code": "invalid_json",
                "message": f"Failed to parse AI response: {str(e)}",
                "response": response_text
            }
        }
    except Exception as e:
        logger.error(f"Unexpected parsing error: {str(e)}")
        return {
            "error": {
                "code": "parsing_error",
                "message": f"Failed to process response: {str(e)}",
                "response": response_text
            }
        }
