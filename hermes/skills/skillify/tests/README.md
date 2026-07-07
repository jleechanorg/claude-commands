# Skillify 11-item contract — captured Layer-2 evidence

These are the canonical invocations for /er (NON_PRODUCTION tier) and `/advice` to use.
Each block below is the actual `stdout` from the shipped scripts running against the live tree.

## 1. `skillify_check.py` — the 11-item audit

```text
Skillify audit: skillify  score=10/11 defer=1 na=0 fail=0
  [OK]  1. SKILL.md                    present
  [OK]  2. deterministic_code          4-scripts
  [DEFER]  3. cross_modal_eval            documented-in-references-port
  [OK]  4. unit_tests                  4-test_-py
  [OK]  5. integration_tests           4-scripts-referenced-in-tests
  [OK]  6. llm_evals                   all-evals-artifacts
  [OK]  7. resolver_trigger_entry      triggers-on-heading-line
  [OK]  8. resolver_trigger_eval       6-intents
  [OK]  9. check_resolvable            present-with-CLI
  [OK] 10. e2e_test                    3-stages
  [OK] 11. brain_filing                filing-rule-described
```

## 2. `check_resolvable.py` — structural resolver pass

```text
check-resolvable: headings=38 valid=33 orphans=5 dups=0 ambiguous=0
  ORPHAN: {'skill': 'ao-babysit', 'reason': 'no-SKILL-dir'}
  ORPHAN: {'skill': 'x-to-skill', 'reason': 'no-SKILL-dir'}
  ORPHAN: {'skill': 'slack-thread-routing-investigation', 'reason': 'no-SKILL-dir-and-no-File-directive'}
  ORPHAN: {'skill': 'qa-test-failure-dismissal-anti-pattern', 'reason': 'no-SKILL-dir'}
  ORPHAN: {'skill': 'github-api-fallback', 'reason': 'no-SKILL-dir-and-no-File-directive'}
```

## 3. `trigger_eval.py` — semantic routing pass

```text
{
  "total": 6,
  "passed": 6,
  "ambiguous_rows": 1,
  "results": [
    {
      "intent": "skillify this workflow",
      "status": "ok",
      "expected": "skillify"
    },
    {
      "intent": "is this a skill?",
      "status": "ok",
      "expected": "skillify"
    },
    {
      "intent": "make this proper",
      "status": "ok",
      "expected": "skillify"
    },
    {
      "intent": "add tests and evals for this",
      "status": "ok",
      "expected": "skillify"
    },
    {
      "intent": "check skill completeness",
      "status": "ok",
      "expected": "skillify"
    },
    {
      "intent": "audit this skill",
      "status": "ok",
      "expected": "skillify"
    }
  ],
  "use_llm": false
}
```

## 4. `pytest tests/ -v` — full test suite

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0 -- /Users/$USER/.local/orch-venv/bin/python3.13
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: /Users/$USER/.worktrees/skillify-routing
configfile: pyproject.toml
plugins: cov-7.1.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.4.0, hypothesis-6.152.5, testmon-2.2.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 14 items

skills/skillify/tests/test_check_resolvable.py::test_resolver_md_exists_and_parses PASSED [  7%]
skills/skillify/tests/test_check_resolvable.py::test_skillify_in_resolver PASSED [ 14%]
skills/skillify/tests/test_check_resolvable.py::test_no_dup_keys_for_skillify PASSED [ 21%]
skills/skillify/tests/test_e2e.py::test_e2e_skillify_check_returns_valid_score PASSED [ 28%]
skills/skillify/tests/test_e2e.py::test_e2e_check_resolvable_against_live_resolver PASSED [ 35%]
skills/skillify/tests/test_e2e.py::test_e2e_trigger_eval_full_pass PASSED [ 42%]
skills/skillify/tests/test_skillify_check.py::test_skillify_check_returns_parseable_json PASSED [ 50%]
skills/skillify/tests/test_skillify_check.py::test_items_required_present PASSED [ 57%]
skills/skillify/tests/test_skillify_check.py::test_cross_modal_eval_deferred_with_rationale PASSED [ 64%]
skills/skillify/tests/test_skillify_check.py::test_brain_filing_rationale_present PASSED [ 71%]
skills/skillify/tests/test_skillify_check.py::test_lying_skill_fails_audit PASSED [ 78%]
skills/skillify/tests/test_trigger_eval.py::test_fixture_exists_and_is_valid_jsonl PASSED [ 85%]
skills/skillify/tests/test_trigger_eval.py::test_trigger_eval_resolves_every_intent PASSED [ 92%]
skills/skillify/tests/test_trigger_eval.py::test_ambiguous_row_handled_without_llm PASSED [100%]

============================== 14 passed in 0.63s ==============================
```

## Summary

- **score**: 10/11 (item 3 deferred with documented rationale in `references/gbrain-skillify-v1.1.0-port.md`)
- **layer**: 2 (live integration tests against the live skill tree, not mocks)
- **tier**: NON_PRODUCTION (docs / tests / tooling / scripts); /er verdict must be **PARTIAL** or better
- **files changed**: `SKILL.md`, `scripts/{skillify_check,check_resolvable,trigger_eval}.py`, `tests/test_*.py`, `routing-eval.jsonl`, `evals/{rubric.json,cases.jsonl,run_eval.py}`, `references/gbrain-skillify-v1.1.0-port.md`
