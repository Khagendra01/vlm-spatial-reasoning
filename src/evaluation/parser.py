"""
Output parser for VLM spatial reasoning classification.

Normalizes model outputs into True, False, or None (for invalid output).
"""

import re
from typing import Optional


# Patterns that indicate True
TRUE_PATTERNS = [
    r"^true$",
    r"^yes$",
    r"^correct$",
    r"^the answer is true$",
    r"^the statement is true$",
    r"^the statement is correct$",
    r"^this is true$",
    r"^this statement is true$",
    r"^it is true$",
    r"^it's true$",
    r"^absolutely$",
    r"^definitely$",
]

# Patterns that indicate False
FALSE_PATTERNS = [
    r"^false$",
    r"^no$",
    r"^incorrect$",
    r"^the answer is false$",
    r"^the statement is false$",
    r"^the statement is incorrect$",
    r"^this is false$",
    r"^this statement is false$",
    r"^it is false$",
    r"^it's false$",
    r"^not true$",
    r"^not correct$",
]


def parse_true_false(output: str) -> Optional[bool]:
    """
    Parse model output into True, False, or None.

    Args:
        output: Raw model output string

    Returns:
        True if output indicates True
        False if output indicates False
        None if output is invalid/unparseable
    """
    if not output or not isinstance(output, str):
        return None

    # Normalize the output
    normalized = output.strip().lower()

    # Remove common prefixes/suffixes
    normalized = re.sub(r"^(the answer is|answer:|response:|output:)\s*", "", normalized)
    normalized = re.sub(r"[.\s]+$", "", normalized)

    # Check for True patterns
    for pattern in TRUE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return True

    # Check for False patterns
    for pattern in FALSE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return False

    # Try to find True/False anywhere in the output as a fallback
    if "true" in normalized and "false" not in normalized:
        return True
    if "false" in normalized and "true" not in normalized:
        return False

    # Invalid output
    return None


def parse_batch(outputs: list[str]) -> list[Optional[bool]]:
    """
    Parse a batch of model outputs.

    Args:
        outputs: List of raw model output strings

    Returns:
        List of parsed values (True, False, or None)
    """
    return [parse_true_false(output) for output in outputs]
