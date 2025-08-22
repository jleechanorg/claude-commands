"""
Firebase utility functions for consistent initialization checks.
"""

import os
import logging_util


def _env_truthy(name: str) -> bool:
    """
    Returns True if the environment variable `name` is set to
    a truthy value (case-insensitive): "true", "1", "yes", "y", or "on".
    """
    return os.environ.get(name, "").strip().lower() in {"true", "1", "yes", "y", "on"}


def should_skip_firebase_init():
    """
    Check if Firebase initialization should be skipped based on environment variables.
    
    Production mode ALWAYS overrides testing/mock modes to ensure real services are used.
    
    Returns:
        bool: True if Firebase should be skipped (testing or mock mode), False otherwise
    """
    production_mode = _env_truthy("PRODUCTION_MODE")
    testing_mode = _env_truthy("TESTING")
    mock_mode = _env_truthy("MOCK_SERVICES_MODE")
    
    # PRODUCTION_MODE overrides any testing/mock modes
    if production_mode:
        logging_util.info(f"PRODUCTION_MODE enabled - Firebase initialization REQUIRED (overrides TESTING={testing_mode}, MOCK_SERVICES_MODE={mock_mode})")
        return False
    
    if testing_mode or mock_mode:
        logging_util.info(f"Skipping Firebase initialization (TESTING={testing_mode}, MOCK_SERVICES_MODE={mock_mode})")
        return True
    
    return False