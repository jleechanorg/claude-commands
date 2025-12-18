"""End-to-end coverage for provider-aware settings persistence."""

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


import constants  # noqa: E402
from main import create_app  # noqa: E402
from tests.fake_firestore import FakeFirestoreClient  # noqa: E402


class TestLLMProviderSettingsEndToEnd(unittest.TestCase):
    """Verify that settings API round-trips both Gemini and OpenRouter providers."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "provider-e2e-user"

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

    def test_round_trips_openrouter_and_gemini_preferences(self):
        # Initial fetch should include default Gemini provider
        response = self.client.get("/api/settings", headers=self.headers)
        assert response.status_code == 200
        payload = json.loads(response.data)
        assert payload["llm_provider"] == "gemini"
        assert payload["gemini_model"] == constants.DEFAULT_GEMINI_MODEL

        # Switch to OpenRouter and persist
        update_payload = {
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        }
        update_resp = self.client.post(
            "/api/settings", data=json.dumps(update_payload), headers=self.headers
        )
        assert update_resp.status_code == 200

        # Fetch again to verify provider + model persisted
        reread = self.client.get("/api/settings", headers=self.headers)
        reread_payload = json.loads(reread.data)
        assert reread_payload["llm_provider"] == "openrouter"
        assert reread_payload["openrouter_model"] == "meta-llama/llama-3.1-70b-instruct"

        # Switch to Cerebras and persist
        cerebras_payload = {
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
        }
        cerebras_resp = self.client.post(
            "/api/settings", data=json.dumps(cerebras_payload), headers=self.headers
        )
        assert cerebras_resp.status_code == 200

        cerebras_read = self.client.get("/api/settings", headers=self.headers)
        cerebras_payload_read = json.loads(cerebras_read.data)
        assert cerebras_payload_read["llm_provider"] == "cerebras"
        assert cerebras_payload_read["cerebras_model"] == "llama-3.3-70b"

        # Switch back to Gemini and ensure round-trip
        revert_payload = {
            "llm_provider": "gemini",
            "gemini_model": constants.DEFAULT_GEMINI_MODEL,
        }
        revert_resp = self.client.post(
            "/api/settings", data=json.dumps(revert_payload), headers=self.headers
        )
        assert revert_resp.status_code == 200

        final_read = self.client.get("/api/settings", headers=self.headers)
        final_payload = json.loads(final_read.data)
        assert final_payload["llm_provider"] == "gemini"
        assert final_payload["gemini_model"] == constants.DEFAULT_GEMINI_MODEL


if __name__ == "__main__":
    unittest.main()
