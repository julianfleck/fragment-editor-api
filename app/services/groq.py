import os
import groq
import json
import logging
from typing import Optional, Dict, Any, List, TypedDict, Literal, cast
from openai import APIError
from json_repair import repair_json
from app.config.ai_settings import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_TEMPERATURE
)
from app.models.validation import ValidationError

# Define message type structures that match Groq's expected types


class ChatCompletionMessageParam(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


# Initialize logger and client
logger = logging.getLogger(__name__)
groq_client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))


def get_ai_completion(
    system_prompt: str,
    user_message: str,
    temperature: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
    style: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get completion from Groq API with proper type handling and validation
    """
    try:
        # Validate and adjust temperature
        if temperature is not None:
            if not isinstance(temperature, (int, float)):
                raise ValidationError(
                    code="INVALID_TEMPERATURE_TYPE",
                    message="Temperature must be a number"
                )
            if not 0 <= temperature <= MAX_TEMPERATURE:
                raise ValidationError(
                    code="INVALID_TEMPERATURE_RANGE",
                    message=f"Temperature must be between 0 and {
                        MAX_TEMPERATURE}"
                )
        temp = temperature if temperature is not None else DEFAULT_TEMPERATURE

        # Construct properly typed messages
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add context and style as system messages if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Context information: {json.dumps(context)}"
            })
        if style:
            messages.append({
                "role": "system",
                "content": f"Style parameters: {json.dumps(style)}"
            })

        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        logger.debug(f"Sending messages to Groq: {messages}")

        # Create chat completion
        response = groq_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temp
        )

        # Extract and parse response
        content = response.choices[0].message.content
        if not content:
            raise ValidationError(
                code="EMPTY_RESPONSE",
                message="Received empty response from AI"
            )

        logger.info("Received response from Groq API")
        logger.debug(f"Raw AI response: {content}")

        # Parse JSON response with enhanced error handling
        try:
            # First attempt: direct JSON parse
            if isinstance(content, str):
                if content.startswith('"') and content.endswith('"'):
                    content = json.loads(content)
                try:
                    result = json.loads(str(content))
                except json.JSONDecodeError:
                    # Second attempt: repair and parse
                    logger.warning(
                        "Initial JSON parse failed, attempting repair")
                    repaired = repair_json(str(content))
                    result = json.loads(repaired)
                    logger.info("Successfully repaired and parsed JSON")
            else:
                result = content

            logger.debug(f"Final parsed JSON: {result}")
            return cast(Dict[str, Any], result)

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            if isinstance(content, str):
                logger.debug(f"Invalid JSON content: {content[:200]}...")
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
