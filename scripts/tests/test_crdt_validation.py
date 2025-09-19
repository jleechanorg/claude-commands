"""Pytest wrapper around the consolidated CRDT validation harness."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent / 'crdt_validation.py'
spec = importlib.util.spec_from_file_location('crdt_validation_suite', MODULE_PATH)
crdt_validation = importlib.util.module_from_spec(spec)
sys.modules.setdefault('crdt_validation_suite', crdt_validation)
assert spec.loader is not None
spec.loader.exec_module(crdt_validation)

from crdt_validation_suite import Scenario, ScenarioResult


def _execute_scenario(scenario: Scenario) -> ScenarioResult:
    result = scenario.runner()
    if result.status == "skip":
        details = "; ".join(result.details) if result.details else "skipped"
        pytest.skip(details)
    assert result.status == "pass", \
        f"Scenario '{scenario.name}' failed: {'; '.join(result.details)}"
    return result


@pytest.mark.parametrize(
    "scenario",
    crdt_validation.SCENARIO_GROUPS["properties"].scenarios,
    ids=lambda scenario: scenario.name,
)
def test_crdt_properties(scenario: Scenario) -> None:
    _execute_scenario(scenario)


@pytest.mark.parametrize(
    "scenario",
    crdt_validation.SCENARIO_GROUPS["edge_cases"].scenarios,
    ids=lambda scenario: scenario.name,
)
def test_crdt_edge_cases(scenario: Scenario) -> None:
    _execute_scenario(scenario)


@pytest.mark.parametrize(
    "scenario",
    crdt_validation.SCENARIO_GROUPS["production"].scenarios,
    ids=lambda scenario: scenario.name,
)
def test_crdt_production_scenarios(scenario: Scenario) -> None:
    _execute_scenario(scenario)


@pytest.mark.parametrize(
    "scenario",
    crdt_validation.SCENARIO_GROUPS["performance"].scenarios,
    ids=lambda scenario: scenario.name,
)
def test_crdt_performance(scenario: Scenario) -> None:
    _execute_scenario(scenario)


@pytest.mark.parametrize(
    "scenario",
    crdt_validation.SCENARIO_GROUPS["security"].scenarios,
    ids=lambda scenario: scenario.name,
)
def test_crdt_security(scenario: Scenario) -> None:
    _execute_scenario(scenario)
