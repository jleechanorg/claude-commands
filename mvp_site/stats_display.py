"""
Shared stats and spells display utilities.

Used by both:
- GET /api/campaigns/{id}/stats endpoint in main.py
- scripts/fetch_campaign_gamestate.py CLI tool

This ensures consistent output between API and CLI tools.
"""

import re
from typing import Any


def calc_modifier(score: int) -> int:
    """Calculate ability modifier from score (D&D 5e formula)."""
    return (score - 10) // 2


# Map full stat names to abbreviations
STAT_NAME_MAP = {
    "strength": "str",
    "str": "str",
    "dexterity": "dex",
    "dex": "dex",
    "constitution": "con",
    "con": "con",
    "intelligence": "int",
    "int": "int",
    "wisdom": "wis",
    "wis": "wis",
    "charisma": "cha",
    "cha": "cha",
}

STAT_ORDER = ["str", "dex", "con", "int", "wis", "cha"]

STAT_DISPLAY_NAMES = {
    "str": "STR",
    "dex": "DEX",
    "con": "CON",
    "int": "INT",
    "wis": "WIS",
    "cha": "CHA",
}

# Equipment slots to check for bonuses
EQUIPMENT_SLOTS = {
    "head",
    "body",
    "armor",
    "cloak",
    "neck",
    "hands",
    "feet",
    "ring_1",
    "ring_2",
    "ring",
    "instrument",
    "main_hand",
    "off_hand",
}

# Pattern matches: "+2 CHA", "CHA +2", "+2 Charisma", "Charisma +2", etc.
BONUS_PATTERN = re.compile(
    r"(?:(?P<val>[+-]?\d+)\s*(?:to\s+)?(?P<stat>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma))|"
    r"(?:(?P<stat_alt>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*(?P<val_alt>[+-]?\d+))",
    re.IGNORECASE,
)


def extract_equipment_bonuses(pc_data: dict) -> dict[str, int]:
    """Extract stat bonuses from equipped items."""
    equipment = pc_data.get("equipment", {})
    if not isinstance(equipment, dict):
        equipment = {}

    # Collect equipped items from flat structure
    equipped_items = {}
    for slot in EQUIPMENT_SLOTS:
        item = equipment.get(slot)
        if item and isinstance(item, dict) and item.get("equipped", True):
            equipped_items[slot] = item

    # Calculate equipment bonuses
    equipment_bonuses: dict[str, int] = {}

    for slot, item_data in equipped_items.items():
        stat_string = item_data.get("stats", "")
        if not stat_string:
            continue

        for match in BONUS_PATTERN.finditer(str(stat_string)):
            stat_name = match.group("stat") or match.group("stat_alt")
            bonus_val = match.group("val") or match.group("val_alt")
            if not stat_name or bonus_val is None:
                continue
            # Normalize stat name to abbreviation
            stat_key = STAT_NAME_MAP.get(stat_name.lower(), stat_name.lower())
            # Skip unsigned AC values (base armor, not bonus)
            if stat_key == "ac" and not str(bonus_val).startswith(("+", "-")):
                continue
            equipment_bonuses[stat_key] = equipment_bonuses.get(stat_key, 0) + int(
                bonus_val
            )

    return equipment_bonuses


def normalize_stats(stats: dict) -> dict[str, Any]:
    """Normalize stats dict to use abbreviations."""
    normalized = {}
    for key, val in stats.items():
        abbrev = STAT_NAME_MAP.get(key.lower(), key.lower())
        normalized[abbrev] = val
    return normalized


def deduplicate_features(features: list) -> list[str]:
    """Deduplicate features list while preserving order."""
    unique_features: list[str] = []
    if features and isinstance(features, list):
        seen: set[str] = set()
        for feat in features:
            feat_str = str(feat).strip()
            if feat_str and feat_str not in seen:
                seen.add(feat_str)
                unique_features.append(feat_str)
    return unique_features


def build_stats_summary(game_state: dict) -> str:
    """Build stats summary string for display.

    Args:
        game_state: Dict containing player_character_data

    Returns:
        Formatted stats summary string
    """
    pc_data = game_state.get("player_character_data", {})
    if not isinstance(pc_data, dict):
        pc_data = vars(pc_data) if hasattr(pc_data, "__dict__") else {}

    # Stats can be in 'stats', 'attributes', or 'ability_scores'
    stats = (
        pc_data.get("stats")
        or pc_data.get("attributes")
        or pc_data.get("ability_scores")
        or {}
    )
    normalized_stats = normalize_stats(stats)

    # Get equipment bonuses
    equipment_bonuses = extract_equipment_bonuses(pc_data)

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

    for stat in STAT_ORDER:
        base_score = normalized_stats.get(stat, 10)
        if isinstance(base_score, dict):
            base_score = base_score.get("score", 10)
        base_score = int(base_score)
        bonus = equipment_bonuses.get(stat, 0)
        effective_score = base_score + bonus
        mod = calc_modifier(effective_score)
        sign = "+" if mod >= 0 else ""

        if bonus:
            lines.append(
                f"  • {STAT_DISPLAY_NAMES[stat]}: {base_score} → {effective_score} ({sign}{mod}) [+{bonus} from gear]"
            )
        else:
            lines.append(f"  • {STAT_DISPLAY_NAMES[stat]}: {base_score} ({sign}{mod})")

    # Extract and deduplicate features/feats
    features = pc_data.get("features", [])
    unique_features = deduplicate_features(features)

    # Only add header if there are actual features after deduplication
    if unique_features:
        lines.append("")
        lines.append("▸ Features & Feats:")
        for feat in unique_features:
            lines.append(f"  • {feat}")

    return "\n".join(lines)


def build_spells_summary(game_state: dict, get_spell_level_fn=None) -> str:
    """Build spells summary string for display.

    Args:
        game_state: Dict containing player_character_data
        get_spell_level_fn: Optional function to look up spell level from name

    Returns:
        Formatted spells summary string
    """
    pc_data = game_state.get("player_character_data", {})
    if not isinstance(pc_data, dict):
        pc_data = vars(pc_data) if hasattr(pc_data, "__dict__") else {}

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
            elif get_spell_level_fn:
                level = get_spell_level_fn(str(name))
            else:
                level = "?"
            level_str = str(level) if level is not None else "0"
            if level_str not in spells_by_level:
                spells_by_level[level_str] = []
            spells_by_level[level_str].append(name)
        # Sort by level and display
        for level_key in sorted(
            spells_by_level.keys(), key=lambda x: int(x) if x.isdigit() else 99
        ):
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
