import functools
import logging
import traceback

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def log_exceptions(func):
    """
    A decorator that wraps a function in a try-except block
    and logs any exceptions with a full stack trace.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
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
            logger.error(error_message)
            # Re-raise the exception so it can be handled by the calling code (e.g., the route)
            raise
    return wrapper
