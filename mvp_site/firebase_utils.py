"""
Firebase utility functions for consistent initialization checks.
"""

import os
import logging_util


def should_skip_firebase_init():
    """
    Check if Firebase initialization should be skipped based on environment variables.
    
    Returns:
        bool: True if Firebase should be skipped (testing or mock mode), False otherwise
    """
    testing_mode = os.environ.get("TESTING", "").lower() in ["true", "1", "yes"]
    mock_mode = os.environ.get("MOCK_SERVICES_MODE", "").lower() in ["true", "1", "yes"]
    
    if testing_mode or mock_mode:
        logging_util.info(f"Skipping Firebase initialization (TESTING={testing_mode}, MOCK_SERVICES_MODE={mock_mode})")
        return True
    
    return False