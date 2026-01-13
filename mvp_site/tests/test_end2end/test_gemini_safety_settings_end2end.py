"""End-to-end test to verify Gemini safety settings application."""

import unittest
from unittest.mock import MagicMock, patch
import os

from mvp_site import constants, llm_service
from mvp_site.game_state import GameState
from mvp_site.custom_types import UserId

class TestGeminiSafetySettingsEndToEnd(unittest.TestCase):
    def setUp(self):
        # Disable MOCK_SERVICES_MODE to allow patching generate_content
        self._original_mock_mode = os.environ.get("MOCK_SERVICES_MODE")
        os.environ["MOCK_SERVICES_MODE"] = "false"
        
        self.mock_client = MagicMock()
        self.mock_models = MagicMock()
        self.mock_client.models = self.mock_models
        
        # Patch get_client in gemini_provider
        self.client_patcher = patch(
            "mvp_site.llm_providers.gemini_provider.get_client",
            return_value=self.mock_client
        )
        self.client_patcher.start()

    def tearDown(self):
        self.client_patcher.stop()
        # Restore original MOCK_SERVICES_MODE
        if self._original_mock_mode is not None:
            os.environ["MOCK_SERVICES_MODE"] = self._original_mock_mode
        else:
            os.environ.pop("MOCK_SERVICES_MODE", None)

    def test_safety_settings_passed_correctly(self):
        """Verify safety_settings are passed inside GenerateContentConfig (not as top-level arg)."""
        
        # Mock response to avoid downstream errors
        mock_response = MagicMock()
        mock_response.text = '{"narrative": "test"}'
        self.mock_models.generate_content.return_value = mock_response

        # Call llm_service.continue_story (which calls gemini_provider)
        # We need to ensure it selects Gemini
        with patch("mvp_site.llm_service._select_provider_and_model") as mock_select:
            mock_select.return_value.provider = constants.LLM_PROVIDER_GEMINI
            mock_select.return_value.model = constants.DEFAULT_GEMINI_MODEL
            
            llm_service.continue_story(
                user_input="test input",
                mode="action",
                story_context=[],
                current_game_state=GameState(),
                user_id=UserId("test_user")
            )

        # Verification
        call_args = self.mock_models.generate_content.call_args
        assert call_args is not None, "generate_content was not called"
        
        kwargs = call_args.kwargs
        
        # 1. safety_settings should NOT be a top-level argument (SDK doesn't accept it)
        if "safety_settings" in kwargs:
             self.fail("safety_settings should NOT be a top-level argument! SDK only accepts model, contents, config.")
             
        # 2. safety_settings MUST be in config (correct way per SDK docs)
        config = kwargs.get("config")
        if not config:
            self.fail("config is missing from generate_content call")
        
        # Verify safety_settings are in the config object
        if not hasattr(config, "safety_settings") or config.safety_settings is None:
            self.fail("safety_settings MISSING from GenerateContentConfig! They must be passed inside the config object.")

        print("✅ Test passed: safety_settings found in GenerateContentConfig (correct location)")

if __name__ == "__main__":
    unittest.main()
