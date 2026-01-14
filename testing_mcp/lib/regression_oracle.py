"""Regression Oracle for WorldArchitect MCP Server.

This module provides utilities to detect regressions in system instruction
behaviors by comparing prior test snapshots against current test results.

The oracle checks that EXISTING behaviors still work as specified by:
1. Comparing structural invariants (required keys, schema stability)
2. Validating boolean invariants (living world cadence, event generation)
3. Classifying differences as SAFE, SUSPICIOUS, or BREAKING

Usage:
    from testing_mcp.lib.regression_oracle import RegressionOracle, InvariantChecker

    # Compare snapshots
    oracle = RegressionOracle()
    result = oracle.compare_snapshots(prior, current)

    # Validate single response
    checker = InvariantChecker()
    validation = checker.validate_response(response, turn_number=6)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class DifferenceClass(Enum):
    """Classification of differences between snapshots."""
    SAFE = "safe"           # Cosmetic changes (timestamps, narrative text)
    SUSPICIOUS = "suspicious"  # Statistical anomalies that may be noise
    BREAKING = "breaking"      # Invariant violations


@dataclass
class RegressionResult:
    """Result of a regression comparison."""
    overall_status: str  # "pass", "warn", "fail"
    breaking_changes: list[str] = field(default_factory=list)
    suspicious_changes: list[str] = field(default_factory=list)
    safe_differences: list[str] = field(default_factory=list)
    checked_tests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_status": self.overall_status,
            "breaking_changes": self.breaking_changes,
            "suspicious_changes": self.suspicious_changes,
            "safe_differences": self.safe_differences,
            "checked_tests": self.checked_tests,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class InvariantViolation:
    """A single invariant violation."""
    invariant_name: str
    expected: str
    actual: str
    severity: DifferenceClass
    context: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Structural Invariants - Keys and schemas that MUST remain stable
# ============================================================================

REQUIRED_RESPONSE_KEYS = {
    "narrative": "string",
    "state_updates": "object",
    "planning_block": "object",
}

REQUIRED_STATE_UPDATE_KEYS = {
    "game_state": "object",
}

REQUIRED_GAME_STATE_KEYS = {
    "player_character_data": "object",
}

REQUIRED_PLAYER_CHARACTER_KEYS = {
    "experience": "object",
    "level": "integer",
}

REQUIRED_COMBAT_STATE_KEYS = {
    "in_combat": "boolean",
}

REQUIRED_COMBAT_ACTIVE_KEYS = {
    "combatants": "object",
    "initiative_order": "array",
    "combat_session_id": "string",
}

REQUIRED_WORLD_EVENT_KEYS = {
    "event_type": "string",
    "status": "string",
}

REQUIRED_GOD_MODE_DIRECTIVE_KEYS = {
    "rule": "string",
}

# ============================================================================
# Living World Invariants
# ============================================================================

LIVING_WORLD_TURN_INTERVAL = 3  # Default from constants.py
MIN_BACKGROUND_EVENTS_PER_LW_TURN = 4
MIN_IMMEDIATE_EVENTS_PER_LW_TURN = 3
MIN_LONG_TERM_EVENTS_PER_LW_TURN = 1
MIN_SCENE_EVENTS_PER_10_TURNS = 1


class InvariantChecker:
    """Checks individual responses against structural and behavioral invariants."""

    def __init__(self, living_world_interval: int = LIVING_WORLD_TURN_INTERVAL):
        self.living_world_interval = living_world_interval

    def validate_response(
        self,
        response: dict[str, Any],
        *,
        turn_number: int = 0,
        is_combat: bool = False,
        has_god_mode_directives: bool = False,
    ) -> list[InvariantViolation]:
        """Validate a response against all applicable invariants.

        Args:
            response: The LLM response dictionary.
            turn_number: Current turn number for living world checks.
            is_combat: Whether this is a combat response.
            has_god_mode_directives: Whether god mode directives should be present.

        Returns:
            List of invariant violations found.
        """
        violations: list[InvariantViolation] = []

        # Check response structure
        violations.extend(self._check_response_structure(response))

        state_updates_raw = response.get("state_updates", {})
        state_updates = state_updates_raw if isinstance(state_updates_raw, dict) else {}
        is_living_world_turn = turn_number > 0 and self._is_living_world_turn(turn_number)

        # Only run structural checks when we have state data or when a living world
        # turn requires it. This avoids noisy violations for synthetic non-LW turns
        # that intentionally omit state updates.
        if state_updates or is_living_world_turn:
            violations.extend(self._check_state_updates(state_updates))

            # Check game_state structure
            game_state = state_updates.get("game_state", {})
            if isinstance(game_state, dict):
                violations.extend(self._check_game_state(game_state))

                # Check combat state if in combat
                combat_state = game_state.get("combat_state", {})
                if isinstance(combat_state, dict) and is_combat:
                    violations.extend(self._check_combat_state(combat_state))

            # Check world_events on living world turns
            if is_living_world_turn:
                violations.extend(
                    self._check_living_world_events(state_updates, turn_number)
                )

        # Check god mode directives persistence
        if has_god_mode_directives:
            violations.extend(
                self._check_god_mode_directives(response, state_updates)
            )

        return violations

    def _check_response_structure(
        self, response: dict[str, Any]
    ) -> list[InvariantViolation]:
        """Check top-level response structure."""
        violations = []

        for key, expected_type in REQUIRED_RESPONSE_KEYS.items():
            if key not in response:
                violations.append(InvariantViolation(
                    invariant_name=f"response.{key}_present",
                    expected=f"{key} key must be present",
                    actual=f"{key} key is missing",
                    severity=DifferenceClass.BREAKING,
                ))
            else:
                actual_type = self._get_type_name(response[key])
                if actual_type != expected_type:
                    violations.append(InvariantViolation(
                        invariant_name=f"response.{key}_type",
                        expected=f"{key} must be {expected_type}",
                        actual=f"{key} is {actual_type}",
                        severity=DifferenceClass.BREAKING,
                    ))

        return violations

    def _check_state_updates(
        self, state_updates: dict[str, Any]
    ) -> list[InvariantViolation]:
        """Check state_updates structure."""
        violations = []

        # game_state should be present in most responses
        if "game_state" not in state_updates:
            violations.append(InvariantViolation(
                invariant_name="state_updates.game_state_present",
                expected="game_state should be present in state_updates",
                actual="game_state is missing",
                severity=DifferenceClass.SUSPICIOUS,
            ))

        return violations

    def _check_game_state(
        self, game_state: dict[str, Any]
    ) -> list[InvariantViolation]:
        """Check game_state structure."""
        violations = []

        # player_character_data should persist
        pc_data = game_state.get("player_character_data", {})
        if isinstance(pc_data, dict):
            # Check experience tracking
            exp = pc_data.get("experience", {})
            if isinstance(exp, dict):
                if "current" not in exp:
                    violations.append(InvariantViolation(
                        invariant_name="pc_data.experience.current",
                        expected="experience.current must be present",
                        actual="experience.current is missing",
                        severity=DifferenceClass.SUSPICIOUS,
                    ))

        return violations

    def _check_combat_state(
        self, combat_state: dict[str, Any]
    ) -> list[InvariantViolation]:
        """Check combat state structure when in combat."""
        violations = []

        in_combat = combat_state.get("in_combat", False)
        if in_combat:
            for key, expected_type in REQUIRED_COMBAT_ACTIVE_KEYS.items():
                if key not in combat_state:
                    violations.append(InvariantViolation(
                        invariant_name=f"combat_state.{key}_present",
                        expected=f"{key} must be present when in combat",
                        actual=f"{key} is missing",
                        severity=DifferenceClass.BREAKING,
                    ))

            # Check combatants/initiative_order consistency
            combatants = combat_state.get("combatants", {})
            initiative = combat_state.get("initiative_order", [])
            if isinstance(combatants, dict) and isinstance(initiative, list):
                combatant_keys = set(combatants.keys())
                initiative_names = {
                    entry.get("name") for entry in initiative
                    if isinstance(entry, dict)
                }
                if initiative_names and not combatant_keys:
                    violations.append(InvariantViolation(
                        invariant_name="combat_state.combatants_populated",
                        expected="combatants dict must be populated when initiative_order has entries",
                        actual="combatants is empty but initiative_order has entries",
                        severity=DifferenceClass.BREAKING,
                    ))

        return violations

    def _check_living_world_events(
        self,
        state_updates: dict[str, Any],
        turn_number: int,
    ) -> list[InvariantViolation]:
        """Check living world event generation on LW turns."""
        violations = []

        if "world_events" not in state_updates:
            violations.append(InvariantViolation(
                invariant_name="living_world.world_events_present",
                expected=f"world_events must be present on turn {turn_number} (LW turn)",
                actual="world_events is missing",
                severity=DifferenceClass.BREAKING,
                context={"turn_number": turn_number},
            ))
            return violations

        world_events = state_updates.get("world_events", {})
        if not isinstance(world_events, dict):
            violations.append(InvariantViolation(
                invariant_name="living_world.world_events_present",
                expected=f"world_events must be present on turn {turn_number} (LW turn)",
                actual="world_events is missing or not a dict",
                severity=DifferenceClass.BREAKING,
                context={"turn_number": turn_number},
            ))
            return violations

        background_events = world_events.get("background_events", [])
        if not isinstance(background_events, list):
            violations.append(InvariantViolation(
                invariant_name="living_world.background_events_type",
                expected="background_events must be a list",
                actual=f"background_events is {type(background_events).__name__}",
                severity=DifferenceClass.BREAKING,
                context={"turn_number": turn_number},
            ))
            return violations

        # Check event count
        event_count = len(background_events)
        if event_count < MIN_BACKGROUND_EVENTS_PER_LW_TURN:
            violations.append(InvariantViolation(
                invariant_name="living_world.event_count",
                expected=f"At least {MIN_BACKGROUND_EVENTS_PER_LW_TURN} background events per LW turn",
                actual=f"Only {event_count} events generated",
                severity=DifferenceClass.SUSPICIOUS,
                context={"turn_number": turn_number, "event_count": event_count},
            ))

        # Check event types
        immediate_count = 0
        long_term_count = 0
        for event in background_events:
            if not isinstance(event, dict):
                continue
            event_type = event.get("event_type", "")
            if event_type == "immediate":
                immediate_count += 1
            elif event_type == "long_term":
                long_term_count += 1

            # Check required keys
            for key in REQUIRED_WORLD_EVENT_KEYS:
                if key not in event:
                    violations.append(InvariantViolation(
                        invariant_name=f"living_world.event.{key}_present",
                        expected=f"background_event must have {key}",
                        actual=f"{key} missing from event",
                        severity=DifferenceClass.SUSPICIOUS,
                        context={"turn_number": turn_number, "event": event},
                    ))

        # Validate event type distribution
        if immediate_count < MIN_IMMEDIATE_EVENTS_PER_LW_TURN:
            violations.append(InvariantViolation(
                invariant_name="living_world.immediate_event_count",
                expected=f"At least {MIN_IMMEDIATE_EVENTS_PER_LW_TURN} immediate events",
                actual=f"Only {immediate_count} immediate events",
                severity=DifferenceClass.SUSPICIOUS,
                context={"turn_number": turn_number},
            ))

        if long_term_count < MIN_LONG_TERM_EVENTS_PER_LW_TURN:
            violations.append(InvariantViolation(
                invariant_name="living_world.long_term_event_count",
                expected=f"At least {MIN_LONG_TERM_EVENTS_PER_LW_TURN} long-term event",
                actual=f"Only {long_term_count} long-term events",
                severity=DifferenceClass.SUSPICIOUS,
                context={"turn_number": turn_number},
            ))

        return violations

    def _check_god_mode_directives(
        self,
        response: dict[str, Any],
        state_updates: dict[str, Any],
    ) -> list[InvariantViolation]:
        """Check god mode directive persistence."""
        violations = []

        # Directives should be in custom_campaign_state
        custom_state = state_updates.get("custom_campaign_state", {})
        if isinstance(custom_state, dict):
            directives = custom_state.get("god_mode_directives", [])
            if not isinstance(directives, list) or not directives:
                violations.append(InvariantViolation(
                    invariant_name="god_mode.directives_persist",
                    expected="god_mode_directives must persist in custom_campaign_state",
                    actual="god_mode_directives is missing or empty",
                    severity=DifferenceClass.BREAKING,
                ))
            else:
                # Check directive structure
                for idx, directive in enumerate(directives):
                    if isinstance(directive, dict):
                        if "rule" not in directive:
                            violations.append(InvariantViolation(
                                invariant_name=f"god_mode.directive[{idx}].rule",
                                expected="directive must have 'rule' key",
                                actual=f"directive {idx} missing 'rule'",
                                severity=DifferenceClass.SUSPICIOUS,
                            ))

        return violations

    def _is_living_world_turn(self, turn_number: int) -> bool:
        """Check if this is a living world turn."""
        return turn_number > 0 and turn_number % self.living_world_interval == 0

    @staticmethod
    def _get_type_name(value: Any) -> str:
        """Get type name for comparison."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return type(value).__name__


class RegressionOracle:
    """Compares prior vs current test snapshots to detect regressions."""

    def __init__(self, living_world_interval: int = LIVING_WORLD_TURN_INTERVAL):
        self.checker = InvariantChecker(living_world_interval)

    def compare_snapshots(
        self,
        prior: dict[str, Any],
        current: dict[str, Any],
    ) -> RegressionResult:
        """Compare prior and current test snapshots.

        Args:
            prior: Known-good test snapshot from earlier run.
            current: Current test snapshot to validate.

        Returns:
            RegressionResult with classification of differences.
        """
        result = RegressionResult(overall_status="pass")
        test_name = prior.get("test_name") or current.get("test_name", "unknown")
        result.checked_tests.append(test_name)

        # Check structural differences
        self._compare_structure(prior, current, result)

        # Check turn-by-turn results if available
        prior_turns = prior.get("turn_results", [])
        current_turns = current.get("turn_results", [])
        self._compare_turns(prior_turns, current_turns, result)

        # Check summary fields
        self._compare_summary(prior, current, result)

        # Determine overall status
        if result.breaking_changes:
            result.overall_status = "fail"
        elif result.suspicious_changes:
            result.overall_status = "warn"
        else:
            result.overall_status = "pass"

        return result

    def _compare_structure(
        self,
        prior: dict[str, Any],
        current: dict[str, Any],
        result: RegressionResult,
    ) -> None:
        """Compare structural keys between snapshots."""
        prior_keys = set(prior.keys())
        current_keys = set(current.keys())

        # Keys that existed before but are now missing
        missing_keys = prior_keys - current_keys
        for key in missing_keys:
            if self._is_stable_key(key):
                result.breaking_changes.append(
                    f"Required key '{key}' is missing from current snapshot"
                )
            else:
                result.safe_differences.append(
                    f"Optional key '{key}' is missing from current snapshot"
                )

        # Keys that are new (usually OK)
        new_keys = current_keys - prior_keys
        for key in new_keys:
            result.safe_differences.append(
                f"New key '{key}' added to current snapshot"
            )

    def _compare_turns(
        self,
        prior_turns: list[dict[str, Any]],
        current_turns: list[dict[str, Any]],
        result: RegressionResult,
    ) -> None:
        """Compare turn-by-turn results."""
        if not prior_turns and not current_turns:
            return

        # Check turn count
        if len(current_turns) != len(prior_turns):
            if len(current_turns) < len(prior_turns):
                result.suspicious_changes.append(
                    f"Turn count decreased: {len(prior_turns)} -> {len(current_turns)}"
                )
            else:
                result.safe_differences.append(
                    f"Turn count increased: {len(prior_turns)} -> {len(current_turns)}"
                )

        # Compare matching turns
        for i, (prior_turn, current_turn) in enumerate(zip(prior_turns, current_turns)):
            self._compare_turn(i + 1, prior_turn, current_turn, result)

    def _compare_turn(
        self,
        turn_number: int,
        prior_turn: dict[str, Any],
        current_turn: dict[str, Any],
        result: RegressionResult,
    ) -> None:
        """Compare a single turn's results."""
        # Check for living world content on LW turns
        if turn_number % self.checker.living_world_interval == 0:
            prior_has_lw = self._has_living_world_content(prior_turn)
            current_has_lw = self._has_living_world_content(current_turn)

            if prior_has_lw and not current_has_lw:
                result.breaking_changes.append(
                    f"Turn {turn_number}: Living world content missing "
                    "(was present in prior snapshot)"
                )
            elif not prior_has_lw and current_has_lw:
                result.safe_differences.append(
                    f"Turn {turn_number}: Living world content now present"
                )

        # Check for scene events (statistical over many turns)
        prior_scene = prior_turn.get("scene_event")
        current_scene = current_turn.get("scene_event")
        if prior_scene and not current_scene:
            result.suspicious_changes.append(
                f"Turn {turn_number}: scene_event missing (was present)"
            )

    def _compare_summary(
        self,
        prior: dict[str, Any],
        current: dict[str, Any],
        result: RegressionResult,
    ) -> None:
        """Compare summary fields."""
        # Check boolean invariants
        bool_fields = [
            "living_world_triggered",
            "scene_event_occurred",
            "combat_ended_with_rewards",
            "god_mode_directives_persisted",
        ]

        prior_summary = prior.get("summary", prior)
        current_summary = current.get("summary", current)

        for field in bool_fields:
            prior_val = prior_summary.get(field)
            current_val = current_summary.get(field)

            if prior_val is True and current_val is False:
                result.breaking_changes.append(
                    f"Boolean invariant '{field}' flipped from True to False"
                )
            elif prior_val is False and current_val is True:
                result.safe_differences.append(
                    f"Boolean '{field}' now True (was False)"
                )

        # Check count fields
        count_fields = [
            "total_background_events",
            "total_scene_events",
            "total_faction_updates",
        ]

        for field in count_fields:
            prior_val = prior_summary.get(field, 0)
            current_val = current_summary.get(field, 0)

            if isinstance(prior_val, (int, float)) and isinstance(current_val, (int, float)):
                if prior_val > 0 and current_val == 0:
                    result.breaking_changes.append(
                        f"Count '{field}' went to zero (was {prior_val})"
                    )
                elif current_val < prior_val * 0.5:
                    result.suspicious_changes.append(
                        f"Count '{field}' significantly decreased: {prior_val} -> {current_val}"
                    )
                elif prior_val > 0 and current_val > prior_val * 2:
                    result.suspicious_changes.append(
                        f"Count '{field}' significantly increased: {prior_val} -> {current_val}"
                    )

    def _has_living_world_content(self, turn: dict[str, Any]) -> bool:
        """Check if turn has living world content."""
        response = turn.get("response", {})
        state_updates = response.get("state_updates", {})
        world_events = state_updates.get("world_events", {})
        background_events = world_events.get("background_events", [])
        return bool(background_events)

    @staticmethod
    def _is_stable_key(key: str) -> bool:
        """Determine if a key is expected to be stable."""
        stable_keys = {
            "test_name",
            "test_type",
            "turn_results",
            "summary",
            "game_state",
            "custom_campaign_state",
            "player_character_data",
            "npc_data",
            "combat_state",
            "world_events",
        }
        return key in stable_keys


def validate_multi_turn_test(
    turn_results: list[dict[str, Any]],
    *,
    expect_scene_events: bool = True,
    min_turns: int = 10,
) -> RegressionResult:
    """Validate a multi-turn test for living world invariants.

    This is a convenience function for validating that a multi-turn test
    properly exercises the living world system.

    Args:
        turn_results: List of turn result dicts.
        expect_scene_events: Whether to expect scene events.
        min_turns: Minimum turns for scene event expectation.

    Returns:
        RegressionResult with validation findings.
    """
    result = RegressionResult(overall_status="pass")
    result.checked_tests.append("multi_turn_validation")

    checker = InvariantChecker()
    lw_turns_with_events = 0
    scene_event_count = 0

    for i, turn in enumerate(turn_results):
        turn_number = i + 1
        provided_turn = turn.get("turn_number")
        if provided_turn is not None:
            try:
                turn_number = int(provided_turn)
            except (TypeError, ValueError):
                pass
        response = turn.get("response", {})

        # Validate each response
        violations = checker.validate_response(
            response,
            turn_number=turn_number,
        )

        for violation in violations:
            if violation.severity == DifferenceClass.BREAKING:
                result.breaking_changes.append(
                    f"Turn {turn_number}: {violation.invariant_name} - {violation.actual}"
                )
            elif violation.severity == DifferenceClass.SUSPICIOUS:
                result.suspicious_changes.append(
                    f"Turn {turn_number}: {violation.invariant_name} - {violation.actual}"
                )

        # Track living world turns
        if checker._is_living_world_turn(turn_number):
            state_updates = response.get("state_updates", {})
            world_events = state_updates.get("world_events", {})
            if world_events.get("background_events"):
                lw_turns_with_events += 1

        # Track scene events
        state_updates = response.get("state_updates", {})
        if state_updates.get("scene_event"):
            scene_event_count += 1

    # Check living world cadence
    expected_lw_turns = len(turn_results) // checker.living_world_interval
    if lw_turns_with_events < expected_lw_turns:
        result.suspicious_changes.append(
            f"Living world events on {lw_turns_with_events}/{expected_lw_turns} expected turns"
        )

    # Check scene events over many turns
    if expect_scene_events and len(turn_results) >= min_turns:
        if scene_event_count < MIN_SCENE_EVENTS_PER_10_TURNS:
            result.suspicious_changes.append(
                f"Only {scene_event_count} scene events across {len(turn_results)} turns "
                f"(expected at least {MIN_SCENE_EVENTS_PER_10_TURNS})"
            )

    # Determine overall status
    if result.breaking_changes:
        result.overall_status = "fail"
    elif result.suspicious_changes:
        result.overall_status = "warn"

    return result


def save_regression_snapshot(
    output_path: Path,
    test_name: str,
    test_type: str,
    turn_results: list[dict[str, Any]],
    summary: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Save a test snapshot for future regression comparison.

    Args:
        output_path: Path to save the snapshot JSON.
        test_name: Name of the test.
        test_type: Type of test (e.g., "living_world", "combat", "god_mode").
        turn_results: List of turn results.
        summary: Optional summary statistics.
        metadata: Optional additional metadata.
    """
    snapshot = {
        "test_name": test_name,
        "test_type": test_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "turn_results": turn_results,
        "summary": summary or {},
        "metadata": metadata or {},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, default=str))


def load_regression_snapshot(snapshot_path: Path) -> dict[str, Any]:
    """Load a regression snapshot from disk.

    Args:
        snapshot_path: Path to the snapshot JSON.

    Returns:
        Snapshot dictionary.
    """
    return json.loads(snapshot_path.read_text())
