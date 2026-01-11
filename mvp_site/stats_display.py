"""
Shared stats and spells display utilities.

Used by both:
- GET /api/campaigns/{id}/stats endpoint in main.py
- scripts/fetch_campaign_gamestate.py CLI tool

This ensures consistent output between API and CLI tools.
"""

import re
from typing import Any

from mvp_site.game_state import PROFICIENCY_BY_LEVEL, coerce_int

# Spellcasting ability by class (D&D 5e rules)
# Includes base classes and common subclasses
SPELLCASTING_ABILITY_MAP = {
    # INT-based casters
    "wizard": "int",
    "bladesinger": "int",  # Wizard subclass
    "evocation wizard": "int",
    "abjuration wizard": "int",
    "divination wizard": "int",
    "necromancer": "int",
    "artificer": "int",
    "eldritch knight": "int",  # Fighter subclass
    "arcane trickster": "int",  # Rogue subclass
    "blood hunter": "int",  # Matt Mercer homebrew
    "bloodhunter": "int",
    # WIS-based casters
    "cleric": "wis",
    "druid": "wis",
    "ranger": "wis",
    "gloom stalker": "wis",  # Ranger subclass
    "beast master": "wis",
    "way of the four elements": "wis",  # Monk subclass (ki spells)
    "way of the sun soul": "wis",  # Monk subclass
    # CHA-based casters
    "sorcerer": "cha",
    "bard": "cha",
    "warlock": "cha",
    "paladin": "cha",
    "hexblade": "cha",  # Warlock subclass
    "oath of devotion": "cha",
    "oath of vengeance": "cha",
    "college of lore": "cha",  # Bard subclass
    "college of swords": "cha",
    # Non-casters (return None) - no Spell DC/Spell Attack
    "fighter": None,
    "rogue": None,
    "barbarian": None,
    "monk": None,  # Base monks use Ki, not spells
}


def calc_modifier(score: int) -> int:
    """Calculate ability modifier from score (D&D 5e formula)."""
    return (score - 10) // 2


def get_proficiency_bonus(level: int | str | float) -> int:
    """Get proficiency bonus for a given character level."""
    coerced_level = coerce_int(level, 1) or 1
    level = max(1, min(20, coerced_level))  # Clamp to 1-20
    return PROFICIENCY_BY_LEVEL.get(level, 2)


def get_spellcasting_ability(class_name: str) -> str | None:
    """Get the spellcasting ability for a class."""
    if not class_name or not isinstance(class_name, str):
        return None
    normalized = class_name.lower().strip()
    # Handle multi-class (e.g., "Fighter/Wizard") - use first spellcasting class
    for part_raw in normalized.split("/"):
        part = part_raw.strip()
        ability = SPELLCASTING_ABILITY_MAP.get(part)
        if ability:
            return ability
    return None


def extract_equipped_weapons(pc_data: dict, item_registry: dict | None = None) -> list[dict]:
    """Extract equipped weapon information for combat stats display.

    Args:
        pc_data: Player character data dict
        item_registry: Optional item registry dict for looking up items by ID

    Returns list of dicts with: name, damage, properties, is_finesse, is_ranged, is_thrown
    """
    equipment = pc_data.get("equipment", {})
    if not isinstance(equipment, dict):
        return []

    registry = item_registry or pc_data.get("item_registry") or {}

    weapons: list[dict] = []
    weapon_slots = ["main_hand", "off_hand", "mainhand", "offhand", "weapon"]

    equipped_items = _gather_equipped_items(equipment)

    for slot in weapon_slots:
        item_ref = equipped_items.get(slot)
        if item_ref is None:
            continue

        item_data: dict[str, Any] | None = None
        if isinstance(item_ref, dict):
            item_data = item_ref
        elif isinstance(item_ref, str) and item_ref in registry:
            candidate = registry[item_ref]
            if isinstance(candidate, dict):
                item_data = candidate

        if not isinstance(item_data, dict):
            continue

        name = item_data.get("name", "Unknown")
        damage = item_data.get("damage", "")
        properties_raw = item_data.get("properties", "")
        proficient = item_data.get("proficient")

        # Normalize properties to string
        if isinstance(properties_raw, list):
            properties = ", ".join(str(p).lower() for p in properties_raw if p)
        else:
            properties = str(properties_raw).lower()

        # Determine weapon characteristics
        is_thrown = "thrown" in properties
        # Thrown weapons use Strength unless they also have the finesse property
        is_finesse = "finesse" in properties
        is_ranged = (
            any(kw in properties for kw in ["ranged", "ammunition"]) and not is_thrown
        )
        is_versatile = "versatile" in properties

        weapons.append(
            {
                "name": name,
                "damage": damage,
                "properties": properties,
                "is_finesse": is_finesse,
                "is_thrown": is_thrown,
                "is_ranged": is_ranged,
                "is_versatile": is_versatile,
                "proficient": proficient if isinstance(proficient, bool) else None,
                "slot": slot,
            }
        )

    return weapons


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

# D&D 5e class saving throw proficiencies
CLASS_SAVE_PROFICIENCIES = {
    "barbarian": ["str", "con"],
    "bard": ["dex", "cha"],
    "cleric": ["wis", "cha"],
    "druid": ["int", "wis"],
    "fighter": ["str", "con"],
    "monk": ["str", "dex"],
    "paladin": ["wis", "cha"],
    "ranger": ["str", "dex"],
    "rogue": ["dex", "int"],
    "sorcerer": ["con", "cha"],
    "warlock": ["wis", "cha"],
    "wizard": ["int", "wis"],
    "artificer": ["con", "int"],
    # Subclasses inherit from base class
    "bladesinger": ["int", "wis"],
    "eldritch knight": ["str", "con"],
    "arcane trickster": ["dex", "int"],
    "hexblade": ["wis", "cha"],
}

# D&D 5e skills and their associated abilities
SKILLS = {
    "acrobatics": "dex",
    "animal handling": "wis",
    "arcana": "int",
    "athletics": "str",
    "deception": "cha",
    "history": "int",
    "insight": "wis",
    "intimidation": "cha",
    "investigation": "int",
    "medicine": "wis",
    "nature": "int",
    "perception": "wis",
    "performance": "cha",
    "persuasion": "cha",
    "religion": "int",
    "sleight of hand": "dex",
    "stealth": "dex",
    "survival": "wis",
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
    "mainhand",
    "offhand",
    "weapon",
    "shield",
    "amulet",
    "necklace",
    "belt",
    "boots",
    "gloves",
    "bracers",
}

# Pattern matches: "+2 CHA", "CHA +2", "+2 Charisma", "Charisma +2", etc.
BONUS_PATTERN = re.compile(
    r"(?:(?P<val>[+-]?\d+)\s*(?:to\s+)?(?P<stat>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma))|"
    r"(?:(?P<stat_alt>STR|DEX|CON|INT|WIS|CHA|AC|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*(?P<val_alt>[+-]?\d+))",
    re.IGNORECASE,
)


def _gather_equipped_items(equipment: dict) -> dict:
    """Collect equipped items from common equipment schemas."""

    equipped_items: dict[str, Any] = {}

    nested_equipped = equipment.get("equipped")
    if isinstance(nested_equipped, dict):
        for slot, item_ref in nested_equipped.items():
            if item_ref is None:
                continue
            if isinstance(item_ref, dict) and item_ref.get("equipped") is False:
                continue
            equipped_items[slot] = item_ref

    for slot in EQUIPMENT_SLOTS:
        item_ref = equipment.get(slot)
        if item_ref is None:
            continue
        if isinstance(item_ref, dict) and item_ref.get("equipped", True) is False:
            continue
        equipped_items.setdefault(slot, item_ref)

    return equipped_items


def extract_equipment_bonuses(  # noqa: PLR0912, PLR0915
    pc_data: dict, base_stats: dict | None = None, item_registry: dict | None = None
) -> dict[str, int]:
    """Extract stat bonuses from equipped items, respecting caps and registries."""
    equipment = pc_data.get("equipment", {})
    if not isinstance(equipment, dict):
        equipment = {}

    equipped_items = _gather_equipped_items(equipment)
    registry = item_registry or pc_data.get("item_registry") or {}

    equipment_bonuses: dict[str, int] = {}

    normalized_base: dict[str, int] = {}
    if base_stats:
        for key, val in base_stats.items():
            try:
                normalized_base[key] = int(val.get("score", val)) if isinstance(val, dict) else int(val)
            except (TypeError, ValueError):
                continue

    for _slot, item_ref in equipped_items.items():
        if not item_ref:
            continue

        stat_string: str | None = None
        if isinstance(item_ref, str):
            if item_ref in registry:
                item_data = registry[item_ref]
                item_stats = item_data.get("stats", "") if isinstance(item_data, dict) else ""
                if isinstance(item_stats, str):
                    stat_string = item_stats
            if stat_string is None:
                stat_string = item_ref
        elif isinstance(item_ref, dict):
            inline_stats = item_ref.get("stats")
            if isinstance(inline_stats, str):
                stat_string = inline_stats
            else:
                inline_name = item_ref.get("name")
                if isinstance(inline_name, str):
                    stat_string = inline_name

        if not stat_string:
            continue

        used_spans: list[tuple[int, int]] = []
        max_cap_pattern = re.compile(r"\(Max\s*(\d+)\)", re.IGNORECASE)

        for match in BONUS_PATTERN.finditer(str(stat_string)):
            span = match.span()
            if any(start < span[1] and span[0] < end for start, end in used_spans):
                continue
            stat_name = match.group("stat") or match.group("stat_alt")
            bonus_val = match.group("val") or match.group("val_alt")
            if not stat_name or bonus_val is None:
                continue
            stat_key = STAT_NAME_MAP.get(stat_name.lower(), stat_name.lower())
            if stat_key == "ac" and not str(bonus_val).startswith(("+", "-")):
                continue

            # Check for max cap immediately after this stat match
            # Look for (Max X) pattern within 20 characters after the match
            match_end = span[1]
            remaining_text = stat_string[match_end : match_end + 20]
            max_cap_match = max_cap_pattern.search(remaining_text)
            stat_max_cap = int(max_cap_match.group(1)) if max_cap_match else None

            try:
                bonus_int = int(bonus_val)
                if stat_max_cap is not None and stat_key in normalized_base:
                    naked_val = normalized_base.get(stat_key, 0)
                    max_bonus = max(0, stat_max_cap - naked_val)
                    bonus_int = min(bonus_int, max_bonus)
                equipment_bonuses[stat_key] = equipment_bonuses.get(stat_key, 0) + bonus_int
                used_spans.append(span)
                # Also mark the max cap span as used if found
                if max_cap_match:
                    cap_span = (match_end + max_cap_match.start(), match_end + max_cap_match.end())
                    used_spans.append(cap_span)
            except (ValueError, TypeError):
                continue

    return equipment_bonuses


def normalize_stats(stats: dict) -> dict[str, Any]:
    """Normalize stats dict to use abbreviations."""
    normalized = {}
    for key, val in stats.items():
        abbrev = STAT_NAME_MAP.get(key.lower(), key.lower())
        normalized[abbrev] = val
    return normalized


def get_weapon_proficiencies(pc_data: dict) -> set[str]:
    """Collect weapon proficiencies from common locations in pc_data."""

    def _normalize_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).lower() for v in value if v]
        return []

    proficiencies: set[str] = set()
    potential_sources: list[Any] = [pc_data.get("weapon_proficiencies")]

    prof_data = pc_data.get("proficiencies")
    if isinstance(prof_data, dict):
        potential_sources.append(prof_data.get("weapons"))

    stats_data = pc_data.get("stats")
    if isinstance(stats_data, dict):
        combat_data = stats_data.get("combat")
        if isinstance(combat_data, dict):
            potential_sources.append(combat_data.get("weapon_proficiencies"))

    for source in potential_sources:
        for prof in _normalize_list(source):
            proficiencies.add(prof)

    return proficiencies


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


def compute_saving_throws(
    class_name: str | None,
    effective_scores: dict[str, int],
    proficiency_bonus: int,
    explicit_saves: list | None = None,
) -> list[dict[str, Any]]:
    """Compute saving throws with proficiency support (multi-class aware)."""

    save_proficiencies: set[str] = set()
    if class_name and isinstance(class_name, str):
        for part_raw in class_name.lower().split("/"):
            part = part_raw.strip()
            for save in CLASS_SAVE_PROFICIENCIES.get(part, []):
                save_proficiencies.add(save)

    if isinstance(explicit_saves, list):
        for save in explicit_saves:
            save_proficiencies.add(str(save).lower()[:3])

    saving_throws: list[dict[str, Any]] = []
    for stat in STAT_ORDER:
        raw_score = effective_scores.get(stat, 10)
        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            score = 10
        stat_mod = calc_modifier(score)
        is_proficient = stat in save_proficiencies
        bonus = stat_mod + (proficiency_bonus if is_proficient else 0)
        saving_throws.append(
            {
                "stat": stat,
                "bonus": bonus,
                "proficient": is_proficient,
                "modifier": stat_mod,
            }
        )

    return saving_throws


def build_stats_summary(game_state: dict) -> str:  # noqa: PLR0912, PLR0915
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

    # Get equipment bonuses (respecting registries and caps)
    equipment_bonuses = extract_equipment_bonuses(
        pc_data, base_stats=normalized_stats, item_registry=game_state.get("item_registry")
    )

    # Get basic combat info
    hp_current = pc_data.get("hp_current", pc_data.get("hp", 0))
    hp_max = pc_data.get("hp_max", 0)
    level = pc_data.get("level", 1)
    base_ac = pc_data.get("armor_class", pc_data.get("ac", 10))
    ac_bonus = equipment_bonuses.get("ac", 0)
    try:
        ac_base_val = int(base_ac)
    except (TypeError, ValueError):
        ac_base_val = 10
    effective_ac = ac_base_val + ac_bonus

    lines = ["━━━ Character Stats ━━━"]
    ac_display = f"AC: {base_ac}" + (f" → {effective_ac}" if ac_bonus else "")
    lines.append(f"Level {level} | HP: {hp_current}/{hp_max} | {ac_display}")
    lines.append("")
    lines.append("▸ Ability Scores (Base → Effective):")

    effective_scores: dict[str, int] = {}

    for stat in STAT_ORDER:
        base_score_raw = normalized_stats.get(stat, 10)
        if isinstance(base_score_raw, dict):
            base_score_raw = base_score_raw.get("score", 10)
        try:
            base_score = int(base_score_raw)
        except (TypeError, ValueError):
            base_score = 10
        bonus = equipment_bonuses.get(stat, 0)
        effective_score = base_score + bonus
        effective_scores[stat] = effective_score
        mod = calc_modifier(effective_score)
        sign = "+" if mod >= 0 else ""

        if bonus:
            bonus_sign = "+" if bonus >= 0 else ""
            lines.append(
                f"  • {STAT_DISPLAY_NAMES[stat]}: {base_score} → {effective_score} ({sign}{mod}) [{bonus_sign}{bonus} from gear]"
            )
        else:
            lines.append(f"  • {STAT_DISPLAY_NAMES[stat]}: {base_score} ({sign}{mod})")

    # Calculate effective stat modifiers for combat calculations
    def get_effective_mod(stat_key: str) -> int:
        return calc_modifier(effective_scores.get(stat_key, 10))

    str_mod = get_effective_mod("str")
    dex_mod = get_effective_mod("dex")
    proficiency = get_proficiency_bonus(level)

    # Combat Stats section (BG3-style)
    lines.append("")
    lines.append("▸ Combat Stats:")
    lines.append(f"  • Proficiency Bonus: +{proficiency}")
    init_sign = "+" if dex_mod >= 0 else ""
    lines.append(f"  • Initiative: {init_sign}{dex_mod}")

    # Speed (if available)
    speed = pc_data.get("speed", pc_data.get("movement_speed"))
    if speed is not None and speed != "":
        speed_str = str(speed).strip()
        # Match "ft" as a whole word (avoid appending duplicate units like "30 ft ft")
        if re.search(r"\bft\b", speed_str, re.IGNORECASE):
            lines.append(f"  • Speed: {speed_str}")
        else:
            lines.append(f"  • Speed: {speed_str} ft")

    # Spellcasting stats (if character is a spellcaster)
    class_name = pc_data.get("class_name", pc_data.get("class", ""))
    spellcasting_ability = get_spellcasting_ability(class_name)
    if spellcasting_ability:
        spell_mod = get_effective_mod(spellcasting_ability)
        spell_dc = 8 + proficiency + spell_mod
        spell_attack = proficiency + spell_mod
        spell_attack_sign = "+" if spell_attack >= 0 else ""
        ability_display = STAT_DISPLAY_NAMES.get(
            spellcasting_ability, spellcasting_ability.upper()
        )
        lines.append(f"  • Spell Save DC: {spell_dc} ({ability_display})")
        lines.append(f"  • Spell Attack: {spell_attack_sign}{spell_attack}")

    # Saving Throws section
    lines.append("")
    lines.append("▸ Saving Throws:")
    explicit_saves = pc_data.get("saving_throw_proficiencies", [])
    saving_throws = compute_saving_throws(
        class_name, effective_scores, proficiency, explicit_saves
    )
    for save in saving_throws:
        sign = "+" if save["bonus"] >= 0 else ""
        prof_marker = "●" if save["proficient"] else "○"
        lines.append(
            f"  {prof_marker} {STAT_DISPLAY_NAMES[save['stat']]}: {sign}{save['bonus']}"
        )

    # Skills section (condensed - only show proficient skills and key skills)
    skill_proficiencies = set()
    skill_expertise = set()
    # Check various locations for skill proficiencies
    skills_data = pc_data.get("skill_proficiencies", pc_data.get("skills", []))
    if isinstance(skills_data, list):
        for skill in skills_data:
            skill_proficiencies.add(str(skill).lower())
    elif isinstance(skills_data, dict):
        for skill, val in skills_data.items():
            if val:
                skill_proficiencies.add(str(skill).lower())
                # Case-insensitive expertise detection: match "expertise" (any case) or integer 2
                if isinstance(val, str):
                    val_normalized = val.strip().lower()
                    if val_normalized.isdigit():
                        val_normalized = int(val_normalized)
                else:
                    val_normalized = val
                if val_normalized in {"expertise", 2}:
                    skill_expertise.add(str(skill).lower())

    # Calculate and display skills
    lines.append("")
    lines.append("▸ Skills:")
    for skill_name, ability in sorted(SKILLS.items()):
        ability_mod = get_effective_mod(ability)
        is_proficient = skill_name in skill_proficiencies
        has_expertise = skill_name in skill_expertise
        skill_bonus = ability_mod
        if has_expertise:
            skill_bonus += proficiency * 2
            marker = "◆"  # Double proficiency marker
        elif is_proficient:
            skill_bonus += proficiency
            marker = "●"  # Proficient marker
        else:
            marker = "○"  # Not proficient
        sign = "+" if skill_bonus >= 0 else ""
        # Capitalize skill name properly
        display_name = skill_name.title()
        lines.append(f"  {marker} {display_name}: {sign}{skill_bonus}")

    # Passive stats
    perception_mod = get_effective_mod("wis")
    perception_prof = "perception" in skill_proficiencies
    perception_expertise = "perception" in skill_expertise
    passive_perception = 10 + perception_mod
    if perception_expertise:
        passive_perception += proficiency * 2
    elif perception_prof:
        passive_perception += proficiency

    investigation_mod = get_effective_mod("int")
    investigation_prof = "investigation" in skill_proficiencies
    investigation_expertise = "investigation" in skill_expertise
    passive_investigation = 10 + investigation_mod
    if investigation_expertise:
        passive_investigation += proficiency * 2
    elif investigation_prof:
        passive_investigation += proficiency

    lines.append("")
    lines.append("▸ Passives:")
    lines.append(f"  • Passive Perception: {passive_perception}")
    lines.append(f"  • Passive Investigation: {passive_investigation}")

    # Weapon Attack & Damage section
    weapon_proficiencies = get_weapon_proficiencies(pc_data)
    weapons = extract_equipped_weapons(pc_data, item_registry=game_state.get("item_registry"))
    if weapons:
        lines.append("")
        lines.append("▸ Weapons:")
        for weapon in weapons:
            name = weapon["name"]
            damage = weapon["damage"] or "—"

            # Determine attack modifier: finesse uses higher of STR/DEX, ranged uses DEX
            if weapon["is_finesse"]:
                attack_mod = max(str_mod, dex_mod)
            elif weapon["is_ranged"]:
                attack_mod = dex_mod
            else:
                attack_mod = str_mod

            explicit_prof = weapon.get("proficient")
            assumed_proficiency = False
            if explicit_prof is not None:
                is_proficient = bool(explicit_prof)
            elif weapon_proficiencies:
                lower_name = str(name).lower()
                is_proficient = any(
                    prof in lower_name or lower_name in prof
                    for prof in weapon_proficiencies
                )
            else:
                is_proficient = True
                assumed_proficiency = True

            prof_bonus = proficiency if is_proficient else 0
            attack_bonus = prof_bonus + attack_mod
            attack_sign = "+" if attack_bonus >= 0 else ""

            # Add damage modifier (same logic as attack)
            damage_mod_sign = "+" if attack_mod >= 0 else ""
            damage_display = damage
            if weapon["damage"] and weapon["damage"] != "—" and attack_mod != 0:
                damage_display = f"{damage}{damage_mod_sign}{attack_mod}"

            note = ""
            if not is_proficient:
                note = " (not proficient)"
            elif assumed_proficiency:
                note = " (assumes proficiency)"

            lines.append(
                f"  • {name}: {attack_sign}{attack_bonus} to hit | "
                f"{damage_display} damage{note}"
            )

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


def build_spells_summary(  # noqa: PLR0912, PLR0915
    game_state: dict, get_spell_level_fn=None
) -> str:
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
                    try:
                        current = int(data.get("current", data.get("max", 0)) or 0)
                        max_val = int(data.get("max", 0) or 0)
                        slot_parts.append(f"L{level}: {current}/{max_val}")
                    except (ValueError, TypeError):
                        continue
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
