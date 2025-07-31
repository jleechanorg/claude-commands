from dotenv import load_dotenv

"""
Configuration for FULL API browser tests using real Firebase and Gemini.

WARNING: These tests use REAL APIs and will:
- Cost money (Gemini API charges)
- Create real Firebase data
- Use API quotas
- Require proper authentication

Setup required:
1. Copy .env.template to .env
2. Fill in your real API credentials
3. Ensure Firebase project is properly configured
"""

import os
from pathlib import Path

import requests

# Try to load from .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration
BASE_URL = "http://localhost:8080"  # Main server port
FULL_API_MODE = True

# Credentials (from environment)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FIREBASE_CREDS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# Test user configuration
TEST_USER_EMAIL = os.environ.get("FIREBASE_TEST_USER_EMAIL", "test@worldarchitect.ai")
TEST_USER_PASSWORD = os.environ.get("FIREBASE_TEST_USER_PASSWORD", "TestPassword123!")

# Cost safety limits
MAX_GEMINI_CALLS_PER_TEST = int(os.environ.get("MAX_GEMINI_CALLS_PER_TEST", "5"))
MAX_TEST_COST_USD = float(os.environ.get("MAX_TEST_COST_USD", "0.10"))


def get_test_session():
    """Get a session configured for full API testing."""
    session = requests.Session()

    # For now, still use test bypass headers
    # TODO: Implement real Firebase auth flow
    session.headers.update(
        {"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-full-api-user"}
    )

    return session


def validate_config():
    """Validate that all required configuration is present."""
    errors = []

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY not set in environment")

    if not FIREBASE_CREDS:
        errors.append("GOOGLE_APPLICATION_CREDENTIALS not set")
    elif not os.path.exists(FIREBASE_CREDS):
        errors.append(f"Firebase credentials file not found: {FIREBASE_CREDS}")

    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    return True


class CostTracker:
    """Track API usage and estimated costs."""

    def __init__(self):
        self.gemini_calls = 0
        self.gemini_tokens = 0
        self.firestore_reads = 0
        self.firestore_writes = 0
        self.start_time = None

    def track_gemini(self, estimated_tokens=1000):
        """Track a Gemini API call."""
        self.gemini_calls += 1
        self.gemini_tokens += estimated_tokens

        # Check cost limit
        if self.get_total_cost() > MAX_TEST_COST_USD:
            raise Exception(
                f"Cost limit exceeded: ${self.get_total_cost():.4f} > ${MAX_TEST_COST_USD}"
            )

        # Check call limit
        if self.gemini_calls > MAX_GEMINI_CALLS_PER_TEST:
            raise Exception(
                f"Gemini call limit exceeded: {self.gemini_calls} > {MAX_GEMINI_CALLS_PER_TEST}"
            )

    def track_firestore(self, operation, count=1):
        """Track Firestore operations."""
        if operation == "read":
            self.firestore_reads += count
        elif operation == "write":
            self.firestore_writes += count

    def get_gemini_cost(self):
        """Estimate Gemini API cost."""
        # Gemini 1.5 Flash pricing: ~$0.00025 per 1K tokens
        return (self.gemini_tokens / 1000) * 0.00025

    def get_firestore_cost(self):
        """Estimate Firestore cost."""
        # Rough estimates
        read_cost = self.firestore_reads * 0.00003
        write_cost = self.firestore_writes * 0.00018
        return read_cost + write_cost

    def get_total_cost(self):
        """Get total estimated cost."""
        return self.get_gemini_cost() + self.get_firestore_cost()

    def print_summary(self):
        """Print cost summary."""
        print("\n💰 API Usage Summary:")
        print(f"   Gemini calls: {self.gemini_calls} (~{self.gemini_tokens} tokens)")
        print(
            f"   Firestore: {self.firestore_reads} reads, {self.firestore_writes} writes"
        )
        print(f"   Estimated cost: ${self.get_total_cost():.4f}")
        print(f"   - Gemini: ${self.get_gemini_cost():.4f}")
        print(f"   - Firestore: ${self.get_firestore_cost():.4f}")
