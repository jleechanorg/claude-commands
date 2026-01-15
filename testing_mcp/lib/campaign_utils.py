"""Campaign management utilities for MCP tests.

This module provides high-level utilities for creating campaigns and processing
actions via the MCP server. It includes automatic invariant validation that
runs on every response without requiring test code changes.

Automatic Validation:
    - Structural invariants (required keys, schema stability)
    - Living world checks (on turns divisible by the configured interval)
    - Combat state validation (when in_combat is true)
    - God mode directive persistence

Configuration via environment variables:
    - MCP_INVARIANT_CHECK: Set to "0" or "false" to disable (default: enabled)
    - MCP_INVARIANT_STRICT: Set to "1" or "true" to raise on breaking changes

Results are attached to responses as:
    - response["_invariant_validation"]: Dict with validation results
    - response["_invariant_violations"]: List of violation strings (if any)
"""

from __future__ import annotations

import json
import os
from typing import Any

from .mcp_client import MCPClient
from .regression_oracle import DifferenceClass, InvariantChecker

# Configuration
_INVARIANT_CHECK_ENABLED = os.getenv("MCP_INVARIANT_CHECK", "1").lower() not in (
    "0",
    "false",
    "no",
)
_INVARIANT_STRICT_MODE = os.getenv("MCP_INVARIANT_STRICT", "0").lower() in (
    "1",
    "true",
    "yes",
)

# Track turn counts per campaign for living world validation
_campaign_turn_counts: dict[str, int] = {}
# Track whether god mode directives have ever been present per campaign
_campaign_god_mode_expected: dict[str, bool] = {}

# Shared invariant checker instance
_invariant_checker = InvariantChecker()


def create_campaign(
    client: MCPClient,
    user_id: str,
    *,
    title: str = "MCP Test Campaign",
    character: str = "Aric the Fighter (STR 16)",
    setting: str = "A roadside ambush outside Phandalin",
    description: str = "Test campaign for MCP validation",
    selected_prompts: list[str] | None = None,
) -> str:
    """Create a campaign and return its ID.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        title: Campaign title.
        character: Character description.
        setting: Setting description.
        description: Campaign description.
        selected_prompts: List of prompt types to load (e.g., ["narrative", "mechanics"]).

    Returns:
        Campaign ID string.

    Raises:
        RuntimeError: If campaign creation fails.
    """
    args = {
        "user_id": user_id,
        "title": title,
        "character": character,
        "setting": setting,
        "description": description,
    }

    if selected_prompts is not None:
        args["selected_prompts"] = selected_prompts

    payload = client.tools_call("create_campaign", args)
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise RuntimeError(f"create_campaign returned unexpected payload: {payload}")
    return campaign_id


def process_action(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    user_input: str,
    mode: str = "character",
    include_raw_llm_payloads: bool | None = None,
    track_turn: bool = True,
) -> dict[str, Any]:
    """Process a player action in a campaign.

    This function automatically validates the response against invariants
    and attaches validation results. To disable, set MCP_INVARIANT_CHECK=0.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        user_input: Player action text.
        mode: Interaction mode (default: "character").
        include_raw_llm_payloads: Whether to include raw LLM payloads in response.
        track_turn: When False, do not advance turn counters or run invariant
            validation (useful for administrative seeding actions).

    Notes:
        include_raw_llm_payloads defaults to TESTING_MCP_INCLUDE_RAW_LLM=true.

    Returns:
        Response dict from server with added keys:
        - _invariant_validation: Validation summary dict (when tracking turns)
        - _invariant_violations: List of violation strings (if any, when tracking turns)
        - _turn_number: Current turn number for this campaign (when tracking turns)

    Raises:
        AssertionError: If MCP_INVARIANT_STRICT=1 and breaking changes detected.
    """
    if include_raw_llm_payloads is None:
        include_raw_llm_payloads = (
            os.getenv("TESTING_MCP_INCLUDE_RAW_LLM", "true").lower() == "true"
        )

    current_turn = _campaign_turn_counts.get(campaign_id, 0)

    payload = {
        "user_id": user_id,
        "campaign_id": campaign_id,
        "user_input": user_input,
        "mode": mode,
    }
    if include_raw_llm_payloads:
        payload["include_raw_llm_payloads"] = True
    response = client.tools_call("process_action", payload)

    if track_turn:
        turn_number = current_turn + 1
        _campaign_turn_counts[campaign_id] = turn_number

        # Attach turn number
        response["_turn_number"] = turn_number

        # Run automatic invariant validation if enabled
        if _INVARIANT_CHECK_ENABLED:
            response = _validate_response(response, turn_number, mode, campaign_id)

    return response


def _validate_response(
    response: dict[str, Any],
    turn_number: int,
    mode: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Run invariant validation on a response and attach results.

    Args:
        response: Server response dict.
        turn_number: Current turn number.
        mode: Interaction mode.
        campaign_id: Campaign identifier for tracking persistent invariants.

    Returns:
        Response with validation results attached.
    """
    # Detect context from response
    state_updates = response.get("state_updates", {})
    if not isinstance(state_updates, dict):
        state_updates = {}

    game_state = state_updates.get("game_state", {})
    if not isinstance(game_state, dict):
        game_state = {}

    combat_state = game_state.get("combat_state", {})
    if not isinstance(combat_state, dict):
        combat_state = {}

    custom_state = state_updates.get("custom_campaign_state", {})
    if not isinstance(custom_state, dict):
        custom_state = {}

    is_combat = combat_state.get("in_combat", False)
    god_mode_present = bool(custom_state.get("god_mode_directives"))
    prior_god_mode_expected = _campaign_god_mode_expected.get(campaign_id, False)
    expects_god_mode_directives = prior_god_mode_expected or god_mode_present

    # Run validation
    violations = _invariant_checker.validate_response(
        response,
        turn_number=turn_number,
        is_combat=is_combat,
        has_god_mode_directives=expects_god_mode_directives,
    )

    _campaign_god_mode_expected[campaign_id] = expects_god_mode_directives

    # Classify violations
    breaking = []
    suspicious = []
    safe = []

    for v in violations:
        msg = f"{v.invariant_name}: {v.actual}"
        if v.severity == DifferenceClass.BREAKING:
            breaking.append(msg)
        elif v.severity == DifferenceClass.SUSPICIOUS:
            suspicious.append(msg)
        else:
            safe.append(msg)

    # Attach validation results
    validation_result = {
        "turn_number": turn_number,
        "mode": mode,
        "is_combat": is_combat,
        "is_living_world_turn": (
            turn_number > 0
            and turn_number % _invariant_checker.living_world_interval == 0
        ),
        "breaking_count": len(breaking),
        "suspicious_count": len(suspicious),
        "safe_count": len(safe),
        "status": "fail" if breaking else ("warn" if suspicious else "pass"),
    }

    response["_invariant_validation"] = validation_result
    response["_invariant_violations"] = breaking + suspicious

    # Strict mode: raise on breaking changes
    if _INVARIANT_STRICT_MODE and breaking:
        raise AssertionError(
            f"Breaking invariant violations on turn {turn_number}:\n"
            + "\n".join(f"  - {v}" for v in breaking)
        )

    return response


def reset_turn_tracking(campaign_id: str | None = None) -> None:
    """Reset turn tracking for a campaign or all campaigns.

    Useful at the start of a test to ensure clean turn counting.

    Args:
        campaign_id: Specific campaign to reset, or None to reset all.
    """
    if campaign_id is None:
        _campaign_turn_counts.clear()
        _campaign_god_mode_expected.clear()
    else:
        _campaign_turn_counts.pop(campaign_id, None)
        _campaign_god_mode_expected.pop(campaign_id, None)


def get_turn_count(campaign_id: str) -> int:
    """Get the current turn count for a campaign.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        Current turn count (0 if not tracked).
    """
    return _campaign_turn_counts.get(campaign_id, 0)


def aggregate_validation_summary(responses: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate validation results from multiple responses.

    This is useful for getting a summary at the end of a test run.

    Args:
        responses: List of response dicts from process_action.

    Returns:
        Aggregated summary dict with:
        - total_turns: Number of responses
        - total_breaking: Count of breaking violations
        - total_suspicious: Count of suspicious violations
        - living_world_turns: Count of LW turns
        - living_world_turns_valid: Count of LW turns that passed
        - all_violations: List of all violation strings
        - overall_status: "pass", "warn", or "fail"
    """
    total_breaking = 0
    total_suspicious = 0
    all_violations = []
    living_world_turns = 0
    living_world_turns_valid = 0

    for resp in responses:
        validation = resp.get("_invariant_validation", {})
        violations = resp.get("_invariant_violations", [])

        total_breaking += validation.get("breaking_count", 0)
        total_suspicious += validation.get("suspicious_count", 0)
        all_violations.extend(violations)

        if validation.get("is_living_world_turn"):
            living_world_turns += 1
            if validation.get("status") != "fail":
                living_world_turns_valid += 1

    if total_breaking > 0:
        status = "fail"
    elif total_suspicious > 0:
        status = "warn"
    else:
        status = "pass"

    return {
        "total_turns": len(responses),
        "total_breaking": total_breaking,
        "total_suspicious": total_suspicious,
        "living_world_turns": living_world_turns,
        "living_world_turns_valid": living_world_turns_valid,
        "all_violations": all_violations,
        "overall_status": status,
    }


def get_campaign_state(
    client: MCPClient, *, user_id: str, campaign_id: str, include_story: bool = False
) -> dict[str, Any]:
    """Get current campaign state.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        include_story: Whether to include story entries (default: False).

    Returns:
        Campaign state dict.

    Raises:
        RuntimeError: If server returns an error.
    """
    payload = client.tools_call(
        "get_campaign_state",
        {"user_id": user_id, "campaign_id": campaign_id, "include_story": include_story},
    )
    if payload.get("error"):
        raise RuntimeError(f"get_campaign_state error: {payload['error']}")
    return payload


def create_campaign_with_god_mode(
    client: MCPClient,
    user_id: str,
    *,
    title: str = "MCP Test Campaign",
    god_mode_data: str,
) -> str:
    """Create a campaign with God Mode data (matches real user flow with templates).

    This creates campaigns exactly like production templates that include
    pre-defined character data, world lore, and campaign setup in God Mode.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        title: Campaign title.
        god_mode_data: Full God Mode content (character, setting, world history, etc.)

    Returns:
        Campaign ID string.

    Raises:
        RuntimeError: If campaign creation fails.
    """
    payload = client.tools_call(
        "create_campaign",
        {
            "user_id": user_id,
            "title": title,
            "selected_prompts": [],
            "use_default_world": False,
            "god_mode_data": god_mode_data,
        },
    )
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise RuntimeError(f"create_campaign returned unexpected payload: {payload}")
    return campaign_id


def ensure_game_state_seed(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> bool:
    """Ensure campaign has minimal game state for dice tests.

    Seeds a basic player character (Aric the Fighter) and a Goblin NPC
    if not already present. This is useful for tests that need combat
    or skill check scenarios.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.

    Returns:
        True if state was seeded, False if already adequate.

    Raises:
        RuntimeError: If GOD_MODE_UPDATE_STATE fails.
    """
    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    npc_data = game_state.get("npc_data") or {}

    missing_pc = not (pc.get("name") and pc.get("attributes"))
    missing_goblin = not any(
        isinstance(value, dict) and value.get("name", "").lower() == "goblin"
        for value in npc_data.values()
    )

    if not missing_pc and not missing_goblin:
        return False

    seeded_pc = {
        "string_id": "pc_aric_001",
        "name": "Aric",
        "level": 1,
        "class": "Fighter",
        "hp_current": 12,
        "hp_max": 12,
        "attributes": {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 12,
        },
        "proficiency_bonus": 2,
    }
    seeded_goblin = {
        "string_id": "npc_goblin_001",
        "name": "Goblin",
        "hp_current": 7,
        "hp_max": 7,
        "armor_class": 13,
        "status": "healthy",
        "present": True,
    }

    state_changes: dict[str, Any] = {}
    if missing_pc:
        state_changes["player_character_data"] = seeded_pc
    if missing_goblin:
        state_changes["npc_data"] = dict(npc_data)
        state_changes["npc_data"]["npc_goblin_001"] = seeded_goblin

    # CRITICAL: Mark character creation as complete so StoryAgent is used
    # instead of CharacterCreationAgent. This ensures narrative_system_instruction.md
    # is loaded with its guardrails (outcome declaration rejection, etc.)
    state_changes["custom_campaign_state"] = {
        "character_creation_in_progress": False,
        "character_creation_completed": True,
    }

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
        track_turn=False,
    )
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")
    return True


def ensure_story_mode(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    request_responses: list | None = None,
) -> None:
    """Ensure campaign is in Story Mode (not Character Creation).
    
    Exits character creation if needed and verifies we're in Story Mode.
    Captures request/response pairs if request_responses list is provided.
    
    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        request_responses: Optional list to append request/response captures.
    """
    # Seed game state (exits character creation)
    ensure_game_state_seed(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Verify we're in Story Mode
    state_check = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    char_creation_in_progress = (
        state_check.get("game_state", {})
        .get("custom_campaign_state", {})
        .get("character_creation_in_progress", True)
    )

    if char_creation_in_progress:
        # Fallback: try to exit character creation explicitly
        char_complete_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I approve this character. Let's start the adventure.",
        )
        if request_responses is not None:
            request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()


def end_combat_if_active(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    request_responses: list | None = None,
    verbose: bool = False,
) -> bool:
    """Detect and end combat if active, with God Mode fallback.
    
    Returns True if combat was active and ended, False otherwise.
    Captures request/response pairs if request_responses list is provided.
    
    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        request_responses: Optional list to append request/response captures.
        verbose: If True, print status messages.
    
    Returns:
        True if combat was active and ended, False if no combat was active.
    """
    # Check if combat is active
    combat_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state = combat_state.get("game_state", {})
    in_combat = game_state.get("combat_state", {}).get("in_combat", False)

    if not in_combat:
        return False

    if verbose:
        print("   Combat detected, ending combat first...")

    # End combat
    combat_end = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I defeat all remaining enemies in combat.",
    )
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Verify combat ended
    combat_check = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_check = combat_check.get("game_state", {})
    still_in_combat = game_state_check.get("combat_state", {}).get("in_combat", False)

    if still_in_combat:
        # Force end combat via God Mode fallback
        if verbose:
            print("   Combat still active, forcing end via God Mode...")
        god_mode_end = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="[GOD MODE] All enemies are defeated. Combat ends.",
        )
        if request_responses is not None:
            request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        # Final verification
        final_check = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        if request_responses is not None:
            request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        final_game_state = final_check.get("game_state", {})
        still_in_combat_after_god = final_game_state.get("combat_state", {}).get("in_combat", False)
        if still_in_combat_after_god and verbose:
            print("   ⚠️  WARNING: Combat still active after God Mode - proceeding anyway")

    return True


def complete_mission_with_sanctuary(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    completion_text: str,
    request_responses: list | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Complete a mission and verify sanctuary activation.
    
    Ends combat first if needed, then sends completion text.
    Returns the completion response and sanctuary state.
    
    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        completion_text: Mission completion message (should use explicit completion language).
        request_responses: Optional list to append request/response captures.
        verbose: If True, print status messages.
    
    Returns:
        Dict with keys:
        - completion_response: Response from completion action
        - sanctuary_mode: Sanctuary state dict
        - sanctuary_active: Boolean
        - current_turn: Current turn number
    """
    # End combat first if active
    end_combat_if_active(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
        verbose=verbose,
    )

    # Complete the mission
    completion_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=completion_text,
    )
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Verify agent mode (for diagnostics)
    completion_agent_mode = completion_response.get("agent_mode", "unknown")
    if verbose and completion_agent_mode == "combat":
        print(f"   ⚠️  WARNING: Mission completion routed to CombatAgent (agent_mode={completion_agent_mode})")

    # Get sanctuary state
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state = state.get("game_state", {})
    sanctuary_mode = game_state.get("custom_campaign_state", {}).get("sanctuary_mode", {})
    sanctuary_active = sanctuary_mode.get("active", False)
    current_turn = game_state.get("player_turn", 0)

    return {
        "completion_response": completion_response,
        "sanctuary_mode": sanctuary_mode,
        "sanctuary_active": sanctuary_active,
        "current_turn": current_turn,
    }


def advance_to_living_world_turn(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    request_responses: list | None = None,
    verbose: bool = False,
) -> tuple[int, bool]:
    """Advance turns until we reach a Living World turn (every 3 turns).
    
    Returns the current turn number and whether it's a Living World turn.
    Captures request/response pairs if request_responses list is provided.
    
    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        request_responses: Optional list to append request/response captures.
        verbose: If True, print status messages.
    
    Returns:
        Tuple of (current_turn, is_living_world_turn).
    """
    # Get current state
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    if request_responses is not None:
        request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state = state.get("game_state", {})
    current_turn = game_state.get("player_turn", 0)
    is_living_world_turn = current_turn > 0 and current_turn % 3 == 0

    if not is_living_world_turn:
        if verbose:
            print(f"   Current turn: {current_turn} (not a Living World turn)")
            print(f"   Advancing to next Living World turn...")

        # Calculate turns needed to reach next Living World turn
        turns_to_advance = 3 - (current_turn % 3)
        for i in range(turns_to_advance):
            advance = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input="I continue my journey.",
            )
            if request_responses is not None:
                request_responses.extend(client.get_captures_as_dict())
            client.clear_captures()

        # Verify we're now on a Living World turn
        state_after = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        if request_responses is not None:
            request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        game_state_after = state_after.get("game_state", {})
        new_turn = game_state_after.get("player_turn", 0)
        is_living_world_turn = new_turn > 0 and new_turn % 3 == 0

        if verbose:
            status = "🌍 (Living World turn)" if is_living_world_turn else "⚠️ (Still not a Living World turn)"
            print(f"   Now on turn: {new_turn} {status}")

        return new_turn, is_living_world_turn
    else:
        if verbose:
            print(f"   Current turn: {current_turn} 🌍 (Living World turn)")
        return current_turn, True
