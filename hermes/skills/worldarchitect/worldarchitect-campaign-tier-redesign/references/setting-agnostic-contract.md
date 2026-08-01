# Setting-Agnostic Contract — `test_divine_prompts_setting_agnostic.py`

**Verified PR #8488 (2026-07-21).** This test file enforces a non-negotiable
contract on every prompt in `$PROJECT_ROOT/prompts/divine/`:

1. **No D&D-specific names in default text.** `Mystra`, `Helm`, `Ao`,
   `Bhaal`, `Netheril`, `Netherese`, `Shar`, `Bane`, `Kelemvor`,
   `Karsus`, `Myrkul`, `Torm`, `Oghma`, `Savras`, `Mystryl`,
   `"Forgotten Realms"`, `"Dale Reckoning"` must NOT appear in the
   default-text portion of any divine prompt. They only belong in the
   **explicit `Setting Adaptation` / `D&D Forgotten Realms Adaptation
   Appendix`** at the bottom of `divine_leverage_system.md`.
2. **The `SETTING-AGNOSTIC SYSTEM (CRITICAL)` header** must be in the
   **first 20 lines** of any ascension-ceremony prompt (test
   `test_setting_agnostic_header_is_prominent`). Prepending content to
   the file pushes the header past line 20 — keep the header at the top.
3. **No Mind-Blanks-style D&D entities** appear in HUD observers —
   observers must be generic ("The Overseer", "The Source-Fabric",
   "The Pantheon", "The Watchers").

## Why this exists

The campaign-templating layer is meant to be **setting-agnostic** —
same prompts work for D&D / Cyberpunk / Wuxia / Marvel / Naruto with a
campaign-supplied `Setting Adaptation` mapping. If Mystra/Helm/Ao leak
into the default text, the LLM assumes the campaign is set in Faerûn
and refuses to apply the user's actual setting.

Issue: #7958. Original PR: #7959.

## Test file

`$PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py` (337 lines,
19 tests). Run with:

```bash
cd ~/.worktrees/<branch>/your-project.com
TESTING_AUTH_BYPASS=true python3 -m pytest $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py
```

## What fails if you ignore it (case study, PR #8488)

When I added the V2 god-mechanics overlay as a prepend to
`divine_ascension_ceremony.md`, **three tests broke simultaneously**:

| Test | Cause | Fix |
|---|---|---|
| `test_setting_agnostic_header_is_prominent` | V2 overlay prepended; SETTING-AGNOSTIC header moved past line 20 | Move SETTING-AGNOSTIC header back to top |
| `test_no_mystra_in_default_text` | V2.3 example table had "Mystra" by name | Replace with "Arcane / Weave deity" |
| `test_no_forgotten_realms_in_default_text` | V2.3 table header literally said "(D&D Forgotten Realms — replace per setting)" | Drop the parenthetical entirely |

Lesson: **before writing any example in a divine prompt, ask "is this a
campaign-agnostic placeholder, or a setting-specific name?"** If the
latter, it goes in the Appendix, not the body.

## Running the test in CI

The Green Gate's `core-mvp-2(self hosted)` shard runs this test as part
of its 186-test suite. A failure here blocks the PR. Run it locally
before pushing:

```bash
TESTING_AUTH_BYPASS=true python3 -m pytest $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py -v
```

19 tests, runs in <2 seconds. If any FAIL, fix before pushing.
