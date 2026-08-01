from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


# This test ships alongside cmux_resume_watchdog.py inside the
# cmux-resume-watchdog skill. The script lives in the same dir as this test
# (NOT in a sibling scripts/ subdir as it does in $GITHUB_REPOSITORY).
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "cmux_resume_watchdog.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cmux_resume_watchdog", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUOTA_EXAMPLES = [
    "API Error: Request rejected (429) · Token Plan usage limit reached: Upgrade your Token Plan or purchase Credits for more usage. (2056)",
    "Rate limited after 10 retries — HTTP 429: Token Plan usage limit reached: Upgrade your Token Plan or purchase Credits for more usage. (2056)",
    "You've hit your weekly limit · resets Aug 3, 2026 (America/Los_Angeles)",
    "You've hit your session limit · resets 9:50pm (America/Los_Angeles)",
    "You've hit your limit for Claude messages. Limits will reset at 10:00 PM.",
    "You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 2026-08-01T00:00:00Z.",
    "RESOURCE_EXHAUSTED: Individual quota reached.",
    "RESOURCE_EXHAUSTED (code 429): Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 2 hours.",
    "Too many requests to Gemini API.",
    "HTTP 429: Monthly usage limit reached. Resets in 7 days. To continue using this model now, enable usage from your available balance.",
    '{"type":"error","error":{"type":"rate_limit_error","message":"account quota exhausted"}}',
]


@pytest.mark.parametrize("message", QUOTA_EXAMPLES)
def test_historical_quota_examples_are_fastembed_eligible(message):
    watchdog = load_module()
    calls = []

    def semantic_predict(text):
        calls.append(text)
        return "quota", 0.81

    screen = f"⏺ {message}\n\n❯ "
    decision = watchdog.classify_screen(screen, semantic_predict, lambda _: "clear")

    assert decision.kind == "quota"
    assert decision.path in {"chrome", "fastembed"}
    assert decision.eligible is True


@pytest.mark.parametrize(
    "message",
    [
        "<h3>Usage limit reached</h3> Bugbot is counted against Cursor usage for this user or team.",
        "GitHub API quota prose in a source file; do not treat this discussion as a live failure.",
    ],
)
def test_discussion_and_bot_controls_are_not_eligible(message):
    watchdog = load_module()
    screen = f"Agent finished successfully.\n{message}\n\n❯ "
    decision = watchdog.classify_screen(screen, lambda _: ("clear", 0.79), lambda _: "quota")

    assert decision.kind is None
    assert decision.path == "fastembed"
    assert decision.eligible is False


def test_ambiguous_fastembed_result_uses_llm_fallback():
    watchdog = load_module()
    screen = "⏺ API Error: account allocation rejected (429)\n\n❯ "
    decision = watchdog.classify_screen(
        screen,
        lambda _: ("ambiguous", 0.56),
        lambda _: "quota",
    )

    assert decision.kind == "quota"
    assert decision.path == "llm-fallback"


def test_reset_hint_without_structural_marker_stays_fastembed_quota():
    watchdog = load_module()
    screen = (
        "⚠ Individual quota reached. Please upgrade your subscription to increase your limits.\n"
        "Resets in 4h16m6s.\nError ID: 96c749fe...\n❯ "
    )
    decision = watchdog.classify_screen(screen, lambda _: ("quota", 0.84), lambda _: "quota")

    assert decision.kind == "quota"
    assert decision.path in {"chrome", "fastembed"}
    assert decision.eligible is True


@pytest.mark.parametrize(
    "bullet",
    ["⎿", "▝", "▜", "█", "›", "»", "•", "·"],
)
def test_claude_code_ui_bullet_before_quota_hint_still_eligible(bullet):
    """Regression: QUICK_QUOTA_HINT_RE was line-anchored to ^\\s* which skipped
    Claude Code's `⎿  You've hit your weekly limit` format and let surfaces
    like workspace:8 surface:140 'ponytail policy' slip into NOT_ELIGIBLE
    while still being quota-blocked."""
    watchdog = load_module()
    line = f"  {bullet}  You've hit your weekly limit · resets Aug 1 at 4pm (America/Los_Angeles)"
    screen = (
        f"─ Worked for 3m 52s ─\n"
        f"{line}\n"
        "   /upgrade or /usage-credits to finish what you're working on.\n"
        "❯ "
    )

    # Direct regex assertion: the chrome short-circuit must fire.
    assert watchdog.QUICK_QUOTA_HINT_RE.search(screen) is not None, (
        f"QUICK_QUOTA_HINT_RE missed the {bullet!r}-prefixed quota line"
    )

    # End-to-end: classify_screen must return kind=quota regardless of fastembed score.
    decision = watchdog.classify_screen(screen, lambda _: ("clear", 0.79), lambda _: "quota")

    assert decision.kind == "quota"
    assert decision.path in {"chrome", "fastembed"}
    assert decision.eligible is True


def test_usage_limit_menu_without_structural_markers_is_fastembed_quota():
    watchdog = load_module()
    screen = (
        "What do you want to do?\n"
        "  1. Stop and wait for limit to reset\n"
        "  2. Switch to usage credits\n"
        "  3. Upgrade your plan\n"
        "❯ "
    )
    decision = watchdog.classify_screen(screen, lambda _: ("ambiguous", 0.10), lambda _: None)

    assert decision.kind == "quota"
    assert decision.path in {"chrome", "fastembed"}
    assert decision.eligible is True


def test_quota_hint_before_resume_marker_still_classifies_as_quota():
    """Regression: classification_text() drops everything before the last
    [cmux-resume-watchdog] marker, so when the watchdog's own resume prompt
    was just typed into a Claude session, the weekly-limit banner that came
    BEFORE the marker falls out of the tail passed to classify_screen and
    fastembed then sees an empty `❯` prompt and labels the surface 'clear'
    with a high confidence — even though the agent is still quota-blocked.

    Fix: chrome short-circuit must run on the full screen, not the
    post-marker tail. Observed live: workspace:8 surface:139 on the dev-fork
    socket scored 0.722 / kind=clear instead of kind=quota."""
    watchdog = load_module()
    screen = (
        "  ⎿  You've hit your weekly limit · resets Aug 1 at 4pm (America/Los_Angeles)\n"
        "     /upgrade or /usage-credits to finish what you're working on.\n"
        "\n"
        "✻ Crunched for 0s\n"
        "\n"
        "────────────────────────\n"
        "❯ Continue the in-flight work from where it stopped. Read any STATE.md or checkpoint first. [cmux-resume-watchdog]\n"
        "\n"
        "────────────────────────\n"
        "❯\n"
    )

    # The chrome short-circuit must fire on the full screen, even though
    # the [cmux-resume-watchdog] marker appears AFTER the quota banner.
    decision = watchdog.classify_screen(screen, lambda _: ("clear", 0.92), lambda _: "quota")

    assert decision.kind == "quota", (
        f"weekly-limit banner before the [cmux-resume-watchdog] marker was "
        f"dropped; got kind={decision.kind!r} path={decision.path!r} "
        f"action={decision.action!r} score={decision.score:.3f}"
    )
    assert decision.path == "chrome"
    assert decision.action == "WOULD_RESUME"
    assert decision.eligible is True


@pytest.mark.parametrize("status", ["Retrying in 36s · attempt 7/10", "Working (42s · esc to interrupt)"])
def test_active_retry_or_generation_is_never_resume_eligible(status):
    watchdog = load_module()
    screen = (
        "⏺ API Error: Request rejected (429) · Token Plan usage limit reached. (2056)\n"
        f"{status}\n❯ "
    )
    decision = watchdog.classify_screen(screen, lambda _: ("quota", 0.91), lambda _: "quota")

    assert decision.eligible is False
    assert decision.action == "WAIT_RETRY"


def test_spinner_surface_title_is_busy():
    watchdog = load_module()

    assert watchdog.title_is_busy("⠹ user_scope") is True
    assert watchdog.title_is_busy("user_scope") is False


def test_socket_discovery_keeps_all_responsive_candidates(tmp_path, monkeypatch):
    watchdog = load_module()
    live = tmp_path / "cmux-debug-dev-fork.sock"
    default = tmp_path / "cmux.sock"
    live.touch()
    default.touch()
    monkeypatch.setenv("CMUX_SOCKET_PATH", str(default))
    monkeypatch.setattr(watchdog, "SOCKET_GLOBS", (str(tmp_path / "*.sock"),))
    monkeypatch.setattr(watchdog, "socket_responds", lambda path: path == str(live))

    assert watchdog.discover_cmux_sockets() == [str(live)]


def test_dry_run_sends_nothing_and_writes_no_state(tmp_path, monkeypatch, capsys):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(socket_path, "workspace:15", "surface:31", "Token Plan"),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: "⏺ API Error: Request rejected (429) · Token Plan usage limit reached. (2056)\n❯ ",
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.88)),
    )
    sent = []
    monkeypatch.setattr(watchdog, "send_resume", lambda *args: sent.append(args))

    assert watchdog.main(["--dry-run", "--no-debounce"]) == 0
    output = capsys.readouterr().out

    assert "workspace:15" in output
    assert "surface:31" in output
    assert "WOULD_RESUME" in output
    assert "path=fastembed" in output
    assert sent == []
    assert not state_file.exists()


def test_dry_run_treats_busy_title_as_would_resume(monkeypatch, tmp_path, capsys):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(
                socket_path,
                "workspace:15",
                "surface:96",
                "⠦ user_scope",
            ),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: "⏺ API Error: Request rejected (429) · Token Plan usage limit reached: Upgrade your Token Plan or purchase Credits for more usage. (2056)\\n❯ ",
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.84)),
    )
    sent = []
    monkeypatch.setattr(watchdog, "send_resume", lambda *args: sent.append(args))

    assert watchdog.main(["--dry-run", "--workspace", "workspace:15", "--surface", "surface:96"]) == 0
    output = capsys.readouterr().out

    assert "action=WOULD_RESUME" in output
    assert sent == []
    assert not state_file.exists()


def test_dry_run_collects_menu_based_quota_signals(monkeypatch, tmp_path, capsys):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(
                socket_path,
                "workspace:22",
                "surface:44",
                "jleechan@jeffreys-macbook-pro: ~/projects/cold-reviewer",
            ),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: (
            "What do you want to do?\n"
            "  1. Stop and wait for limit to reset\n"
            "  2. Switch to usage credits\n"
            "  3. Upgrade your plan\n"
            "Enter to confirm · Esc to cancel\n"
            "❯ "
        ),
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("ambiguous", 0.10)),
    )

    sent = []
    monkeypatch.setattr(watchdog, "send_resume", lambda *args: sent.append(args))

    assert watchdog.main(["--dry-run", "--workspace", "workspace:22", "--surface", "surface:44"]) == 0
    output = capsys.readouterr().out

    assert "action=WOULD_RESUME" in output
    assert sent == []
    assert not state_file.exists()


def test_resume_backoff_is_exponential_with_one_hour_cap():
    watchdog = load_module()

    assert watchdog.resume_backoff_seconds(1) == 900
    assert watchdog.resume_backoff_seconds(2) == 1800
    assert watchdog.resume_backoff_seconds(3) == 3600
    assert watchdog.resume_backoff_seconds(10) == 3600


def test_backoff_is_enforced_before_resuming(tmp_path, monkeypatch, capsys):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    now = 2_000_000.0
    key = "/tmp/live.sock|workspace:1|surface:31"
    state_file.write_text(json.dumps({key: {"last_resume": now - 1000, "attempt_count": 2}}))
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog.time, "time", lambda: now)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(socket_path, "workspace:1", "surface:31", "Token Plan"),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: "API Error: Request rejected (429) · Token Plan usage limit reached. (2056)\\n❯ ",
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.91)),
    )
    sent = []
    monkeypatch.setattr(watchdog, "send_resume", lambda *args: sent.append(args))

    assert watchdog.main(["--workspace", "workspace:1", "--surface", "surface:31"]) == 0
    output = capsys.readouterr().out

    assert "action=WAIT_DEBOUNCE" in output
    assert sent == []


def test_relative_reset_hint_is_stable_until_expiry(tmp_path, monkeypatch, capsys):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    key = "/tmp/live.sock|workspace:1|surface:31"
    state_file.write_text(json.dumps({key: {}}))
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog.time, "time", lambda: 1_000_000.0)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(socket_path, "workspace:1", "surface:31", "Token Plan"),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: "⚠ Individual quota reached. Please upgrade your subscription to increase your limits.\nResets in 7 minutes.\n❯ ",
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.91)),
    )
    assert watchdog.main(["--workspace", "workspace:1", "--surface", "surface:31", "--no-debounce"]) == 0
    output = capsys.readouterr().out
    # WAIT_RESET is no longer a gating action — reset_hint is still tracked
    # in state.json so the operator can see when the wait ends, but the
    # resume proceeds either way.
    assert "action=WOULD_RESUME" in output
    assert "reset=" in output and "2026-" in output  # reset hint is still logged

    monkeypatch.setattr(watchdog.time, "time", lambda: 1_000_700.0)
    assert watchdog.main(["--workspace", "workspace:1", "--surface", "surface:31", "--no-debounce"]) == 0
    output = capsys.readouterr().out
    assert "action=WOULD_RESUME" in output


def test_resume_attempt_count_is_persisted_for_backoff(tmp_path, monkeypatch):
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog.time, "time", lambda: 2_000_001.0)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(socket_path, "workspace:1", "surface:31", "Token Plan"),
        ],
    )
    monkeypatch.setattr(
        watchdog,
        "read_screen",
        lambda surface: "API Error: Request rejected (429) · Token Plan usage limit reached. (2056)\\n❯ ",
    )
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.91)),
    )
    monkeypatch.setattr(watchdog, "send_resume", lambda *args: None)

    assert watchdog.main(["--no-debounce", "--workspace", "workspace:1", "--surface", "surface:31"]) == 0

    state = json.loads(state_file.read_text(encoding="utf-8"))
    key = "/tmp/live.sock|workspace:1|surface:31"
    assert state[key]["attempt_count"] == 1


def test_wait_reset_gate_is_always_bypassed(monkeypatch, tmp_path, capsys):
    """Regression: when the screen shows a future reset time (e.g. "Resets in 3h15m"),
    the watchdog used to default to action=WAIT_RESET and skip the resume. For
    surfaces the operator wants to keep pinging (e.g. a code-agent stuck on
    its own weekly quota that the user is waiting on), the resume must still
    land.

    Concrete miss observed: workspace:30 surface:134 'agyd' is
    kind=quota with reset_epoch 4h15m in the future, last_resume=never,
    operator wants watchdog to keep submitting the prompt so the agent's
    input buffer stays primed for when the limit lifts.

    The previous --force-resume flag was removed; bypassing WAIT_RESET is
    now the default behavior so the operator doesn't have to remember it."""
    watchdog = load_module()
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog.time, "time", lambda: 2_000_000.0)
    monkeypatch.setattr(watchdog, "discover_cmux_sockets", lambda: ["/tmp/live.sock"])
    monkeypatch.setattr(
        watchdog,
        "list_terminal_surfaces",
        lambda socket_path: [
            watchdog.Surface(socket_path, "workspace:30", "surface:134", "agyd"),
        ],
    )
    screen = (
        "⏺ Continue the in-flight work... [cmux-resume-watchdog]\n"
        "⚠ Individual quota reached. Resets in 3h15m17s. Error ID: 9d7fa473-346\n"
        "❯ "
    )
    monkeypatch.setattr(watchdog, "read_screen", lambda surface: screen)
    monkeypatch.setattr(
        watchdog,
        "build_semantic_predictor",
        lambda: (lambda _: ("quota", 0.88)),
    )
    sent = []
    monkeypatch.setattr(watchdog, "send_resume", lambda *args, **kwargs: sent.append(args))

    # No --force-resume flag (it doesn't exist anymore) — default behavior
    # must still bypass WAIT_RESET.
    assert watchdog.main(
        ["--no-debounce", "--workspace", "workspace:30", "--surface", "surface:134"]
    ) == 0
    output = capsys.readouterr().out
    assert "action=WOULD_RESUME" in output, f"expected WOULD_RESUME, got:\n{output}"
    assert "WAIT_RESET" not in output, f"WAIT_RESET must never gate by default, got:\n{output}"
    assert len(sent) == 1, f"default behavior should resume once, sent={sent}"


def test_no_force_resume_argparse_flag(monkeypatch):
    """The --force-resume flag was removed — bypassing WAIT_RESET is now
    the default. Asserting argparse rejects the flag keeps us from
    re-introducing it as a hidden opt-in."""
    watchdog = load_module()
    with pytest.raises(SystemExit):
        watchdog.main(["--no-debounce", "--force-resume"])


def test_list_terminal_surfaces_returns_selected_and_inactive(monkeypatch):
    """Regression: cmux tree --all --json enumerates every terminal surface in
    every pane, including non-selected (inactive) ones — verified against
    cmux 0.64.16 (2026-08-01). Earlier revisions of this function assumed
    tree only returned the selected surface per pane and added a fallback
    enumerator that called a non-existent `cmux list_surfaces <UUID>`
    subcommand; that fallback was silently a no-op (cmux 0.64.x has no
    `list_surfaces` verb) and has now been deleted.

    The watchdog must therefore see both surface:134 (selected) AND
    AB28223F... (non-selected in the same pane) in a single tree call.
    """
    watchdog = load_module()

    # Real cmux 0.64.x tree --all --json returns BOTH the selected AND
    # non-selected terminal surfaces in every pane — no per-workspace
    # fallback enumerator is required.
    tree_payload = {
        "windows": [
            {
                "ref": "window:1",
                "workspaces": [
                    {
                        "ref": "workspace:30",
                        "title": "quota",
                        "panes": [
                            {
                                "ref": "pane:88",
                                "surfaces": [
                                    {"ref": "surface:134", "title": "token-plan", "type": "terminal", "selected": True},
                                    {"ref": "AB28223F-C0D4-4D9B-A75C-2508FBE9B1D8", "title": "agyd", "type": "terminal", "selected": False},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    cmux_calls: list[tuple] = []

    def fake_run_cmux(socket_path, args, timeout=12):
        cmux_calls.append(tuple(args))
        from unittest.mock import MagicMock
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        if "tree" in args:
            result.stdout = json.dumps(tree_payload)
        else:
            result.stdout = ""
        return result

    monkeypatch.setattr(watchdog, "_run_cmux", fake_run_cmux)

    rows = watchdog.list_terminal_surfaces("/tmp/live.sock")
    surface_ids = {(r.workspace, r.surface) for r in rows}

    assert ("workspace:30", "surface:134") in surface_ids, "selected surface must come through"
    assert ("workspace:30", "AB28223F-C0D4-4D9B-A75C-2508FBE9B1D8") in surface_ids, (
        "non-selected surface AB28223F must also come through — cmux tree --all --json "
        "returns every terminal surface in every pane in cmux 0.64.x"
    )

    # And critically: no fallback enumerator call. The non-existent
    # `list_surfaces <UUID>` subcommand that the old code issued must be gone.
    assert not any("list_surfaces" in a for a in cmux_calls), (
        f"list_terminal_surfaces must not shell out to a non-existent cmux verb: calls={cmux_calls}"
    )
    assert not any("list_workspaces" in a for a in cmux_calls), (
        f"list_terminal_surfaces must not call list_workspaces either: calls={cmux_calls}"
    )


def test_list_terminal_surfaces_skips_browser_surfaces(monkeypatch):
    """Regression: the watchdog should only see terminal surfaces. Browser
    surfaces (cmux browser panels) must be filtered out so the watchdog
    doesn't try to read-screen / send-text to a browser."""
    watchdog = load_module()
    tree_payload = {
        "windows": [
            {
                "ref": "window:1",
                "workspaces": [
                    {
                        "ref": "workspace:5",
                        "title": "docs",
                        "panes": [
                            {
                                "ref": "pane:9",
                                "surfaces": [
                                    {"ref": "surface:11", "title": "shell", "type": "terminal"},
                                    {"ref": "surface:12", "title": "docs page", "type": "browser", "selected": True},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    def fake_run_cmux(socket_path, args, timeout=12):
        from unittest.mock import MagicMock
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        if "tree" in args:
            result.stdout = json.dumps(tree_payload)
        else:
            result.stdout = ""
        return result

    monkeypatch.setattr(watchdog, "_run_cmux", fake_run_cmux)

    rows = watchdog.list_terminal_surfaces("/tmp/live.sock")
    surface_ids = {r.surface for r in rows}
    assert surface_ids == {"surface:11"}, f"only the terminal surface should come through, got {surface_ids}"


def test_list_terminal_surfaces_accepts_both_json_flag_orderings(monkeypatch):
    """Both `cmux --json tree --all` (flag before subcommand) and
    `cmux tree --all --json` (flag after subcommand) are accepted by cmux
    0.64.x. The watchdog tries both orderings so a future cmux CLI change
    that removes one form doesn't silently break surface enumeration."""
    watchdog = load_module()

    # tree_payload intentionally empty — we just want to see which
    # `--json` ordering the watchdog picked.
    tree_payload = {"windows": []}

    call_log: list[tuple] = []

    def fake_run_cmux(socket_path, args, timeout=12):
        call_log.append(tuple(args))
        from unittest.mock import MagicMock
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        # Accept any ordering that has all three of --json, tree, --all
        if "--json" in args and "tree" in args and "--all" in args:
            result.stdout = json.dumps(tree_payload)
        else:
            result.stdout = ""
        return result

    monkeypatch.setattr(watchdog, "_run_cmux", fake_run_cmux)

    watchdog.list_terminal_surfaces("/tmp/live.sock")
    assert len(call_log) >= 1, "watchdog must issue at least one tree call"
    # First attempt is `--json tree --all` — the form that worked in the
    # original commit. If the future cmux removes that form, the fallback
    # `tree --all --json` kicks in.
    assert call_log[0] == ("--json", "tree", "--all") or call_log[0] == ("tree", "--all", "--json"), (
        f"unexpected first tree call: {call_log[0]}"
    )


def test_list_terminal_surfaces_raises_when_cmux_tree_fails(monkeypatch):
    """If both `--json` orderings fail (cmux down, socket gone), the
    watchdog must raise so the per-tick error handler logs it and
    `KeepAlive` respawns us — not silently return []."""
    watchdog = load_module()

    def fake_run_cmux(socket_path, args, timeout=12):
        from unittest.mock import MagicMock
        result = MagicMock()
        result.returncode = 1  # cmux returns non-zero on socket-down
        result.stderr = "socket gone"
        result.stdout = ""
        return result

    monkeypatch.setattr(watchdog, "_run_cmux", fake_run_cmux)

    with pytest.raises(RuntimeError, match="cmux tree failed"):
        watchdog.list_terminal_surfaces("/tmp/live.sock")


def test_send_resume_sleeps_between_typed_text_and_enter(monkeypatch):
    """Regression: send_resume() used to type the resume prompt via
    `cmux send` and then immediately `cmux send-key enter`. On a fast
    surface the Enter landed BEFORE the typed text was committed to the
    input buffer, so Claude Code processed an empty submit and replied
    with "did not submit input" instead of doing the resume work.

    Fix: assert that time.sleep is called between the text `send` and the
    `send-key enter` so the typed text has time to land in the buffer."""
    watchdog = load_module()
    surface = watchdog.Surface(
        "/tmp/live.sock",
        "workspace:1",
        "surface:31",
        "Token Plan",
    )

    # Track the order of cmux subcommands and the timing of sleep calls.
    cmux_calls: list[tuple[float, tuple]] = []
    sleep_calls: list[float] = []
    fake_now = {"t": 1000.0}

    def fake_clock() -> float:
        return fake_now["t"]

    def fake_run_cmux(socket_path, args, timeout=12):
        cmux_calls.append((fake_now["t"], tuple(args)))
        # Advance the fake clock so the next call has a different time.
        fake_now["t"] += 0.05
        from unittest.mock import MagicMock
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        fake_now["t"] += seconds

    monkeypatch.setattr(watchdog.time, "time", fake_clock)
    monkeypatch.setattr(watchdog, "_run_cmux", fake_run_cmux)
    monkeypatch.setattr(watchdog.time, "sleep", fake_sleep)

    watchdog.send_resume(surface, menu_open=False)

    # The 3 cmux subcommands in order: send text → send-key enter.
    assert len(cmux_calls) == 2, f"expected 2 cmux calls, got {cmux_calls}"
    text_call, enter_call = cmux_calls
    assert text_call[1][0] == "send"
    assert text_call[1][-1] == watchdog.RESUME_PROMPT
    assert enter_call[1][0] == "send-key"
    assert enter_call[1][-1] == "enter"

    # At least one sleep must happen between the text call and the enter call.
    assert len(sleep_calls) >= 1, "no sleep between typed text and Enter — Enter can race the buffer"
    assert sleep_calls[0] > 0, "sleep duration must be positive"
    # And that sleep must have happened AFTER the text call and BEFORE the enter call.
    assert enter_call[0] > text_call[0], "Enter was sent before/with the text — race condition"


def test_quick_quota_hint_matches_bullet_prefixed_429_minimax_error():
    """Regression: 429 errors from MiniMax / Token Plan usage limit preceded by
    bullet symbols (e.g. ⏺ API Error: Request rejected (429) · Token Plan usage limit reached)
    were missed because of restrictive line-start anchors in QUICK_QUOTA_HINT_RE."""
    watchdog = load_module()
    screen = (
        "Last login: Sun Jul 26 18:53:12 on ttys040\n"
        " ▐▛███▜▌   Claude Code v2.1.220\n"
        "▝▜█████▛▘  MiniMax-M3 with high effort · API Usage Billing\n"
        "  ☘☘ ☝☝    ~/projects_other/llm_inspector\n"
        "⏺ API Error: Request rejected (429) · Token Plan usage limit reached: Upgrade your \n"
        "  Token Plan or purchase Credits for more usage. (2056)\n"
        "❯ \n"
    )
    predict = watchdog.build_semantic_predictor()
    decision = watchdog.classify_screen(screen, predict, None)
    assert decision.eligible, f"screen should be eligible, got {decision}"
    assert decision.kind == "quota", f"kind should be quota, got {decision}"
    assert decision.action == "WOULD_RESUME"


def test_empty_or_malformed_response_http_200_network_error_classified_as_network():
    """Regression: '⏺ API Error: API returned an empty or malformed response (HTTP 200)'
    was missed because fastembed returned ('clear', 0.62) and structural_evidence fallback
    only checked for quota regexes, defaulting to 'clear' / NOT_ELIGIBLE."""
    watchdog = load_module()
    screen = (
        "⏺ API Error: API returned an empty or malformed response (HTTP 200) — check for a \n"
        "  proxy or gateway intercepting the request\n"
        "\n"
        "✻ Crunched for 1m 48s\n"
        "\n"
        "─────────────────────────────────────────────────────────────────────────────── ultracode ─\n"
        "❯ \n"
    )
    # Mock fastembed returning ('clear', 0.62)
    decision = watchdog.classify_screen(screen, lambda _: ("clear", 0.62), None)
    assert decision.eligible, f"screen should be eligible, got {decision}"
    assert decision.kind == "network", f"kind should be network, got {decision}"
    assert decision.action == "WOULD_RESUME"


HISTORICAL_ERROR_PERMUTATIONS = [
    # (snippet, expected_kind)
    ("API Error: Request rejected (429) · Token Plan usage limit reached", "quota"),
    ("Rate limited after 10 retries — HTTP 429: Token Plan usage limit reached", "quota"),
    ("You've hit your weekly limit · resets Aug 3 at 8pm (America/Los_Angeles)", "quota"),
    ("You've hit your session limit · resets 9:50pm (America/Los_Angeles)", "quota"),
    ("You've hit your limit for Claude messages. Limits will reset at 10:00 PM.", "quota"),
    ("You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage", "quota"),
    ("RESOURCE_EXHAUSTED: Individual quota reached.", "quota"),
    ("RESOURCE_EXHAUSTED (code 429): Individual quota reached.", "quota"),
    ("Too many requests to Gemini API.", "quota"),
    ("HTTP 429: Monthly usage limit reached. Resets in 7 days.", "quota"),
    ('{"type":"error","error":{"type":"rate_limit_error","message":"account quota exhausted"}}', "quota"),
    ("API Error: Claude's response exceeded the 20000 output token maximum.", "quota"),
    ("API Error: 529 Overloaded. This is a server-side issue, usually temporary", "quota"),
    ("overloaded_error: The server is currently overloaded. Please try again later.", "quota"),
    ("API Error: API returned an empty or malformed response (HTTP 200)", "network"),
    ("API Error: Response stalled mid-stream. The response above may be incomplete.", "network"),
    ("API Error: Stream idle timeout - no chunks received", "network"),
    ("network connection failed with ENOTFOUND api.anthropic.com", "network"),
    ("connection reset by peer — socket hang up", "network"),
    ("HTTP 502 Bad Gateway: Proxy error communicating with server", "network"),
    ("HTTP 503 Service Unavailable: Server is undergoing maintenance", "network"),
    ("HTTP 504 Gateway Timeout: Upstream gateway timed out", "network"),
    ("fetch failed: connection failed with ECONNREFUSED 127.0.0.1:8643", "network"),
    ("API Error: 402 Insufficient credits. Add more using openrouter.ai/settings/credits", "quota"),
    ("API Error: 529 The server cluster is currently under high load. Please retry after a short wait (2064)", "network"),
    ("API Error: Connection closed mid-response. The response above may be incomplete.", "network"),
]

BULLET_PREFIXES = ["⏺ ", "● ", "⎿  ", "› ", "» ", "• ", ""]


@pytest.mark.parametrize("bullet", BULLET_PREFIXES)
@pytest.mark.parametrize("snippet,expected_kind", HISTORICAL_ERROR_PERMUTATIONS)
def test_all_historical_error_permutations_backtest(bullet, snippet, expected_kind):
    """Back-test every historical error phrase across all bullet prefixes and fastembed baseline ambiguity."""
    watchdog = load_module()
    screen = f"Previous turn output...\n{bullet}{snippet}\n\n❯ "

    # Test under ambiguous / clear fastembed baseline score (0.62) to verify structural fallback
    decision = watchdog.classify_screen(screen, lambda _: ("clear", 0.62), None)
    assert decision.eligible is True, f"Failed eligibility backtest for '{bullet}{snippet}': got {decision}"
    assert decision.kind == expected_kind, f"Failed kind backtest for '{bullet}{snippet}': expected {expected_kind}, got {decision.kind}"
    assert decision.action == "WOULD_RESUME"


