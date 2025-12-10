from mvp_site import world_time


class DummyResponse:
    def __init__(self, world_data: dict):
        self._world_data = world_data

    def get_state_updates(self):
        return {"world_data": self._world_data}


def test_parse_timestamp_string_to_world_time():
    timestamp = "2025-03-15T10:45:30.123456Z"

    parsed = world_time.parse_timestamp_to_world_time(timestamp)

    assert parsed == {
        "year": 2025,
        "month": 3,
        "day": 15,
        "hour": 10,
        "minute": 45,
        "second": 30,
        "microsecond": 123456,
    }


def test_extract_world_time_from_timestamp_only_response():
    response = DummyResponse({"timestamp_iso": "2026-12-01T08:00:00+02:00"})

    extracted = world_time.extract_world_time_from_response(response)

    assert extracted == {
        "year": 2026,
        "month": 12,
        "day": 1,
        "hour": 6,
        "minute": 0,
        "second": 0,
        "microsecond": 0,
    }


def test_apply_timestamp_populates_missing_world_time():
    state_changes = {"world_data": {"timestamp": "2027-07-04T21:05:45"}}

    updated = world_time.apply_timestamp_to_world_time(state_changes)

    assert updated["world_data"]["world_time"] == {
        "year": 2027,
        "month": 7,
        "day": 4,
        "hour": 21,
        "minute": 5,
        "second": 45,
        "microsecond": 0,
    }
