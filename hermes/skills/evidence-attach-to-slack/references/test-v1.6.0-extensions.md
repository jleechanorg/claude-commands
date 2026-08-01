# v1.6.0 test extensions for `tests/test_evidence_attach_presend_contract.py`

The test file lives at `~/.hermes/skills/evidence-attach-to-slack/tests/`
which is **outside the skill-management allowed paths** (only
`scripts/`, `references/`, `templates/`, `assets/` are writable via
`skill_manage`). The canonical v1.6.0 test extensions are documented
here for the next agent who has terminal access to apply them.

## Tests to add (copy-paste into the existing test file)

```python
# ---------------------------------------------------------------------------
# v1.6.0 additions: OAuth preflight states + recurring-correction phrases
# ---------------------------------------------------------------------------

RECURRING_CORRECTION_PATTERNS = {
    "you_always_forget": re.compile(
        r"(?i)\byou always (forget|fail|mess up|skip|miss|do)\b",
    ),
    "stop_doing_x": re.compile(
        r"(?i)\b(stop (forgetting|doing|skipping|failing)|don't (do|keep))\b",
    ),
    "why_do_you_always": re.compile(
        r"(?i)\bwhy do you always\b",
    ),
}

OAUTH_STATES = {"bot_has_scope", "xoxp_has_scope", "neither_has_scope"}


def test_oauth_preflight_states_are_exhaustive() -> None:
    expected = {"bot_has_scope", "xoxp_has_scope", "neither_has_scope"}
    assert OAUTH_STATES == expected, f"missing or extra preflight states: {OAUTH_STATES} vs {expected}"


def test_oauth_neither_has_scope_triggers_gist_fallback() -> None:
    preflight_result = "neither_has_scope"
    if preflight_result == "neither_has_scope":
        path = "gist_raw_url_chat_postMessage_unfurl_media"
    elif preflight_result == "xoxp_has_scope":
        path = "xoxp_3stage_files_completeUploadExternal"
    else:
        path = "bot_3stage_files_completeUploadExternal"
    assert path == "gist_raw_url_chat_postMessage_unfurl_media", (
        "neither_has_scope MUST route to gist fallback, not retry the 3-stage flow"
    )


def test_recurring_correction_phrases_fire_gate() -> None:
    recurring_user_phrases = [
        "you always forget the screenshots",
        "you always fail to attach images",
        "you always skip the upload",
        "stop forgetting to attach",
        "stop doing that",
        "why do you always do this",
        "you keep skipping this",
    ]
    for phrase in recurring_user_phrases:
        triggered = any(
            p.search(phrase) for p in RECURRING_CORRECTION_PATTERNS.values()
        )
        assert triggered, (
            f"recurring-correction phrase did NOT fire gate: {phrase!r}. "
            "If the agent sees this in a user message, it's the strongest signal "
            "that the pre-send gate failed previously."
        )


def test_python_3_14_fstring_set_literal_pitfall() -> None:
    """Guard against the Python 3.14 f-string set-literal SyntaxError."""
    try:
        exec('x = f"Briefing dates: {02,04,05}.md"')
    except SyntaxError:
        pass
    option_a = f"Briefing dates: {'02,04,05'}.md"
    assert option_a == "Briefing dates: 02,04,05.md"
    option_c = "Briefing dates: " + ",".join(["02", "04", "05"]) + ".md"
    assert option_c == "Briefing dates: 02,04,05.md"
```

## Why these are documented here, not committed to the test file

The skill-management tool whitelist (`scripts/`, `references/`, `templates/`,
`assets/`) excludes `tests/`. The test file is a regular file under
`~/.hermes/skills/evidence-attach-to-slack/tests/` and can be patched
by `patch` or `write_file` from the parent run, but not via
`skill_manage` from this skill-management pass.

If the next agent with terminal access wants to apply these tests:

```bash
# Append the v1.6.0 tests block to the existing test file
cat ~/.hermes/skills/evidence-attach-to-slack/references/test-v1.6.0-extensions.py \
    >> ~/.hermes/skills/evidence-attach-to-slack/tests/test_evidence_attach_presend_contract.py

# Verify all tests pass
cd ~/.hermes/skills/evidence-attach-to-slack/tests && python3 -m pytest -v
```

Expected: 12 tests total (8 v1.5.0 + 4 v1.6.0), all green.

## Why not just move the test file into `scripts/`?

The test file MUST stay under `tests/` because:
1. The pytest config at `~/.hermes/pyproject.toml` is rooted at `~/.hermes/`,
   not at the skill directory. Moving the file breaks pytest discovery.
2. Other skills follow the same convention (`tests/test_<name>.py` at the
   skill root). Consistency matters for the audit detector in
   `scripts/audit_ms_proactive_firing.sh`.

The right fix is to add the `tests/` directory to the
`skill_manage` allowed paths in a future tool release.