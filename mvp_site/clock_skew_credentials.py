"""
Clock-skew adjustment for Google Auth library.

This module provides a workaround for systems where the local clock is ahead
of Google's servers by more than the allowed JWT clock skew tolerance (~5 min).

It monkey-patches the google.auth._helpers.utcnow() function to return an
adjusted time, compensating for the clock being ahead.

Usage:
    from mvp_site.clock_skew_credentials import apply_clock_skew_patch
    apply_clock_skew_patch()  # Call once before any Firebase operations
"""

import os
from datetime import datetime, timedelta

from google.auth import _helpers

from mvp_site import logging_util

# Store the original function and adjustment
_original_utcnow = None
_clock_skew_seconds = 0
_patch_applied = False

# Hardcoded clock skew: 12 minutes (720 seconds)
# This compensates for local clock being ahead of Google's servers.
# Safe for both local development and production - Firebase handles actual time.
CLOCK_SKEW_SECONDS = 720


def validate_deployment_config() -> bool:
    """Validate WORLDAI_* environment variable configuration.

    Prevents accidental use of development credentials in production by requiring
    explicit dev mode acknowledgment.

    Returns:
        True if in dev mode (WORLDAI_DEV_MODE=true or TESTING_AUTH_BYPASS=true), False if in production mode.

    Raises:
        ValueError: If WORLDAI_GOOGLE_APPLICATION_CREDENTIALS is set without
                    WORLDAI_DEV_MODE=true (and not in TESTING_AUTH_BYPASS mode).

    Note:
        TESTING_AUTH_BYPASS=true unconditionally bypasses all validation and returns True,
        allowing for hermetic test environments.
    """
    testing_mode = os.getenv("TESTING_AUTH_BYPASS", "").lower() == "true"
    if testing_mode:
        return True

    has_worldai_creds = os.getenv("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") is not None
    dev_mode = os.getenv("WORLDAI_DEV_MODE", "").lower() == "true"

    if has_worldai_creds and not dev_mode:
        raise ValueError(
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS requires WORLDAI_DEV_MODE=true. "
            "Set WORLDAI_DEV_MODE=true to explicitly acknowledge development mode."
        )

    return dev_mode


def get_clock_skew_seconds() -> int:
    """Get clock skew adjustment.

    Returns:
        720 seconds (12 minutes) - hardcoded value that works for all environments.
        This compensates for local clock being ahead of Google's servers.
    """
    # In TESTING_AUTH_BYPASS or MOCK_SERVICES_MODE, skip validation to allow hermetic tests
    testing_mode = os.getenv("TESTING_AUTH_BYPASS", "").lower() == "true"
    mock_mode = os.getenv("MOCK_SERVICES_MODE", "").lower() == "true"
    
    if not testing_mode and not mock_mode:
        validate_deployment_config()

    return CLOCK_SKEW_SECONDS


def _adjusted_utcnow() -> datetime:
    """Return current UTC time adjusted for clock skew."""
    # Get actual current time and subtract the clock skew to compensate for being ahead
    return _original_utcnow() - timedelta(seconds=_clock_skew_seconds)


def apply_clock_skew_patch() -> bool:
    """Apply clock skew patch to Google Auth library.

    This patches google.auth._helpers.utcnow() to return adjusted time.
    Safe to call multiple times - only applies once.

    Returns:
        True if patch was applied, False if already applied or no adjustment needed.
    """
    global _original_utcnow, _clock_skew_seconds, _patch_applied  # noqa: PLW0603

    if _patch_applied:
        return False

    skew = get_clock_skew_seconds()
    if skew <= 0:
        return False

    _original_utcnow = _helpers.utcnow
    _clock_skew_seconds = skew

    # Apply the patch
    _helpers.utcnow = _adjusted_utcnow
    _patch_applied = True

    logging_util.info(f"Applied clock skew patch: adjusting time by -{skew} seconds")
    return True


def remove_clock_skew_patch() -> bool:
    """Remove the clock skew patch (restore original behavior).

    Returns:
        True if patch was removed, False if not applied.
    """
    global _patch_applied  # noqa: PLW0603

    if not _patch_applied or _original_utcnow is None:
        return False

    _helpers.utcnow = _original_utcnow
    _patch_applied = False
    return True


class UseActualTime:
    """Context manager to temporarily use actual time (bypass clock skew patch).

    Use this when verifying incoming tokens that were issued at Google's actual time.

    Usage:
        with use_actual_time():
            decoded_token = auth.verify_id_token(id_token)
    """

    def __enter__(self):
        """Temporarily restore original utcnow function."""
        self._was_patched = _patch_applied
        if _patch_applied and _original_utcnow is not None:
            _helpers.utcnow = _original_utcnow
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Re-apply the clock skew patch if it was active."""
        if self._was_patched and _original_utcnow is not None:
            _helpers.utcnow = _adjusted_utcnow
        return False  # Don't suppress exceptions
