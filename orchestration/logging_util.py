import logging
import sys
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger configured for stdout output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(_DEFAULT_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


# Backwards compatibility for legacy callers
def getLogger(name: Optional[str] = None) -> logging.Logger:  # noqa: N802
    return get_logger(name)
