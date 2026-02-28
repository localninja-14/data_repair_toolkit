"""Utility functions for data repair toolkit."""

import re


def sanitize_column_name(name: str) -> str:
    """
    Sanitize column name to be a valid Python identifier.
    
    - Replace non-alphanumeric with underscore
    - Ensure starts with letter or underscore
    - Return lowercase sanitized name
    """
    # replace non-alphanumeric with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    
    # ensure starts with letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    
    # handle empty case
    if not sanitized:
        sanitized = "_col"
    
    return sanitized.lower()
