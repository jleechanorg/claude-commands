from mvp_site import world_logic


def test_temporal_violation_allows_punctuated_month_names():
    """Future times with trailing punctuation should not be flagged as backward.

    Some LLM responses include month names with trailing punctuation (e.g., "Kythorn."),
    which previously caused the temporal comparison to treat the month as zero and
    incorrectly flag a backward jump even when the response was in the future.
    """

    old_time = {
        "year": 1492,
        "month": "Kythorn",
        "day": 1,
        "hour": 15,
        "minute": 15,
        "second": 0,
        "microsecond": 0,
    }
    # Same date but one hour later; trailing punctuation on month should be normalized
    new_time = {
        "year": 1492,
        "month": "Kythorn.",
        "day": 1,
        "hour": 16,
        "minute": 0,
        "second": 0,
        "microsecond": 0,
    }

    assert not world_logic._check_temporal_violation(old_time, new_time)
