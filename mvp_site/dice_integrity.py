from __future__ import annotations

import os
import re
from typing import Any

from mvp_site import constants, dice, dice_strategy, logging_util
from mvp_site.game_state import GameState, format_tool_results_text
from mvp_site.narrative_response_schema import NarrativeResponse

DICE_ROLL_PATTERN = re.compile(
    r"\b\d*d\d+(?:\s*[+\-]\s*\d+)?\b|\brolls?\s+(?:a\s+)?\d+\b",
    re.IGNORECASE,
)
_NARRATIVE_DICE_NOTATION_PATTERN = re.compile(
    r"\b\d*d\d+(?:\s*[+\-]\s*\d+)?\b", re.IGNORECASE
)
_NARRATIVE_DICE_TAG_PATTERN = re.compile(r"\[dice:[^\]]+\]", re.IGNORECASE)
_NARRATIVE_DICE_ROLL_RESULT_PATTERN = re.compile(
    r"\brolls?\s+(?:a\s+)?\d+\b", re.IGNORECASE
)
_NARRATIVE_DICE_CONTEXT_PATTERN = re.compile(
    r"\b(attack|hit|damage|save|saving throw|skill|check|initiative|ac|dc)\b",
    re.IGNORECASE,
)
_NARRATIVE_DICE_SCAN_MAX_CHARS = 5000


def _narrative_contains_dice(text: str) -> bool:
    if not text:
        return False
    if len(text) > _NARRATIVE_DICE_SCAN_MAX_CHARS:
        text = text[:_NARRATIVE_DICE_SCAN_MAX_CHARS]

    if _NARRATIVE_DICE_TAG_PATTERN.search(text):
        return True
    if _NARRATIVE_DICE_NOTATION_PATTERN.search(text):
        return True

    # "rolls a 15" is only treated as dice if nearby context suggests a check/attack
    for match in _NARRATIVE_DICE_ROLL_RESULT_PATTERN.finditer(text):
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        window = text[start:end]
        if _NARRATIVE_DICE_CONTEXT_PATTERN.search(window):
            return True

    return False


def _detect_narrative_dice_fabrication(
    *,
    narrative_text: str,
    structured_response: NarrativeResponse | None,
    api_response: Any,
    code_execution_evidence: dict[str, Any] | None,
) -> bool:
    """Detect dice patterns in narrative OR structured response that lack tool/code_execution evidence."""
    # CRITICAL FIX: Check for dice in BOTH narrative AND structured response
    # Cerebras may put dice only in structured dice_rolls field, not narrative text
    has_dice_in_narrative = narrative_text and _narrative_contains_dice(narrative_text)

    has_dice_in_structured = False
    if structured_response:
        dice_rolls = getattr(structured_response, "dice_rolls", None)
        dice_audit_events = getattr(structured_response, "dice_audit_events", None)
        has_dice_in_structured = (
            isinstance(dice_rolls, list) and any(str(r).strip() for r in dice_rolls)
        ) or (isinstance(dice_audit_events, list) and any(dice_audit_events))

    dice.log_narrative_dice_detected(bool(has_dice_in_narrative))

    dice.log_dice_fabrication_check(
        has_dice_in_narrative=bool(has_dice_in_narrative),
        has_dice_in_structured=has_dice_in_structured,
        code_execution_used=(
            code_execution_evidence.get("code_execution_used")
            if code_execution_evidence
            else "N/A"
        ),
        tool_requests_executed=getattr(api_response, "_tool_requests_executed", "N/A"),
        debug_enabled=os.getenv("DICE_INTEGRITY_DEBUG", "").lower() == "true",
    )

    # If no dice anywhere, no fabrication possible
    if not has_dice_in_narrative and not has_dice_in_structured:
        return False

    # GREEN FIX (Dec 2024): Use rng_verified instead of code_execution_used
    # This detects fabrication via print('{"rolls": [16]}') without random.randint()
    if code_execution_evidence:
        rng_verified = code_execution_evidence.get("rng_verified", False)
        if rng_verified:
            return False  # Dice came from actual RNG, not fabrication
        # At this point rng_verified=False, check if code was executed without RNG
        code_execution_used = code_execution_evidence.get("code_execution_used", False)
        if code_execution_used:
            dice.log_code_exec_fabrication_violation()
            # This is fabrication - code ran but didn't use RNG
            return True

    # CRITICAL FIX: Don't blindly trust tool_requests_executed flag
    # Verify that tool_results actually contain dice data (non-empty, valid results)
    tool_requests_executed = getattr(api_response, "_tool_requests_executed", None)
    tool_results = getattr(api_response, "_tool_results", None)

    dice.log_tool_results_inspection(
        tool_results=tool_results,
        debug_enabled=os.getenv("DICE_INTEGRITY_DEBUG", "").lower() == "true",
    )

    # ENHANCED: Only accept dice-specific tool results (prevents non-dice tool loophole)
    if tool_requests_executed and tool_results:
        # Verify tool_results contain dice tools specifically
        # This prevents accepting non-dice tools (e.g., search_location) as proof
        if _has_dice_tool_results(tool_results):
            return False  # Dice tool results valid, dice are real

        # Check if dice tools were called but returned errors (e.g., missing dc_reasoning)
        # This is NOT fabrication - the LLM tried to use tools correctly but failed validation
        has_tool_errors, tool_errors = _has_dice_tool_errors(tool_results)
        if has_tool_errors:
            logging_util.warning(
                logging_util.with_campaign(
                    f"🎲 DICE_TOOL_ERROR: Dice tools called but returned errors: {tool_errors}. "
                    "This is a tool validation failure, not fabrication. Will reprompt."
                )
            )
            # Still return True to trigger reprompt, but with better context
            return True

        # If we get here, tool_requests_executed=True but tool_results lack dice tools
        # This is suspicious - LLM may have called a non-dice tool and fabricated dice
        # Fall through to fabrication check

    # If we found dice but no tool/code_execution evidence, that's FABRICATION
    if has_dice_in_narrative or has_dice_in_structured:
        dice.log_dice_fabrication_detected(
            has_dice_in_narrative=bool(has_dice_in_narrative),
            has_dice_in_structured=has_dice_in_structured,
        )
        return True

    # Backward compatibility: if metadata is missing and no dice detected, be permissive
    if tool_requests_executed is None and code_execution_evidence is None:
        return False

    # If we got here, something unexpected happened
    return False


def add_missing_dice_fields(
    missing: list[str],
    *,
    structured_response: NarrativeResponse | None,
    require_dice_rolls: bool,
    dice_integrity_violation: bool,
) -> None:
    """Append missing dice fields based on current enforcement policy."""
    if require_dice_rolls:
        dice_rolls = getattr(structured_response, "dice_rolls", None)
        has_dice_rolls = isinstance(dice_rolls, list) and any(
            str(r).strip() for r in dice_rolls
        )
        if not has_dice_rolls:
            missing.append("dice_rolls")

    if dice_integrity_violation:
        missing.append("dice_integrity")


def build_dice_integrity_reprompt_lines(
    dice_roll_strategy: str | None,
) -> list[str]:
    """Return dice integrity reprompt guidance based on strategy."""
    if dice_roll_strategy == dice_strategy.DICE_STRATEGY_CODE_EXECUTION:
        return [
            "- DICE INTEGRITY VIOLATION: Your response claims dice_rolls but you did NOT "
            "execute code to generate them. Dice values are UNKNOWABLE without execution - "
            "you cannot predict random.randint() results. You MUST use code_execution:\n"
            "  * Execute Python code with random.randint() to generate dice rolls\n"
            "Do NOT write dice values directly in narrative. Regenerate with ACTUAL code execution."
        ]
    if dice_roll_strategy == dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE:
        return [
            "- DICE INTEGRITY VIOLATION: Your dice tool call failed or was not made. "
            "You MUST use tool_requests with ALL required parameters:\n"
            "  * roll_skill_check REQUIRES: skill_name, attribute_modifier, dc, AND dc_reasoning\n"
            "  * roll_saving_throw REQUIRES: save_type, attribute_modifier, dc, AND dc_reasoning\n"
            "  * dc_reasoning MUST explain WHY you chose this DC BEFORE seeing the roll\n"
            "Example: {\"tool\": \"roll_skill_check\", \"args\": {\"skill_name\": \"perception\", "
            "\"attribute_modifier\": 3, \"dc\": 15, \"dc_reasoning\": \"guard is alert but area is noisy\"}}\n"
            "Do NOT write dice values directly in narrative. Regenerate using tool_requests with dc_reasoning."
        ]
    return [
        "- DICE INTEGRITY VIOLATION: Your dice tool call failed or you did not execute code/tools. "
        "Dice values are UNKNOWABLE without execution. You MUST either:\n"
        "  * Use code_execution: Execute Python code with random.randint() to generate dice\n"
        "  * Use tool_requests with ALL required params:\n"
        "    - roll_skill_check/roll_saving_throw REQUIRE dc_reasoning (explain DC choice BEFORE roll)\n"
        "    - Example: {\"tool\": \"roll_skill_check\", \"args\": {\"skill_name\": \"perception\", "
        "\"dc\": 15, \"dc_reasoning\": \"guard is alert\"}}\n"
        "Do NOT write dice values directly in narrative. Regenerate with ACTUAL execution and dc_reasoning."
    ]


def build_dice_processing_metadata(
    *,
    api_response: Any,
    dice_roll_strategy: str,
    capture_tools: bool = True,
) -> dict[str, Any]:
    """Build dice-specific processing metadata for downstream auditing."""
    metadata: dict[str, Any] = {"dice_strategy": dice_roll_strategy}
    if not capture_tools:
        return metadata

    tool_results = getattr(api_response, "_tool_results", None)
    if tool_results is not None:
        metadata["tool_results"] = tool_results
        metadata["tool_requests_executed"] = bool(
            getattr(api_response, "_tool_requests_executed", False)
        )
    return metadata


def apply_dice_metadata_to_structured_response(
    *,
    structured_response: NarrativeResponse | None,
    dice_metadata: dict[str, Any],
    dice_roll_strategy: str,
) -> None:
    """Attach dice metadata to structured response and align dice rolls."""
    if not structured_response:
        return

    debug_info = structured_response.debug_info or {}
    if "dice_strategy" in dice_metadata:
        debug_info.setdefault("dice_strategy", dice_metadata["dice_strategy"])
    if "tool_results" in dice_metadata:
        debug_info["tool_results"] = dice_metadata["tool_results"]
        debug_info["tool_requests_executed"] = dice_metadata.get(
            "tool_requests_executed", False
        )
    structured_response.debug_info = debug_info

    if "tool_results" in dice_metadata:
        _apply_tool_results_to_structured_response(
            structured_response,
            dice_metadata.get("tool_results"),
            dice_roll_strategy,
        )


def _is_code_execution_fabrication(
    structured_response: Any, code_execution_evidence: dict[str, Any] | None
) -> bool:
    """Check if dice results appear without verified RNG code_execution evidence.

    GREEN FIX (Dec 2024): Now uses rng_verified instead of code_execution_used.
    This detects fabrication via print('{"rolls": [16]}') without random.randint().
    """
    if not structured_response:
        return False

    has_dice_rolls = bool(
        getattr(structured_response, "dice_rolls", None)
        or getattr(structured_response, "dice_audit_events", None)
    )
    if not has_dice_rolls:
        return False

    if code_execution_evidence is None:
        logging_util.warning(
            logging_util.with_campaign(
                "⚠️ MISSING_CODE_EXEC_EVIDENCE: Dice present but no code_execution evidence. "
                "Treating as potential fabrication."
            )
        )
        return True

    # GREEN FIX: Use rng_verified instead of code_execution_used
    # rng_verified = True only if code contained actual random.randint() calls
    rng_verified = code_execution_evidence.get("rng_verified", False)
    if rng_verified:
        return False  # Verified RNG usage - not fabrication

    # If code was executed but no RNG detected, it's fabrication
    code_was_executed = code_execution_evidence.get("code_execution_used", False)
    if code_was_executed:
        logging_util.warning(
            logging_util.with_campaign(
                "🚨 CODE_EXEC_FABRICATION: code_execution_used=True but rng_verified=False. "
                "LLM ran code but did NOT use random.randint() - dice values are fabricated!"
            )
        )
        return True

    return True  # No code execution at all - also fabrication


def _log_fabricated_dice_if_detected(
    structured_response: Any, code_execution_evidence: dict[str, Any]
) -> None:
    """Log if dice results appear without code_execution evidence."""
    if _is_code_execution_fabrication(structured_response, code_execution_evidence):
        logging_util.error(
            logging_util.with_campaign(
                "🚨 FABRICATED_DICE_DETECTED: Gemini returned dice_rolls but did NOT use "
                "code_execution (executable_code_parts=0). Dice values may be hallucinated! "
                f"dice_rolls={getattr(structured_response, 'dice_rolls', [])}, "
                f"evidence={code_execution_evidence}"
            )
        )


_DICE_TOOL_NAMES = {"roll_dice", "roll_attack", "roll_skill_check", "roll_saving_throw"}


def _has_dice_tool_results(tool_results: Any) -> bool:
    """Check if tool_results contain any SUCCESSFUL dice-related tools.

    Returns False if dice tools were called but returned errors (e.g., missing dc_reasoning).
    This prevents false positive fabrication detection when tools fail validation.
    """
    if not isinstance(tool_results, list):
        return False

    for result in tool_results:
        if not isinstance(result, dict):
            continue

        tool_name = result.get("tool") or result.get("name", "")
        if isinstance(tool_name, str) and tool_name in _DICE_TOOL_NAMES:
            result_data = result.get("result")
            if result_data and isinstance(result_data, dict):
                # CRITICAL: Check for error responses - these are NOT valid dice results
                # This happens when dice tool is called without required params (e.g., dc_reasoning)
                if "error" in result_data:
                    continue  # Tool call failed, not a valid dice result
                # Valid dice result should have roll/total/formatted data
                if any(k in result_data for k in ("roll", "total", "formatted", "rolls")):
                    return True

    return False


def _has_dice_tool_errors(tool_results: Any) -> tuple[bool, list[str]]:
    """Check if dice tools were called but returned errors.

    Returns:
        Tuple of (has_errors, list of error messages)
    """
    if not isinstance(tool_results, list):
        return False, []

    errors: list[str] = []
    for result in tool_results:
        if not isinstance(result, dict):
            continue

        tool_name = result.get("tool") or result.get("name", "")
        if isinstance(tool_name, str) and tool_name in _DICE_TOOL_NAMES:
            result_data = result.get("result")
            if result_data and isinstance(result_data, dict):
                if "error" in result_data:
                    errors.append(f"{tool_name}: {result_data['error']}")

    return bool(errors), errors


def _extract_dice_rolls_from_tool_results(tool_results: Any) -> list[str]:
    """Convert server tool_results into dice_rolls strings (authoritative)."""
    if not isinstance(tool_results, list):
        return []

    dice_tool_results: list[dict[str, Any]] = []
    for item in tool_results:
        if not isinstance(item, dict):
            continue
        tool_name = item.get("tool")
        if isinstance(tool_name, str) and tool_name in _DICE_TOOL_NAMES:
            dice_tool_results.append(item)

    if not dice_tool_results:
        return []

    text = format_tool_results_text(dice_tool_results)
    if not text:
        return []

    rolls: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("- "):
            cleaned = cleaned[2:].strip()
        elif cleaned.startswith("-"):
            cleaned = cleaned[1:].strip()
        if cleaned:
            rolls.append(cleaned)

    return rolls


def _extract_dice_audit_events_from_tool_results(
    tool_results: Any,
) -> list[dict[str, Any]]:
    """Build dice_audit_events from tool_results (native_two_phase source of truth)."""
    if not isinstance(tool_results, list):
        return []

    def _coerce_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _notation_from_modifier(modifier: Any) -> str | None:
        mod = _coerce_int(modifier)
        if mod is None:
            return None
        sign = "+" if mod >= 0 else ""
        return f"1d20{sign}{mod}"

    events: list[dict[str, Any]] = []
    for item in tool_results:
        if not isinstance(item, dict):
            continue
        tool_name = item.get("tool")
        if not isinstance(tool_name, str) or tool_name not in _DICE_TOOL_NAMES:
            continue
        result = item.get("result")
        if not isinstance(result, dict):
            continue

        if tool_name == "roll_attack":
            attack = result.get("attack_roll")
            if isinstance(attack, dict):
                events.append(
                    {
                        "source": "server_tool",
                        "label": item.get("args", {}).get("purpose") or "Attack Roll",
                        "notation": attack.get("notation")
                        or _notation_from_modifier(attack.get("modifier")),
                        "rolls": attack.get("rolls") or [],
                        "modifier": attack.get("modifier") or 0,
                        "total": attack.get("total"),
                    }
                )
            damage = result.get("damage")
            if isinstance(damage, dict):
                events.append(
                    {
                        "source": "server_tool",
                        "label": "Damage",
                        "notation": damage.get("notation"),
                        "rolls": damage.get("rolls") or [],
                        "modifier": damage.get("modifier") or 0,
                        "total": damage.get("total"),
                    }
                )
            continue

        if tool_name == "roll_skill_check":
            skill = result.get("skill") or "Skill Check"
            event = {
                "source": "server_tool",
                "label": str(skill).title(),
                "notation": result.get("notation")
                or _notation_from_modifier(result.get("modifier")),
                "rolls": result.get("rolls")
                or ([result.get("roll")] if result.get("roll") is not None else []),
                "modifier": result.get("modifier") or 0,
                "total": result.get("total"),
            }
            # Include DC and reasoning for audit trail - proves DC set before roll
            if result.get("dc") is not None:
                event["dc"] = result.get("dc")
            if result.get("dc_reasoning"):
                event["dc_reasoning"] = result.get("dc_reasoning")
            if result.get("success") is not None:
                event["success"] = result.get("success")
            events.append(event)
            continue

        if tool_name == "roll_saving_throw":
            save_type = result.get("save_type") or "Save"
            event = {
                "source": "server_tool",
                "label": f"{str(save_type).upper()} Save",
                "notation": result.get("notation")
                or _notation_from_modifier(result.get("modifier")),
                "rolls": result.get("rolls")
                or ([result.get("roll")] if result.get("roll") is not None else []),
                "modifier": result.get("modifier") or 0,
                "total": result.get("total"),
            }
            # Include DC and reasoning for audit trail - proves DC set before roll
            if result.get("dc") is not None:
                event["dc"] = result.get("dc")
            if result.get("dc_reasoning"):
                event["dc_reasoning"] = result.get("dc_reasoning")
            if result.get("success") is not None:
                event["success"] = result.get("success")
            events.append(event)
            continue

        if tool_name == "roll_dice":
            events.append(
                {
                    "source": "server_tool",
                    "label": result.get("purpose") or "Dice Roll",
                    "notation": result.get("notation"),
                    "rolls": result.get("rolls") or [],
                    "modifier": result.get("modifier") or 0,
                    "total": result.get("total"),
                }
            )

    return events


def _apply_tool_results_to_structured_response(
    structured_response: NarrativeResponse | None,
    tool_results: Any,
    dice_roll_strategy: str,
) -> bool:
    """Override dice_rolls using tool_results for native two-phase strategies."""
    if not structured_response:
        return False
    if dice_roll_strategy != dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE:
        return False

    derived_rolls = _extract_dice_rolls_from_tool_results(tool_results)
    if not derived_rolls:
        return False

    existing_rolls = getattr(structured_response, "dice_rolls", None) or []
    if existing_rolls and existing_rolls != derived_rolls:
        debug_info = structured_response.debug_info or {}
        debug_info.setdefault("dice_rolls_model", existing_rolls)
        debug_info["dice_rolls_overridden"] = True
        structured_response.debug_info = debug_info
        logging_util.warning(
            logging_util.with_campaign(
                "DICE_ROLLS_MISMATCH: Replacing model dice_rolls with tool_results "
                "(native_two_phase authoritative)."
            )
        )
    elif not existing_rolls:
        logging_util.info(
            logging_util.with_campaign(
                "DICE_ROLLS_FROM_TOOL_RESULTS: Populated dice_rolls from tool_results "
                "(native_two_phase authoritative)."
            )
        )

    structured_response.dice_rolls = derived_rolls

    audit_events = _extract_dice_audit_events_from_tool_results(tool_results)
    if audit_events:
        existing_audit = getattr(structured_response, "dice_audit_events", None)
        if existing_audit and existing_audit != audit_events:
            debug_info = structured_response.debug_info or {}
            debug_info.setdefault("dice_audit_events_model", existing_audit)
            debug_info["dice_audit_events_overridden"] = True
            structured_response.debug_info = debug_info
            logging_util.warning(
                logging_util.with_campaign(
                    "DICE_AUDIT_MISMATCH: Replacing model dice_audit_events with tool_results "
                    "(native_two_phase authoritative)."
                )
            )
        structured_response.dice_audit_events = audit_events

    return True


def _should_require_dice_rolls_for_turn(
    *,
    current_game_state: GameState | None,
    user_input: str,
    mode: str,
    is_god_mode: bool,
    is_dm_mode: bool,
) -> bool:
    """Check if dice rolls should be required for this turn."""
    if mode != constants.MODE_CHARACTER or is_god_mode or is_dm_mode:
        return False

    text = (user_input or "").strip().lower()
    if not text or text.startswith("/"):
        return False

    text = _truncate_for_combat_scan(text)
    has_combat_keywords = any(
        pattern.search(text) for pattern in _COMBAT_KEYWORD_PATTERNS_USER_INPUT
    )

    in_combat = bool(
        current_game_state and current_game_state.combat_state.get("in_combat", False)
    )

    return has_combat_keywords or in_combat


COMBAT_ACTION_KEYWORDS = (
    "attack",
    "shoot",
    "strike",
    "stab",
    "slash",
    "swing",
    "hit",
    "cast",
    "spell",
    "fireball",
    "roll",
    "save",
    "saving throw",
    "skill",
    "check",
    "initiative",
    "grapple",
    "shove",
    "dodge",
    "dash",
    "disengage",
    "help",
)

_COMBAT_ACTION_KEYWORDS_USER_INPUT = (
    "attack",
    "shoot",
    "strike",
    "stab",
    "slash",
    "swing",
    "hit",
    "cast",
    "spell",
    "fireball",
    "saving throw",
    "initiative",
    "grapple",
    "shove",
    "dodge",
    "dash",
    "disengage",
)

_COMBAT_KEYWORD_MAX_CHARS = 5000
_COMBAT_KEYWORD_PATTERNS = tuple(
    re.compile(r"\b" + re.escape(keyword) + r"\b") for keyword in COMBAT_ACTION_KEYWORDS
)
_COMBAT_KEYWORD_PATTERNS_USER_INPUT = tuple(
    re.compile(r"\b" + re.escape(keyword) + r"\b")
    for keyword in _COMBAT_ACTION_KEYWORDS_USER_INPUT
)


def _truncate_for_combat_scan(text: str) -> str:
    if len(text) > _COMBAT_KEYWORD_MAX_CHARS:
        return text[:_COMBAT_KEYWORD_MAX_CHARS]
    return text


_PAST_TENSE_MARKERS = (
    "died",
    "killed",
    "defeated",
    "was attacked",
    "were attacked",
    "had attacked",
    "was hit",
    "were hit",
    "had hit",
    "was struck",
    "were struck",
    "had struck",
    "previously",
    "last session",
    "earlier",
    "before",
    "remembered",
    "recalled",
)

_HYPOTHETICAL_MARKERS = (
    "could attack",
    "could strike",
    "could hit",
    "might attack",
    "might strike",
    "might hit",
    "would attack",
    "would strike",
    "would hit",
    "if you attack",
    "if you strike",
    "if you hit",
    "you could",
    "you might",
    "you would",
    "want to attack",
    "plan to attack",
    "decide to attack",
)

_ACTIVE_COMBAT_PATTERNS = (
    "attacks you",
    "strikes at",
    "swings at",
    "shoots at",
    "casts at",
    "hits you",
    "damage to",
    "takes damage",
    "deals damage",
    "dealing damage",
    "roll to hit",
    "rolls to hit",
    "attack roll",
    "makes an attack",
    "roll for initiative",
    "rolls initiative",
    "d20",
    "1d20",
    "2d6",
    "1d8",
    "1d6",
)


def _detect_combat_in_narrative(narrative_text: str) -> bool:
    """Detect ACTIVE combat in LLM-generated narrative text."""
    if not narrative_text:
        return False

    text = _truncate_for_combat_scan(narrative_text.lower())

    has_past_marker = any(marker in text for marker in _PAST_TENSE_MARKERS)
    has_hypothetical_marker = any(marker in text for marker in _HYPOTHETICAL_MARKERS)
    has_active_pattern = any(pattern in text for pattern in _ACTIVE_COMBAT_PATTERNS)

    if has_active_pattern and not has_hypothetical_marker:
        return True

    has_combat_keyword = any(
        pattern.search(text) for pattern in _COMBAT_KEYWORD_PATTERNS
    )

    if has_combat_keyword:
        if has_hypothetical_marker:
            return False
        if has_past_marker and not has_active_pattern:
            return False
        return True

    return False


def _check_dice_integrity(
    *,
    structured_response: NarrativeResponse | None,
    api_response: Any,
) -> tuple[bool, str]:
    """Check if dice_rolls in response came from legitimate tool execution."""
    if not structured_response:
        return True, ""

    dice_rolls = getattr(structured_response, "dice_rolls", None) or []
    if not dice_rolls:
        return True, ""

    has_real_dice = any(str(roll).strip() for roll in dice_rolls)
    if not has_real_dice:
        return True, ""

    tool_requests_executed = getattr(api_response, "_tool_requests_executed", None)

    if tool_requests_executed is None:
        logging_util.debug(
            logging_util.with_campaign(
                "DICE_INTEGRITY: No _tool_requests_executed metadata on response, "
                "skipping integrity check for backward compatibility"
            )
        )
        return True, ""

    if tool_requests_executed:
        return True, ""

    return False, (
        f"Response contains dice_rolls ({len(dice_rolls)} entries) but no tool_requests were executed. "
        "Dice rolls must come from tool execution, not fabrication."
    )


def _validate_combat_dice_integrity(
    *,
    user_input: str,
    narrative_text: str,
    structured_response: NarrativeResponse | None,
    current_game_state: GameState | None,
    api_response: Any,
    mode: str,
    is_god_mode: bool,
    is_dm_mode: bool,
) -> tuple[bool, str | None]:
    """Validate dice integrity when combat is detected."""
    if is_god_mode or is_dm_mode:
        return True, None

    if mode != constants.MODE_CHARACTER:
        return True, None

    user_text = (user_input or "").strip().lower()
    if user_text:
        user_text = _truncate_for_combat_scan(user_text)
    user_has_combat = (
        any(pattern.search(user_text) for pattern in _COMBAT_KEYWORD_PATTERNS)
        if user_text
        else False
    )

    narrative_has_combat = _detect_combat_in_narrative(narrative_text)

    if not user_has_combat and not narrative_has_combat:
        return True, None

    is_valid, reason = _check_dice_integrity(
        structured_response=structured_response,
        api_response=api_response,
    )

    if is_valid:
        return True, None

    combat_source = []
    if user_has_combat:
        combat_source.append("user_input")
    if narrative_has_combat:
        combat_source.append("narrative")

    logging_util.warning(
        logging_util.with_campaign(
            f"DICE_INTEGRITY_VIOLATION: Combat detected in {', '.join(combat_source)} "
            f"but dice_rolls were not from tool execution. Reason: {reason}"
        )
    )

    return False, (
        "DICE INTEGRITY VIOLATION: Your response includes dice results but you did not use "
        "tool_requests to roll them. In combat, you MUST use tool_requests (roll_dice, roll_attack, etc.) "
        "to generate dice rolls. Do NOT fabricate dice results. "
        "Regenerate your response using tool_requests for all dice rolls."
    )


def _validate_dice_integrity_always(
    *,
    structured_response: NarrativeResponse | None,
    api_response: Any,
    mode: str,
    is_god_mode: bool,
    is_dm_mode: bool,
    dice_roll_strategy: str | None = None,
) -> tuple[bool, str | None]:
    """Validate dice integrity for ALL responses with dice_rolls.

    This catches fabricated dice even when combat is not detected - e.g., skill checks
    for absorbing items, Arcana checks, etc. Any response with dice_rolls must have
    tool_requests_executed.

    NOTE: This function only applies to NATIVE_TWO_PHASE strategy (tool_requests).
    For CODE_EXECUTION strategy (Gemini 3), use _is_code_execution_fabrication instead.
    """
    if is_god_mode or is_dm_mode:
        return True, None

    if mode != constants.MODE_CHARACTER:
        return True, None

    # Skip for code_execution strategy - that has its own check (_is_code_execution_fabrication)
    if dice_roll_strategy == dice_strategy.DICE_STRATEGY_CODE_EXECUTION:
        return True, None

    is_valid, reason = _check_dice_integrity(
        structured_response=structured_response,
        api_response=api_response,
    )

    if is_valid:
        return True, None

    logging_util.warning(
        logging_util.with_campaign(
            f"DICE_INTEGRITY_ALWAYS_VIOLATION: Response has dice_rolls but no tool execution. "
            f"Reason: {reason}"
        )
    )

    return False, (
        "DICE INTEGRITY VIOLATION: Your response includes dice_rolls but you did not use "
        "tool_requests to roll them. For ANY dice roll (combat, skill checks, saving throws), "
        "you MUST use tool_requests (roll_skill_check, roll_saving_throw, roll_attack, etc.). "
        "Do NOT fabricate dice results. Regenerate your response using tool_requests."
    )
