"""
Common configuration for all browser tests.
"""

import requests

BASE_URL = "http://localhost:8086"

def get_test_session():
    """Get a requests session with test auth headers."""
    session = requests.Session()
    session.headers.update({
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-browser-user'
    })
    return session