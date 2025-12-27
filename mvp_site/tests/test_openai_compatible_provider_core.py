from __future__ import annotations

import unittest
from unittest.mock import patch

from mvp_site.llm_providers.openai_compatible_provider_core import (
    generate_openai_compatible_content,
)


class TestOpenAICompatibleProviderCore(unittest.TestCase):
    def test_generates_payload_with_response_format_when_no_tools(self):
        seen = {}

        def fake_post(
            *, url, headers, payload, timeout, logger=None, error_log_prefix=""
        ):
            seen["url"] = url
            seen["headers"] = headers
            seen["payload"] = payload
            return {"choices": [{"message": {"content": '{"narrative":"ok"}'}}]}

        with patch(
            "mvp_site.llm_providers.openai_compatible_provider_core.post_chat_completions",
            new=fake_post,
        ):
            text, raw = generate_openai_compatible_content(
                url="http://x",
                headers={"a": "b"},
                model_name="m",
                prompt_contents=["hi"],
                system_instruction_text="sys",
                temperature=0.0,
                max_output_tokens=10,
                stringify_chat_parts_fn=lambda parts: "\n\n".join(parts),
                tools=None,
                response_format={"type": "json_object"},
            )

        self.assertEqual(text, '{"narrative":"ok"}')
        self.assertIn("response_format", seen["payload"])
        self.assertNotIn("tools", seen["payload"])
        self.assertEqual(raw["choices"][0]["message"]["content"], '{"narrative":"ok"}')

    def test_generates_payload_with_tools_and_tool_choice(self):
        seen = {}

        def fake_post(
            *, url, headers, payload, timeout, logger=None, error_log_prefix=""
        ):
            seen["payload"] = payload
            return {
                "choices": [{"message": {"content": None, "tool_calls": [{"id": "1"}]}}]
            }

        with patch(
            "mvp_site.llm_providers.openai_compatible_provider_core.post_chat_completions",
            new=fake_post,
        ):
            text, _raw = generate_openai_compatible_content(
                url="http://x",
                headers={"a": "b"},
                model_name="m",
                prompt_contents=["hi"],
                system_instruction_text=None,
                temperature=0.0,
                max_output_tokens=10,
                stringify_chat_parts_fn=lambda parts: "\n\n".join(parts),
                tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                tool_choice="required",
                response_format={"type": "json_object"},
            )

        # Content can be absent if tool_calls exist
        self.assertEqual(text, "")
        self.assertIn("tools", seen["payload"])
        self.assertIn("tool_choice", seen["payload"])
        self.assertNotIn("response_format", seen["payload"])

    def test_raises_when_no_content_and_no_tool_calls(self):
        def fake_post(
            *, url, headers, payload, timeout, logger=None, error_log_prefix=""
        ):
            return {"choices": [{"message": {"content": None}}]}

        with patch(
            "mvp_site.llm_providers.openai_compatible_provider_core.post_chat_completions",
            new=fake_post,
        ):
            with self.assertRaises(ValueError):
                generate_openai_compatible_content(
                    url="http://x",
                    headers={"a": "b"},
                    model_name="m",
                    prompt_contents=["hi"],
                    system_instruction_text=None,
                    temperature=0.0,
                    max_output_tokens=10,
                    stringify_chat_parts_fn=lambda parts: "\n\n".join(parts),
                    tools=None,
                    response_format={"type": "json_object"},
                )

    def test_custom_validator_can_override_default(self):
        def fake_post(
            *, url, headers, payload, timeout, logger=None, error_log_prefix=""
        ):
            return {
                "choices": [{"message": {"content": None}}],
                "usage": {"prompt_tokens": 1},
            }

        def validator(_data, _message, _raw_text, _tool_calls):
            # Allow missing content (provider will handle it elsewhere)
            return None

        with patch(
            "mvp_site.llm_providers.openai_compatible_provider_core.post_chat_completions",
            new=fake_post,
        ):
            text, _raw = generate_openai_compatible_content(
                url="http://x",
                headers={"a": "b"},
                model_name="m",
                prompt_contents=["hi"],
                system_instruction_text=None,
                temperature=0.0,
                max_output_tokens=10,
                stringify_chat_parts_fn=lambda parts: "\n\n".join(parts),
                tools=None,
                response_format={"type": "json_object"},
                validate_response_fn=validator,
            )
        self.assertEqual(text, "")
