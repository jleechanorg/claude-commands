"""
Tests for temporal correction loop to ensure player input preservation.

This test verifies that when the LLM generates a backward time jump,
the original player input is always preserved and saved to Firestore.

NOTE: Temporal corrections are currently DISABLED (MAX_TEMPORAL_CORRECTION_ATTEMPTS=0)
to reduce multiple LLM calls. This test verifies the core behavior still works:
- Original player input is preserved
- Backward time responses are accepted without retry
"""

from unittest.mock import MagicMock, patch

import pytest

from mvp_site import world_logic
from mvp_site.game_state import GameState
from mvp_site.llm_response import LLMResponse


@pytest.mark.asyncio
async def test_temporal_correction_preserves_original_user_input():
    """
    Verify that player input is preserved even when LLM generates backward time.

    With temporal corrections DISABLED (MAX_TEMPORAL_CORRECTION_ATTEMPTS=0):
    1. Player inputs: "Can I subjugate Tiamat?"
    2. LLM generates backward time (15:15 -> 15:00)
    3. System accepts the response (no retry) but logs a warning
    4. Original "Can I subjugate Tiamat?" must be saved to Firestore
    5. Only 1 LLM call is made (no correction retries)
    """
    # Setup
    user_id = "test_user_123"
    campaign_id = "test_campaign_456"
    original_player_input = "Can I subjugate Tiamat with an infernal contract?"

    # Mock game state with current time
    mock_game_state = MagicMock(spec=GameState)
    mock_game_state.world_data = {
        "world_time": {
            "year": 1492,
            "month": "Kythorn",
            "day": 1,
            "hour": 15,
            "minute": 15,
            "second": 0,
            "microsecond": 0,
        },
        "current_location_name": "Avernus (Tiamat's Lair)",
    }
    mock_game_state.to_dict.return_value = {"world_data": mock_game_state.world_data}
    mock_game_state.debug_mode = False

    # Mock first LLM response - backward time violation
    backward_response = MagicMock(spec=LLMResponse)
    backward_response.narrative_text = "Scene at Throne Room"
    backward_response.get_state_updates.return_value = {
        "world_data": {
            "world_time": {
                "year": 1492,
                "month": "Kythorn",
                "day": 1,
                "hour": 15,  # Same hour
                "minute": 0,  # Earlier minute - VIOLATION
                "second": 0,
                "microsecond": 0,
            },
            "current_location_name": "The High Hall (Throne Room)",
        }
    }

    # Mock second LLM response - corrected
    corrected_response = MagicMock(spec=LLMResponse)
    corrected_response.narrative_text = "Scene at Avernus continues"
    corrected_response.get_state_updates.return_value = {
        "world_data": {
            "world_time": {
                "year": 1492,
                "month": "Kythorn",
                "day": 1,
                "hour": 15,
                "minute": 20,  # Forward in time - CORRECT
                "second": 0,
                "microsecond": 0,
            },
            "current_location_name": "Avernus (Tiamat's Lair)",
        }
    }

    # Track what gets saved to Firestore
    saved_user_inputs: list[str] = []

    with (
        patch("mvp_site.world_logic.firestore_service") as mock_firestore,
        patch("mvp_site.world_logic.llm_service") as mock_llm,
        patch("mvp_site.world_logic.preventive_guards") as mock_guards,
    ):
        # Setup mocks
        mock_firestore.get_campaign_game_state.return_value = MagicMock(
            to_dict=lambda: mock_game_state.to_dict()
        )
        mock_firestore.get_campaign_by_id.return_value = (
            {"selected_prompts": [], "use_default_world": False},
            [],  # story_context
        )
        mock_firestore.get_user_settings.return_value = {}

        # With corrections disabled, LLM only returns backward time response (no retry)
        mock_llm.continue_story.return_value = backward_response

        # Preventive guards passthrough - uses backward_response since no correction happens
        mock_guards.enforce_preventive_guards.return_value = (
            backward_response.get_state_updates(),
            {},
        )

        # Capture add_story_entry calls
        def capture_story_entry(*args, **kwargs):
            if len(args) >= 4:
                actor = args[2]
                text = args[3]
                if actor == "user":
                    saved_user_inputs.append(text)

        mock_firestore.add_story_entry.side_effect = capture_story_entry
        mock_firestore.update_campaign_game_state.return_value = None

        # Execute
        request_data = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": original_player_input,
            "mode": "character",
        }

        # Need to patch asyncio.to_thread to execute synchronously in test
        async def mock_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("mvp_site.world_logic.get_user_settings", return_value={}),
            patch(
                "mvp_site.world_logic.asyncio.to_thread",
                side_effect=mock_to_thread,
            ),
        ):
            await world_logic.process_action_unified(request_data)

    # ASSERTIONS
    # 1. Should have saved exactly one user input (not multiple)
    assert len(saved_user_inputs) == 1, (
        f"Expected 1 user input saved, got {len(saved_user_inputs)}: {saved_user_inputs}"
    )

    # 2. The saved input must be the ORIGINAL player input
    saved_input = saved_user_inputs[0]
    assert saved_input == original_player_input, (
        f"FAIL: Player input was corrupted.\n"
        f"Expected: '{original_player_input}'\n"
        f"Got: '{saved_input}'\n"
        f"Bug: Correction prompt leaked into player history!"
    )

    # 3. The saved input must NOT contain correction prompt text
    assert "TEMPORAL VIOLATION" not in saved_input, (
        "FAIL: Correction prompt text leaked into saved player input!"
    )
    assert "REGENERATION REQUIRED" not in saved_input, (
        "FAIL: Correction prompt text leaked into saved player input!"
    )

    # 4. Verify LLM was called only ONCE (corrections disabled)
    assert mock_llm.continue_story.call_count == 1, (
        f"Expected 1 LLM call (corrections disabled), got {mock_llm.continue_story.call_count}"
    )

    # 5. Verify the single call received the ORIGINAL player input (not correction prompt)
    single_call_args = mock_llm.continue_story.call_args_list[0]
    # continue_story(user_input, mode, story_context, ...) - first positional arg is user_input
    call_input = single_call_args[0][0]
    assert call_input == original_player_input, (
        f"LLM should receive original player input, got: {call_input}"
    )
