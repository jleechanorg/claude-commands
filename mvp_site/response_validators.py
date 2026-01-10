"""Centralized LLM Response Validation Module

Consolidates validation logic for LLM-generated responses:
- Item/equipment validation (FULLY CENTRALIZED from equipment_display.py)
- LLM rejection detection (FULLY CENTRALIZED from llm_service.py)
- Story-mode required fields (CENTRALIZED; invoked via llm_service wrapper)
- Entity tracking validation (CENTRALIZED; invoked via llm_service wrapper)
- Planning block validation (CENTRALIZED; invoked via llm_service wrapper)
- Companion generation validation (CENTRALIZED; invoked via llm_service wrapper)

Functions:
- get_all_inventory_items: Extract inventory from game state
- validate_items_used: Check items_used against inventory
- comprehensive_item_validation: 3-layer item exploit defense
- extract_item_claims_from_input: Pre-process player input for items
- scan_narrative_for_unlisted_items: Post-process narrative for items
- check_llm_rejection: Detect if LLM rejected invalid claims
- check_missing_required_fields: Validate response schema
- validate_entity_tracking: Entity tracking validator (used via llm_service wrapper)
- validate_and_enforce_planning_block: Planning block validator (used via llm_service wrapper)
- check_missing_required_fields_story_mode: Story-mode required fields (used via llm_service wrapper)
- validate_companion_generation_response: Companion generation validator (used via llm_service wrapper)
"""

from __future__ import annotations

import re
from typing import Any

from mvp_site import constants, dice_integrity, logging_util
from mvp_site.narrative_sync_validator import NarrativeSyncValidator

__all__ = [
    "get_all_inventory_items",
    "validate_items_used",
    "comprehensive_item_validation",
    "extract_item_claims_from_input",
    "scan_narrative_for_unlisted_items",
    "check_llm_rejection",
    "validate_entity_tracking",
    "validate_planning_block",
    "validate_companion_generation",
    "validate_and_enforce_planning_block",
    "check_missing_required_fields_story_mode",
    "validate_companion_generation_response",
    "check_missing_required_fields",
]


# =============================================================================
# INVENTORY EXTRACTION
# =============================================================================


def get_all_inventory_items(game_state: Any) -> set[str]:  # noqa: PLR0912, PLR0915
    """Extract all item names from player inventory for validation.

    Returns a set of lowercase item names for case-insensitive matching.
    Includes: equipped items, weapons, and backpack contents.

    Args:
        game_state: Current GameState object

    Returns:
        Set of lowercase item names the player actually has
    """
    items: set[str] = set()

    try:
        # Get item registry for string ID lookups
        item_registry = getattr(game_state, "item_registry", {}) or {}

        # Get player character data
        pc_data = (
            game_state.player_character_data
            if hasattr(game_state, "player_character_data")
            else {}
        )

        # Helper to extract from dict or object
        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        raw_eq = get_val(pc_data, "equipment")
        raw_inv = get_val(pc_data, "inventory")

        # Process equipment
        if hasattr(raw_eq, "to_dict"):
            raw_eq = raw_eq.to_dict()

        equipment = {}
        inventory_items: list[Any] = []

        if isinstance(raw_eq, dict):
            equipment = raw_eq
        elif isinstance(raw_eq, list):
            inventory_items.extend(raw_eq)

        # Process inventory
        if hasattr(raw_inv, "to_dict"):
            raw_inv = raw_inv.to_dict()

        if isinstance(raw_inv, list):
            inventory_items.extend(raw_inv)
        elif isinstance(raw_inv, dict):
            if not equipment:
                equipment = raw_inv
            else:
                merged_equipment = dict(raw_inv)
                merged_equipment.update(equipment)
                equipment = merged_equipment

        def resolve_item_name(item_ref: Any) -> str:
            """Resolve an item reference to its name."""
            if not item_ref:
                return ""
            if isinstance(item_ref, dict):
                item_id = (
                    item_ref.get("item_id")
                    or item_ref.get("id")
                    or item_ref.get("itemId")
                    or item_ref.get("key")
                )
                if item_id and item_id in item_registry:
                    item_data = item_registry[item_id]
                    return str(item_data.get("name", item_id)).lower()
                name = item_ref.get("name") or item_ref.get("title") or item_id
                return str(name).lower() if name else ""
            if item_ref in item_registry:
                item_data = item_registry[item_ref]
                return str(item_data.get("name", item_ref)).lower()
            # Legacy: parse inline format "Item Name (stats)"
            if "(" in str(item_ref):
                parts = str(item_ref).split("(", 1)
                return parts[0].strip().lower()
            return str(item_ref).lower()

        # Extract equipped items
        equipped = equipment.get("equipped", {}) if isinstance(equipment, dict) else {}
        if isinstance(equipped, dict):
            for _slot, item_ref in equipped.items():
                name = resolve_item_name(item_ref)
                if name:
                    items.add(name)

        # Check flat-format equipment slots
        if isinstance(equipment, dict):
            equipment_slots = {
                "head",
                "body",
                "armor",
                "cloak",
                "neck",
                "hands",
                "feet",
                "ring",
                "ring_1",
                "ring_2",
                "instrument",
                "main_hand",
                "off_hand",
                "mainhand",
                "offhand",
                "weapon",
                "weapon_main",
                "weapon_secondary",
                "shield",
                "amulet",
                "necklace",
                "belt",
                "boots",
                "gloves",
                "bracers",
            }
            for slot in equipment_slots:
                if slot in equipment and (
                    not isinstance(equipped, dict) or slot not in equipped
                ):
                    item_data = equipment[slot]
                    if isinstance(item_data, dict) and not item_data.get(
                        "equipped", True
                    ):
                        continue
                    name = resolve_item_name(item_data)
                    if name:
                        items.add(name)

        # Extract weapons
        weapons = equipment.get("weapons", []) if isinstance(equipment, dict) else []
        for weapon_ref in weapons:
            if isinstance(weapon_ref, dict):
                name = weapon_ref.get("name", "")
                if name:
                    items.add(name.lower())
            elif weapon_ref:
                name = resolve_item_name(weapon_ref)
                if name:
                    items.add(name)

        # Extract backpack items
        backpack = equipment.get("backpack", []) if isinstance(equipment, dict) else []
        for item in backpack:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    items.add(name.lower())
            elif item:
                name = resolve_item_name(item)
                if name:
                    items.add(name)

        # Extract explicit inventory list if present
        if isinstance(equipment, dict):
            inventory_items.extend(equipment.get("inventory", []) or [])
        for item in inventory_items:
            name = resolve_item_name(item)
            if name:
                items.add(name)

    except Exception as e:
        logging_util.warning(f"⚠️ Error extracting inventory items: {e}")
        return set()

    return items


# =============================================================================
# ITEM NAME NORMALIZATION
# =============================================================================


def _normalize_item_name(item_name: str | None) -> str:
    """Normalize item name for fuzzy matching.

    Handles common variations like:
    - "my longsword" -> "longsword"
    - "the potion of healing" -> "potion of healing"
    - "a torch" -> "torch"
    """
    if not item_name:
        return ""
    normalized = str(item_name).lower().strip()
    # Remove common prefixes
    prefixes = ["my ", "the ", "a ", "an ", "his ", "her ", "their "]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return normalized


def _item_in_inventory(item_name: str, inventory: set[str]) -> bool:
    """Check if an item is in the player's inventory with fuzzy matching.

    Supports:
    - Exact match (case-insensitive)
    - Common variations ("healing potion" matches "potion of healing")

    Args:
        item_name: The item name to check
        inventory: Set of lowercase inventory item names

    Returns:
        True if item is in inventory, False otherwise
    """
    normalized = _normalize_item_name(item_name)

    # Exact match
    if normalized in inventory:
        return True

    # Check if claimed item is a substring of any inventory item
    # This allows "longsword" to match "longsword +1"
    # But PREVENTS "longsword" matching "sword" (upgrade exploit)
    return any(normalized in inv_item for inv_item in inventory)


# =============================================================================
# ITEM VALIDATION
# =============================================================================


def validate_items_used(
    items_used: list[str], game_state: Any
) -> tuple[bool, list[str], str]:
    """Validate that items_used are actually in the player's inventory.

    This is the core post-processing validator for item spawning exploits.
    Called after LLM response to catch cases where the LLM accepted a player
    claiming to use items they don't have.

    Args:
        items_used: List of item names the LLM says the player used
        game_state: Current GameState object

    Returns:
        tuple: (
            is_valid: bool - True if all items are in inventory,
            invalid_items: list[str] - Items that are NOT in inventory,
            rejection_message: str - Message to use if invalid
        )

    Example:
        >>> is_valid, invalid, msg = validate_items_used(
        ...     ["longsword", "ring of invisibility"],
        ...     game_state
        ... )
        >>> if not is_valid:
        ...     # Replace LLM narrative with rejection
        ...     narrative = msg
    """
    if not items_used:
        return True, [], ""

    inventory = get_all_inventory_items(game_state)
    invalid_items: list[str] = []

    for item in items_used:
        if not _item_in_inventory(item, inventory):
            invalid_items.append(item)

    if invalid_items:
        if len(invalid_items) == 1:
            rejection_message = (
                f"You reach for the {invalid_items[0]}, but realize you don't have one. "
                f"Check your inventory for what you actually possess."
            )
        else:
            items_list = ", ".join(invalid_items[:-1]) + f" and {invalid_items[-1]}"
            rejection_message = (
                f"You reach for the {items_list}, but realize you don't have them. "
                f"Check your inventory for what you actually possess."
            )

        logging_util.warning(
            f"⚠️ ITEM_SPAWNING_BLOCKED: Player tried to use items not in inventory: {invalid_items}"
        )
        return False, invalid_items, rejection_message

    return True, [], ""


# =============================================================================
# PRE-PROCESSING: Extract item claims from player input
# =============================================================================

# Patterns that indicate item usage/claim in player input
ITEM_CLAIM_PATTERNS = [
    # "take X from Y" / "grab X from Y"
    r"\b(?:take|grab|get|pull|retrieve|remove)\s+(?:the\s+|a\s+|an\s+|my\s+)?(.+?)\s+(?:from|out of|off)\b",
    # "drink X" / "use X" / "activate X"
    r"\b(?:drink|use|activate|consume|eat|apply)\s+(?:the\s+|a\s+|an\s+|my\s+)?(.+?)(?:\s+on|\s+to|$|[.,!?])",
    # "equip X" / "don X" / "wear X" / "put on X"
    r"\b(?:equip|don|wear|put on|wield)\s+(?:the\s+|a\s+|an\s+|my\s+)?(.+?)(?:$|[.,!?])",
    # "reach for X" / "pull out X"
    r"\b(?:reach for|pull out|draw)\s+(?:the\s+|a\s+|an\s+|my\s+)?(.+?)(?:$|[.,!?])",
    # "with my X" / "using my X"
    r"\b(?:with|using)\s+my\s+(.+?)(?:$|[.,!?])",
]

# Compiled patterns for efficiency
_COMPILED_CLAIM_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ITEM_CLAIM_PATTERNS]


def extract_item_claims_from_input(user_input: str) -> list[str]:
    """Extract potential item claims from player input text.

    Pre-processing step to identify items the player is claiming to use,
    even before the LLM sees the input. This enables validation even when
    the LLM fails to list items in items_used.

    Args:
        user_input: The player's action text

    Returns:
        List of extracted item names (may include false positives)

    Example:
        >>> extract_item_claims_from_input("Take the ring of invisibility from my bag")
        ['ring of invisibility']
        >>> extract_item_claims_from_input("I attack with my sword")
        ['sword']
    """
    claims: list[str] = []

    for pattern in _COMPILED_CLAIM_PATTERNS:
        matches = pattern.findall(user_input)
        for match in matches:
            # Clean up the match
            item = match.strip().rstrip(".,!?")
            # Filter out very short matches and common false positives
            if len(item) >= 3 and item.lower() not in {
                "it",
                "the",
                "this",
                "that",
                "them",
            }:
                claims.append(item)

    return claims


# =============================================================================
# POST-PROCESSING: Scan narrative for unlisted items
# =============================================================================

# Common item-related words to detect in narrative
ITEM_INDICATOR_WORDS = [
    "potion",
    "ring",
    "amulet",
    "scroll",
    "wand",
    "staff",
    "rod",
    "sword",
    "dagger",
    "bow",
    "arrow",
    "shield",
    "armor",
    "helm",
    "bag",
    "pouch",
    "sack",
    "cloak",
    "boots",
    "gloves",
    "gauntlets",
    "necklace",
    "bracelet",
    "belt",
    "robe",
    "orb",
    "gem",
    "stone",
    "vial",
    "flask",
    "bottle",
    "torch",
    "lantern",
    "rope",
    "key",
]


def scan_narrative_for_unlisted_items(
    narrative: str, items_used: list[str], inventory: set[str]
) -> list[str]:  # noqa: PLR0912
    """Scan narrative for item references not in items_used or inventory.

    Post-processing safety net that catches items the LLM may have
    "silently" allowed by mentioning in narrative without listing
    in items_used.

    Args:
        narrative: The LLM-generated narrative text
        items_used: Items the LLM listed in items_used field
        inventory: Set of valid inventory item names (lowercase)

    Returns:
        List of suspicious item references found in narrative but not
        in items_used or inventory

    Example:
        >>> scan_narrative_for_unlisted_items(
        ...     "You drink the potion of invisibility and vanish.",
        ...     [],  # LLM didn't list it
        ...     {"longsword", "torch"}  # Player doesn't have it
        ... )
        ['potion of invisibility']
    """
    suspicious: list[str] = []
    narrative_lower = narrative.lower()

    # Normalize items_used for comparison
    items_used_normalized = {
        _normalize_item_name(item)
        for item in (items_used or [])
        if _normalize_item_name(item)
    }

    # Stopwords that shouldn't be part of item names
    stopwords = {
        "and",
        "but",
        "or",
        "the",
        "a",
        "an",
        "to",
        "from",
        "in",
        "on",
        "at",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "you",
        "your",
        "his",
        "her",
        "its",
        "their",
        "our",
        "my",
        "i",
        "he",
        "she",
        "it",
        "they",
        "we",
        "who",
        "which",
        "that",
        "this",
        "these",
        "those",
        "with",
        "for",
        "as",
        "by",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "up",
        "down",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "can",
        "just",
        "now",
        "also",
        "back",
        "even",
        "still",
        "way",
        "well",
        "new",
        "first",
        "glows",
        "glowing",
        "appears",
        "feel",
        "feels",
        "surge",
        "surges",
        "vanish",
        "vanishes",
        "drink",
        "drinks",
        "don",
        "dons",
        "wear",
        "wears",
    }

    # Look for item indicator words in narrative
    for indicator in ITEM_INDICATOR_WORDS:
        if indicator in narrative_lower:
            # Find the indicator and extract words after "of" if present
            pattern = rf"\b{indicator}(?:\s+of\s+(the\s+)?(\w+(?:\s+\w+){{0,2}}))?"
            for match in re.finditer(pattern, narrative_lower):
                the_part = match.group(1)  # "the " or None
                name_part = match.group(2)  # The actual name words

                if name_part:
                    # Clean up - remove stopwords from end
                    words = name_part.split()
                    while words and words[-1] in stopwords:
                        words.pop()
                    if words:
                        # Preserve "the" if it was there (e.g., "amulet of the Wise Beholder")
                        if the_part:
                            item_name = f"{indicator} of the {' '.join(words)}"
                        else:
                            item_name = f"{indicator} of {' '.join(words)}"
                    else:
                        item_name = indicator
                else:
                    item_name = indicator

                normalized = _normalize_item_name(item_name)

                # Check if this item is:
                # 1. Not in items_used (LLM didn't declare it)
                # 2. Not in inventory (player doesn't have it)
                if (
                    normalized not in items_used_normalized
                    and not _item_in_inventory(normalized, inventory)
                    and not any(
                        _normalize_item_name(s) == normalized for s in suspicious
                    )
                ):
                    suspicious.append(item_name)

    return suspicious


# =============================================================================
# COMPREHENSIVE 3-LAYER VALIDATION
# =============================================================================


def comprehensive_item_validation(  # noqa: PLR0912
    user_input: str,
    narrative: str,
    items_used: list[str],
    game_state: Any,
) -> tuple[bool, list[str], str]:
    """Comprehensive 3-layer item validation.

    Combines:
    1. Pre-processing: Extract item claims from player input
    2. LLM audit: Check items_used against inventory
    3. Post-processing: Scan narrative for unlisted items

    Args:
        user_input: Original player input text
        narrative: LLM-generated narrative response
        items_used: Items the LLM declared in items_used field
        game_state: Current game state

    Returns:
        tuple: (is_valid, invalid_items, rejection_message)
    """
    inventory = get_all_inventory_items(game_state)
    all_invalid: list[str] = []

    # CRITICAL: Do NOT skip validation when inventory is empty
    # An empty inventory means player has NO items - any item claims should be rejected
    # Only log for debugging, but continue validation
    if not inventory:
        logging_util.debug(
            "ITEM_VALIDATION: Empty inventory - any item claims will be flagged as invalid"
        )

    # Layer 1: Pre-processing - check items extracted from player input
    input_claims = extract_item_claims_from_input(user_input)
    for claim in input_claims:
        normalized = _normalize_item_name(claim)
        if not normalized:
            continue
        if not _item_in_inventory(claim, inventory) and normalized not in [
            _normalize_item_name(i) for i in all_invalid
        ]:
            all_invalid.append(claim)

    # Layer 2: LLM audit trail - check items_used
    for item in items_used or []:
        normalized = _normalize_item_name(item)
        if not normalized:
            continue
        if not _item_in_inventory(item, inventory) and normalized not in [
            _normalize_item_name(i) for i in all_invalid
        ]:
            all_invalid.append(item)

    # Layer 3: Post-processing - scan narrative for unlisted items
    narrative_suspicious = scan_narrative_for_unlisted_items(
        narrative, items_used, inventory
    )
    for item in narrative_suspicious:
        normalized = _normalize_item_name(item)
        if not normalized:
            continue
        if normalized not in [_normalize_item_name(i) for i in all_invalid]:
            all_invalid.append(item)

    if all_invalid:
        if len(all_invalid) == 1:
            rejection_message = (
                f"You reach for the {all_invalid[0]}, but realize you don't have one. "
                f"Check your inventory for what you actually possess."
            )
        else:
            items_list = ", ".join(all_invalid[:-1]) + f" and {all_invalid[-1]}"
            rejection_message = (
                f"You reach for the {items_list}, but realize you don't have them. "
                f"Check your inventory for what you actually possess."
            )

        logging_util.warning(
            f"⚠️ ITEM_EXPLOIT_BLOCKED (3-layer): Invalid items detected: {all_invalid}"
        )
        return False, all_invalid, rejection_message

    return True, [], ""


# =============================================================================
# LLM REJECTION DETECTION
# =============================================================================

# Rejection phrases that indicate LLM already handled an exploit attempt
_LLM_REJECTION_PHRASES = [
    "don't have",
    "do not have",
    "don't possess",
    "do not possess",
    "possess neither",
    "have neither",
    "no such",
    "doesn't exist",
    "does not exist",
    "find no",
    "find nothing",
    "finds only",
    "find only",
    "nothing there",
    "nothing but",
    "not in your",
    "cannot find",
    "can't find",
    "nowhere to be found",
    "unable to",
    "no magical",
    "no such item",
    "only the gear",
    "only what you brought",
]


def check_llm_rejection(narrative: str, invalid_items: list[str]) -> bool:
    """Check if the LLM already rejected an exploit attempt in its narrative.

    This prevents overwriting a creative LLM rejection with a generic message.
    The LLM may use phrases like "you possess neither X nor Y" or "your hand
    finds only your rope" - these ARE rejections and should be preserved.

    Args:
        narrative: The LLM-generated narrative text
        invalid_items: List of invalid items that were detected

    Returns:
        True if the LLM appears to have already rejected the exploit
    """
    narrative_lower = narrative.lower()

    # Check for rejection phrases
    for phrase in _LLM_REJECTION_PHRASES:
        if phrase in narrative_lower:
            return True

    # Also check if the narrative explicitly mentions not having one of the items
    for item in invalid_items:
        item_lower = item.lower()
        # Check for patterns like "you don't have a [item]" or "no [item]"
        if f"no {item_lower}" in narrative_lower:
            return True
        if f"without {item_lower}" in narrative_lower:
            return True
        if f"lack {item_lower}" in narrative_lower:
            return True

    return False


# =============================================================================
# ENTITY TRACKING VALIDATION
# =============================================================================


def validate_entity_tracking(
    response_text: str,
    expected_entities: list[str],
    game_state: Any,
    *,
    logger: Any = logging_util,
) -> str:
    """Validate that the narrative includes all expected entities.

    Centralized version of the old `llm_service._validate_entity_tracking`.
    This validation is currently advisory (logs warnings) and does not mutate
    the narrative text.
    """
    try:
        location = "Unknown"
        if hasattr(game_state, "world_data"):
            world_data = getattr(game_state, "world_data", {}) or {}
            if isinstance(world_data, dict):
                location = world_data.get("current_location_name", "Unknown")
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=response_text,
            expected_entities=expected_entities,
            location=location,
        )
        if not validation_result.all_entities_present:
            logger.warning(
                "ENTITY_TRACKING_VALIDATION: Narrative failed entity validation"
            )
            logger.warning(f"Missing entities: {validation_result.entities_missing}")
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Validation warning: {warning}")
    except Exception as e:
        logger.warning(f"ENTITY_TRACKING_VALIDATION: Failed to validate: {e}")

    return response_text


# =============================================================================
# PLANNING BLOCK VALIDATION
# =============================================================================


def validate_planning_block(planning_block: dict[str, Any] | None) -> tuple[bool, str]:
    """Validate planning block structure and content.

    Args:
        planning_block: Planning block from LLM response

    Returns:
        tuple: (is_valid, error_message)
    """
    if not planning_block:
        return False, "Missing planning block"

    required_fields = ["thinking", "choices"]
    missing = [f for f in required_fields if f not in planning_block]

    if missing:
        return False, f"Planning block missing fields: {', '.join(missing)}"

    choices = planning_block.get("choices", {})
    if not isinstance(choices, dict) or len(choices) < 2:
        return False, "Planning block must have at least 2 choices"

    return True, ""


def validate_and_enforce_planning_block(
    response_text: str | None,
    structured_response: Any = None,
    *,
    logger: Any = logging_util,
) -> str:
    """Validate that `structured_response.planning_block` exists and is JSON.

    Centralized version of the old `llm_service._validate_and_enforce_planning_block`.
    This function does not generate fallback planning blocks; it logs and returns
    `response_text` unchanged.
    """
    if response_text is None:
        logger.warning(
            "🔍 VALIDATION_INPUT: Response text is None, returning empty string"
        )
        return ""

    # Skip planning block validation if AI response indicates mode switch
    if "[Mode: DM MODE]" in response_text or "[Mode: GOD MODE]" in response_text:
        logger.info(
            "Response indicates mode switch - skipping planning block validation"
        )
        return response_text

    planning_block = getattr(structured_response, "planning_block", None)
    if planning_block:
        if isinstance(planning_block, dict):
            has_content = planning_block.get("thinking", "").strip() or (
                planning_block.get("choices")
                and len(planning_block.get("choices", {})) > 0
            )
            if has_content:
                logger.info("✅ Planning block found in JSON structured response")
                return response_text
            logger.warning(
                "⚠️ PLANNING_BLOCK_EMPTY: Planning block exists but has no content"
            )
            return response_text

        logger.error(
            "❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: "
            f"Found {type(planning_block).__name__} planning block, only JSON format is allowed"
        )
        return response_text

    logger.warning(
        "⚠️ PLANNING_BLOCK_MISSING: Story mode response missing required planning block. "
        "The LLM should have generated this - no fallback will be used."
    )
    return response_text


# =============================================================================
# COMPANION VALIDATION
# =============================================================================


def validate_companion_generation(
    companions: list[dict[str, Any]], max_companions: int = 3
) -> tuple[bool, str]:
    """Validate companion generation constraints.

    Args:
        companions: List of generated companion data
        max_companions: Maximum allowed companions (default 3)

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(companions) > max_companions:
        return (
            False,
            f"Too many companions: {len(companions)} (max {max_companions})",
        )

    # Check for duplicate names
    names = [c.get("name", "").lower() for c in companions if c.get("name")]
    if len(names) != len(set(names)):
        return False, "Duplicate companion names detected"

    return True, ""


def validate_companion_generation_response(
    gemini_response: Any,
    expected_companion_count: int,
    *,
    logger: Any = logging_util,
) -> None:
    """Validate companion generation results.

    Centralized version of the old `llm_service._validate_companion_generation`.
    This logs companion counts but does not throw or mutate state.
    """
    structured_response = getattr(gemini_response, "structured_response", None)
    if not structured_response:
        logger.error(
            "🎭 COMPANION GENERATION: ❌ No structured response received from Gemini!"
        )
        return

    extra_fields = getattr(structured_response, "extra_fields", {})
    companions = (
        extra_fields.get("companions", {}) if isinstance(extra_fields, dict) else {}
    )
    npc_data = (
        extra_fields.get("npc_data", {}) if isinstance(extra_fields, dict) else {}
    )

    state_updates = getattr(structured_response, "state_updates", {}) or {}
    if not npc_data and isinstance(state_updates, dict) and "npc_data" in state_updates:
        npc_data = state_updates["npc_data"]
    if (
        not companions
        and isinstance(state_updates, dict)
        and "companions" in state_updates
    ):
        companions = state_updates["companions"]

    if not isinstance(companions, dict):
        companions = {}
    if not isinstance(npc_data, dict):
        npc_data = {}

    companion_names = set(companions.keys())
    allied_npcs = {
        name
        for name, data in npc_data.items()
        if isinstance(data, dict) and data.get("relationship") in ["companion", "ally"]
    }
    unique_allied_npcs = allied_npcs - companion_names

    total_companions = len(companion_names) + len(unique_allied_npcs)
    if total_companions == 0:
        logger.warning("🎭 No companions generated despite request")
    elif total_companions < expected_companion_count:
        logger.warning(
            f"🎭 Only {total_companions}/{expected_companion_count} companions generated"
        )
    else:
        logger.info(f"🎭 {total_companions} companions generated successfully")


# =============================================================================
# REQUIRED FIELDS VALIDATION
# =============================================================================


def check_missing_required_fields(
    response_data: dict[str, Any], required_fields: list[str]
) -> list[str]:
    """Check for missing required fields in LLM response.

    Args:
        response_data: Parsed LLM response
        required_fields: List of field names that must be present

    Returns:
        List of missing field names (empty if all present)
    """
    missing = []
    for field in required_fields:
        if field not in response_data or response_data[field] is None:
            missing.append(field)
    return missing


def check_missing_required_fields_story_mode(
    structured_response: Any,
    mode: str,
    *,
    is_god_mode: bool = False,
    is_dm_mode: bool = False,
    require_dice_rolls: bool = False,
    dice_integrity_violation: bool = False,
    require_social_hp_challenge: bool = False,
) -> list[str]:
    """Story-mode required-fields checker (centralized from llm_service).

    Mirrors `llm_service._check_missing_required_fields` so llm_service can delegate.
    """
    if mode != constants.MODE_CHARACTER or is_god_mode or is_dm_mode:
        return []

    if not structured_response:
        return ["planning_block", "session_header"]

    missing: list[str] = []

    planning_block = getattr(structured_response, "planning_block", None)
    if not planning_block or not isinstance(planning_block, dict):
        missing.append("planning_block")
    else:
        thinking_value = planning_block.get("thinking", "")
        has_thinking = isinstance(thinking_value, str) and bool(thinking_value.strip())

        choices_value = planning_block.get("choices")
        has_choices = isinstance(choices_value, dict) and len(choices_value) > 0

        if not (has_thinking or has_choices):
            missing.append("planning_block")

    session_header = getattr(structured_response, "session_header", None)
    if not session_header or not str(session_header).strip():
        missing.append("session_header")

    dice_integrity.add_missing_dice_fields(
        missing,
        structured_response=structured_response,
        require_dice_rolls=require_dice_rolls,
        dice_integrity_violation=dice_integrity_violation,
    )

    if require_social_hp_challenge:
        social_hp_challenge = getattr(structured_response, "social_hp_challenge", None)
        is_missing = True
        if isinstance(social_hp_challenge, dict):
            npc_name = str(social_hp_challenge.get("npc_name", "")).strip()
            objective = str(social_hp_challenge.get("objective", "")).strip()
            resistance = str(social_hp_challenge.get("resistance_shown", "")).strip()
            social_hp_val = social_hp_challenge.get("social_hp")
            social_hp_max = social_hp_challenge.get("social_hp_max")
            is_missing = not (
                npc_name
                and objective
                and resistance
                and social_hp_val is not None
                and isinstance(social_hp_max, (int, float))
                and social_hp_max > 0
            )
        if is_missing:
            missing.append("social_hp_challenge")

    return missing
