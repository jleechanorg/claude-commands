import unittest

from mvp_site import constants, llm_service


class TestContextBudgeting(unittest.TestCase):
    def test_safe_budget_uses_ratio_for_qwen(self):
        model = "meta-llama/llama-3.1-70b-instruct"
        expected_tokens = int(
            constants.MODEL_CONTEXT_WINDOW_TOKENS[model]
            * constants.CONTEXT_WINDOW_SAFETY_RATIO
        )
        assert (
            llm_service._get_safe_context_token_budget(
                constants.LLM_PROVIDER_OPENROUTER, model
            )
            == expected_tokens
        )

    def test_safe_budget_falls_back_for_unknown_model(self):
        fallback_expected = int(
            constants.DEFAULT_CONTEXT_WINDOW_TOKENS
            * constants.CONTEXT_WINDOW_SAFETY_RATIO
        )
        assert (
            llm_service._get_safe_context_token_budget("unknown", "mystery-model")
            == fallback_expected
        )


if __name__ == "__main__":
    unittest.main()
