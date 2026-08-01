# workflow_dispatch Green Gate Smoke-Wait 25min Timeout — Pitfall

**Added:** 2026-07-14 (skill v1.7.0)
**Bug-ref:** Babysit tick on PR #8290 ($GITHUB_REPOSITORY), Slack thread `C0AH3RY3DK6 / 1784030452.318509`
**Author:** cron-tick babysit protocol

## Symptom

`gh pr checks <N>` reports `Green Gate` as `failure` with a recent run that completed in 5-30 seconds. The PR's code did not change between ticks. All other checks (`Directory tests`, `Bugbot Gate Wait`, `Green Gate Precheck (Gates 1-6)`) are PASS or SKIPPED. The PR is mergeable. CodeRabbit APPROVED the diff.

## Root cause

The babysit cron re-triggered the Green Gate via `workflow_dispatch` (the standard babysit pattern: `gh workflow run green-gate.yml -f pr_number=N -f head_sha=<sha>`). The workflow's `Smoke Gate Wait (Gate 8)` step has a **hard 25-minute wait timeout** for an upstream smoke-test event to land. If no smoke event arrives within 25 min, the wait job is **cancelled**. The downstream `Apply smoke gate result (gate 8)` step then fails with `SMOKE_RESULT=cancelled, SMOKE_GATE=unset`, propagating `failure` to the main Green Gate rollup.

This is **infrastructure exhaustion**, not a test assertion failure. The PR's code is unchanged. The natural `pull_request`-triggered Green Gate has different behavior (it runs in parallel with the rest of CI and its smoke wait is bounded by the PR's overall CI lifetime, not a hard 25-min cap).

## Diagnostic recipe (per tick)

When `Green Gate` reports `failure`, do NOT immediately treat it as a real test failure. Run:

```bash
TOKEN=$(gh auth token 2>/dev/null)

# 1. Find the failing run + its dispatch vs pull_request origin
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs?head_sha=${HEAD_SHA}&per_page=20" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['workflow_runs']:
    if r['name'] == 'Green Gate':
        print(f\"event={r['event']}  status={r['status']}  conclusion={r.get('conclusion')}  id={r['id']}\")"

# 2. For each failing Green Gate run, fetch jobs and find the failed step
RUN_ID=<failing_run_id>
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${RUN_ID}/jobs" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for j in d['jobs']:
    print(f\"job_id={j['id']} name={j['name']} status={j['status']} conclusion={j.get('conclusion')}\")
    if j.get('conclusion') == 'failure':
        for step in j.get('steps', []):
            if step.get('conclusion') == 'failure':
                print(f\"  FAILED STEP: {step.get('name')}\")"
```

**Interpretation:**
- `event == workflow_dispatch` + `FAILED STEP: Apply smoke gate result (gate 8)` + `Smoke Gate Wait (Gate 8)` job has `conclusion=cancelled` → **infra wait exhaustion**, post reassurance format.
- `event == pull_request` + `FAILED STEP: Apply smoke gate result (gate 8)` + `Smoke Gate Wait (Gate 8)` job has `conclusion=cancelled` → unusual; investigate upstream smoke pipeline.
- `FAILED STEP` is something else (e.g. `Run python tests`, `Lint`, `Validate imports`) → **real test failure**, surface to operator with run URL.

## Post format

**Infra timeout (most common babysit scenario):**
```
:hourglass_flowing_sand: PR #N tick HH:MMZ — Gates 1-6 PASS, Gate-8 Smoke wait timed out (25min, workflow_dispatch infra). Skeptic verdict pending.
```

**Real test failure (escalate):**
```
:x: PR #N tick HH:MMZ — Gate <NAME> failed: <FAILED_STEP>. Run: <URL>. Action needed.
```

## Why the dispatch pattern exists

Babysits use `workflow_dispatch` to re-trigger Green Gate because:

1. The natural `pull_request` trigger only fires on new commits; a babysit that watches the same SHA for 30+ min would otherwise have no fresh CI signal.
2. The dispatch re-trigger gets a clean fresh run that re-evaluates all gates against the current `head_sha`, which is useful when waiting on the Skeptic launchd cron to dispatch its verdict.

The trade-off: dispatch runs hit the 25-min smoke-wait cap, which means a long-running babysit will see a `failure` rollup every ~25 min even when the PR is genuinely green. The recipe above lets the babysit distinguish that signal from a real regression.

## Companion references

- `references/rest-pr-json-parse-pitfall.md` — for when `gh pr view --json` is rate-limited.
- `references/graphql-rate-limit-rest-fallback.md` — for when GraphQL core is exhausted but REST is fine.
- `references/post-skeptic-green-protocol.md` — v1.5.0 Skeptic merge-ready protocol (the Skeptic verdict may still arrive after a smoke-wait timeout if Gates 1-6 PASS).