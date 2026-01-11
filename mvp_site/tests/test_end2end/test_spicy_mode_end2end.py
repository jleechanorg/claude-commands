"""End-to-end coverage for spicy mode toggle functionality.

Tests the complete flow of:
1. Enabling spicy mode (saves pre-spicy settings, switches to Grok on OpenRouter)
2. Disabling spicy mode (restores previous model/provider)
3. Settings persistence across enable/disable cycles
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["TESTING"] = "true"
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")


# Ensure both the repo root (for `infrastructure`) and mvp_site (for `main`) are importable
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MVP_SITE_ROOT = PROJECT_ROOT / "mvp_site"
for path in (PROJECT_ROOT, MVP_SITE_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from main import create_app  # noqa: E402

from mvp_site import constants  # noqa: E402
from tests.fake_firestore import FakeFirestoreClient  # noqa: E402

# Spicy mode constants (sourced from backend definitions)
SPICY_MODEL = constants.SPICY_OPENROUTER_MODEL
DEFAULT_GEMINI_MODEL = constants.DEFAULT_GEMINI_MODEL


class TestSpicyModeEndToEnd(unittest.TestCase):
    """Verify spicy mode toggle saves and restores model settings correctly."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "spicy-mode-e2e-user"

        # Stub auth and Firestore
        self._auth_patcher = patch(
            "main.auth.verify_id_token", return_value={"uid": self.test_user_id}
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        self.fake_firestore = FakeFirestoreClient()
        self._db_patcher = patch(
            "firestore_service.get_db", return_value=self.fake_firestore
        )
        self._db_patcher.start()
        self.addCleanup(self._db_patcher.stop)

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

    def test_enable_spicy_mode_switches_to_grok(self):
        """Enabling spicy mode should switch to Grok on OpenRouter."""
        # Get initial settings (should be default Gemini)
        initial_resp = self.client.get("/api/settings", headers=self.headers)
        assert initial_resp.status_code == 200
        initial_settings = json.loads(initial_resp.data)
        assert initial_settings["llm_provider"] == "gemini"

        # Enable spicy mode - this simulates what the frontend does
        enable_payload = {
            "spicy_mode": True,
            "pre_spicy_model": initial_settings.get(
                "gemini_model", DEFAULT_GEMINI_MODEL
            ),
            "pre_spicy_provider": initial_settings.get("llm_provider", "gemini"),
            "llm_provider": "openrouter",
            "openrouter_model": SPICY_MODEL,
        }
        enable_resp = self.client.post(
            "/api/settings", data=json.dumps(enable_payload), headers=self.headers
        )
        assert enable_resp.status_code == 200, f"Enable failed: {enable_resp.data}"

        # Verify settings were saved correctly
        verify_resp = self.client.get("/api/settings", headers=self.headers)
        verify_settings = json.loads(verify_resp.data)

        assert verify_settings["spicy_mode"] is True, "spicy_mode should be True"
        assert (
            verify_settings["llm_provider"] == "openrouter"
        ), "Provider should be openrouter"
        assert (
            verify_settings["openrouter_model"] == SPICY_MODEL
        ), f"Model should be {SPICY_MODEL}, got {verify_settings.get('openrouter_model')}"
        assert "pre_spicy_model" in verify_settings, "pre_spicy_model should be saved"
        assert (
            "pre_spicy_provider" in verify_settings
        ), "pre_spicy_provider should be saved"

    def test_disable_spicy_mode_restores_previous_model(self):
        """Disabling spicy mode should restore the previous model and provider."""
        # First, enable spicy mode with a known pre-spicy state
        enable_payload = {
            "spicy_mode": True,
            "pre_spicy_model": DEFAULT_GEMINI_MODEL,
            "pre_spicy_provider": "gemini",
            "llm_provider": "openrouter",
            "openrouter_model": SPICY_MODEL,
        }
        self.client.post(
            "/api/settings", data=json.dumps(enable_payload), headers=self.headers
        )

        # Verify spicy mode is enabled
        mid_resp = self.client.get("/api/settings", headers=self.headers)
        mid_settings = json.loads(mid_resp.data)
        assert mid_settings["spicy_mode"] is True
        assert mid_settings["llm_provider"] == "openrouter"

        # Now disable spicy mode - restore Gemini
        disable_payload = {
            "spicy_mode": False,
            "llm_provider": "gemini",
            "gemini_model": DEFAULT_GEMINI_MODEL,
        }
        disable_resp = self.client.post(
            "/api/settings", data=json.dumps(disable_payload), headers=self.headers
        )
        assert disable_resp.status_code == 200, f"Disable failed: {disable_resp.data}"

        # Verify settings were restored
        final_resp = self.client.get("/api/settings", headers=self.headers)
        final_settings = json.loads(final_resp.data)

        assert final_settings["spicy_mode"] is False, "spicy_mode should be False"
        assert (
            final_settings["llm_provider"] == "gemini"
        ), "Provider should be restored to gemini"
        assert (
            final_settings["gemini_model"] == DEFAULT_GEMINI_MODEL
        ), f"Model should be restored to {DEFAULT_GEMINI_MODEL}"

    def test_spicy_mode_preserves_openrouter_user_preference(self):
        """If user was already on OpenRouter, disabling spicy should restore that."""
        # Set initial state: user prefers OpenRouter with Llama
        initial_payload = {
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        }
        self.client.post(
            "/api/settings", data=json.dumps(initial_payload), headers=self.headers
        )

        # Enable spicy mode, saving the OpenRouter preference
        enable_payload = {
            "spicy_mode": True,
            "pre_spicy_model": "meta-llama/llama-3.1-70b-instruct",
            "pre_spicy_provider": "openrouter",
            "llm_provider": "openrouter",
            "openrouter_model": SPICY_MODEL,
        }
        self.client.post(
            "/api/settings", data=json.dumps(enable_payload), headers=self.headers
        )

        # Verify we're now on Grok
        mid_resp = self.client.get("/api/settings", headers=self.headers)
        mid_settings = json.loads(mid_resp.data)
        assert mid_settings["openrouter_model"] == SPICY_MODEL

        # Disable spicy mode - should restore Llama on OpenRouter
        disable_payload = {
            "spicy_mode": False,
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        }
        self.client.post(
            "/api/settings", data=json.dumps(disable_payload), headers=self.headers
        )

        # Verify restored to original OpenRouter model
        final_resp = self.client.get("/api/settings", headers=self.headers)
        final_settings = json.loads(final_resp.data)

        assert final_settings["spicy_mode"] is False
        assert final_settings["llm_provider"] == "openrouter"
        assert (
            final_settings["openrouter_model"] == "meta-llama/llama-3.1-70b-instruct"
        ), "Should restore user's original OpenRouter model preference"

    def test_spicy_mode_preserves_cerebras_user_preference(self):
        """If user was on Cerebras, disabling spicy should restore that."""

        # Set initial state: user prefers Cerebras
        initial_payload = {
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",
        }
        self.client.post(
            "/api/settings", data=json.dumps(initial_payload), headers=self.headers
        )

        # Enable spicy mode, saving the Cerebras preference
        enable_payload = {
            "spicy_mode": True,
            "pre_spicy_model": "llama-3.3-70b",
            "pre_spicy_provider": "cerebras",
            "llm_provider": "openrouter",
            "openrouter_model": SPICY_MODEL,
        }
        self.client.post(
            "/api/settings", data=json.dumps(enable_payload), headers=self.headers
        )

        # Disable spicy mode - should restore Cerebras
        disable_payload = {
            "spicy_mode": False,
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",
        }
        self.client.post(
            "/api/settings", data=json.dumps(disable_payload), headers=self.headers
        )

        # Verify restored to Cerebras
        final_resp = self.client.get("/api/settings", headers=self.headers)
        final_settings = json.loads(final_resp.data)

        assert final_settings["spicy_mode"] is False
        assert final_settings["llm_provider"] == "cerebras"
        assert final_settings["cerebras_model"] == "llama-3.3-70b"

    def test_spicy_mode_toggle_cycle(self):
        """Test multiple enable/disable cycles maintain consistency."""
        # Start with default Gemini
        initial_resp = self.client.get("/api/settings", headers=self.headers)
        initial_settings = json.loads(initial_resp.data)
        assert initial_settings["llm_provider"] == "gemini"

        # Cycle 1: Enable
        self.client.post(
            "/api/settings",
            data=json.dumps(
                {
                    "spicy_mode": True,
                    "pre_spicy_model": DEFAULT_GEMINI_MODEL,
                    "pre_spicy_provider": "gemini",
                    "llm_provider": "openrouter",
                    "openrouter_model": SPICY_MODEL,
                }
            ),
            headers=self.headers,
        )

        resp = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(resp.data)
        assert settings["spicy_mode"] is True
        assert settings["llm_provider"] == "openrouter"

        # Cycle 1: Disable
        self.client.post(
            "/api/settings",
            data=json.dumps(
                {
                    "spicy_mode": False,
                    "llm_provider": "gemini",
                    "gemini_model": DEFAULT_GEMINI_MODEL,
                }
            ),
            headers=self.headers,
        )

        resp = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(resp.data)
        assert settings["spicy_mode"] is False
        assert settings["llm_provider"] == "gemini"

        # Cycle 2: Enable again
        self.client.post(
            "/api/settings",
            data=json.dumps(
                {
                    "spicy_mode": True,
                    "pre_spicy_model": DEFAULT_GEMINI_MODEL,
                    "pre_spicy_provider": "gemini",
                    "llm_provider": "openrouter",
                    "openrouter_model": SPICY_MODEL,
                }
            ),
            headers=self.headers,
        )

        resp = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(resp.data)
        assert settings["spicy_mode"] is True
        assert settings["openrouter_model"] == SPICY_MODEL

        # Cycle 2: Disable again
        self.client.post(
            "/api/settings",
            data=json.dumps(
                {
                    "spicy_mode": False,
                    "llm_provider": "gemini",
                    "gemini_model": DEFAULT_GEMINI_MODEL,
                }
            ),
            headers=self.headers,
        )

        final_resp = self.client.get("/api/settings", headers=self.headers)
        final_settings = json.loads(final_resp.data)
        assert final_settings["spicy_mode"] is False
        assert final_settings["llm_provider"] == "gemini"
        assert final_settings["gemini_model"] == DEFAULT_GEMINI_MODEL


class TestSpicyModeSettingsValidation(unittest.TestCase):
    """Verify that spicy mode settings are properly validated."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "spicy-validation-user"

        self._auth_patcher = patch(
            "main.auth.verify_id_token", return_value={"uid": self.test_user_id}
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        self.fake_firestore = FakeFirestoreClient()
        self._db_patcher = patch(
            "firestore_service.get_db", return_value=self.fake_firestore
        )
        self._db_patcher.start()
        self.addCleanup(self._db_patcher.stop)

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

    def test_spicy_mode_accepts_boolean_true(self):
        """spicy_mode=True should be accepted."""
        resp = self.client.post(
            "/api/settings",
            data=json.dumps({"spicy_mode": True}),
            headers=self.headers,
        )
        assert resp.status_code == 200

        verify = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(verify.data)
        assert settings["spicy_mode"] is True

    def test_spicy_mode_accepts_boolean_false(self):
        """spicy_mode=False should be accepted."""
        # First set to true
        self.client.post(
            "/api/settings",
            data=json.dumps({"spicy_mode": True}),
            headers=self.headers,
        )

        # Then set to false
        resp = self.client.post(
            "/api/settings",
            data=json.dumps({"spicy_mode": False}),
            headers=self.headers,
        )
        assert resp.status_code == 200

        verify = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(verify.data)
        assert settings["spicy_mode"] is False

    def test_pre_spicy_settings_are_persisted(self):
        """pre_spicy_model and pre_spicy_provider should be saved."""
        payload = {
            "spicy_mode": True,
            "pre_spicy_model": "custom-model",
            "pre_spicy_provider": "cerebras",
        }
        resp = self.client.post(
            "/api/settings",
            data=json.dumps(payload),
            headers=self.headers,
        )
        assert resp.status_code == 200

        verify = self.client.get("/api/settings", headers=self.headers)
        settings = json.loads(verify.data)
        assert settings["pre_spicy_model"] == "custom-model"
        assert settings["pre_spicy_provider"] == "cerebras"


if __name__ == "__main__":
    unittest.main()
