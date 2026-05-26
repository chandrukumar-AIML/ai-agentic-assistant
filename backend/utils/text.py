"""
Text utility functions used across agent nodes.
"""
import re
from typing import Iterable


def strip_code_fence(text: str) -> str:
    """
    Remove markdown code fences from LLM output.
    Handles ```json ... ```, ``` ... ```, and plain text.
    Returns the inner content, stripped.
    """
    text = text.strip()
    # Match optional language tag after opening fence
    pattern = r"^```(?:\w+)?\s*\n?(.*?)\n?```$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def deduplicate_ordered(items: Iterable[str]) -> list[str]:
    """
    Remove duplicates from an iterable while preserving insertion order.
    Empty strings are filtered out.
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
