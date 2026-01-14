"""Centralized logging utilities for automation components.

This module provides standardized logging setup to eliminate code duplication
across the automation package. All logging configuration should use this module.

Consolidates implementations previously scattered across:
- utils.py
- automation_utils.py
- automation_safety_wrapper.py
- openai_automation/codex_github_mentions.py
"""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """Standardized logging setup for automation components.

    Args:
        name: Logger name (typically __name__ of calling module)
        level: Logging level (default: INFO)
        log_file: Optional specific log file path
        log_dir: Optional log directory (creates default filename if set)

    Returns:
        Configured logger instance

    Examples:
        # Basic usage
        logger = setup_logging(__name__)

        # With specific log file
        logger = setup_logging(__name__, log_file="/tmp/mylog.log")

        # With log directory (auto-generates filename)
        logger = setup_logging(__name__, log_dir=Path("/tmp/logs"))
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler setup
    if log_file:
        # Explicit log file specified
        log_dir = os.path.dirname(log_file)
        if log_dir:  # Only create directory if log_file has a directory component
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    elif log_dir:
        # Log directory specified - create default filename
        log_dir.mkdir(parents=True, exist_ok=True)
        log_filename = f"{name.replace('.', '_')}.log"
        log_path = log_dir / log_filename
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Backward compatibility aliases for common usage patterns
def get_logger(name: str, **kwargs) -> logging.Logger:
    """Alias for setup_logging() for backward compatibility."""
    return setup_logging(name, **kwargs)
