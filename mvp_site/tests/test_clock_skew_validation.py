"""
RED PHASE: Tests for deployment validation of clock skew settings.

These tests verify that WORLDAI_* environment variables require explicit
dev mode acknowledgment to prevent accidental use in production.

The validation should:
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
        RED TEST: WORLDAI_GOOGLE_APPLICATION_CREDENTIALS without WORLDAI_DEV_MODE
        should raise ConfigurationError to prevent accidental production use.

        This test should FAIL initially because validation doesn't exist yet.
        """
        from mvp_site.clock_skew_credentials import validate_deployment_config

        env_vars = {
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Remove WORLDAI_DEV_MODE if it exists
            os.environ.pop("WORLDAI_DEV_MODE", None)
            os.environ.pop("TESTING", None)

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

        with patch.dict(os.environ, env_vars, clear=True):
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

        with patch.dict(os.environ, env_vars, clear=True):
            os.environ.pop("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", None)
            os.environ.pop("TESTING", None)

            # Should not raise
            result = validate_deployment_config()
            assert result is True  # Dev mode flag set

    def test_get_clock_skew_validates_config(self):
        """
        get_clock_skew_seconds() should call validate_deployment_config()
        to ensure config is valid before returning skew value.
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            os.environ.pop("WORLDAI_DEV_MODE", None)
            os.environ.pop("TESTING", None)

            # Should raise because validation fails
            with pytest.raises(
                ValueError,
                match="WORLDAI_GOOGLE_APPLICATION_CREDENTIALS requires WORLDAI_DEV_MODE=true",
            ):
                get_clock_skew_seconds()

    def test_clock_skew_returns_600_with_valid_dev_config(self):
        """
        get_clock_skew_seconds() returns 600 when properly configured for dev.
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json",
            "WORLDAI_DEV_MODE": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            skew = get_clock_skew_seconds()
            assert skew == 600  # Default dev skew

    def test_clock_skew_returns_600_when_testing_true(self):
        """
        get_clock_skew_seconds() returns 600 when TESTING=true is set alone.
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {
            "TESTING": "true",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("os.stat", side_effect=FileNotFoundError),
        ):
            skew = get_clock_skew_seconds()
            assert skew == 600

    def test_clock_skew_returns_0_in_production(self):
        """
        get_clock_skew_seconds() returns 0 in production mode.
        """
        from mvp_site.clock_skew_credentials import get_clock_skew_seconds

        env_vars = {}

        with patch.dict(os.environ, env_vars, clear=True):
            skew = get_clock_skew_seconds()
            assert skew == 0  # No skew in production


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
