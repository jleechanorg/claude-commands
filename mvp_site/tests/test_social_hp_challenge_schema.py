from mvp_site.narrative_response_schema import NarrativeResponse


def _base_social_hp() -> dict:
    return {
        "npc_name": "Empress Sariel",
        "objective": "Demand her surrender",
        "social_hp": 42,
        "social_hp_max": 45,
        "successes": 3,
        "successes_needed": 5,
        "status": "WAVERING",
        "skill_used": "Intimidation",
        "roll_result": 28,
        "roll_dc": 25,
        "social_hp_damage": 2,
    }


def test_social_hp_challenge_normalizes_request_severity_and_resistance():
    payload = _base_social_hp()
    payload["request_severity"] = "Submission"
    payload["resistance_shown"] = "Her jaw tightens as she steps back."

    response = NarrativeResponse(narrative="n", social_hp_challenge=payload)

    assert response.social_hp_challenge["request_severity"] == "submission"
    assert (
        response.social_hp_challenge["resistance_shown"]
        == "Her jaw tightens as she steps back."
    )


def test_social_hp_challenge_invalid_request_severity_defaults_to_information():
    payload = _base_social_hp()
    payload["request_severity"] = "extortion"

    response = NarrativeResponse(narrative="n", social_hp_challenge=payload)

    assert response.social_hp_challenge["request_severity"] == "information"
