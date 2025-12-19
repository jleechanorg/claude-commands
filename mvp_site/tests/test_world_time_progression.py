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


def test_completes_partial_world_time_from_existing_state():
    """When LLM generates partial time (missing year/month/day), complete from existing state."""
    # LLM only provides hour and minute, missing year/month/day
    partial_time = {"hour": 8, "minute": 15, "time_of_day": "Morning"}
    state_changes = {"world_data": {"world_time": partial_time}}

    # Existing state has full time context
    existing_time = {
        "year": 3641,
        "month": "Mirtul",
        "day": 20,
        "hour": 8,
        "minute": 0,
        "second": 0,
        "microsecond": 0,
        "time_of_day": "Morning",
    }

    updated = world_time.ensure_progressive_world_time(
        copy.deepcopy(state_changes),
        is_god_mode=False,
        existing_time=existing_time,
    )

    result_time = updated["world_data"]["world_time"]

    # Should preserve LLM's values for provided fields
    assert result_time["hour"] == 8
    assert result_time["minute"] == 15
    assert result_time["time_of_day"] == "Morning"

    # Should complete missing fields from existing state
    assert result_time["year"] == 3641, f"Year should be from existing state, got {result_time.get('year')}"
    assert result_time["month"] == "Mirtul", f"Month should be from existing state, got {result_time.get('month')}"
    assert result_time["day"] == 20, f"Day should be from existing state, got {result_time.get('day')}"
    assert result_time["second"] == 0
    assert result_time["microsecond"] == 0


def test_validate_world_time_completeness_identifies_missing_fields():
    """Test that validation identifies missing required fields."""
    # Complete time
    complete_time = _base_time(time_of_day="Afternoon")
    is_complete, missing = world_time.validate_world_time_completeness(complete_time)
    assert is_complete is True, f"Complete time should pass validation, missing: {missing}"
    assert len(missing) == 0

    # Partial time (missing year, month, day)
    partial_time = {"hour": 8, "minute": 15, "time_of_day": "Morning"}
    is_complete, missing = world_time.validate_world_time_completeness(partial_time)
    assert is_complete is False, "Partial time should fail validation"
    assert "year" in missing
    assert "month" in missing
    assert "day" in missing
    assert "second" in missing
    assert "microsecond" in missing

    # Empty/None time
    is_complete, missing = world_time.validate_world_time_completeness(None)
    assert is_complete is False
    assert len(missing) == 8  # All required fields missing


def test_complete_partial_world_time_with_defaults():
    """Test fallback defaults when no existing time is provided."""
    partial_time = {"hour": 15, "minute": 30}

    completed = world_time.complete_partial_world_time(partial_time, None)

    # Should preserve provided values
    assert completed["hour"] == 15
    assert completed["minute"] == 30

    # Should use defaults for missing values
    assert completed["year"] == 1492  # Default Forgotten Realms year
    assert completed["month"] == 1
    assert completed["day"] == 1
    assert completed["second"] == 0
    assert completed["microsecond"] == 0
    assert completed["time_of_day"] == "Midday"
