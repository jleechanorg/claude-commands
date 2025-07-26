"""
Decorators Module

This module provides utility decorators for common cross-cutting concerns in the application.
Currently focuses on exception logging to provide consistent error handling across services.

Key Features:
- Exception logging with full context (function name, args, kwargs)
- Stack trace preservation for debugging
- Consistent error message formatting
- Logger integration with emoji-enhanced logging

Usage:
    @log_exceptions
    def my_function():
        # Function logic here
        pass
"""

import functools
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

import logging_util

# Get a logger instance for this module
logger = logging_util.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


def log_exceptions(func: F) -> F:
    """A decorator that wraps a function in a try-except block
    and logs any exceptions with a full stack trace.

    Args:
        func: The function to be decorated.

    Returns:
        The wrapper function that includes exception logging.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that executes the decorated function and logs exceptions.

        Args:
            *args: Variable length argument list for the decorated function.
            **kwargs: Arbitrary keyword arguments for the decorated function.

        Raises:
            Exception: Re-raises any exception caught from the decorated function
                       after logging it.

        Returns:
            Any: The result of the decorated function's execution.
        """
        try:
            # Attempt to execute the decorated function
            return func(*args, **kwargs)
        except Exception as e:
            # Construct a detailed error message
            # The function name is retrieved using func.__name__
            # Args and kwargs are included for context
            error_message = (
                f"--- EXCEPTION IN: {func.__name__} ---\n"
                f"Args: {args}\n"
                f"Kwargs: {kwargs}\n"
                f"Error: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
                f"--- END EXCEPTION ---"
            )
            logging_util.error(error_message, logger=logger)
            # Re-raise the exception so it can be handled by the calling code (e.g., the route)
            raise

    return wrapper  # type: ignore[return-value]
