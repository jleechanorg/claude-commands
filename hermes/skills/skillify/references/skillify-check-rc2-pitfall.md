# Skillify check exit code 2 — what it actually means (added 2026-07-28)

## The trap

`scripts/skillify_check.py` returns exit code **2** when the score is `< 9/9`,
even when there are **zero `fail` items** — only `defer` or `na` items reduce the
score below the threshold. Exit code **0** is reserved for `9/9 or better`.

A naive E2E test that asserts `result.returncode == 0` will report false failures
on otherwise-perfect skills.

## The correct E2E assertion

```python
import subprocess, json, sys

def test_skillify_check_pipeline():
    skill_dir = "/path/to/skill"
    result = subprocess.run(
        [sys.executable,
         "$HOME/.hermes/skills/skillify/scripts/skillify_check.py",
         skill_dir, "--repo-root", "$HOME/.hermes", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    # rc=2 is fine if fail_count == 0; only rc=1 is a real Python error
    assert result.returncode in (0, 2), (
        f"skillify_check unexpected rc={result.returncode}: {result.stderr}"
    )
    payload = json.loads(result.stdout)
    fail_count = sum(1 for item in payload["items"] if item["status"] == "fail")
    pass_count = sum(1 for item in payload["items"] if item["status"] == "pass")
    print(f"score: {payload['score']} ({pass_count} pass, {fail_count} fail)")
    assert fail_count == 0, f"expected 0 fails, got {fail_count}: {payload}"
    assert pass_count >= 7, f"expected >=7 pass items, got {pass_count}"
```

## Why rc=2 exists

The return-code contract:

- `0` = score ≥ 9/9 (fully skilled)
- `1` = Python error / I/O failure / malformed skill
- `2` = score < 9/9 (skillify audit says "you're not done yet")

This is useful for CI gates that want to enforce "every skill must score 9/9"
(scripts can `set -e` on rc=2). But it's hostile to E2E tests that just want to
verify "the audit script runs successfully."

## Real instance (2026-07-28, wa-campaign-premise-find)

A new skill that scored **8/9 with 0 fails** was rejected by its own E2E test
because the test asserted `returncode == 0`. Fix was a one-line change to
`assert result.returncode in (0, 2)`. After the fix, all 20 pytest tests passed.

The skillify_check output at the time:

```json
{
  "score": "8/9",
  "pass": 8,
  "fail": 0,
  "defer": 1,    // cross_modal_eval — deferred by design
  "na": 2         // 2 N/A items
}
```

rc=2 because score < 9/9. NOT a failure — just a "not yet at the ceiling" signal.

## How to think about it

`fail_count == 0` is the bar for "this skill is in good shape." The score-as-N/M
is a coarse measure of completeness — `9/9` includes one item (`cross_modal_eval`)
that is explicitly deferred in Hermes. So **8/9 with 0 fails IS the
production-grade floor** for Hermes skills today.

## All skillify_check exit codes

| rc | Meaning | What to do |
|---|---|---|
| 0 | Score ≥ 9/9 | All good |
| 1 | Python error / I/O failure / parse error | Real failure — fix the script or skill |
| 2 | Score < 9/9 | Skillify audit incomplete — either add the missing items or accept the ceiling |

## Adding this to a new skill's E2E test

If you write `tests/test_e2e.py` for a new skill and it shells out to
`skillify_check.py`, **always** use the `assert result.returncode in (0, 2)`
pattern. The naked `assert result.returncode == 0` will fail whenever your
skill has any deferred or N/A items (which is the norm).

## Cross-references

- `skillify/SKILL.md` § "Phase 7 — Verify" — has the recipe; this file is the
  detailed pitfall.
- `skillify/SKILL.md` § "Pitfall — oneline RESOLVER heading needs SPACE between
  name and colon" — companion pitfall for the same code path.
- `wa-campaign-premise-find/tests/test_e2e.py::test_iseki_v1_via_skillify_check_pipeline`
  — verified working example of the correct assertion pattern.
