"""
Shared JSON parsing utilities for handling incomplete or malformed JSON responses
"""
import json
import re
from typing import Tuple, Optional, Dict, Any


def count_unmatched_quotes(text: str) -> int:
    """
    Count unmatched quotes in text, accounting for escape sequences.
    
    Returns:
        Number of unmatched quotes (odd number indicates we're in a string)
    """
    quote_count = 0
    escape_next = False
    
    for char in text:
        if escape_next:
            escape_next = False
            continue
        if char == '\\':
            escape_next = True
            continue
        if char == '"' and not escape_next:
            quote_count += 1
    
    return quote_count


def count_unmatched_braces(text: str) -> Tuple[int, int]:
    """
    Count unmatched braces and brackets, accounting for strings.
    
    Returns:
        tuple: (unmatched_braces, unmatched_brackets)
    """
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for char in text:
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
    
    return (brace_count, bracket_count)


def unescape_json_string(text: str) -> str:
    """
    Unescape common JSON escape sequences.
    """
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    text = text.replace('\\"', '"')
    text = text.replace('\\\\', '\\')
    text = text.replace('\\/', '/')
    text = text.replace('\\b', '\b')
    text = text.replace('\\f', '\f')
    text = text.replace('\\r', '\r')
    return text


def try_parse_json(text: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Try to parse JSON text, returning (result, success).
    """
    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        return None, False


def extract_json_boundaries(text: str) -> Optional[str]:
    """
    Extract JSON content between first { and its matching }.
    
    Returns:
        Extracted JSON string or None if no valid JSON boundaries found
    """
    start_match = re.search(r'[{\[]', text)
    if not start_match:
        return None
    
    text = text[start_match.start():]
    
    if text.startswith('{'):
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[:i + 1]
    
    return text


def complete_truncated_json(text: str) -> str:
    """
    Attempt to complete truncated JSON by adding missing quotes and braces.
    """
    if not text.strip():
        return "{}"
    
    # Ensure it starts with { or [
    if not text.strip().startswith(('{', '[')):
        return text
    
    completed = text
    
    # Check for unclosed strings
    quote_count = count_unmatched_quotes(text)
    if quote_count % 2 == 1:
        # Odd number of quotes means we're in a string
        if completed.rstrip().endswith('}'):
            # Insert quote before the closing brace
            completed = completed[:-1] + '"}'
        else:
            completed += '"'
    
    # Count and close brackets/braces
    open_braces, open_brackets = count_unmatched_braces(completed)
    
    # Close arrays first, then objects
    completed += ']' * open_brackets
    completed += '}' * open_braces
    
    return completed


def extract_field_value(text: str, field_name: str) -> Optional[str]:
    """
    Extract a specific field value from potentially malformed JSON.
    
    Args:
        text: The JSON-like text
        field_name: The field to extract
        
    Returns:
        The extracted value or None
    """
    # Try multiple patterns
    patterns = [
        rf'"{field_name}"\s*:\s*"((?:[^"\\]|\\.)*)"',  # Standard JSON string
        rf'"{field_name}"\s*:\s*"((?:[^"\\]|\\.)*?)(?=\s*[,}}]|$)',  # Incomplete string
        rf'"{field_name}"\s*:\s*"(.*?)(?:"|$)',  # Very loose match
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            value = match.group(1)
            return unescape_json_string(value)
    
    return None