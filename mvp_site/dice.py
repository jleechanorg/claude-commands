from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from typing import Any

from mvp_site import logging_util

# Optional deterministic dice RNG for reproducible test evidence.
_DICE_SEED = os.getenv("DICE_SEED")
if _DICE_SEED:
    try:
        _DICE_SEED_VALUE: int | str = int(_DICE_SEED)
    except ValueError:
        _DICE_SEED_VALUE = _DICE_SEED
    _DICE_RNG = random.Random(_DICE_SEED_VALUE)
    logging_util.info(f"DICE_SEED enabled for deterministic rolls: {_DICE_SEED}")
else:
    _DICE_RNG = random


@dataclass
class DiceRollResult:
    """Result of a dice roll with full context."""

    notation: str
    individual_rolls: list[int]
    modifier: int
    total: int
    natural_20: bool = False
    natural_1: bool = False
    # Optional context for rich formatting
    purpose: str = ""
    modifier_breakdown: dict[str, int] | None = None
    target_dc: int | None = None
    success: bool | None = None

    def __str__(self) -> str:
        if not self.individual_rolls:
            return f"{self.notation} = {self.total}"

        if len(self.individual_rolls) == 1:
            rolls_value = str(self.individual_rolls[0])
        else:
            rolls_sum = sum(self.individual_rolls)
            rolls_value = f"[{'+'.join(str(r) for r in self.individual_rolls)}={rolls_sum}]"

        if self.modifier_breakdown:
            mod_parts = []
            for label, value in self.modifier_breakdown.items():
                if value >= 0:
                    mod_parts.append(f"+{value} {label}")
                else:
                    mod_parts.append(f"{value} {label}")
            mod_str = " ".join(mod_parts)
            mod_display = f" {mod_str}" if mod_str else ""
        else:
            if self.modifier > 0:
                mod_display = f"+{self.modifier}"
            elif self.modifier < 0:
                mod_display = str(self.modifier)
            else:
                mod_display = ""

        parts = [f"{self.notation} {mod_display}".strip()]

        if self.modifier_breakdown:
            parts.append(f"= {rolls_value}{mod_display} = {self.total}")
        elif mod_display:
            parts.append(f"= {rolls_value}{mod_display} = {self.total}")
        else:
            parts.append(f"= {rolls_value} = {self.total}")

        if self.target_dc is not None:
            parts.append(f"vs DC {self.target_dc}")
            if self.success is not None:
                parts.append(f"({'Success' if self.success else 'Fail'})")
            elif self.natural_20:
                parts.append("(NAT 20!)")
            elif self.natural_1:
                parts.append("(NAT 1!)")
        else:
            if self.natural_20:
                parts[-1] += " (NAT 20!)"
            elif self.natural_1:
                parts[-1] += " (NAT 1!)"

        return " ".join(parts)


# =============================================================================
# DICE ROLL TOOL DEFINITIONS (for tool use / function calling)
# =============================================================================

DICE_ROLL_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "Roll dice for damage, healing, or random effects ONLY. "
            "DO NOT use for skill checks, attacks, or saving throws - use the specific tools instead. "
            "This tool just returns numbers, it does NOT determine success/failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "description": "Dice notation (e.g., '2d6+3' for damage, '1d8' for healing)",
                    },
                    "purpose": {
                        "type": "string",
                        "description": "What this roll is for (e.g., 'damage', 'healing', 'random table')",
                    },
                },
                "required": ["notation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_attack",
            "description": "Roll a COMPLETE attack with hit check vs AC and damage if hit. Returns success/failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attack_modifier": {
                        "type": "integer",
                        "description": "Total attack bonus (ability + proficiency combined)",
                    },
                    "ability_modifier": {
                        "type": "integer",
                        "description": "Ability modifier component (STR or DEX)",
                    },
                    "ability_name": {
                        "type": "string",
                        "description": "Ability used for attack: STR or DEX",
                    },
                    "proficiency_bonus": {
                        "type": "integer",
                        "description": "Proficiency bonus component",
                    },
                    "weapon_name": {
                        "type": "string",
                        "description": "Name of the weapon used (e.g., 'Longsword', 'Shortbow')",
                    },
                    "damage_notation": {
                        "type": "string",
                        "description": "Damage dice (e.g., '1d8+3')",
                    },
                    "target_ac": {
                        "type": "integer",
                        "description": "Target's Armor Class",
                    },
                    "advantage": {"type": "boolean", "default": False},
                    "disadvantage": {"type": "boolean", "default": False},
                },
                "required": ["attack_modifier", "damage_notation", "target_ac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_skill_check",
            "description": "Roll a skill check vs a DC. Covers ALL skills: "
            "Persuasion, Intimidation, Deception (social), Perception, Stealth, Investigation, "
            "Athletics, Acrobatics, Thieves' Tools, etc. "
            "ALWAYS use this for skill checks - it returns success/failure based on DC comparison. "
            "Examples: Persuasion to convince an NPC, Intimidation to threaten, "
            "Stealth to sneak past guards, Thieves' Tools to pick a lock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attribute_modifier": {"type": "integer", "description": "Relevant ability modifier (DEX for Stealth, INT for Investigation, etc.)"},
                    "attribute_name": {"type": "string", "description": "Ability score abbreviation: STR, DEX, CON, INT, WIS, or CHA"},
                    "proficiency_bonus": {"type": "integer", "description": "Character's proficiency bonus (typically 2-6)"},
                    "proficient": {"type": "boolean", "default": False, "description": "True if proficient in this skill"},
                    "expertise": {"type": "boolean", "default": False, "description": "True if character has expertise (double proficiency)"},
                    "dc": {"type": "integer", "description": "Difficulty Class to beat (10=easy, 15=medium, 20=hard, 25=very hard)"},
                    "skill_name": {"type": "string", "description": "Name of the skill (e.g., 'Thieves Tools', 'Stealth', 'Perception')"},
                },
                "required": ["attribute_modifier", "attribute_name", "proficiency_bonus", "dc", "skill_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_saving_throw",
            "description": "Roll a saving throw vs a DC (e.g., DEX save vs fireball, WIS save vs charm). "
            "ALWAYS use this for saving throws - it returns success/failure based on DC comparison. "
            "Example: Thieves' Tools check to pick a lock, Stealth check to sneak past guards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attribute_modifier": {"type": "integer", "description": "Relevant ability modifier for the save"},
                    "proficiency_bonus": {"type": "integer", "description": "Character's proficiency bonus"},
                    "proficient": {"type": "boolean", "default": False, "description": "True if proficient in this saving throw"},
                    "dc": {"type": "integer", "description": "Difficulty Class to beat"},
                    "save_type": {"type": "string", "description": "Type of save: STR, DEX, CON, INT, WIS, or CHA"},
                },
                "required": ["attribute_modifier", "proficiency_bonus", "dc", "save_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "declare_no_roll_needed",
            "description": "Declare that no dice roll is needed for this action. "
            "Use ONLY for trivial actions that auto-succeed: opening unlocked doors, picking up items, "
            "walking in safe areas, asking for directions, casual greetings. "
            "DO NOT use this for: combat, Persuasion/Intimidation/Deception checks, "
            "convincing resistant NPCs, negotiations, skill checks, saving throws, contested actions, "
            "or anything with meaningful risk/uncertainty. "
            "If an NPC is resisting or needs convincing, use roll_skill_check instead. "
            "You MUST provide a reason explaining why no roll is needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The player action being evaluated (e.g., 'open the unlocked door')",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why no dice roll is needed (e.g., 'Door is unlocked, no check required')",
                    },
                },
                "required": ["action", "reason"],
            },
        },
    },
]


def roll_dice(notation: str) -> DiceRollResult:
    """Roll dice using standard notation (e.g., '2d6+3')."""
    pattern = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(pattern, notation.lower().replace(" ", ""))

    if not match:
        logging_util.warning(f"DICE_AUDIT: Invalid notation '{notation}' - could not parse")
        return DiceRollResult(notation, [], 0, 0)

    num_dice = int(match.group(1))
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if num_dice < 1 or die_size < 1:
        logging_util.warning(
            f"DICE_AUDIT: Invalid dice params num_dice={num_dice}, die_size={die_size}"
        )
        return DiceRollResult(notation, [], modifier, modifier)

    rolls = [_DICE_RNG.randint(1, die_size) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    natural_20 = die_size == 20 and num_dice == 1 and rolls[0] == 20
    natural_1 = die_size == 20 and num_dice == 1 and rolls[0] == 1

    logging_util.info(
        f"DICE_AUDIT: notation={notation} | rolls={rolls} | modifier={modifier} | "
        f"total={total} | nat20={natural_20} | nat1={natural_1}"
    )

    return DiceRollResult(notation, rolls, modifier, total, natural_20, natural_1)


def roll_with_advantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    roll1 = roll_dice(notation)
    roll2 = roll_dice(notation)
    total = max(roll1.total, roll2.total)
    return roll1, roll2, total


def roll_with_disadvantage(notation: str) -> tuple[DiceRollResult, DiceRollResult, int]:
    roll1 = roll_dice(notation)
    roll2 = roll_dice(notation)
    total = min(roll1.total, roll2.total)
    return roll1, roll2, total


def calculate_attack_roll(
    attack_modifier: int, advantage: bool = False, disadvantage: bool = False
) -> dict:
    notation = f"1d20+{attack_modifier}" if attack_modifier >= 0 else f"1d20{attack_modifier}"

    if advantage and disadvantage:
        roll = roll_dice(notation)
        return {
            "rolls": roll.individual_rolls,
            "total": roll.total,
            "is_critical": roll.natural_20,
            "is_fumble": roll.natural_1,
            "used_roll": "single",
        }

    if advantage:
        roll1, roll2, total = roll_with_advantage(notation)
        used_roll = "higher" if roll1.total >= roll2.total else "lower"
        chosen_roll = roll1 if used_roll == "higher" else roll2
    elif disadvantage:
        roll1, roll2, total = roll_with_disadvantage(notation)
        used_roll = "lower" if roll1.total <= roll2.total else "higher"
        chosen_roll = roll1 if used_roll == "lower" else roll2
    else:
        chosen_roll = roll_dice(notation)
        total = chosen_roll.total
        used_roll = "single"

    return {
        "rolls": chosen_roll.individual_rolls,
        "total": total,
        "is_critical": chosen_roll.natural_20,
        "is_fumble": chosen_roll.natural_1,
        "used_roll": used_roll,
        "notation": notation,
    }


def calculate_damage(damage_notation: str, is_critical: bool = False) -> DiceRollResult:
    if is_critical:
        pattern = r"(\d+)d(\d+)([+-]\d+)?"
        match = re.match(pattern, damage_notation.lower().replace(" ", ""))
        if match:
            num_dice = int(match.group(1)) * 2
            die_size = int(match.group(2))
            modifier = match.group(3) if match.group(3) else ""
            crit_notation = f"{num_dice}d{die_size}{modifier}"
            return roll_dice(crit_notation)
    return roll_dice(damage_notation)


def calculate_skill_check(
    attribute_modifier: int,
    proficiency_bonus: int,
    proficient: bool = False,
    expertise: bool = False,
) -> DiceRollResult:
    total_modifier = attribute_modifier
    if proficient or expertise:
        total_modifier += proficiency_bonus
    if expertise:
        total_modifier += proficiency_bonus
    notation = f"1d20+{total_modifier}" if total_modifier >= 0 else f"1d20{total_modifier}"
    return roll_dice(notation)


def calculate_saving_throw(
    attribute_modifier: int, proficiency_bonus: int, proficient: bool = False
) -> DiceRollResult:
    total_modifier = attribute_modifier
    if proficient:
        total_modifier += proficiency_bonus
    notation = f"1d20+{total_modifier}" if total_modifier >= 0 else f"1d20{total_modifier}"
    return roll_dice(notation)


def _get_damage_total_for_log(damage: Any) -> Any:
    if isinstance(damage, dict):
        return damage.get("total", "N/A")
    return "N/A"


def execute_dice_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a dice roll tool call and return the result."""
    logging_util.info(f"DICE_TOOL_EXEC: tool={tool_name} | args={arguments}")

    def _coerce_int_inner(value: Any, default: int | None = 0) -> int | None:
        if isinstance(value, bool):
            return int(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        if value is None:
            return default
        return bool(value)

    if tool_name == "roll_dice":
        notation = arguments.get("dice_notation") or arguments.get("notation", "1d20")
        purpose = arguments.get("purpose", "")
        result = roll_dice(notation)
        tool_result = {
            "notation": result.notation,
            "rolls": result.individual_rolls,
            "modifier": result.modifier,
            "total": result.total,
            "natural_20": result.natural_20,
            "natural_1": result.natural_1,
            "purpose": purpose,
            "formatted": str(result),
        }
        if _DICE_SEED:
            tool_result["seed"] = _DICE_SEED
        logging_util.info(
            f"DICE_TOOL_RESULT: tool=roll_dice | notation={notation} | "
            f"rolls={result.individual_rolls} | total={result.total} | purpose={purpose}"
        )
        return tool_result

    if tool_name == "roll_attack":
        raw_attack_mod = arguments.get("attack_modifier")
        if raw_attack_mod is None and "modifier" in arguments:
            raw_attack_mod = arguments.get("modifier")
        attack_mod = _coerce_int_inner(raw_attack_mod, 0)
        ability_mod = _coerce_int_inner(arguments.get("ability_modifier"), None)
        ability_name = arguments.get("ability_name", "").upper() or None
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), None)
        weapon_name = arguments.get("weapon_name", "")
        damage_notation = arguments.get("damage_notation") or arguments.get("damage_dice") or "1d6"
        target_ac = _coerce_int_inner(arguments.get("target_ac"), 10)
        advantage = _coerce_bool(arguments.get("advantage"), False)
        disadvantage = _coerce_bool(arguments.get("disadvantage"), False)

        attack = calculate_attack_roll(attack_mod, advantage, disadvantage)
        rolls = attack["rolls"]
        hit = not attack["is_fumble"] and (attack["total"] >= target_ac or attack["is_critical"])

        mod_parts = []
        if ability_mod is not None and ability_name:
            mod_parts.append(
                f"+{ability_mod} {ability_name}" if ability_mod >= 0 else f"{ability_mod} {ability_name}"
            )
        if prof_bonus is not None and prof_bonus > 0:
            mod_parts.append(f"+{prof_bonus} PROF")
        if not mod_parts:
            mod_parts.append(f"+{attack_mod}" if attack_mod >= 0 else f"{attack_mod}")
        mod_str = " ".join(mod_parts)

        attack_label = weapon_name or "Attack"
        hit_str = (
            "CRITICAL!"
            if attack["is_critical"]
            else ("FUMBLE!" if attack["is_fumble"] else ("Hit!" if hit else "Miss"))
        )

        if len(rolls) == 2:
            used = attack.get("used_roll", "higher")
            roll_display = f"({rolls[0]}, {rolls[1]} - {used})"
        elif not rolls:
            roll_display = "0"
        else:
            roll_display = str(rolls[0])
        formatted = (
            f"{attack_label}: 1d20 {mod_str} = {roll_display} {mod_str} = "
            f"{attack['total']} vs AC {target_ac} ({hit_str})"
        )

        result = {
            "attack_roll": attack,
            "target_ac": target_ac,
            "hit": hit,
            "critical": attack["is_critical"],
            "fumble": attack["is_fumble"],
            "weapon_name": weapon_name,
            "ability_name": ability_name,
            "formatted": formatted,
        }
        if hit:
            damage = calculate_damage(damage_notation, attack["is_critical"])
            result["damage"] = {
                "notation": damage.notation,
                "rolls": damage.individual_rolls,
                "modifier": damage.modifier,
                "total": damage.total,
                "critical": attack["is_critical"],
            }
            result["formatted"] += f" | Damage: {damage}"
        else:
            result["damage"] = None
        damage_total = _get_damage_total_for_log(result.get("damage"))
        logging_util.info(
            f"DICE_TOOL_RESULT: tool=roll_attack | weapon={weapon_name} | "
            f"rolls={attack.get('rolls', [])} | total={attack['total']} | hit={hit} | "
            f"critical={attack['is_critical']} | damage={damage_total}"
        )
        return result

    if tool_name == "roll_skill_check":
        raw_attr_mod = arguments.get("attribute_modifier")
        if raw_attr_mod is None and "modifier" in arguments:
            raw_attr_mod = arguments.get("modifier")
        attr_mod = _coerce_int_inner(raw_attr_mod, 0)
        attr_name = arguments.get("attribute_name", "").upper() or "MOD"
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), 2)
        proficient = _coerce_bool(arguments.get("proficient"), False)
        expertise = _coerce_bool(arguments.get("expertise"), False)
        dc = _coerce_int_inner(arguments.get("dc"), 10)
        skill_name = arguments.get("skill_name") or arguments.get("skill") or ""

        result = calculate_skill_check(attr_mod, prof_bonus, proficient, expertise)
        roll = result.individual_rolls[0] if result.individual_rolls else 0
        success = result.total >= dc

        mod_parts = [
            f"+{attr_mod} {attr_name}" if attr_mod >= 0 else f"{attr_mod} {attr_name}"
        ]
        if expertise:
            effective_prof = prof_bonus * 2
            prof_label = "EXPERT"
        elif proficient:
            effective_prof = prof_bonus
            prof_label = "PROF"
        else:
            effective_prof = 0
            prof_label = ""
        if effective_prof > 0:
            mod_parts.append(f"+{effective_prof} {prof_label}")
        mod_str = " ".join(mod_parts)
        formatted = (
            f"{skill_name}: 1d20 {mod_str} = {roll} {mod_str} = {result.total} "
            f"vs DC {dc} ({'Success' if success else 'Fail'})"
        )

        logging_util.info(
            f"DICE_TOOL_RESULT: tool=roll_skill_check | skill={skill_name} | "
            f"roll={roll} | total={result.total} | dc={dc} | success={success}"
        )
        return {
            "skill": skill_name,
            "roll": roll,
            "modifier": result.modifier,
            "total": result.total,
            "dc": dc,
            "success": success,
            "natural_20": result.natural_20,
            "natural_1": result.natural_1,
            "proficiency_applied": effective_prof,
            "formatted": formatted,
        }

    if tool_name == "roll_saving_throw":
        raw_attr_mod = arguments.get("attribute_modifier")
        if raw_attr_mod is None and "modifier" in arguments:
            raw_attr_mod = arguments.get("modifier")
        attr_mod = _coerce_int_inner(raw_attr_mod, 0)
        attr_name = arguments.get("attribute_name", "").upper() or "MOD"
        prof_bonus = _coerce_int_inner(arguments.get("proficiency_bonus"), 2)
        proficient = _coerce_bool(arguments.get("proficient"), False)
        dc = _coerce_int_inner(arguments.get("dc"), 10)
        save_type = arguments.get("save_type", "").upper() or "SAVE"

        result = calculate_saving_throw(attr_mod, prof_bonus, proficient)
        roll = result.individual_rolls[0] if result.individual_rolls else 0
        success = result.total >= dc

        mod_parts = [
            f"+{attr_mod} {attr_name}" if attr_mod >= 0 else f"{attr_mod} {attr_name}"
        ]
        if proficient:
            mod_parts.append(f"+{prof_bonus} PROF")
        mod_str = " ".join(mod_parts)
        formatted = (
            f"{save_type} save: 1d20 {mod_str} = {roll} {mod_str} = {result.total} "
            f"vs DC {dc} ({'Success' if success else 'Fail'})"
        )

        logging_util.info(
            f"DICE_TOOL_RESULT: tool=roll_saving_throw | save_type={save_type} | "
            f"roll={roll} | total={result.total} | dc={dc} | success={success}"
        )
        return {
            "save_type": save_type,
            "roll": roll,
            "modifier": result.modifier,
            "total": result.total,
            "dc": dc,
            "success": success,
            "natural_20": result.natural_20,
            "natural_1": result.natural_1,
            "proficiency_applied": prof_bonus if proficient else 0,
            "formatted": formatted,
        }

    if tool_name == "declare_no_roll_needed":
        action = arguments.get("action", "unspecified action")
        reason = arguments.get("reason", "no reason provided")
        logging_util.info(f"DICE_TOOL_RESULT: tool={tool_name} | no_roll=True | action={action}")
        return {
            "no_roll": True,
            "action": action,
            "reason": reason,
            "formatted": f"No roll needed for '{action}': {reason}",
        }

    logging_util.warning(f"DICE_TOOL_RESULT: Unknown tool={tool_name}")
    return {"error": f"Unknown tool: {tool_name}"}
