"""
Tests for clock skew settings and deployment validation.

The clock skew is now hardcoded to 720 seconds (12 minutes) for all environments.
This compensates for local clock being ahead of Google's servers.

The validation still checks:
1. FAIL if WORLDAI_GOOGLE_APPLICATION_CREDENTIALS set without WORLDAI_DEV_MODE=true
2. PASS if both WORLDAI_GOOGLE_APPLICATION_CREDENTIALS and WORLDAI_DEV_MODE=true are set
3. PASS if neither is set (production behavior)
"""

import os
from unittest.mock import patch

import pytest


class TestClockSkewDeploymentValidation:
    """Tests for deployment validation of clock skew credentials."""

    def test_worldai_creds_without_dev_mode_raises_error(self):
        """
        WORLDAI_GOOGLE_APPLICATION_CREDENTIALS without WORLDAI_DEV_MODE
        should raise ValueError to prevent accidental production use.
        """
        from mvp_site.clock_skew_credentials import validate_deployment_config

        env_vars = {
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Remove WORLDAI_DEV_MODE and TESTING_AUTH_BYPASS if they exist
            os.environ.pop("WORLDAI_DEV_MODE", None)
            os.environ.pop("TESTING_AUTH_BYPASS", None)

            with pytest.raises(
                ValueError,
                match="WORLDAI_GOOGLE_APPLICATION_CREDENTIALS requires WORLDAI_DEV_MODE=true",
            ):
                validate_deployment_config()

    def test_worldai_creds_with_dev_mode_true_allowed(self):
        """
        WORLDAI_GOOGLE_APPLICATION_CREDENTIALS with WORLDAI_DEV_MODE=true
        should be allowed (explicit acknowledgment of dev mode).
        """
        from mvp_site.clock_skew_credentials import validate_deployment_config

        env_vars = {
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json",
            "WORLDAI_DEV_MODE": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            os.environ.pop("TESTING_AUTH_BYPASS", None)
            # Should not raise - dev mode explicitly acknowledged
            result = validate_deployment_config()
            assert result is True  # Returns True for dev mode

    def test_no_worldai_vars_production_mode(self):
        """
        No WORLDAI_* variables = production mode.
        Should pass validation and return False (not dev mode).
        """
        from mvp_site.clock_skew_credentials import validate_deployment_config

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", None)
            os.environ.pop("WORLDAI_DEV_MODE", None)
            os.environ.pop("TESTING_AUTH_BYPASS", None)

            # Should not raise - production mode
            result = validate_deployment_config()
            assert result is False  # Returns False for production mode

    def test_dev_mode_without_creds_allowed(self):
        """
        WORLDAI_DEV_MODE=true without credentials is allowed.
        """
        from mvp_site.clock_skew_credentials import validate_deployment_config

        env_vars = {
            "WORLDAI_DEV_MODE": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            os.environ.pop("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", None)
            os.environ.pop("TESTING_AUTH_BYPASS", None)

            # Should not raise
            result = validate_deployment_config()
            assert result is True  # Dev mode flag set

    def test_clock_skew_always_returns_720(self):
        """
        get_clock_skew_seconds() always returns 720 (12 minutes).
        This is hardcoded and no longer depends on environment.
        """
        from mvp_site.clock_skew_credentials import (
            CLOCK_SKEW_SECONDS,
            get_clock_skew_seconds,
        )

        # Hardcoded constant should be 720
        assert CLOCK_SKEW_SECONDS == 720

        # Function should return 720 regardless of environment
        skew = get_clock_skew_seconds()
        assert skew == 720

    def test_clock_skew_in_testing_mode(self):
        """
        Clock skew returns 720 even in testing mode (TESTING_AUTH_BYPASS=true).
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {"TESTING_AUTH_BYPASS": "true"}

        with patch.dict(os.environ, env_vars, clear=False):
            os.environ.pop("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", None)
            os.environ.pop("WORLDAI_DEV_MODE", None)

            skew = get_clock_skew_seconds()
            assert skew == 720

    def test_clock_skew_in_dev_mode(self):
        """
        Clock skew returns 720 in dev mode.
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {"WORLDAI_DEV_MODE": "true"}

        with patch.dict(os.environ, env_vars, clear=False):
            os.environ.pop("TESTING_AUTH_BYPASS", None)

            skew = get_clock_skew_seconds()
            assert skew == 720


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
