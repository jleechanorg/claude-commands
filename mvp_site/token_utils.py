"""Token counting utilities for consistent logging across the application."""

import logging_util
from typing import Union, List

def estimate_tokens(text: Union[str, List[str]]) -> int:
    """
    Estimate token count for text.
    
    Uses the rough approximation of 1 token per 4 characters for Gemini models.
    This is a simple estimation - for exact counts, use the Gemini API's count_tokens method.
    
    Args:
        text: String or list of strings to count tokens for
        
    Returns:
        Estimated token count
    """
    if isinstance(text, list):
        total_chars = sum(len(s) for s in text if isinstance(s, str))
    else:
        total_chars = len(text) if text else 0
    
    # Gemini uses roughly 1 token per 4 characters
    return total_chars // 4

def log_with_tokens(message: str, text: str, logger=None):
    """
    Log a message with both character and token counts.
    
    Args:
        message: Base message to log
        text: Text to count
        logger: Logger instance (uses logging if not provided)
    """
    if logger is None:
        logger = logging
        
    char_count = len(text) if text else 0
    token_count = estimate_tokens(text)
    
    logger.info(f"{message}: {char_count} characters (~{token_count} tokens)")

def format_token_count(char_count: int) -> str:
    """
    Format character count with estimated tokens.
    
    Args:
        char_count: Number of characters
        
    Returns:
        Formatted string like "1000 characters (~250 tokens)"
    """
    token_count = char_count // 4
    return f"{char_count} characters (~{token_count} tokens)"