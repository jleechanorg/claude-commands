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

# Store the original function and adjustment
_original_utcnow = None
_clock_skew_seconds = 0
_patch_applied = False


def validate_deployment_config() -> bool:
    """Validate WORLDAI_* environment variable configuration.

    Prevents accidental use of development credentials in production by requiring
    explicit dev mode acknowledgment.

    Returns:
        True if in dev mode (WORLDAI_DEV_MODE=true or TESTING=true), False if in production mode.

    Raises:
        ValueError: If WORLDAI_GOOGLE_APPLICATION_CREDENTIALS is set without
                    WORLDAI_DEV_MODE=true or TESTING=true (prevents accidental production use).

    Note:
        TESTING=true bypasses the validation to allow test collection without
        special env vars. Tests should ALWAYS run, never silently skip.
    """
    # TESTING mode bypasses all credential validation - tests must always run
    testing_mode = os.getenv("TESTING", "").lower() == "true"
    if testing_mode:
        return True  # Treat as dev mode in tests

    has_worldai_creds = os.getenv("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") is not None
    dev_mode = os.getenv("WORLDAI_DEV_MODE", "").lower() == "true"

    if has_worldai_creds and not dev_mode:
        raise ValueError(
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS requires WORLDAI_DEV_MODE=true. "
            "Set WORLDAI_DEV_MODE=true to explicitly acknowledge development mode. "
            "(Or set TESTING=true for test execution)"
        )

    return dev_mode


def get_clock_skew_seconds() -> int:
    """Get clock skew from environment variable.

    Returns:
        Number of seconds the local clock is ahead (positive value to subtract).

    Raises:
        ValueError: If deployment configuration is invalid (see validate_deployment_config).
    """
    # Validate configuration before returning skew
    is_dev_mode = validate_deployment_config()

    skew_env = os.getenv("WORLDAI_CLOCK_SKEW_SECONDS")
    if skew_env:
        return int(skew_env)

    # Default to 10 minutes (600 seconds) if in dev mode
    # This indicates local development where clock skew is expected
    if is_dev_mode:
        return 600

    return 0


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
    global _original_utcnow, _clock_skew_seconds, _patch_applied

    if _patch_applied:
        return False

    skew = get_clock_skew_seconds()
    if skew <= 0:
        return False

    try:
        from google.auth import _helpers

        _original_utcnow = _helpers.utcnow
        _clock_skew_seconds = skew

        # Apply the patch
        _helpers.utcnow = _adjusted_utcnow
        _patch_applied = True

        # Log the patch
        from mvp_site import logging_util

        logging_util.info(
            f"Applied clock skew patch: adjusting time by -{skew} seconds"
        )
        return True

    except ImportError:
        return False


def remove_clock_skew_patch() -> bool:
    """Remove the clock skew patch (restore original behavior).

    Returns:
        True if patch was removed, False if not applied.
    """
    global _original_utcnow, _patch_applied

    if not _patch_applied or _original_utcnow is None:
        return False

    try:
        from google.auth import _helpers

        _helpers.utcnow = _original_utcnow
        _patch_applied = False
        return True

    except ImportError:
        return False


class UseActualTime:
    """Context manager to temporarily use actual time (bypass clock skew patch).

    Use this when verifying incoming tokens that were issued at Google's actual time.

    Usage:
        with use_actual_time():
            decoded_token = auth.verify_id_token(id_token)
    """

    def __enter__(self):
        """Temporarily restore original utcnow function."""
        global _patch_applied
        self._was_patched = _patch_applied
        if _patch_applied and _original_utcnow is not None:
            try:
                from google.auth import _helpers

                _helpers.utcnow = _original_utcnow
            except ImportError:
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Re-apply the clock skew patch if it was active."""
        if self._was_patched and _original_utcnow is not None:
            try:
                from google.auth import _helpers

                _helpers.utcnow = _adjusted_utcnow
            except ImportError:
                pass
        return False  # Don't suppress exceptions
