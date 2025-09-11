"""
Centralized logging utility with emoji-enhanced messages.
Provides consistent error and warning logging across the application.
Supports both module-level convenience functions and logger-aware functions
that preserve logger context.
"""

import logging
import os
import subprocess
from typing import Any

# Export logging level constants
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
# WARN is an alias of WARNING; export WARNING only to avoid ambiguity.
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

# Export common logging classes
StreamHandler = logging.StreamHandler
FileHandler = logging.FileHandler
Handler = logging.Handler
Formatter = logging.Formatter
Logger = logging.Logger


class LoggingUtil:
    """Centralized logging utility with emoji-enhanced messages."""

    # Emoji constants
    ERROR_EMOJI = "🔥🔴"
    WARNING_EMOJI = "⚠️"

    @staticmethod
    def get_log_directory() -> str:
        """
        Get the standardized log directory path with branch isolation.

        Returns:
            str: Path to the log directory in format /tmp/worldarchitect.ai/{branch_name}
        """
        try:
            # Get current git branch
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=os.path.dirname(__file__),
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            branch = "unknown"

        # Convert forward slashes to underscores for valid directory name
        safe_branch = branch.replace("/", "_")
        log_dir = f"/tmp/worldarchitect.ai/{safe_branch}"

        # Ensure directory exists
        os.makedirs(log_dir, exist_ok=True)

        return log_dir

    @staticmethod
    def get_log_file(service_name: str) -> str:
        """
        Get the standardized log file path for a specific service.

        Args:
            service_name: Name of the service (e.g., 'flask-server', 'mcp-server', 'test-server')

        Returns:
            str: Full path to the log file
        """
        log_dir = LoggingUtil.get_log_directory()
        return os.path.join(log_dir, f"{service_name}.log")

    @staticmethod
    def error(
        message: str, *args: Any, logger: logging.Logger | None = None, **kwargs: Any
    ) -> None:
        """
        Log an error message with fire and red dot emojis.

        Args:
            message: The error message to log
            *args: Additional positional arguments for logging
            logger: Optional logger instance to preserve context. If None, uses root logger.
            **kwargs: Additional keyword arguments for logging
        """
        enhanced_message = f"{LoggingUtil.ERROR_EMOJI} {message}"
        if logger is not None:
            logger.error(enhanced_message, *args, **kwargs)
        else:
            logging.error(enhanced_message, *args, **kwargs)

    @staticmethod
    def warning(
        message: str, *args: Any, logger: logging.Logger | None = None, **kwargs: Any
    ) -> None:
        """
        Log a warning message with warning emoji.

        Args:
            message: The warning message to log
            *args: Additional positional arguments for logging
            logger: Optional logger instance to preserve context. If None, uses root logger.
            **kwargs: Additional keyword arguments for logging
        """
        enhanced_message = f"{LoggingUtil.WARNING_EMOJI} {message}"
        if logger is not None:
            logger.warning(enhanced_message, *args, **kwargs)
        else:
            logging.warning(enhanced_message, *args, **kwargs)

    @staticmethod
    def get_error_prefix() -> str:
        """Get the error emoji prefix for manual use."""
        return LoggingUtil.ERROR_EMOJI

    @staticmethod
    def get_warning_prefix() -> str:
        """Get the warning emoji prefix for manual use."""
        return LoggingUtil.WARNING_EMOJI

    @staticmethod
    def info(message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log an info message (no emoji modification).

        Args:
            message: The info message to log
            *args: Additional positional arguments for logging
            **kwargs: Additional keyword arguments for logging
        """
        logging.info(message, *args, **kwargs)

    @staticmethod
    def debug(message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a debug message (no emoji modification).

        Args:
            message: The debug message to log
            *args: Additional positional arguments for logging
            **kwargs: Additional keyword arguments for logging
        """
        logging.debug(message, *args, **kwargs)

    @staticmethod
    def critical(message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a critical message with double fire emoji.

        Args:
            message: The critical message to log
            *args: Additional positional arguments for logging
            **kwargs: Additional keyword arguments for logging
        """
        enhanced_message = f"🔥🔥 {message}"
        logging.critical(enhanced_message, *args, **kwargs)

    @staticmethod
    def exception(message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log an exception message with traceback.

        Args:
            message: The exception message to log
            *args: Additional positional arguments for logging
            **kwargs: Additional keyword arguments for logging
        """
        enhanced_message = f"{LoggingUtil.ERROR_EMOJI} {message}"
        logging.exception(enhanced_message, *args, **kwargs)

    @staticmethod
    def basicConfig(**kwargs: Any) -> None:
        """
        Configure basic logging settings.

        Args:
            **kwargs: Arguments to pass to logging.basicConfig
        """
        logging.basicConfig(**kwargs)

    @staticmethod
    def getLogger(name: str | None = None) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name: Logger name (optional)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)


# Convenience module-level functions
def error(message: str, *args: Any, **kwargs: Any) -> None:
    """
    Log an error message with fire and red dot emojis.

    Args:
        message: The error message to log
        *args: Additional positional arguments for logging
        **kwargs: Additional keyword arguments for logging.
                 Use logger=my_logger to preserve logger context.
    """
    LoggingUtil.error(message, *args, **kwargs)


def warning(message: str, *args: Any, **kwargs: Any) -> None:
    """
    Log a warning message with warning emoji.

    Args:
        message: The warning message to log
        *args: Additional positional arguments for logging
        **kwargs: Additional keyword arguments for logging.
                 Use logger=my_logger to preserve logger context.
    """
    LoggingUtil.warning(message, *args, **kwargs)


def info(message: str, *args: Any, **kwargs: Any) -> None:
    """Log an info message (no emoji modification)."""
    LoggingUtil.info(message, *args, **kwargs)


def debug(message: str, *args: Any, **kwargs: Any) -> None:
    """Log a debug message (no emoji modification)."""
    LoggingUtil.debug(message, *args, **kwargs)


def critical(message: str, *args: Any, **kwargs: Any) -> None:
    """Log a critical message with double fire emoji."""
    LoggingUtil.critical(message, *args, **kwargs)


def exception(message: str, *args: Any, **kwargs: Any) -> None:
    """Log an exception message with traceback."""
    LoggingUtil.exception(message, *args, **kwargs)


def basicConfig(**kwargs: Any) -> None:
    """Configure basic logging settings."""
    LoggingUtil.basicConfig(**kwargs)


def getLogger(name: str | None = None) -> logging.Logger:
    """Get a logger instance."""
    return LoggingUtil.getLogger(name)
