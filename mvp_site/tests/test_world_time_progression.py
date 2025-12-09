import copy

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


def test_missing_world_time_is_not_inferred():
    state_changes = {"world_data": {}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        is_god_mode=False,
    )

    assert "world_time" not in updated["world_data"]


def test_parses_string_world_time_from_llm():
    state_changes = {"world_data": {"world_time": "2025-03-15T10:45:30.123456Z"}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        is_god_mode=False,
    )

    assert updated["world_data"]["world_time"] == {
        "year": 2025,
        "month": 3,
        "day": 15,
        "hour": 10,
        "minute": 45,
        "second": 30,
        "microsecond": 123456,
    }


def test_normalizes_microsecond_field_to_int():
    supplied_time = _base_time(second=42, microsecond="123")
    state_changes = {"world_data": {"world_time": supplied_time}}

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        is_god_mode=False,
    )

    assert updated["world_data"]["world_time"]["microsecond"] == 123
