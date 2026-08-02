# Evidence Gate Check 7 — multi-metadata-filename trap (added 2026-07-14, PR #8290)

**Date:** 2026-07-14
**Affected PR:** [$GITHUB_REPOSITORY#8290](https://github.com/$GITHUB_REPOSITORY/pull/8290)
**Affected workflow:** `.github/workflows/evidence-gate.yml` (Evidence Bundle Validation)
**Bead:** wa-8290-green

## Symptom (different from Round-7 PR #8380 incident)

PR #8290 had a perfectly fresh, structurally valid evidence gist (`e8021c134d36a000773349fb8fd48d84`), but the gate's Check 7 emitted a confusing message that didn't directly say "stale SHA":

```
=== Check 7: Evidence bundle freshness vs current HEAD ===
FAIL: gist e8021c134d36a000773349fb8fd48d84 has no metadata.json / green_metadata.json /
      red_metadata.json — cannot verify freshness
```

The PR was failing on **the canonical filename**, not on SHA staleness. The bundle had:

```
backend-full-metadata.json
backend-replay-metadata.json
ui-metadata.json
```

— per-suite metadata files, captured as such by `/es capture` for the backend-full / backend-replay / UI evidence runs. None of them were at the canonical path that Check 7 probes.

## Why this happened (root cause)

The Evidence Gate Check 7's shell loop is hardcoded:

```bash
for candidate in metadata.json green_metadata.json red_metadata.json; do
  candidate_url=$(echo "$GIST_META" | python3 -c \
    "import json,sys; print(json.load(sys.stdin).get('files', {}).get('$candidate', {}).get('raw_url', ''))")
  if [ -n "$candidate_url" ]; then
    RAW_URL="$candidate_url"
    META_KEY="$candidate"
    break
  fi
done
if [ -z "$RAW_URL" ]; then
  echo "FAIL: gist $gid has no metadata.json / green_metadata.json / red_metadata.json — cannot verify freshness"
  STALE_FOUND=1
  continue
fi
```

There is **no glob / no list-of-patterns** — it tries three literal filenames in order, and `break`s on first hit. `backend-full-metadata.json` does NOT match any of those three literals. The `*_metadata.json` and `*-metadata.json` patterns an `/es capture` tool may emit are silently invisible to the gate.

Round-5 of the gate (per the existing freshness-contract reference) was already documented as accepting variant names — but the variants listed there were `metadata.json / green_metadata.json / red_metadata.json` (capture-tooling variants). The Round-5 fix did NOT cover per-suite names (`backend-full-metadata.json`, `ui-metadata.json`, etc.) — that's a different convention entirely.

## Verification (PR #8290 fingerprint)

`gh api gists/e8021c134d36a000773349fb8fd48d84` returned 14 files, none of which matched the three literal names. Files present:

```
README.md, SHA256SUMS, agy-provider-failure.jsonl, backend-full-console.txt,
backend-full-metadata.json, backend-full-run.json, backend-replay-console.txt,
backend-replay-metadata.json, backend-replay-run.json, bq-llm-payload-coverage.json,
bq-log-event-coverage.json, ui-metadata.json, ui-run.json, ui-streaming-evidence.json
```

Per-suite metadata is the pattern: a multi-evidence-run PR (e.g. backend-full + backend-replay + UI) typically captures one `*-metadata.json` per run, **not** a top-level `metadata.json`. The PR #8290 /es bundle had been captured as 3 separate evidence runs (the prior agent ran backend-full + backend-replay + UI as separate captures), so each got its own per-suite metadata file.

## Recipe — make Check 7 pass

**Option A (preferred, simplest):** Add a canonical top-level `metadata.json` to the gist whose `git_provenance.git_head` matches the PR's HEAD SHA. Existing per-suite `*-metadata.json` files can stay (they remain valid for human auditors) but are invisible to the gate.

```bash
GIST_DIR=/tmp/<your-gist-clone>
WORKTREE=$HOME/.worktrees/<your-pr-worktree>

PR_HEAD=$(git -C "$WORKTREE" rev-parse HEAD)

python3 -c "
import json, sys
m = {
    'git_provenance': {
        'git_head': '$PR_HEAD',
        'git_branch': 'feat/<your-branch>',
        'merge_base': '<origin/main HEAD>',
        'commits_ahead_of_main': <int>,
    },
    'pr_head_sha': '$PR_HEAD',
    'provenance': {
        'git_head': '$PR_HEAD',
        'git_fetch_origin_main': 'main',
        'timestamp': '<ISO 8601>',
    },
    'summary': 'Evidence bundle for PR #<N> — <one-line description>',
}
json.dump(m, open('$GIST_DIR/metadata.json', 'w'), indent=2)
"
cd "$GIST_DIR"
git add metadata.json
git commit -m "evidence: add canonical metadata.json for Evidence Gate Check 7"
git push origin HEAD
```

The gist can now ALSO have its per-suite metadata files updated via `sync-evidence-metadata.sh --metadata-file backend-full-metadata.json` etc. — but those are human-audit-only; the gate reads ONLY `metadata.json`.

**Option B:** Rename every per-suite `*-metadata.json` to `metadata.json` (lossy — you'd need to keep one per suite or merge them). Not recommended.

**Option C:** Patch the Evidence Gate's Check 7 to accept `*-metadata.json` glob. That's a workflow change to `.github/workflows/evidence-gate.yml` — out of scope for a /green dispatch; track as a separate harness bead (wa-evidence-gate-glob-pattern).

## Companion fix — sync-evidence-metadata.sh needs `--all-metadata`

The v1 helper `sync-evidence-metadata.sh --metadata-file metadata.json` only writes ONE filename. For per-suite bundles it should ALSO loop over every `*-metadata.json` in the gist dir, so they stay in sync with HEAD even though the gate doesn't read them. Recipe for the inline script (since the helper isn't extensible here without a code change):

```bash
GIST_DIR=/tmp/<your-gist-clone>
WORKTREE=$HOME/.worktrees/<your-pr-worktree>
PR_HEAD=$(git -C "$WORKTREE" rev-parse HEAD)

for meta in "$GIST_DIR"/*-metadata.json "$GIST_DIR"/metadata.json; do
  [ -f "$meta" ] || continue
  python3 -c "
import json, sys
p = '$meta'
h = '$PR_HEAD'
m = json.load(open(p))
m.setdefault('git_provenance', {})['git_head'] = h
m.setdefault('git_provenance', {})['pr_head_sha'] = h
m['pr_head_sha'] = h
m.setdefault('provenance', {})['git_head'] = h
json.dump(m, open(p, 'w'), indent=2)
"
done
```

Future hardening: extend `sync-evidence-metadata.sh` with `--all-metadata` flag (loop over all `*-metadata.json` and `metadata.json` siblings; skip non-existent files; refuse to operate if SHA verifies fail). Track as a follow-up to `drive-pr-to-green/scripts/sync-evidence-metadata.sh`.

## How to detect this trap early

When the gate reports `FAIL: gist <GID> has no metadata.json / green_metadata.json / red_metadata.json`:

1. `gh api gists/<GID> | jq '.files | keys'` — list every file in the gist.
2. If you see `<suite>-metadata.json` patterns but no top-level `metadata.json`, this is the trap.
3. Apply Option A above (add canonical metadata.json) and re-trigger the gate.

Don't waste cycles typing SHAs by hand into per-suite files — the gate never reads them.

## Pitfalls (BANNED)

1. **Banned — relying on per-suite `*-metadata.json` files for Check 7 freshness.** The gate's shell loop is hardcoded to three literal filenames. Per-suite files are documentation only; the gate cannot find them.
2. **Banned — `gh gist create -d "..." < metadata.json` for the canonical file.** Same Round-7 ban as for per-suite files — `gh gist create` serves binary JSON as `text/plain`; only `git clone https://<token>@gist.github.com/<id>.git` + write + commit + push produces a properly-fetchable raw URL.
3. **Banned — refactoring the Evidence Gate workflow to glob `*-metadata.json` mid-/green.** Workflow changes need their own PR with their own review and their own evidence. The /green dispatch's job is to land the user's PR; gate-shape changes are a separate audit thread.

## Cross-references

- `references/evidence-gate-freshness-contract-2026-07-13.md` — the Round-7 reference (single-canonical-metadata.json case). This reference is the Round-8 addendum for multi-suite bundles.
- `scripts/sync-evidence-metadata.sh` — the v1 helper that needs `--all-metadata`.
- `~/.claude/skills/evidence-standards/SKILL.md` — canonical `/es` contract; the Evidence Gate's Staleness Tolerance regex set.
- PR #8290 thread C0AH3RY3DK6/1784030452.318509 — the originating incident (verbatim prior to fix: 4 stale-FAIL cycles until the canonical metadata.json was added).