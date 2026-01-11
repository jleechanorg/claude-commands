"""Token counting utilities for consistent logging across the application."""

from mvp_site import logging_util

# Token estimation constant - Gemini uses roughly 1 token per 4 characters
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str | list[str]) -> int:
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

    # Use the centralized token calculation constant
    return total_chars // CHARS_PER_TOKEN


def log_with_tokens(message: str, text: str, logger=None):
    """
    Log a message with both character and token counts.

    Args:
        message: Base message to log
        text: Text to count
        logger: Logger instance (uses logging if not provided)
    """
    if logger is None:
        logger = logging_util

    char_count = len(text) if text else 0
    formatted_count = format_token_count(char_count)

    logger.info(f"{message}: {formatted_count}")


def format_token_count(char_count: int) -> str:
    """
    Format character count with estimated tokens.

    Args:
        char_count: Number of characters

    Returns:
        Formatted string like "1000 characters (~250 tokens)"
    """
    token_count = char_count // CHARS_PER_TOKEN
    token_text = "token" if token_count == 1 else "tokens"
    return f"{char_count} characters (~{token_count} {token_text})"
