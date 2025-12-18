
import os
import unittest
from unittest.mock import MagicMock
from mvp_site import constants
from mvp_site.game_state import GameState
from mvp_site.llm_service import _truncate_context, estimate_tokens

class TestTruncationBug(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "true"
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_game_state.custom_campaign_state = {}
        self.mock_game_state.world_data = {}
        self.mock_game_state.to_dict.return_value = {}
        self.mock_game_state.combat_state = {"in_combat": False}

    def test_recursive_truncation_bug(self):
        """
        Verify if the first hard-trim loop violently over-truncates due to recursive trimming.
        
        Scenario:
        - 2 turns.
        - Total chars: 2000 (approx 500 tokens).
        - Budget: 450 tokens.
        - Iter 1: Ratio ~0.9. Result ~450.
        - Force Iter 2: If we set budget slightly non-fitting, it triggers Iter 2.
        """
        # Create text that is just slightly larger than budget
        # 1000 chars is approx 250 tokens per turn. Total 500 tokens.
        text_len = 2000 
        story_context = [
            {"actor": "user", "text": "x" * text_len},
            {"actor": "gemini", "text": "x" * text_len},
        ]
        
        # Total approx 4000 chars = 1000 tokens.
        # We want budget to be ~900 tokens. So 3600 chars.
        # But we need to ensure it DOESN'T fit in the first iteration to trigger the bug.
        # Iter 1: ratio = 3600 / 4000 = 0.9.
        # New length = 4000 * 0.9 = 3600.
        # If we make the budget slightly smaller than what the ratio produces due to overhead...
        
        # Let's say max_chars = 3600.
        # estimate_tokens(" " * 3600) -> 900 tokens.
        # We need a case where the ratio calculation produces slightly > 900 tokens.
        
        # Let's simple use a large enough iterations count or trick it.
        # Or just rely on the fact that if it fails once, it spirals.
        
        max_chars = 3000 # ~750 tokens. 
        # Original: 1000 tokens. Ratio 0.75.
        # Iter 1: Reduces to 750. 
        # If this fits exactly, we exit.
        
        # We need to craft a scenario where it barely misses.
        # Maybe use the mock token counter or just real one?
        # Real estimate_tokens is len/4 usually.
        
        # Lets try:
        # 1000 tokens input.
        # Budget 900.
        # Ratio 0.9.
        # Reduced to 900.
        # If 900 > budget (e.g. budget was 899).
        # Iter 2: Ratio 0.9 * 0.7 = 0.63.
        # Applied to *already reduced* (900): 900 * 0.63 = 567.
        # Expected if bug wasn't there: Original(1000) * 0.63 = 630.
        # Wait, if we use original, we apply 0.63 to 1000 = 630.
        # If we use reduced, we apply 0.63 to 900 = 567.
        # 630 vs 567. 
        # Difference 63 tokens. 
        
        # This is measurable.
        
        max_chars = 4000 # Budget ~1000 tokens
        # Input: 2000 tokens (8000 chars)
        story_context = [
             {"actor": "user", "text": "x" * 8000}
        ]
        # Total 2000 tokens.
        # Ratio = 1000 / 2000 = 0.5.
        # Iter 1: 2000 -> 1000.
        # Suppose overhead makes it 1001.
        # Iter 2: Ratio 0.5 * 0.7 = 0.35.
        # Buggy: 1000 * 0.35 = 350.
        # Correct: 2000 * 0.35 = 700.
        # 700 vs 350. HUGE difference.
        
        # Triggering the "bit more than budget" is tricky with `estimate_tokens` being linear.
        # But we can force it by adding a system message or something that adds tokens but isn't trimmed?
        # No, the loop trims everything.
        
        # Let's manually fail the first check by using a slightly tighter budget?
        # Actually, `estimate_tokens` is usually `len(text) // 4`.
        # int(len * ratio) // 4.
        # if ratio = 0.5. len=8000. new_len=4000. tokens=1000.
        # if budget was 999. 1000 > 999. Fails.
        # Iter 2: ratio 0.35.
        # Buggy: 4000 * 0.35 = 1400 chars -> 350 tokens.
        # Correct: 8000 * 0.35 = 2800 chars -> 700 tokens.
        # We expect Result < 400 tokens if bug exists.
        # We expect Result ~700 tokens if bug fixed.
        
        max_chars = 3996 # ~999 tokens.
        
        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
            # Force small keep so we don't depend on adaptive part?
            # actually we want to trigger the "Few turns" check L2214.
            turns_to_keep_at_start=1,
            turns_to_keep_at_end=0
        )
        
        result_text = result[0]['text']
        result_tokens = estimate_tokens(result_text)
        
        print(f"Result tokens: {result_tokens}")
        # With bug: ~350
        # Without bug: ~700
        # Budget: ~999
        
        # If result is way below budget (e.g. < 500), it's the bug.
        self.assertGreater(result_tokens, 600, f"Over-truncated! Got {result_tokens} for budget ~1000")

if __name__ == "__main__":
    unittest.main()
