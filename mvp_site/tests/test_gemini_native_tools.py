from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestGeminiNativeTools(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test")

    @patch("mvp_site.llm_providers.gemini_provider.get_client")
    def test_native_tools_does_not_force_tool_calling(self, mock_get_client: MagicMock):
        """Gemini native-tools path should not force at least one tool call."""
        from mvp_site.llm_providers import gemini_provider

        client = MagicMock()
        mock_get_client.return_value = client

        # Return a response that includes no function calls (narrative-only)
        response1 = SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="No dice needed.")]
                    )
                )
            ]
        )
        client.models.generate_content.return_value = response1

        with patch(
            "mvp_site.llm_providers.gemini_provider.generate_json_mode_content"
        ) as mock_json:
            mock_json.return_value = SimpleNamespace(text='{"narrative":"ok"}')

            gemini_provider.generate_content_with_native_tools(
                prompt_contents=["Describe the room."],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        # Capture config passed to Phase 1 call
        _args, kwargs = client.models.generate_content.call_args
        config = kwargs["config"]
        assert config.tool_config is not None
        assert config.tool_config.function_calling_config is not None
        assert config.tool_config.function_calling_config.mode == "AUTO", (
            "Should not use mode='ANY' (forced tool calling)"
        )

    @patch("mvp_site.llm_providers.gemini_provider.get_client")
    def test_native_tools_no_function_calls_still_returns_json(
        self, mock_get_client: MagicMock
    ):
        """No-roll turns should still produce a valid JSON response via Phase 2."""
        from mvp_site.llm_providers import gemini_provider

        client = MagicMock()
        mock_get_client.return_value = client

        # Phase 1 response: no function calls, but some text
        response1 = SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="Some narrative.")]
                    )
                )
            ]
        )
        client.models.generate_content.return_value = response1

        with patch(
            "mvp_site.llm_providers.gemini_provider.generate_json_mode_content"
        ) as mock_json:
            mock_json.return_value = SimpleNamespace(text='{"narrative":"ok"}')

            out = gemini_provider.generate_content_with_native_tools(
                prompt_contents=["Describe the room."],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        assert out.text == '{"narrative":"ok"}'
        assert mock_json.called, (
            "Phase 2 JSON call should happen when no function_calls"
        )
