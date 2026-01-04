#!/usr/bin/env python3
"""
Fetch and display game state data from Firestore for a specific campaign.

Uses shared code from mvp_site for equipment/stats/spells extraction to ensure
consistency with the production API endpoints.

Usage:
    WORLDAI_DEV_MODE=true python scripts/fetch_campaign_gamestate.py <campaign_id>

Example:
    WORLDAI_DEV_MODE=true python scripts/fetch_campaign_gamestate.py kuXKa6vrYY6P99MfhWBn
"""

import json
import os
import re
import sys

# Add project root to path for mvp_site imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# CRITICAL: Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials, firestore

# Import shared display modules from mvp_site
from mvp_site import equipment_display
from mvp_site.game_state import GameState
from mvp_site.main import get_spell_level  # Spell level lookup for legacy string data


# =============================================================================
# SHARED HELPER FUNCTIONS (same logic as main.py API endpoints)
# =============================================================================

def calc_modifier(score: int) -> int:
    """Calculate ability modifier from score (D&D 5e formula)."""
    return (score - 10) // 2


def build_stats_summary(game_state: dict) -> str:
    """Build stats summary - matches /api/campaigns/{id}/stats endpoint."""
    pc_data = game_state.get("player_character_data", {})
    item_registry = game_state.get("item_registry", {})

    # Stats can be in 'stats', 'attributes', or 'ability_scores'
    stats = pc_data.get("stats") or pc_data.get("attributes") or pc_data.get("ability_scores") or {}

    # Map full stat names to abbreviations
    STAT_NAME_MAP = {
        "strength": "str", "str": "str",
        "dexterity": "dex", "dex": "dex",
        "constitution": "con", "con": "con",
        "intelligence": "int", "int": "int",
        "wisdom": "wis", "wis": "wis",
        "charisma": "cha", "cha": "cha",
    }

    # Normalize stats dict to use abbreviations
    normalized_stats = {}
    for key, val in stats.items():
        abbrev = STAT_NAME_MAP.get(key.lower(), key.lower())
        normalized_stats[abbrev] = val

    # Get equipment for bonus calculation - handle FLAT structure
    equipment = pc_data.get("equipment", {})
    if not isinstance(equipment, dict):
        equipment = {}

    # Collect equipped items from flat structure
    equipped_items = {}
    EQUIPMENT_SLOTS = {"head", "body", "armor", "cloak", "neck", "hands", "feet",
                       "ring_1", "ring_2", "ring", "instrument", "main_hand", "off_hand"}
    for slot in EQUIPMENT_SLOTS:
        item = equipment.get(slot)
        if item and isinstance(item, dict) and item.get("equipped", True):
            equipped_items[slot] = item

    # Calculate equipment bonuses
    equipment_bonuses = {}
    # Pattern matches: "+2 CHA", "CHA +2", "+2 Charisma", "Charisma +2", etc.
    bonus_pattern = re.compile(
        r"(?:(?P<val>[+-]?\d+)\s*(?:to\s+)?(?P<stat>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma))|"
        r"(?:(?P<stat_alt>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*(?P<val_alt>[+-]?\d+))",
        re.IGNORECASE,
    )

    for slot, item_data in equipped_items.items():
        stat_string = item_data.get("stats", "")
        if not stat_string:
            continue

        for match in bonus_pattern.finditer(str(stat_string)):
            stat_name = match.group("stat") or match.group("stat_alt")
            bonus_val = match.group("val") or match.group("val_alt")
            if not stat_name or bonus_val is None:
                continue
            # Normalize stat name to abbreviation
            stat_key = STAT_NAME_MAP.get(stat_name.lower(), stat_name.lower())
            # Skip unsigned AC values (base armor, not bonus)
            if stat_key == "ac" and not str(bonus_val).startswith(("+", "-")):
                continue
            equipment_bonuses[stat_key] = equipment_bonuses.get(stat_key, 0) + int(bonus_val)

    # Get basic combat info
    hp_current = pc_data.get("hp_current", pc_data.get("hp", 0))
    hp_max = pc_data.get("hp_max", 0)
    level = pc_data.get("level", 1)
    base_ac = pc_data.get("armor_class", pc_data.get("ac", 10))
    ac_bonus = equipment_bonuses.get("ac", 0)
    effective_ac = int(base_ac) + ac_bonus

    lines = ["━━━ Character Stats ━━━"]
    ac_display = f"AC: {base_ac}" + (f" → {effective_ac}" if ac_bonus else "")
    lines.append(f"Level {level} | HP: {hp_current}/{hp_max} | {ac_display}")
    lines.append("")
    lines.append("▸ Ability Scores (Base → Effective):")

    for stat in ["str", "dex", "con", "int", "wis", "cha"]:
        base_score = normalized_stats.get(stat, 10)
        if isinstance(base_score, dict):
            base_score = base_score.get("score", 10)
        base_score = int(base_score)
        bonus = equipment_bonuses.get(stat, 0)
        effective_score = base_score + bonus
        mod = calc_modifier(effective_score)
        sign = "+" if mod >= 0 else ""

        if bonus:
            lines.append(f"  • {stat.upper()}: {base_score} → {effective_score} ({sign}{mod}) [+{bonus} from gear]")
        else:
            lines.append(f"  • {stat.upper()}: {base_score} ({sign}{mod})")

    return "\n".join(lines)


def build_spells_summary(game_state: dict) -> str:
    """Build spells summary - matches /api/campaigns/{id}/spells endpoint."""
    pc_data = game_state.get("player_character_data", {})
    resources = pc_data.get("resources", {})

    lines = ["━━━ Spells & Magic ━━━"]

    # Spell slots from resources.spell_slots (format: {level_X: {used, max}})
    spell_slots_raw = resources.get("spell_slots", {})
    if spell_slots_raw and isinstance(spell_slots_raw, dict):
        slot_parts = []
        for level_key in sorted(spell_slots_raw.keys()):
            data = spell_slots_raw[level_key]
            if isinstance(data, dict):
                # Convert to int to handle string values from Firestore
                try:
                    max_val = int(data.get("max", 0))
                    used_val = int(data.get("used", 0))
                    current = max_val - used_val
                except (ValueError, TypeError):
                    max_val = 0
                    used_val = 0
                    current = 0
                level = level_key.replace("level_", "L")
                slot_parts.append(f"{level}: {current}/{max_val}")
        if slot_parts:
            lines.append(f"Spell Slots: {' | '.join(slot_parts)}")

    # Also check pc_data.spell_slots (legacy format)
    if not spell_slots_raw:
        legacy_slots = pc_data.get("spell_slots", {})
        if legacy_slots and isinstance(legacy_slots, dict):
            slot_parts = []
            for level, data in sorted(legacy_slots.items()):
                if isinstance(data, dict):
                    current = data.get("current", data.get("max", 0))
                    max_val = data.get("max", 0)
                    slot_parts.append(f"L{level}: {current}/{max_val}")
            if slot_parts:
                lines.append(f"Spell Slots: {' | '.join(slot_parts)}")

    # Known spells
    spells_known = pc_data.get("spells_known", [])
    cantrips = pc_data.get("cantrips_known", pc_data.get("cantrips", []))

    if cantrips:
        lines.append("")
        lines.append("▸ Cantrips:")
        for spell in cantrips:
            name = spell.get("name", spell) if isinstance(spell, dict) else spell
            lines.append(f"  • {name}")

    if spells_known:
        lines.append("")
        lines.append("▸ Known Spells:")
        # Group by spell level
        spells_by_level: dict[str, list[str]] = {}
        for spell in spells_known:
            name = spell.get("name", spell) if isinstance(spell, dict) else spell
            # Get level from dict, or look up from spell name for legacy string data
            if isinstance(spell, dict):
                level = spell.get("level", "?")
            else:
                level = get_spell_level(str(name))
            level_str = str(level) if level is not None else "0"
            if level_str not in spells_by_level:
                spells_by_level[level_str] = []
            spells_by_level[level_str].append(name)
        # Sort by level and display
        for level_key in sorted(spells_by_level.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            spell_names = spells_by_level[level_key]
            if level_key == "0":
                label = "Cantrips"
            elif level_key == "?":
                label = "Unknown Level"
            else:
                label = f"Level {level_key}"
            lines.append(f"  {label}: {', '.join(sorted(spell_names))}")

    if len(lines) == 1:
        lines.append("No spell data available")

    return "\n".join(lines)


def init_firebase():
    """Initialize Firebase if not already initialized."""
    if not firebase_admin._apps:
        cred_path = os.path.expanduser("~/serviceAccountKey.json")
        if not os.path.exists(cred_path):
            print(f"Error: Firebase credentials not found at {cred_path}")
            sys.exit(1)
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Known user UID (jleechan@gmail.com) - avoids auth lookup
PRIMARY_USER_UID = "vnLp2G3m21PJL6kxcuAqmWSOtm73"


def find_campaign(db, campaign_id):
    """Find a campaign by ID - try known user first, then search all users."""
    # Try primary user first (most likely)
    uid = PRIMARY_USER_UID
    print(f"Checking primary user: {uid}")

    campaign_ref = db.collection("users").document(uid).collection("campaigns").document(campaign_id)
    campaign_doc = campaign_ref.get()

    if campaign_doc.exists:
        return uid, campaign_doc.to_dict()

    print("Campaign not found for primary user, searching all users...")

    # Fall back to iterating through users
    users_ref = db.collection("users")

    for user_doc in users_ref.stream():
        user_id = user_doc.id
        if user_id == uid:
            continue  # Already checked
        campaign_ref = users_ref.document(user_id).collection("campaigns").document(campaign_id)
        campaign_doc = campaign_ref.get()

        if campaign_doc.exists:
            return user_id, campaign_doc.to_dict()

    return None, None


def get_game_state(db, user_id, campaign_id):
    """Fetch the current game state for a campaign."""
    game_state_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("game_states")
        .document("current_state")
    )

    doc = game_state_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_campaign_gamestate.py <campaign_id>")
        sys.exit(1)

    campaign_id = sys.argv[1]
    print(f"🔍 Looking up campaign: {campaign_id}")

    db = init_firebase()

    # Find the campaign
    user_id, campaign_data = find_campaign(db, campaign_id)

    if not user_id:
        print(f"❌ Campaign {campaign_id} not found")
        sys.exit(1)

    print(f"✅ Found campaign owned by user: {user_id}")
    print(f"📋 Campaign title: {campaign_data.get('title', 'Untitled')}")

    # Get game state
    game_state = get_game_state(db, user_id, campaign_id)

    if not game_state:
        print("❌ No game state found for this campaign")
        sys.exit(1)

    # Convert to GameState object for shared module compatibility
    game_state_obj = GameState(**game_state)

    # ==========================================================================
    # EQUIPMENT SUMMARY (using shared equipment_display module)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("📦 EQUIPMENT (matches GET /api/campaigns/{id}/equipment)")
    print("=" * 60)

    equipment_list = equipment_display.extract_equipment_display(game_state_obj)
    if equipment_list:
        equipment_summary = equipment_display.build_equipment_summary(equipment_list, "Your Equipment")
        print(equipment_summary)
    else:
        print("No equipment found")

    # ==========================================================================
    # STATS SUMMARY (using shared build_stats_summary function)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("📊 STATS (matches GET /api/campaigns/{id}/stats)")
    print("=" * 60)

    stats_summary = build_stats_summary(game_state)
    print(stats_summary)

    # ==========================================================================
    # SPELLS SUMMARY (using shared build_spells_summary function)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🔮 SPELLS (matches GET /api/campaigns/{id}/spells)")
    print("=" * 60)

    spells_summary = build_spells_summary(game_state)
    print(spells_summary)

    # ==========================================================================
    # API ENDPOINT SUMMARY
    # ==========================================================================
    print("\n" + "=" * 60)
    print("✅ All summaries use shared code with production API")
    print("=" * 60)
    print("  GET /api/campaigns/{id}/equipment → equipment_summary")
    print("  GET /api/campaigns/{id}/stats     → stats_summary")
    print("  GET /api/campaigns/{id}/spells    → spells_summary")


if __name__ == "__main__":
    main()
