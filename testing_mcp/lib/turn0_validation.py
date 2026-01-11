"""
Turn 0 (Campaign Creation) validation utilities.

Validates what users see immediately after creating a campaign,
before sending any messages.
"""

from typing import Dict, Any, Optional


PLACEHOLDER_TEXT = "[Character Creation Mode - Story begins after character is complete]"
MIN_NARRATIVE_LENGTH = 100  # Minimum length for actual content


def validate_turn0_opening_story(
    campaign_result: Dict[str, Any],
    god_mode: Optional[Dict[str, Any]] = None,
    expect_placeholder: bool = False,
) -> tuple[bool, str]:
    """
    Validate Turn 0 opening_story content.

    Args:
        campaign_result: Result from create_campaign MCP call
        god_mode: God Mode template data (if any)
        expect_placeholder: If True, expect placeholder (empty char creation)
                          If False, expect actual narrative

    Returns:
        (success: bool, message: str)
    """
    opening_story = campaign_result.get("opening_story", "")

    # Check if God Mode has pre-populated character
    has_god_mode_character = (
        god_mode
        and isinstance(god_mode, dict)
        and god_mode.get("character")
        and isinstance(god_mode.get("character"), dict)
    )

    # For God Mode with character: Should have immediate narrative
    if has_god_mode_character:
        if PLACEHOLDER_TEXT in opening_story:
            return False, (
                f"God Mode with character should show immediate narrative, "
                f"got placeholder instead. Opening story: '{opening_story[:100]}...'"
            )

        if len(opening_story) < MIN_NARRATIVE_LENGTH:
            return False, (
                f"God Mode with character should have substantial narrative, "
                f"got only {len(opening_story)} characters: '{opening_story}'"
            )

        return True, f"God Mode immediate narrative present ({len(opening_story)} chars)"

    # For empty character creation: Placeholder is acceptable
    if expect_placeholder:
        if PLACEHOLDER_TEXT not in opening_story:
            # Not a failure, but worth noting
            return True, (
                f"Empty character creation can have placeholder, "
                f"but got narrative ({len(opening_story)} chars) - this is fine"
            )

        return True, "Placeholder shown for empty character creation (expected)"

    # For regular campaigns: Should have narrative
    if len(opening_story) < MIN_NARRATIVE_LENGTH:
        return False, (
            f"Regular campaign should have opening narrative, "
            f"got only {len(opening_story)} characters"
        )

    return True, f"Opening story present ({len(opening_story)} chars)"


def log_turn0_validation(
    campaign_result: Dict[str, Any],
    god_mode: Optional[Dict[str, Any]] = None,
    log_func = print,
) -> bool:
    """
    Validate and log Turn 0 opening_story.

    Args:
        campaign_result: Result from create_campaign MCP call
        god_mode: God Mode template data (if any)
        log_func: Logging function (default: print)

    Returns:
        True if validation passed
    """
    opening_story = campaign_result.get("opening_story", "")
    campaign_id = campaign_result.get("campaign_id", "unknown")

    log_func(f"✅ Campaign created: {campaign_id}")
    log_func(f"📊 Turn 0 Validation:")
    log_func(f"   Opening story length: {len(opening_story)} characters")

    # Show preview
    preview = opening_story[:150] if len(opening_story) > 150 else opening_story
    log_func(f"   Preview: {preview}...")

    # Determine if we expect placeholder:
    # - God Mode WITHOUT character: expect placeholder (rare, but possible)
    # - Regular campaigns (no god_mode): expect placeholder (character creation from scratch)
    # - God Mode WITH character: expect immediate narrative (character review)
    has_god_mode_character = (
        god_mode
        and isinstance(god_mode, dict)
        and god_mode.get("character")
        and isinstance(god_mode.get("character"), dict)
    )

    # Regular campaigns (no god_mode) should expect placeholder since ALL campaigns
    # start in character creation mode per mvp_site/world_logic.py:1520
    expect_placeholder = not has_god_mode_character

    # Run validation
    success, message = validate_turn0_opening_story(
        campaign_result, god_mode, expect_placeholder=expect_placeholder
    )

    if success:
        log_func(f"   ✅ {message}")
    else:
        log_func(f"   ❌ {message}")

    return success
