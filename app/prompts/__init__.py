from typing import Dict, Optional
from .expand import EXPAND_BASE, EXPAND_FRAGMENT, USER_MESSAGES as EXPAND_MESSAGES
from .compress import COMPRESS_BASE, COMPRESS_FRAGMENT, USER_MESSAGES as COMPRESS_MESSAGES
from .rephrase import REPHRASE_BASE, USER_MESSAGES as REPHRASE_MESSAGES

SYSTEM_PROMPTS: Dict[str, Dict[str, str]] = {
    'expand': {
        'base': EXPAND_BASE,
        'fragment': EXPAND_FRAGMENT
    },
    'compress': {
        'base': COMPRESS_BASE,
        'fragment': COMPRESS_FRAGMENT
    },
    'rephrase': {
        'base': REPHRASE_BASE,
        'fragment': REPHRASE_BASE  # Same for both
    }
}

USER_MESSAGES: Dict[str, Dict[str, str]] = {
    'expand': EXPAND_MESSAGES,
    'compress': COMPRESS_MESSAGES,
    'rephrase': REPHRASE_MESSAGES
}


def get_prompt(
    operation: str,
    prompt_type: str,
    is_fragment: bool = False
) -> str:
    """Get prompt for specific operation and type"""
    if prompt_type == 'system':
        return SYSTEM_PROMPTS[operation]['fragment' if is_fragment else 'base']
    elif prompt_type == 'user':
        return USER_MESSAGES[operation]['fragment' if is_fragment else 'base']
    raise ValueError(f"Unknown prompt type: {prompt_type}")
