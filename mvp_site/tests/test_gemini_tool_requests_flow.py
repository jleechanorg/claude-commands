from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class TestGeminiToolRequestsFlow(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test")

    def test_tool_requests_flow_runs_phase2_when_needed(self):
        from mvp_site.llm_providers import gemini_provider

        response1 = SimpleNamespace(
            text='{"tool_requests":[{"tool":"roll_dice","args":{"notation":"1d20"}}]}'
        )
        response2 = SimpleNamespace(text='{"narrative":"ok"}')

        with patch(
            "mvp_site.llm_providers.gemini_provider.generate_json_mode_content"
        ) as mock_json, patch(
            "mvp_site.llm_providers.gemini_provider.execute_tool_requests"
        ) as mock_exec, patch(
            "mvp_site.llm_providers.gemini_provider.format_tool_results_text"
        ) as mock_format:
            mock_json.side_effect = [response1, response2]
            mock_exec.return_value = [
                {
                    "tool": "roll_dice",
                    "args": {"notation": "1d20"},
                    "result": {"total": 7},
                }
            ]
            mock_format.return_value = "- roll_dice({\"notation\":\"1d20\"}): {\"total\": 7}"

            out = gemini_provider.generate_content_with_tool_requests(
                prompt_contents=["hi"],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        assert out.text == '{"narrative":"ok"}'
        assert mock_json.call_count == 2
        assert mock_exec.called

    def test_tool_requests_flow_returns_phase1_when_none_present(self):
        from mvp_site.llm_providers import gemini_provider

        response1 = SimpleNamespace(text='{"narrative":"ok"}')

        with patch(
            "mvp_site.llm_providers.gemini_provider.generate_json_mode_content"
        ) as mock_json, patch(
            "mvp_site.llm_providers.gemini_provider.execute_tool_requests"
        ) as mock_exec:
            mock_json.return_value = response1

            out = gemini_provider.generate_content_with_tool_requests(
                prompt_contents=["hi"],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        assert out.text == '{"narrative":"ok"}'
        assert mock_json.call_count == 1
        assert not mock_exec.called

