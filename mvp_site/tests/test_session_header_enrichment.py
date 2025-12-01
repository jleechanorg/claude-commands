import importlib
import sys
import types

import pytest


@pytest.fixture
def world_logic_module():
    modules_to_clear = ["mvp_site.world_logic"]
    backup_modules = {name: sys.modules.get(name) for name in modules_to_clear}
    firebase_backup = {
        "firebase_admin": sys.modules.get("firebase_admin"),
        "firebase_admin.credentials": sys.modules.get("firebase_admin.credentials"),
    }

    for name in modules_to_clear:
        sys.modules.pop(name, None)

    firebase_admin_mock = types.SimpleNamespace()

    def _raise_value_error():
        raise ValueError("app not initialized")

    firebase_admin_mock.get_app = _raise_value_error
    firebase_admin_mock.initialize_app = lambda *args, **kwargs: None

    credentials_module = types.SimpleNamespace(Certificate=lambda *args, **kwargs: None)
    firebase_admin_mock.credentials = credentials_module

    sys.modules["firebase_admin"] = firebase_admin_mock
    sys.modules["firebase_admin.credentials"] = credentials_module

    import mvp_site.world_logic as world_logic

    importlib.reload(world_logic)

    yield world_logic

    for name, module in firebase_backup.items():
        if module is not None:
            sys.modules[name] = module
        else:
            sys.modules.pop(name, None)

    for name, module in backup_modules.items():
        if module is not None:
            sys.modules[name] = module
        else:
            sys.modules.pop(name, None)


def test_enriches_empty_header_with_progress(world_logic_module):
    result = world_logic_module._enrich_session_header_with_progress(
        "",
        {"player_character_data": {"xp_current": 120, "xp_next_level": 200, "gold": 50}},
    )

    assert result == "XP: 120/200 | Gold: 50gp"


def test_enriches_status_line(world_logic_module):
    header = "Status: Healthy"
    result = world_logic_module._enrich_session_header_with_progress(
        header,
        {"player_character_data": {"xp_current": 80, "xp_next_level": 100, "gold": 25}},
    )

    assert result == "Status: Healthy | XP: 80/100 | Gold: 25gp"


def test_appends_to_last_line_without_status(world_logic_module):
    header = "Session 1\nLocation: Forest"
    result = world_logic_module._enrich_session_header_with_progress(
        header,
        {"player_character_data": {"xp_current": 10, "xp_next_level": 20}},
    )

    assert result == "Session 1\nLocation: Forest | XP: 10/20"


def test_respects_existing_tokens(world_logic_module):
    header = "Status: XP: 5 | Gold: 10gp"
    result = world_logic_module._enrich_session_header_with_progress(
        header,
        {"player_character_data": {"xp_current": 99, "xp_next_level": 100, "gold": 30}},
    )

    assert result == header


def test_handles_zero_next_level(world_logic_module):
    result = world_logic_module._enrich_session_header_with_progress(
        "",
        {"player_character_data": {"xp_current": 5, "xp_next_level": 0}},
    )

    assert result == "XP: 5/0"


def test_skips_missing_progress_data(world_logic_module):
    header = "Session 2"
    result = world_logic_module._enrich_session_header_with_progress(
        header,
        {"player_character_data": {}},
    )

    assert result == header
