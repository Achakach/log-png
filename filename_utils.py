"""Shared filename utilities."""
import re


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Strip invalid filename characters. Preserve spaces and hyphens.

    Replaces /, # with _, | with space, $, [, ] with _.
    Collapses runs of spaces/underscores.
    Returns 'unnamed' for empty input.
    """
    result = re.sub(r'[\\/*?:"<>\n\r\t#]', '_', name)
    result = result.replace('|', ' ').replace('$', '_').replace('[', '_').replace(']', '_')
    result = re.sub(r'\s+', ' ', result)       # collapse spaces
    result = re.sub(r'_+', '_', result)        # collapse underscores
    result = result.strip(' _')                # strip leading/trailing spaces/underscores
    if not result.strip():
        return 'unnamed'
    return result[:max_length]
