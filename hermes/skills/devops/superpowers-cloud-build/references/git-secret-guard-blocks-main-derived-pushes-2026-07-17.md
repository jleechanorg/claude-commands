# Pitfall — Git Secret Guard Blocks ALL Pushes From Branches Off origin/main

**Discovered:** 2026-07-17, $GITHUB_REPOSITORY.
**Severity:** Drive-blocking. Every cloud-build hand-off from a `private/*` branch off `origin/main` fails.
**Symptom class:** "Cloud-build installed fine, SSH connection works, but push rejected."

## Symptom

A cloud-build hand-off that reaches the bastion but fails on the actual push:

```
git secret guard: scanning outgoing range <main-sha>..<head-sha> for refs/heads/private/<topic>
git secret guard: blocked sensitive file in outgoing commit <sha>: <path>
git secret guard: blocked sensitive file in outgoing commit <sha>: <path>
...
git secret guard: push blocked. Remove the secret from the outgoing history before pushing.
error: failed to push some refs to 'ssh://cloud.superpowers.build:22/<slug>/<slug>-<run_id>'
```

The hand-off helper exits non-zero with the `cloud_build_handoff` step partial-completed. State on `cloud/status` may have a `failed` row but no work landed.

## Root cause

The git secret guard scans the **full reachable history** of the outgoing ref, not just the diff between the upstream branch and the new commit. If any historical commit on the work branch's ancestry contains a file matching the secret-guard regex (e.g. `\.env$`, `serviceAccountKey\.json`, `ai_token_discovery_results\.json`), the push is rejected wholesale.

This is correct upstream policy — those files SHOULD never reach a third-party build box — but it bites every real-world repo that has accumulated committed secrets over its lifetime, even if those secrets were revoked/rotated long ago.

**Verified on $GITHUB_REPOSITORY (2026-07-17):**

```
git secret guard: blocked sensitive file in outgoing commit 068cd4e3e0b69ca23b479fa90f4ffee35fe42957:
  archive/experimental_testing/testing_http_experimental/testing_full/.env
git secret guard: blocked sensitive file in outgoing commit 39919708997c3262327d2f6d31f09e2d7ad8e5b8:
  $PROJECT_ROOT/ai_token_discovery_results.json
git secret guard: blocked sensitive file in outgoing commit 39919708997c3262327d2f6d31f09e2d7ad8e5b8:
  testing_http/testing_full/.env
git secret guard: blocked sensitive file in outgoing commit ced63833f5ef9f457ae1ef0902f92b95b05329a2:
  testing_http/testing_full/.env
git secret guard: blocked sensitive file in outgoing commit 41a40fe0a17fd7241b1569805f9834098f5cd9e8:
  $PROJECT_ROOT/ai_token_discovery_results.json
git secret guard: blocked sensitive file in outgoing commit b0ef41091135587c6ea2cd1dd80e4a7eed4c6e83:
  $PROJECT_ROOT/serviceAccountKey.json
git secret guard: blocked sensitive file in outgoing commit b419dc056ef943e7d15956f96d40d4f2a149466b:
  $PROJECT_ROOT/venv/lib/python3.12/site-packages/googleapiclient/discovery_cache/documents/iamcredentials.v1.json
git secret guard: blocked sensitive file in outgoing commit b419dc056ef943e7d15956f96d40d4f2a149466b:
  $PROJECT_ROOT/venv/lib/python3.12/site-packages/googleapiclient/discovery_cache/documents/secretmanager.v1.json
  ... (5 more)
```

All 12 commits are in main's git history. The diff between origin/main and the work branch was a single 1-line requirements.txt bump — clean — but the guard rejected because of the historical ancestry.

## Why the demo test repo worked

The cb-demo test repo at `~/cb-demo/` (created during the original 2026-07-16 demo) has zero history with tracked secrets — it's a fresh repo with one or two files. The previous demo's "git secret guard: scanning outgoing range passed" success was because there was nothing for the guard to find. **Do not generalize that success to real projects.**

## Detection (pre-flight gate)

Before any cloud-build hand-off, run this 3-step check on the target repo:

```bash
# 1. Find every .env / credentials / serviceAccount file in the repo's tracked history
git -C "$PROJECT" log --all --oneline -- '*.env' 'serviceAccount*.json' 'ai_token_discovery_results.json' 2>/dev/null | head -5

# 2. Check working tree (live presence matters too — if the file is in HEAD's tree, it'll be on the box)
git -C "$PROJECT" ls-files | grep -E '\.env$|serviceAccount.*\.json$|ai_token_discovery_results\.json$' | head -5

# 3. Check reachable history from origin/main (what the guard will scan)
git -C "$PROJECT" log --all --oneline origin/main 2>/dev/null | head -3
```

If any of the above returns non-empty for known-secret patterns, **cloud-build will fail on hand-off**. Stop and apply the workaround below.

## Workaround A (user-preferred, 2026-07-17): `git rm` from HEAD + `git filter-repo` to scrub history

The user has explicitly preferred this over whitelisting. Trade-off: destructive (rewrites public commit history on `origin/main`, requires force-push, every existing PR will need a rebase), but the secret is actually removed from the repo rather than papered over.

```bash
# 1. Inventory what to remove
git -C "$PROJECT" ls-files | grep -E '\.env$|serviceAccount.*\.json$|ai_token_discovery_results\.json$' | head -10

# 2. git rm currently-tracked files (the ones in HEAD)
git -C "$PROJECT" rm --cached \
  testing_http/testing_full/.env \
  $PROJECT_ROOT/ai_token_discovery_results.json
# Plus add to .gitignore so future commits don't re-introduce them
printf '\ntesting_http/**/.env\n$PROJECT_ROOT/ai_token_discovery_results.json\n' >> "$PROJECT/.gitignore"

# 3. git filter-repo to scrub from history (1 path for the real secret)
git -C "$PROJECT" filter-repo --path $PROJECT_ROOT/serviceAccountKey.json --invert-paths --force
# Repeat for any other historical-only paths:
git -C "$PROJECT" filter-repo --path archive/experimental_testing/testing_http_experimental/testing_full/.env --invert-paths --force

# 4. Force-push to origin/main (DESTRUCTIVE — requires explicit user approval)
git -C "$PROJECT" push --force-with-lease origin main
```

**Pre-flight check:** ask the user for `FORCE PUSH APPROVED` before step 4. After the force-push, ALL in-flight PRs will need a rebase (`git fetch origin && git rebase origin/main` from each PR's branch, then force-push the PR branch).

**Pre-key-rotation safety:** the `$PROJECT_ROOT/serviceAccountKey.json` file is a real Google service account credential (verified $GITHUB_REPOSITORY commit `b0ef410911`, project_id=`worldarchitecture-ai`, client_email=`dev-runner@worldarchitecture-ai.iam.gserviceaccount.com`). Removing it from git history without rotating the key leaves the credential valid to anyone with a copy. **Surface this risk to the user** — they may decide to skip the scrub and stay with the whitelist workaround instead. On 2026-07-17 the user explicitly accepted the residual risk and chose to skip GCP key rotation ("Don't rotate any keys"); the secret-guard blocker was then unblocked via Workaround A.

## Workaround B (avoid cloud-build for these PRs)

If the user doesn't want to delete + scrub, drive the issue PRs inline via `drive-pr-to-green` / `dispatch-task` / `ao spawn`. Cloud-build provides value when the box does work the local session can't (long-running, headless, followable in background) — for a 1-line textual fix, the box ceremony is overhead, not value.

## Workaround C (whitelist known-secret paths in `.gitleaks.toml`)

This is the upstream-policy-aligned fix. The repo's `.gitleaks.toml` typically has an `[allowlist]` block — add the known-historical-secret paths so the guard sees them as already-known-and-OK:

```toml
[allowlist]
  paths = [
    '''archive/experimental_testing/.*\.env$''',
    '''testing_http/.*\.env$''',
    '''$PROJECT_ROOT/ai_token_discovery_results\.json''',
    '''$PROJECT_ROOT/serviceAccountKey\.json''',
    '''$PROJECT_ROOT/venv/.*googleapiclient.*\.json$''',
  ]
```

**Caveat:** This whitelist must be merged to `origin/main` BEFORE the cloud-build hand-off — the guard sees what's on the box, and the box pulls the work branch's tip plus its ancestry, but the policy itself is server-side and independent of the work branch. If the policy is repo-wide, the user's `origin/main` must already have the whitelist entry.

**Requires user approval** — touches shared config. Surface as a blocker with the user before editing.

## Workaround D (orphan branch — DEGRADED, often not viable)

```bash
git checkout --orphan cloud-build-orphan
git rm -rf .   # drops EVERYTHING from index
# Now re-add only the files you want, plus an empty commit, and push
```

This breaks the PR's project history (no ancestor to `origin/main`), so Green Gate / Skeptic / any CI that requires full project history will fail. **Use only if the goal is purely to validate that the box accepts an isolated push**, not to produce a real CI-tested PR.

## Verification after applying workaround A

```bash
# 1. Confirm scrubbed history — the path should no longer appear in any commit reachable from origin/main
git -C "$PROJECT" log --all --diff-filter=A --name-only --pretty=format:'%h %s' -- $PROJECT_ROOT/serviceAccountKey.json | head -3
# Expect: empty

# 2. Confirm HEAD no longer has the file
git -C "$PROJECT" ls-files | grep -E '\.env$|serviceAccount.*\.json$|ai_token_discovery_results\.json$' | head -3
# Expect: empty

# 3. Re-attempt hand-off
cd ~/superpowers-cloud-build-main/skills/cloud-build
bash scripts/lib-client.sh cloud_build_handoff "$PROJECT" "$run_id" "$work_branch" "$run_sha" "$request"

# 4. Verify status moved past 'accepted'
bash scripts/lib-client.sh cloud_build_fetch_status "$PROJECT"
bash scripts/lib-client.sh cloud_build_status "$PROJECT" state
# Expect: 'running' or 'done' within ~90s
```

## Pair with

- `drive-pr-to-green` — the fallback when cloud-build can't be used
- `~/.codex/plugins/cache/superpowers-cloud-build/cloud-build/<v>/scripts/lib-client.sh:cloud_build_handoff` — the helper that emits the guard error
- bead `rev-0ct9g` (2026-07-17) — opened to track the secret-cleanup decision for $GITHUB_REPOSITORY

## Provenance

Discovered on Slack thread C09GRLXF9GR/p1784235917 (2026-07-17), driving top 3 PRs + top 3 issues through superpowers cloud. Hand-off attempt for [PR #8419](https://github.com/$GITHUB_REPOSITORY/pull/8419) (mcp bump) reproduced this exact failure on `private/cloud-build-pr-8419` off `origin/main`. All 12 secret paths are real and traced to specific commit SHAs in the failure output.