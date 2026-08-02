# Check-run observation endpoints (v1.9.0, added 2026-07-14)

When a babysit tick needs to find out *why* a check failed (not just that it
concluded `failure`), the GraphQL `gh pr checks --json` summary leaves a gap.
This reference documents the three REST endpoints that close it, plus the
field-list trap and token-extraction trap that bite every Phase 1 implementation.

## Endpoint 1: `/commits/<sha>/check-runs?per_page=20`

The canonical source of truth for check state on a given HEAD SHA. Returns the
full list of `check_runs` with `name`, `status`, `conclusion`, `started_at`,
`completed_at`, `app`, `check_suite`, and `output`.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs?per_page=20" \
  > /tmp/checks.json
python3 -c "import json; d=json.load(open('/tmp/checks.json')); \
    [print(f\"{c['name'][:60]:60s} {c['status']}/{c.get('conclusion')} started={c['started_at']}\") \
     for c in d['check_runs']]"
```

Returns 36 check-runs for a typical PR (one per workflow + per job matrix
instance). The list deduplicates by check_suite on the GraphQL `gh pr checks`
view; here you see *all* of them, including cancelled ones, which is exactly
what you want when diagnosing the workflow_dispatch Green Gate trap.

## Endpoint 2: `/check-runs/<CHECK_RUN_ID>/annotations`

When the parent check-run `output` block has `title=null, summary=null,
text=null, annotations_count=1` — *very common* for the Green Gate rollup —
the failure detail is on the annotations sub-resource:

```bash
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/check-runs/<CHECK_RUN_ID>/annotations" \
  | python3 -c "import sys,json; [print(f\"  {a['path']}:{a.get('start_line','?')} ({a['annotation_level']}) {a['message']}\") \
                    for a in json.load(sys.stdin)]"
```

Returns an array. Each entry has `path`, `start_line`, `end_line`,
`annotation_level` (one of `notice`/`warning`/`failure`), and `message`.
Verified on PR #8290 (2026-07-14, check-run 87222745926): the parent Green
Gate output was opaque but the annotations endpoint returned
`path=.github start_line=20 annotation_level=failure message="Process completed with exit code 1."` —
exact location of the failing bash step.

## Endpoint 3: `/actions/runs/<RUN_ID>` and `/actions/runs/<RUN_ID>/jobs`

When the check-run summary is opaque you usually want to know *which run*
produced it (was it `pull_request`-triggered or `workflow_dispatch`?). The
`runs/<id>` view returns `display_title`, `head_branch`, `head_sha`,
`event`, `conclusion`, `created_at`, `updated_at`, `run_attempt`.

```bash
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/runs/<RUN_ID>/jobs?per_page=10" \
  > /tmp/jobs.json
python3 -c "import json; d=json.load(open('/tmp/jobs.json')); \
    [print(f\"  job={j['name'][:60]:60s} status={j['status']} concl={j['conclusion']}\") \
     for j in d['jobs']]"
```

The `conclusion` on each job lets you distinguish infra failures
(`cancelled` from wait timeout) from real assertion failures (`failure`).
Combined with the run's `event` field, you can tell whether a `conclusion=cancelled`
on Smoke Gate Wait is the 25-min workflow_dispatch cap vs an intentional
kill. See `references/workflow-dispatch-smoke-wait-pitfall.md`.

## Trap A: exact `gh pr checks --json` field list

The CLI's `--json` flag accepts ONLY these field names:

```
name, state, conclusion, startedAt, completedAt, link, workflow, description, event, bucket
```

Everything else returns:
```
Unknown JSON field: "<name>"
Available fields: name, state, conclusion, startedAt, completedAt, link, workflow, description, event, bucket
```

Specifically:

- `url` is NOT valid; the HTML URL is `link` (it's the nested object).
- `head_sha` / `headSha` is NOT valid.
- `bucket` means "in which check_suite bucket this run lives" (`pull_request`,
  `stale`, etc.). Not the check_suite ID.

Read the available-fields list from the error. If you need a field that
`gh pr checks` does not expose, **switch to the REST `/commits/<sha>/check-runs`
endpoint above**.

## Trap B: SLACK_USER_TOKEN extraction from `~/.profile`

`~/.profile` formats the export with double quotes:
```
export SLACK_USER_TOKEN="xoxp-95..."
```

The brittle pipeline used in earlier babysit prompts:
```bash
TOK=$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//' | sed 's/"//g')
```
produces garbage (verified mid-tick on PR #8290 second tick: `wc -c`
returned ~22 bytes with corrupted content, leading to a 401 from
chat.postMessage).

Use the quote-aware form:
```bash
TOK=$(awk -F'"' '/^export SLACK_USER_TOKEN=/{print $2; exit}' ~/.profile)
wc -c <<<"$TOK"  # sanity: ~80-90 chars for an xoxp-* token
```

If the file uses single quotes (`SLACK_USER_TOKEN='xoxp-...'`), switch the
awk delimiter: `awk -F"'" '/^export SLACK_USER_TOKEN=/{print $2; exit}'`.

**Never** read `~/.bashrc` — per the `bashrc-profile-xapp-drift-blocks-launchd`
memory the bashrc-sourced value is overwritten by `.profile` and the launchd
process picks up the wrong one. Always read `~/.profile`.

## When to load this reference

- A check concluded `failure` and `gh pr checks` did not surface the failing step.
- The parent check-run output is opaque (`title=null, text=null`).
- You need to distinguish `workflow_dispatch` from `pull_request` runs.
- The XOX-P fallback path is taken and the SLACK_USER_TOKEN pipeline produces 401.

## Companion files

- `references/workflow-dispatch-smoke-wait-pitfall.md` — what the 25-min
  `cancelled` conclusion means and how to post around it.
- `references/head-advance-no-green-gate-redispatch.md` — when the parent
  check-run is `failure` because of HEAD advance, not code defect.
- `scripts/gh_pr_json.py` — drop-in REST helper for `--state-only` /
  `--summary` / `--json` of the PR pull request endpoint (sidesteps GraphQL
  rate-limit but does NOT cover check-runs; that's this reference).
