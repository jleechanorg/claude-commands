from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from mvp_site.llm_providers.openai_chat_common import (
    build_messages,
    extract_tool_calls,
    post_chat_completions,
)


class TestOpenAIChatCommon(unittest.TestCase):
    def test_build_messages_includes_system_and_user(self):
        messages = build_messages(
            prompt_contents=["hello"],
            system_instruction_text="system",
            stringify_chat_parts_fn=lambda parts: " ".join(parts),
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "hello")

    def test_build_messages_omits_system_when_none(self):
        messages = build_messages(
            prompt_contents=["hello"],
            system_instruction_text=None,
            stringify_chat_parts_fn=lambda parts: " ".join(parts),
        )
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")

    def test_extract_tool_calls_none_for_missing(self):
        self.assertIsNone(extract_tool_calls({}))
        self.assertIsNone(extract_tool_calls({"choices": []}))
        self.assertIsNone(extract_tool_calls({"choices": [{"message": {"content": "x"}}]}))

    def test_extract_tool_calls_returns_list(self):
        raw = {"choices": [{"message": {"tool_calls": [{"id": "1"}]}}]}
        self.assertEqual(extract_tool_calls(raw), [{"id": "1"}])

    def test_post_chat_completions_posts_and_returns_json(self):
        fake_response = Mock()
        fake_response.ok = True
        fake_response.json.return_value = {"choices": []}
        fake_response.raise_for_status.return_value = None

        with patch("mvp_site.llm_providers.openai_chat_common.requests.post") as post:
            post.return_value = fake_response
            data = post_chat_completions(
                url="http://example",
                headers={"h": "v"},
                payload={"x": 1},
                timeout=1,
            )

        self.assertEqual(data, {"choices": []})
        post.assert_called_once()
        fake_response.raise_for_status.assert_called_once()

