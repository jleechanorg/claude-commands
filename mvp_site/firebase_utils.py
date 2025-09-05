"""
Firebase utility functions.
Note: Testing mode has been removed - Firebase is always initialized with real authentication.
"""

import logging_util

# Testing mode removal: Firebase is now always initialized
# All authentication uses real Firebase in all environments
logging_util.info(
    "Firebase initialization enabled - using real Firebase in all environments"
)
