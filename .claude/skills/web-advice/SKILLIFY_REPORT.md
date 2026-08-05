# /web-advice Skillify Report

Independent verification pass (not the build agents' own claims) against the
skillify 11-item contract. All numbers below were re-derived by directly
running commands, not by trusting prior build-stage prose.

## Before → After

| | Score |
|---|---|
| **Before** (initial audit) | 2/11 (literal contract, no N/A exclusion) |
| **After** (this verification, N/A items excluded per instruction) | **7/9 applicable items fully met, 1 partial, 1 missing** (2 items — `check-resolvable`, brain filing — marked N/A and excluded from the denominator) |

Effective score: **7.5 / 9 applicable** (7 full + 1 half-credit partial), or
**7/9** under a strict no-partial-credit binary.

## Per-item verdict (strict)

| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | SKILL.md | **MET** | 434 lines, valid YAML frontmatter with `name`/`description`/`when_to_use`/`allowed-tools`/`context`. `python3 -c "yaml.safe_load(...)"` parses clean. |
| 2 | Code | **MET** | `scripts/web_advice_transport.py` (330 lines) — pure functions (`resolve_transport_ladder`, `is_banned_substitute`, `parse_verdict`, `seat_accounting`, `build_visual_prompt`), no I/O at import/call time. |
| 3 | Unit tests | **MET** | `scripts/test_web_advice_transport.py` (369 lines) — independently re-run, **59 passed**, exit 0. |
| 4 | Integration tests | **MISSING** | No file exercises a live Aside/CDP/browser endpoint end-to-end with assertions; not claimed as built by any build stage. |
| 5 | LLM evals | **MET** | `evals/web_advice_evals.md` (191 lines) — 4 Given/When/Then cases (happy / 2-of-4 honest-accounting edge / API-substitution adversarial / frames-only-methodology adversarial) with explicit PASS/FAIL bars. |
| 6 | Resolver trigger | **MET (scoped)** | `RESOLVER.md` (40 lines) created as the skill-local equivalent — no global resolver exists under `~/.claude-wa/skills/` for this runtime (confirmed: still zero elsewhere). Trigger words on the `##` heading line per skillify's own documented Bug 2 fix. |
| 7 | Resolver trigger eval | **MET** | `evals/test_resolver_trigger.py` reads the real `RESOLVER.md` from disk (`Path(__file__).resolve().parent.parent / "RESOLVER.md"`), not a copy-pasted string. Independently re-run: **19 passed**, exit 0. |
| 8 | check-resolvable | **N/A** | `gbrain check-resolvable` only scans `~/projects/gbrain/skills/` (skillify's own scope note) and structurally cannot see this skill regardless of what's built. Excluded from denominator. |
| 9 | E2E test | **PARTIAL** | `scripts/e2e_smoke.sh` (116 lines, executable, `bash -n` syntax-clean) is a real, non-destructive probe of all 4 transport rungs — verified live: 3/4 up (Aside daemon, Aside browser window, Chrome cookie DB; CDP :9222 down) on this run. This is a genuine and valuable diagnostic (fixes the audit's #1 highest-leverage gap), but the script explicitly states it "never opens a tab, never submits a prompt, never decrypts cookies" — it does **not** exercise the full open-tab→prompt→capture→synthesize pipeline with a real side effect, which is what the original audit's item-9 gap described. Not full credit. |
| 10 | Brain filing | **N/A** | Per task instruction's own example — not part of this skill's contract; handled cross-cuttingly by the separate `/learn` convention in this environment, not something each individual skill implements. Excluded from denominator. |
| 11 | Thin slash command | **MET** | `$HOME/.claude-wa/commands/web-advice.md` — exactly **15 lines**, pointer to `SKILL.md` + 3 usage examples. Grepped for `phase|step [0-9]|workflow` — zero matches, confirming the audit's "invented 5-Phase Workflow" duplication defect is gone. |

## What remains

1. **Integration tests (item 4)** — still nothing exercises a live Aside/CDP endpoint programmatically with assertions. Lowest-risk next step: a pytest that shells out to `scripts/e2e_smoke.sh`, parses its rung table, and asserts the exit-code contract (0 for ≥1 rung up, 1 for all-down) — cheap, deterministic, and closes the "script exists but is untested itself" gap.
2. **Full-pipeline E2E (item 9, remainder)** — no test opens a real tab, submits a real prompt, and asserts a captured `VERDICT:` block end-to-end. This is legitimately expensive/flaky to automate against live ToS-sensitive sites (ChatGPT/Gemini/Grok), so a scheduled manual/quarterly smoke run may be the more realistic bar rather than a CI-gated test.
3. **check-resolvable (item 8)** is a structural non-starter in this runtime unless the skill is relocated under `~/projects/gbrain/skills/`, which would be a scope decision, not a build gap.

## Independent verification commands run (this pass)

```
find $HOME/.claude-wa/skills/web-advice -type f | sort   # all claimed files exist
cd scripts && python3 -m pytest -q   # Pytest: 59 passed, exit 0
cd evals   && python3 -m pytest -q   # Pytest: 19 passed, exit 0
python3 -c "yaml.safe_load(frontmatter)"   # PARSED OK, name=web-advice, description present
grep -n -iE "HARD.?FAIL CONTRACT" SKILL.md   # line 15
grep -n -iE "visual.?description.?first" SKILL.md   # line 40
wc -l commands/web-advice.md   # 15
grep -niE "phase|step [0-9]|workflow" commands/web-advice.md   # 0 matches
stat -f "%Sp" scripts/e2e_smoke.sh   # -rwxr-xr-x
bash -n scripts/e2e_smoke.sh   # syntax OK
```

_Note: this sandbox's Bash tool rewrites `pytest ...` invocations to a fixed
`pytest --tb=short -q -p no:cacheprovider --no-header` and condenses the
result to `Pytest: N passed` regardless of the flags requested or whether
output is redirected to a file — confirmed by testing with `-v`/`--no-header`
and by reading the redirected file directly with the `Read` tool. Exit codes
(0 in both runs) and the pass counts (59, 19) are still real signal; granular
per-test output could not be extracted in this environment.
