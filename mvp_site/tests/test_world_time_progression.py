import copy

import pytest

from mvp_site import world_time


def _base_time(**overrides):
    base = {
        "year": 1492,
        "month": "Mirtul",
        "day": 10,
        "hour": 14,
        "minute": 30,
        "second": 0,
        "microsecond": 0,
    }
    base.update(overrides)
    return base


def test_think_requests_get_microsecond_tick_when_time_missing():
    previous_time = _base_time(microsecond=5)
    state_changes = {"world_data": {}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        previous_time,
        user_input="think about options",
        is_god_mode=False,
    )

    new_time = updated["world_data"]["world_time"]
    assert new_time["microsecond"] == 6
    assert new_time | {"microsecond": 6} == _base_time(microsecond=6)


def test_story_actions_get_minimum_elapsed_time_when_missing():
    previous_time = _base_time(second=58, minute=12)
    state_changes = {"world_data": {}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        previous_time,
        user_input="attack the bandit",
        is_god_mode=False,
    )

    new_time = updated["world_data"]["world_time"]
    assert new_time["second"] > previous_time["second"]
    assert new_time["minute"] == previous_time["minute"]


def test_preserves_llm_supplied_world_time():
    supplied_time = _base_time(second=42, microsecond=123)
    state_changes = {"world_data": {"world_time": supplied_time}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        _base_time(),
        user_input="advance the plot",
        is_god_mode=False,
    )

    assert updated["world_data"]["world_time"] == supplied_time
