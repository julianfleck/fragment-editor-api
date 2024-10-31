import os
import groq
import json
import logging
from typing import Optional, Dict, Any
from openai import APIError
from app.config.ai_settings import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_TEMPERATURE
)

logger = logging.getLogger(__name__)

# Initialize Groq client (shared instance)
groq_client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))


def get_ai_completion(
    system_prompt: str,
    user_message: str,
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Get completion from Groq API

    Args:
        system_prompt: System instructions
        user_message: User request
        temperature: Optional temperature override (0.0-0.9)

    Returns:
        Dict containing the parsed response or error
    """
    try:
        # Log request
        logger.info("Sending request to Groq API")
        logger.debug(f"System prompt: {system_prompt}")
        logger.debug(f"User message: {user_message}")

        # Validate and adjust temperature
        temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
        temp = min(max(0.0, temp), MAX_TEMPERATURE)

        # Create chat completion
        response = groq_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temp
        )

        # Extract and parse response
        content = response.choices[0].message.content
        logger.info("Received response from Groq API")
        logger.debug(f"Raw response content: {content}")

        # Parse JSON response
        try:
            result = json.loads(content)
            logger.debug(f"Parsed JSON response: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Invalid JSON content: {content}")
            return {
                "error": {
                    "code": "parse_error",
                    "message": "Failed to parse AI response as JSON",
                    "details": str(e) if logger.isEnabledFor(logging.DEBUG) else None
                }
            }

    except APIError as e:
        logger.error(f"Groq API error: {str(e)}")
        return {
            "error": {
                "code": "api_error",
                "message": f"AI service error: {str(e)}",
                "details": str(e) if logger.isEnabledFor(logging.DEBUG) else None
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in AI completion: {str(e)}")
        return {
            "error": {
                "code": "service_error",
                "message": "Unexpected error in AI service",
                "details": str(e) if logger.isEnabledFor(logging.DEBUG) else None
            }
        }
