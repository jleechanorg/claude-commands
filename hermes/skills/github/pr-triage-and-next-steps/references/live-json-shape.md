---
note: reference — copied verbatim from the live 2026-07-08 capture. If the fleet's PR shape changes, delete this file and re-derive from a fresh `gh pr list --json …` run.
---

# Live JSON shape — `gh pr list` per-repo, July 2026

The shape below was captured by `gh --version 2.x` against `$GITHUB_REPOSITORY` on 2026-07-08. Use these field names literally in `jq` / `python -c "json.load..."` calls. **Do NOT** invent field names — `gh pr list` exits 1 with an "Unknown JSON field" error otherwise (verified live).

## Field set returned by the inventory query

```bash
gh pr list --author @me --state open --repo <OWNER>/<REPO> \
  --json number,title,headRepository,isDraft,createdAt,headRefName,url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
```

This returns one JSON object per PR. Required schema:

| Field | Type | Notes |
|---|---|---|
| `number` | int | PR number (`#8284`) |
| `title` | string | First line of PR title |
| `headRepository` | object | Contains `nameWithOwner` (e.g. `"$GITHUB_REPOSITORY"`) |
| `isDraft` | bool | **`true` for drafts, not `state: "draft"`** — that field doesn't exist on `gh pr list` output |
| `createdAt` | string ISO 8601 | |
| `headRefName` | string | branch name, e.g. `feat/smoke-local-command` |
| `url` | string | full PR URL — use for Slack markdown link |
| `mergeable` | enum | one of `MERGEABLE`, `CONFLICTING`, `UNKNOWN` |
| `mergeStateStatus` | enum | richer mergeable state from GraphQL — `DIRTY`, `BEHIND`, `BLOCKED`, `CLEAN`, etc. |
| `reviewDecision` | enum null | `APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, or `null` if no review submitted |
| `statusCheckRollup` | object null | nested `{state: "SUCCESS"|"FAILURE"|"PENDING"}` from `mergeStateStatus`, but **verify with `gh pr checks` before claiming CI is green** — see skill pitfall |

## Common downstream queries

```python
import json
data = json.load(open('/tmp/open_prs.json'))
drafts     = [p for p in data if p['isDraft']]
conflicts  = [p for p in data if p['mergeable'] in ('CONFLICTING', 'UNKNOWN')]
approved   = [p for p in data if p['reviewDecision'] == 'APPROVED']
cr_blocked = [p for p in data if p['reviewDecision'] == 'CHANGES_REQUESTED']
needs_cr   = [p for p in data if p['mergeable'] == 'MERGEABLE' and not p['reviewDecision']]
```

## Fleet repos to iterate (verified 2026-07-08)

```bash
gh repo list jleechanorg --limit 50 --json nameWithOwner \
  | jq -r '.[].nameWithOwner'
```

Returns ~50 repos; the load-bearing ones for PR triage are:

- `$GITHUB_REPOSITORY` — 30 open, biggest surface
- `jleechanorg/jleechanclaw` — 17 open, harness / SOUL.md / skill work
- `jleechanorg/ai_universe_frontend` — 30 open, mostly old UI fix PRs
- `jleechanorg/dark-factory` — 4 open, factory smoke tests
- `jleechanorg/browserclaw` — 2 open, cookie handling
- `jleechanorg/.github` — 1 open, reusable workflows
- `jleechanorg/agent-orchestrator-ts` — 1 open, custom reviewers

Skip forks/mirrors — `jleechanorg/agent-orchestrator`, `jleechanorg/hermes-agent_archive_*` are read-only references.

## Pitfall records

- **`--json repository`** is silently accepted by `gh` but returns blank across all rows when no `--repo` is passed. Always specify `--repo`.
- **Reading `gh pr list` output without `--json`** prints a table that breaks `python3 -c "import json,sys; json.load(sys.stdin)"` with `Expecting value: line 1 column 1`. Pipe-or-redirect to a file FIRST then parse (the variable assignment inside a single shell line above silently swallows stderr).
- **`mergeStateStatus == "BEHIND"`** is NOT the same as `mergeable == "CONFLICTING"` — `BEHIND` means "branch is N commits behind `main`, merge will fast-forward", `CONFLICTING` means "actual diff conflict". For triage purposes, `BEHIND` is still `mergeable == MERGEABLE` and doesn't need a rebase round-trip.
- **`createdAt` vs `mergedAt`** — only `mergedAt` tells you "this is really gone." `updatedAt` is recent for any commented-on PR, even years old.
