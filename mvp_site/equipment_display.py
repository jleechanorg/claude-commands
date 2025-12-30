"""Equipment display and inventory formatting utilities.

This module handles extracting, categorizing, and formatting equipment data
for display in the UI. It provides deterministic (non-LLM) functions for
building equipment summaries from game state.

Public API:
- is_equipment_query: Detect if user is asking about equipment
- classify_equipment_query: Classify scope (backpack, weapons, equipped, all)
- extract_equipment_display: Extract equipment from game_state
- ensure_equipment_summary_in_narrative: Append equipment summary to narrative
"""

import re
from typing import Any

from mvp_site import logging_util

# Maximum backpack items to display in equipment summary
MAX_BACKPACK_ITEMS_DISPLAY: int = 3

# Standard dice notation pattern (e.g., 2d6+1, 1d8 - 2)
DICE_PATTERN = r"\b\d*d\d+(?:\s*[+-]\s*\d+)?\b"

# Canonical weapon slot labels used across filtering and categorization
WEAPON_SLOTS = {"weapon", "main hand", "off hand", "mainhand", "offhand"}

# Keywords that indicate user is asking about equipment/inventory
EQUIPMENT_QUERY_KEYWORDS = [
    "equipment",
    "inventory",
    "gear",
    "items",
    "what do i have",
    "show me my",
    "list my",
    "check my",
    "my stuff",
    "backpack",
    "weapons",
    "armor",
    "what am i wearing",
    "what am i carrying",
]


def is_equipment_query(user_input: str) -> bool:
    """Detect if user is asking about equipment/inventory."""
    user_lower = user_input.lower()
    return any(keyword in user_lower for keyword in EQUIPMENT_QUERY_KEYWORDS)


def classify_equipment_query(user_input: str) -> str:
    """Classify equipment query scope for narrative summaries.

    Returns one of: "backpack", "weapons", "equipped", "all".
    """
    user_lower = user_input.lower()

    if "backpack" in user_lower or "inventory" in user_lower:
        return "backpack"
    if "weapon" in user_lower or "weapons" in user_lower:
        return "weapons"
    if "equipped" in user_lower or "wearing" in user_lower or "armor" in user_lower:
        return "equipped"
    return "all"


def _filter_equipment_for_summary(  # noqa: PLR0912
    equipment_display: list[dict[str, str]], query_type: str
) -> list[dict[str, str]]:
    """Filter equipment_display entries by query scope."""
    if not equipment_display:
        return []

    def is_weapon_slot(slot: str) -> bool:
        return slot.lower() in WEAPON_SLOTS

    def is_backpack_slot(slot: str) -> bool:
        return slot.lower() == "backpack"

    def is_shield_item(name: str, stats: str) -> bool:
        """Detect shields/bucklers so they stay visible in equipped views."""
        combined = f"{name} {stats}".lower()
        return "shield" in combined or "buckler" in combined

    filtered: list[dict[str, str]] = []

    for item in equipment_display:
        slot = item.get("slot", "")
        if query_type == "backpack":
            if is_backpack_slot(slot):
                filtered.append(item)
        elif query_type == "weapons":
            if is_weapon_slot(slot):
                filtered.append(item)
        elif query_type == "equipped":
            if is_backpack_slot(slot):
                continue

            # Keep defensive off-hand gear (e.g., shields) but exclude weapons
            name = item.get("name", "")
            stats = item.get("stats", "")
            if is_weapon_slot(slot) and not is_shield_item(name, stats):
                continue

            filtered.append(item)
        else:
            filtered.append(item)

    # Deduplicate by name and stats while preserving order
    seen_items: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for item in filtered:
        name = item.get("name", "")
        stats = item.get("stats", "")
        if not name:
            continue
        item_key = (name, stats)
        if item_key in seen_items:
            continue
        seen_items.add(item_key)
        deduped.append(item)

    return deduped


def _count_equipment_mentions(narrative_text: str, items: list[dict[str, str]]) -> int:
    """Count how many distinct item names appear in narrative_text."""
    if not narrative_text or not items:
        return 0
    narrative_lower = narrative_text.lower()
    count = 0
    for item in items:
        name = item.get("name", "")
        if name and name.lower() in narrative_lower:
            count += 1
    return count


def _categorize_equipment_slot(slot: str) -> str:  # noqa: PLR0911
    """Map equipment slot to a display category."""
    slot_lower = slot.lower().strip()

    # Armor/worn equipment
    if slot_lower in {"head", "helmet", "helm", "crown"}:
        return "Head"
    if slot_lower in {"armor", "chest", "body", "torso", "plate"}:
        return "Armor"
    if slot_lower in {"boots", "feet", "footwear"}:
        return "Boots"
    if slot_lower in {"gloves", "hands", "gauntlets"}:
        return "Gloves"
    if slot_lower in {"cloak", "back", "cape", "mantle"}:
        return "Cloak"
    if slot_lower in {"ring", "ring1", "ring 1", "ring2", "ring 2", "rings"}:
        return "Rings"
    if slot_lower in {"amulet", "neck", "necklace", "pendant"}:
        return "Amulet"
    if slot_lower in {"belt", "waist"}:
        return "Belt"

    # Weapons
    if slot_lower in WEAPON_SLOTS:
        return "Weapons"

    # Backpack goes to miscellaneous categories based on item analysis
    if slot_lower == "backpack":
        return "Backpack"

    # Default
    return "Other"


def _classify_backpack_item(name: str, stats: str) -> str:  # noqa: PLR0911
    """Classify a backpack item into a subcategory based on name/stats."""
    name_lower = name.lower()
    stats_lower = stats.lower() if stats else ""
    combined = f"{name_lower} {stats_lower}"
    combined_normalized = re.sub(DICE_PATTERN, " ", combined)

    # Documents and papers
    if any(
        kw in combined
        for kw in [
            "document",
            "ledger",
            "cipher",
            "letter",
            "scroll",
            "note",
            "journal",
            "book",
            "tome",
            "manuscript",
            "deed",
            "contract",
        ]
    ):
        return "Documents"

    # Keys and access items
    if any(kw in combined for kw in ["key", "bypass", "lockpick", "access"]):
        return "Keys"

    # Rings and signets (in backpack)
    if any(kw in combined for kw in ["signet", "ring"]):
        return "Signets & Rings"

    # Currency and valuables
    if any(
        kw in combined
        for kw in ["coin", "gold", "platinum", "gem", "jewel", "currency", "purse"]
    ):
        return "Currency"

    # Consumable resources
    if any(kw in combined for kw in ["shard", "crystal", "soul", "essence", "potion"]):
        return "Resources"

    # Tools and kits
    if any(
        kw in combined
        for kw in ["kit", "tools", "thieves", "disguise", "artisan", "instrument"]
    ):
        return "Tools"

    # Magical items (evaluate before generic weapon keywords so enchanted weapons
    # like “Wand of Magic +1 spell DC” are treated as magical, not plain weapons)
    if any(
        kw in combined_normalized
        for kw in [
            "magical",
            "artifact",
            "enchanted",
            "+1",
            "+2",
            "+3",
            "dc",
            "spell",
            "arcane",
            "focus",
            "lens",
            "scepter",
            "amulet",
        ]
    ):
        return "Magical Items"

    # Weapons in backpack
    if any(
        kw in combined
        for kw in [
            "dagger",
            "sword",
            "rapier",
            "crossbow",
            "bow",
            "staff",
            "wand",
            "d4",
            "d6",
            "d8",
            "d10",
            "d12",
            "piercing",
            "slashing",
            "bludgeoning",
        ]
    ):
        return "Weapons"

    # Clothing and apparel
    if any(kw in combined for kw in ["clothes", "robe", "cloak", "boots", "gloves"]):
        return "Apparel"

    # Musical instruments
    if any(
        kw in combined
        for kw in ["lute", "flute", "drum", "harp", "instrument", "horn", "violin"]
    ):
        return "Instruments"

    # Default
    return "Miscellaneous"


def _get_backpack_importance(name: str, stats: str) -> int:  # noqa: PLR0911
    """Return importance score for backpack item (higher = more important)."""
    combined = f"{name} {stats}".lower()
    # Normalize dice notation to avoid false positives (2d4+2 shouldn't match +2 magic)
    combined_normalized = re.sub(DICE_PATTERN, " ", combined)

    # Magical/artifact items are most important
    if any(kw in combined_normalized for kw in ["artifact", "legendary", "+3"]):
        return 100
    if any(kw in combined_normalized for kw in ["+2", "very rare", "arcane"]):
        return 80
    if any(kw in combined_normalized for kw in ["+1", "magical", "rare", "enchanted"]):
        return 60

    # Potions and consumables are important
    if any(kw in combined_normalized for kw in ["potion", "scroll", "wand"]):
        return 50

    # Tools and kits useful for gameplay
    if any(kw in combined_normalized for kw in ["kit", "tools", "thieves"]):
        return 40

    # Documents may contain quest info
    if any(
        kw in combined_normalized for kw in ["document", "letter", "journal", "cipher"]
    ):
        return 30

    # Currency
    if any(kw in combined_normalized for kw in ["gold", "coin", "gem"]):
        return 20

    return 10


def _limit_backpack_for_display(
    items: list[dict[str, str]], max_items: int = MAX_BACKPACK_ITEMS_DISPLAY
) -> list[dict[str, str]]:
    """Limit backpack items to top N most important."""
    scored_items = []
    for item in items:
        name = item.get("name", "")
        stats = item.get("stats", "")
        importance = _get_backpack_importance(name, stats)
        scored_items.append((importance, item))

    # Sort by importance (descending) and take top items
    scored_items.sort(key=lambda x: x[0], reverse=True)

    return [item for _, item in scored_items[:max_items]]


def _build_equipment_summary(items: list[dict[str, str]], label: str) -> str:  # noqa: PLR0912
    """Build a well-formatted equipment summary grouped by category."""
    if not items:
        return ""

    # Define category display order
    category_order = [
        "Head",
        "Armor",
        "Cloak",
        "Gloves",
        "Belt",
        "Boots",
        "Amulet",
        "Rings",
        "Weapons",
        "Magical Items",
        "Tools",
        "Instruments",
        "Apparel",
        "Documents",
        "Keys",
        "Signets & Rings",
        "Currency",
        "Resources",
        "Miscellaneous",
        "Other",
    ]

    # Group items by category
    categorized: dict[str, list[str]] = {}

    for item in items:
        name = item.get("name", "").strip()
        stats = item.get("stats", "").strip()
        slot = item.get("slot", "").strip()

        if not name:
            continue

        # Determine category
        base_category = _categorize_equipment_slot(slot)
        if base_category == "Backpack":
            category = _classify_backpack_item(name, stats)
        else:
            category = base_category

        # Format the item string
        item_str = f"{name} ({stats})" if stats else name

        if category not in categorized:
            categorized[category] = []
        categorized[category].append(item_str)

    if not categorized:
        return ""

    # Build formatted output
    lines: list[str] = [f"━━━ {label} ━━━"]

    for category in category_order:
        if category in categorized:
            items_list = categorized[category]
            lines.append(f"▸ {category}:")
            for item_str in items_list:
                lines.append(f"  • {item_str}")

    # Add any categories not in our predefined order
    for category, items_list in categorized.items():
        if category not in category_order:
            lines.append(f"▸ {category}:")
            for item_str in items_list:
                lines.append(f"  • {item_str}")

    return "\n".join(lines)


def ensure_equipment_summary_in_narrative(
    narrative_text: str,
    equipment_display: list[dict[str, str]],
    *,
    user_input: str,
    min_item_mentions: int = 2,
) -> str:
    """Append deterministic equipment summary if narrative omits item names."""
    if not equipment_display:
        return narrative_text

    query_type = classify_equipment_query(user_input)
    filtered_items = _filter_equipment_for_summary(equipment_display, query_type)
    if not filtered_items:
        filtered_items = equipment_display

    mentions = _count_equipment_mentions(narrative_text, filtered_items)
    if mentions >= min_item_mentions:
        return narrative_text

    if query_type == "backpack":
        label = "Backpack items"
    elif query_type == "weapons":
        label = "Weapons"
    elif query_type == "equipped":
        label = "Equipped items"
    else:
        label = "Equipment summary"

    summary = _build_equipment_summary(filtered_items, label)
    if not summary:
        return narrative_text

    if narrative_text and not narrative_text.endswith("\n"):
        narrative_text = narrative_text.rstrip() + "\n\n"
    elif narrative_text:
        narrative_text = narrative_text + "\n"

    return f"{narrative_text}{summary}"


def extract_equipment_display(game_state: Any) -> list[dict[str, str]]:  # noqa: PLR0912
    """Extract equipment from game_state into structured display format.

    This is deterministic - reads directly from game_state, no LLM involved.
    Guarantees 100% accuracy of item names and stats.

    Supports two data formats:
    1. String IDs: Equipment slots contain item_id strings, looked up in item_registry
    2. Legacy inline: Equipment slots contain full descriptions like "Helm (stats)"
    """
    equipment_list: list[dict[str, str]] = []

    try:
        # Get item registry for string ID lookups
        item_registry = getattr(game_state, "item_registry", {}) or {}

        # Get player character data
        pc_data = (
            game_state.player_character_data
            if hasattr(game_state, "player_character_data")
            else {}
        )
        if isinstance(pc_data, dict):
            equipment = pc_data.get("equipment", {})
        else:
            equipment = getattr(pc_data, "equipment", {}) if pc_data else {}
            if hasattr(equipment, "to_dict"):
                equipment = equipment.to_dict()

        def resolve_item(item_ref: str) -> tuple[str, str]:
            """Resolve an item reference to (name, stats).

            If item_ref is a string ID in item_registry, use registry data.
            Otherwise, parse as inline "Name (stats)" format.
            """
            if item_ref in item_registry:
                item_data = item_registry[item_ref]
                name = item_data.get("name", item_ref)
                stats = item_data.get("stats", "")
                return name, stats
            # Legacy: parse inline format "Item Name (stats)"
            if "(" in str(item_ref):
                parts = str(item_ref).split("(", 1)
                name = parts[0].strip()
                stats = parts[1].rstrip(")").strip() if len(parts) > 1 else ""
                return name, stats
            return str(item_ref), ""

        # Extract equipped items (what player is actually wearing/wielding)
        # This includes armor slots, accessories, AND equipped weapons (main_hand, off_hand)
        equipped = equipment.get("equipped", {})
        for slot, item_ref in equipped.items():
            if item_ref:
                name, stats = resolve_item(item_ref)
                equipment_list.append(
                    {
                        "slot": slot.replace("_", " ").title(),
                        "name": name,
                        "stats": stats,
                    }
                )

        # Add distinct weapons from inventory array so backup weapons are visible alongside equipped ones
        weapons = equipment.get("weapons", [])
        # Include "weapon" slot in deduplication to handle equipped["weapon"] entries
        seen_weapon_entries: set[tuple[str, str]] = {
            (item["name"], item.get("stats", ""))
            for item in equipment_list
            if item.get("slot", "").lower() in WEAPON_SLOTS
        }
        for weapon_ref in weapons:
            if isinstance(weapon_ref, dict):
                name = weapon_ref.get("name", "Unknown Weapon")
                damage = weapon_ref.get("damage", "")
                properties = weapon_ref.get("properties", "")
                stats = " ".join(part for part in [damage, properties] if part).strip()
            else:
                name, stats = resolve_item(str(weapon_ref))
            if (name, stats) in seen_weapon_entries:
                continue
            seen_weapon_entries.add((name, stats))
            equipment_list.append({"slot": "Weapon", "name": name, "stats": stats})

        # Extract backpack items - limit to top 3 most important for cleaner UI
        # Full backpack is available in game_state when user asks for details
        all_backpack: list[dict[str, str]] = []
        backpack = equipment.get("backpack", [])
        for item in backpack:
            if isinstance(item, dict):
                name = item.get("name", "Unknown Item")
                stats = item.get("stats", "")
            else:
                name, stats = resolve_item(str(item))
            all_backpack.append({"slot": "Backpack", "name": name, "stats": stats})

        # Limit backpack to top 3 most important items
        limited_backpack = _limit_backpack_for_display(
            all_backpack, max_items=MAX_BACKPACK_ITEMS_DISPLAY
        )
        equipment_list.extend(limited_backpack)

    except Exception as e:
        logging_util.warning(f"Error extracting equipment display: {e}")

    return equipment_list
