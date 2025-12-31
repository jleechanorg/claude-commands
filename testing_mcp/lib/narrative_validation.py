"""Narrative validation for RPG tests - validates behavior, not word choice.

This module provides semantic validation for LLM-generated narratives.
Unlike BLEU/ROUGE (which penalize creativity), this validates behavioral
compliance: did the NPC appear? Was the secret kept? Did state update correctly?

Usage:
    from lib.narrative_validation import (
        validate_narrative_compliance,
        validate_state_update_compliance,
    )

    # Check narrative mentions required entities
    check = validate_narrative_compliance(
        result["narrative"],
        must_contain=["Aldric", "potion"],
        must_not_contain=["secret plan"],  # Meta-instructions must not leak
    )

    # Check state updates are correct
    state_check = validate_state_update_compliance(
        result["state_updates"],
        expected_npc_updates=["aldric"],
        expected_trust_direction={"aldric": "increase"},
    )
"""

from __future__ import annotations

import re
from typing import Any


def validate_narrative_compliance(
    narrative: str,
    *,
    must_contain: list[str] | None = None,
    must_not_contain: list[str] | None = None,
    min_length: int = 50,
    max_length: int = 10000,
) -> dict[str, Any]:
    """Validate narrative meets behavioral requirements.

    Args:
        narrative: The LLM-generated narrative text.
        must_contain: Entities/keywords that MUST appear (case-insensitive).
        must_not_contain: Secrets/meta-instructions that must NOT leak.
        min_length: Minimum acceptable narrative length.
        max_length: Maximum acceptable narrative length.

    Returns:
        Dict with 'passed', 'errors', 'warnings', and metrics.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not narrative:
        errors.append("narrative is empty or None")
        return {
            "passed": False,
            "errors": errors,
            "warnings": warnings,
            "narrative_length": 0,
            "entities_found": [],
            "secrets_leaked": [],
        }

    narrative_lower = narrative.lower()

    # Length validation
    if len(narrative) < min_length:
        errors.append(f"narrative too short: {len(narrative)} < {min_length}")
    if len(narrative) > max_length:
        warnings.append(f"narrative very long: {len(narrative)} > {max_length}")

    # Must-contain validation (entities, NPCs, key items)
    entities_found: list[str] = []
    if must_contain:
        for entity in must_contain:
            if entity.lower() in narrative_lower:
                entities_found.append(entity)
            else:
                errors.append(f"missing required entity: '{entity}'")

    # Must-NOT-contain validation (secrets, meta-instructions)
    secrets_leaked: list[str] = []
    if must_not_contain:
        for secret in must_not_contain:
            if secret.lower() in narrative_lower:
                secrets_leaked.append(secret)
                errors.append(f"leaked secret/meta-instruction: '{secret}'")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "narrative_length": len(narrative),
        "entities_found": entities_found,
        "secrets_leaked": secrets_leaked,
    }


def validate_state_update_compliance(
    state_updates: dict[str, Any],
    *,
    expected_npc_updates: list[str] | None = None,
    expected_trust_direction: dict[str, str] | None = None,
    expected_reputation_change: bool | None = None,
    expected_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Validate state updates meet behavioral requirements.

    Args:
        state_updates: The state_updates dict from LLM response.
        expected_npc_updates: NPC IDs that should have updates (partial match).
        expected_trust_direction: Dict mapping NPC ID to expected direction
            ("increase", "decrease", or "any").
        expected_reputation_change: Whether reputation should have changed.
        expected_fields: Top-level fields that should be present.

    Returns:
        Dict with 'passed', 'errors', and validation details.
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    if not isinstance(state_updates, dict):
        errors.append("state_updates is not a dict")
        return {"passed": False, "errors": errors, "warnings": warnings, "details": {}}

    npc_data = state_updates.get("npc_data", {})
    custom_state = state_updates.get("custom_campaign_state", {})
    reputation = custom_state.get("reputation", {})

    details["npc_updates_count"] = len(npc_data)
    details["has_reputation_update"] = bool(reputation)

    # Check expected NPC updates occurred
    npcs_found: list[str] = []
    if expected_npc_updates:
        for npc_id in expected_npc_updates:
            found = any(npc_id.lower() in key.lower() for key in npc_data.keys())
            if found:
                npcs_found.append(npc_id)
            else:
                # Soft warning - NPC might be referenced differently
                warnings.append(f"expected update for NPC '{npc_id}' not found in keys: {list(npc_data.keys())}")
        details["expected_npcs_found"] = npcs_found

    # Check trust direction
    trust_checks: dict[str, dict[str, Any]] = {}
    if expected_trust_direction:
        for npc_id, direction in expected_trust_direction.items():
            trust_checks[npc_id] = {"expected": direction, "actual": None, "passed": False}
            for key, update in npc_data.items():
                if npc_id.lower() in key.lower():
                    relationships = update.get("relationships", {})
                    player_rel = relationships.get("player", {})
                    trust = player_rel.get("trust_level")
                    if trust is not None:
                        trust_checks[npc_id]["actual"] = trust
                        if direction == "increase" and trust > 0:
                            trust_checks[npc_id]["passed"] = True
                        elif direction == "decrease" and trust < 0:
                            trust_checks[npc_id]["passed"] = True
                        elif direction == "any":
                            trust_checks[npc_id]["passed"] = True
                        else:
                            errors.append(
                                f"trust direction mismatch for {npc_id}: "
                                f"expected {direction}, got {trust}"
                            )
        details["trust_checks"] = trust_checks

    # Check reputation change
    if expected_reputation_change is not None:
        has_rep = bool(reputation)
        if expected_reputation_change and not has_rep:
            warnings.append("expected reputation change but none found")
        details["reputation_changed"] = has_rep

    # Check expected fields
    if expected_fields:
        for field in expected_fields:
            if field not in state_updates:
                errors.append(f"missing expected field: '{field}'")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }


def validate_directive_compliance(
    narrative: str,
    *,
    directive_type: str,
    directive_content: str,
    npc_name: str | None = None,
) -> dict[str, Any]:
    """Validate that meta-instructions were followed without being revealed.

    This specifically checks the META-INSTRUCTION SEPARATION rule: player OOC
    instructions should be invisible to NPCs.

    Args:
        narrative: The LLM-generated narrative.
        directive_type: Type of directive ("dont_reveal", "pretend", "god_mode").
        directive_content: The content that should be hidden/acted upon.
        npc_name: NPC who should not know the secret (if applicable).

    Returns:
        Dict with 'passed', 'errors', and analysis.
    """
    errors: list[str] = []
    warnings: list[str] = []

    narrative_lower = narrative.lower()

    # Check directive content doesn't appear in narrative
    if directive_type == "dont_reveal":
        if directive_content.lower() in narrative_lower:
            errors.append(
                f"directive violated: '{directive_content}' appeared in narrative "
                f"(should have been hidden from {npc_name or 'NPCs'})"
            )

    # Check for meta-instruction leakage patterns
    meta_patterns = [
        r"the player (told|asked|instructed|said) (me|us) to",
        r"according to (the|your) instructions",
        r"as (you|the player) requested",
        r"following (your|the) directive",
        r"god mode",
        r"ooc instruction",
    ]
    for pattern in meta_patterns:
        if re.search(pattern, narrative_lower):
            errors.append(f"meta-instruction leaked: pattern '{pattern}' found in narrative")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "directive_type": directive_type,
    }
