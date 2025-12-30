"""Campaign management utilities for MCP tests."""

from __future__ import annotations

import json
from typing import Any

from .mcp_client import MCPClient


def create_campaign(
    client: MCPClient,
    user_id: str,
    *,
    title: str = "MCP Test Campaign",
    character: str = "Aric the Fighter (STR 16)",
    setting: str = "A roadside ambush outside Phandalin",
    description: str = "Test campaign for MCP validation",
) -> str:
    """Create a campaign and return its ID.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        title: Campaign title.
        character: Character description.
        setting: Setting description.
        description: Campaign description.

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
            "character": character,
            "setting": setting,
            "description": description,
        },
    )
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
) -> dict[str, Any]:
    """Process a player action in a campaign.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        user_input: Player action text.
        mode: Interaction mode (default: "character").

    Returns:
        Response dict from server.
    """
    return client.tools_call(
        "process_action",
        {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": user_input,
            "mode": mode,
        },
    )


def get_campaign_state(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Get current campaign state.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.

    Returns:
        Campaign state dict.

    Raises:
        RuntimeError: If server returns an error.
    """
    payload = client.tools_call(
        "get_campaign_state",
        {"user_id": user_id, "campaign_id": campaign_id},
    )
    if payload.get("error"):
        raise RuntimeError(f"get_campaign_state error: {payload['error']}")
    return payload


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

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")
    return True
