import unittest


class TestProviderUtils(unittest.TestCase):
    def test_stringify_chat_parts(self):
        from mvp_site.llm_providers.provider_utils import stringify_chat_parts

        self.assertEqual(stringify_chat_parts([]), "")
        self.assertEqual(stringify_chat_parts(["a", "b"]), "a\n\nb")
        # Non-string should JSON-dump
        text = stringify_chat_parts([{"x": 1}])
        self.assertIn('"x"', text)

    def test_build_tool_results_prompt(self):
        from mvp_site.llm_providers.provider_utils import build_tool_results_prompt

        base = build_tool_results_prompt("- roll_dice({}): {\"total\": 1}")
        self.assertIn("Tool results", base)
        self.assertIn("Do NOT include tool_requests", base)

        with_extra = build_tool_results_prompt("X", extra_instructions="EXTRA")
        self.assertIn("EXTRA", with_extra)


if __name__ == "__main__":
    unittest.main()

