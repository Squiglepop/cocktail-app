"""
Security utilities for input sanitization and validation.
"""
import html
import re
from typing import Optional

import bleach


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Remove HTML tags and dangerous content from extracted text.

    This sanitizes AI-extracted content that could contain:
    - Embedded HTML/JavaScript from malicious images
    - Script injection patterns
    - Control characters

    Args:
        text: Text to sanitize (may be None)

    Returns:
        Sanitized text or None if input was None
    """
    if text is None:
        return None

    # Strip ALL HTML tags - we don't want any markup from AI extraction
    cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)

    # Unescape HTML entities (bleach encodes & to &amp;, etc.)
    cleaned = html.unescape(cleaned)

    # Strip control characters except newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)

    # Remove potential script injection patterns (belt and suspenders)
    dangerous_patterns = [
        r'javascript\s*:',
        r'data\s*:\s*text/html',
        r'vbscript\s*:',
        r'on\w+\s*=',  # onclick=, onerror=, etc.
        r'<\s*script',
        r'<\s*/\s*script',
    ]

    for pattern in dangerous_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def sanitize_recipe_name(name: Optional[str]) -> str:
    """Sanitize recipe name, ensuring a valid non-empty result.

    Args:
        name: Recipe name to sanitize

    Returns:
        Sanitized name, defaulting to "Untitled Recipe" if empty
    """
    sanitized = sanitize_text(name)
    if not sanitized:
        return "Untitled Recipe"
    return sanitized


def sanitize_ingredient_name(name: Optional[str]) -> str:
    """Sanitize ingredient name, ensuring a valid non-empty result.

    Args:
        name: Ingredient name to sanitize

    Returns:
        Sanitized name, defaulting to "Unknown Ingredient" if empty
    """
    sanitized = sanitize_text(name)
    if not sanitized:
        return "Unknown Ingredient"
    return sanitized
