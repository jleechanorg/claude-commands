"""
Common test utilities shared across test files.
"""


def has_firebase_credentials():
    """Check if Firebase credentials are available.

    Note: End2end tests use complete mocking and don't require real credentials.
    This function returns False to ensure tests use mocked services.
    """
    # End2end tests should always use mocked services, not real credentials
    return False
