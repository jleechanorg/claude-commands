
from types import SimpleNamespace

import pytest

from mvp_site import constants, llm_service


@pytest.fixture(autouse=True)
def clear_testing_env(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("MOCK_SERVICES_MODE", raising=False)


def test_selects_gemini_by_default(monkeypatch):
    monkeypatch.setattr(llm_service, "get_user_settings", lambda user_id: {})

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.DEFAULT_MODEL


def test_prefers_openrouter_when_configured(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        },
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == "openrouter"
    assert selection.model == "meta-llama/llama-3.1-70b-instruct"


def test_prefers_cerebras_when_configured(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
        },
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == "cerebras"
    assert selection.model == "llama-3.3-70b"


def test_invalid_provider_falls_back_to_gemini(monkeypatch):
    monkeypatch.setattr(
        llm_service, "get_user_settings", lambda user_id: {"llm_provider": "invalid"}
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.DEFAULT_MODEL


def test_no_user_id_returns_defaults(monkeypatch):
    """When no user_id is provided, return default provider and model."""
    selection = llm_service._select_provider_and_model(None)

    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.DEFAULT_MODEL


def test_force_test_model_env(monkeypatch):
    """MOCK_SERVICES_MODE/FORCE_TEST_MODEL should force test model and provider."""
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")
    monkeypatch.setenv("FORCE_TEST_MODEL", "true")

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.TEST_MODEL


def test_mock_mode_returns_defaults_ignoring_user_prefs(monkeypatch):
    """MOCK_SERVICES_MODE=true should bypass user prefs and return defaults."""
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        },
    )

    selection = llm_service._select_provider_and_model("user-1")

    # Should return defaults despite user having openrouter configured
    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.TEST_MODEL


def test_testing_mode_returns_defaults_ignoring_user_prefs(monkeypatch):
    """TESTING=true should bypass user prefs and return defaults."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",
        },
    )

    selection = llm_service._select_provider_and_model("user-1")

    # Should return defaults despite user having cerebras configured
    assert selection.provider == constants.DEFAULT_LLM_PROVIDER
    assert selection.model == llm_service.TEST_MODEL


def test_allowlisted_user_gets_gemini_3(monkeypatch):
    mock_user = SimpleNamespace(email="jleechan@gmail.com")
    monkeypatch.setattr(llm_service.firebase_auth, "get_user", lambda uid: mock_user)
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {"llm_provider": "gemini", "gemini_model": constants.GEMINI_PREMIUM_MODEL},
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.LLM_PROVIDER_GEMINI
    assert selection.model == constants.GEMINI_PREMIUM_MODEL


def test_non_allowlisted_user_falls_back(monkeypatch):
    mock_user = SimpleNamespace(email="other@example.com")
    monkeypatch.setattr(llm_service.firebase_auth, "get_user", lambda uid: mock_user)
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {"llm_provider": "gemini", "gemini_model": constants.GEMINI_PREMIUM_MODEL},
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.LLM_PROVIDER_GEMINI
    assert selection.model == constants.DEFAULT_GEMINI_MODEL


def test_firebase_error_falls_back(monkeypatch):
    def _raise(_):
        raise RuntimeError("firebase unavailable")

    monkeypatch.setattr(llm_service.firebase_auth, "get_user", _raise)
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {"llm_provider": "gemini", "gemini_model": constants.GEMINI_PREMIUM_MODEL},
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.LLM_PROVIDER_GEMINI
    assert selection.model == constants.DEFAULT_GEMINI_MODEL


def test_legacy_gemini_models_are_mapped(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {"llm_provider": "gemini", "gemini_model": "gemini-2.5-flash"},
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.LLM_PROVIDER_GEMINI
    assert selection.model == constants.DEFAULT_GEMINI_MODEL


def test_invalid_gemini_model_defaults(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "get_user_settings",
        lambda user_id: {"llm_provider": "gemini", "gemini_model": "unsupported"},
    )

    selection = llm_service._select_provider_and_model("user-1")

    assert selection.provider == constants.LLM_PROVIDER_GEMINI
    assert selection.model == constants.DEFAULT_GEMINI_MODEL
