"""
Centralized logging utility with emoji-enhanced messages.
Provides consistent error and warning logging across the application.
Supports both module-level convenience functions and logger-aware functions
that preserve logger context.

UNIFIED LOGGING ARCHITECTURE:
- All logs go to BOTH Cloud Logging (stdout/stderr) and local file
- Log files stored under /tmp/<repo>/<branch>/<service>.log
- Single setup function called by all entry points (Flask, MCP, tests)
- Prevents duplicate handlers via initialization guard
"""

import logging
import os
import subprocess
import threading
from typing import Any

# Initialization guard to prevent duplicate handler setup
_logging_initialized = False
_logging_lock = threading.Lock()

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
    def get_repo_name() -> str:
        """
        Get the repository name from git remote or directory name.

        Returns:
            str: Repository name (e.g., 'worktree_dice', 'worldarchitect.ai')
        """
        try:
            # Try to get repo name from git remote URL
            remote_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=os.path.dirname(__file__),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            # Extract repo name from URL (handles both https and ssh)
            # e.g., "https://github.com/user/repo.git" -> "repo"
            # e.g., "git@github.com:user/repo.git" -> "repo"
            if "/" in remote_url:
                repo_name = remote_url.rsplit("/", 1)[-1]
            elif ":" in remote_url:
                repo_name = remote_url.rsplit(":", 1)[-1].rsplit("/", 1)[-1]
            else:
                repo_name = remote_url
            # Remove .git suffix if present
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            if repo_name:
                return repo_name
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            pass

        # Fallback: use directory name of the git root
        try:
            git_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=os.path.dirname(__file__),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return os.path.basename(git_root)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            pass

        return "unknown_repo"

    @staticmethod
    def get_branch_name() -> str:
        """
        Get the current git branch name safely.

        Returns:
            str: Branch name (e.g., 'main', 'dev1766178798', 'unknown')
        """
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=os.path.dirname(__file__),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if branch:
                return branch
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            pass
        return "unknown"

    @staticmethod
    def get_log_directory() -> str:
        """
        Get the standardized log directory path with repo and branch isolation.

        Returns:
            str: Path to the log directory in format /tmp/{repo}/{branch}
        """
        repo = LoggingUtil.get_repo_name()
        branch = LoggingUtil.get_branch_name()

        # Convert forward slashes to underscores for valid directory name
        safe_repo = repo.replace("/", "_")
        safe_branch = branch.replace("/", "_")
        log_dir = f"/tmp/{safe_repo}/{safe_branch}"

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


def setup_unified_logging(service_name: str = "app") -> str:
    """
    Configure unified logging for all entry points (Flask, MCP, tests).

    Sets up both console handler (for Cloud Logging via stdout/stderr)
    and file handler (for local persistence under /tmp/<repo>/<branch>/).

    This function is idempotent - calling it multiple times is safe and
    will not add duplicate handlers.

    Args:
        service_name: Name of the service (e.g., 'flask-server', 'mcp-server')
                     Used to name the log file.

    Returns:
        str: Path to the log file being written to
    """
    global _logging_initialized

    with _logging_lock:
        if _logging_initialized:
            # Already initialized - just return the log file path
            return LoggingUtil.get_log_file(service_name)

        # Get log file path
        log_file = LoggingUtil.get_log_file(service_name)

        # Clear any existing handlers (close them first to prevent ResourceWarning)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        # Set up consistent formatting
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler (goes to stdout/stderr -> Cloud Logging in GCP)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler (persists locally under /tmp/<repo>/<branch>/)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Set level
        root_logger.setLevel(logging.INFO)

        _logging_initialized = True
        info(f"Unified logging configured: {log_file}")

        return log_file


def is_logging_initialized() -> bool:
    """Check if unified logging has been initialized."""
    return _logging_initialized
