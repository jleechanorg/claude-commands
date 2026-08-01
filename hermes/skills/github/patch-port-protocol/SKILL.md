---
name: patch-port-protocol
description: "Take an externally-supplied `.patch` file (Slack attachment, PR text, mail attachment) and push it as a GitHub PR — covers triage, multi-canonical-repo discovery, base-SHA verification, auth-vs-baked-in-user mismatch, `git apply` vs `git am` choice, and PR-baseline decisions. Trigger when the user attaches a `*.patch` or shares a git format-patch and says 'apply this', 'port this', 'push this as PR', 'review and merge', or 'create PR from this patch'."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Git, GitHub, Pull-Requests, Patches, Auth, Workflow]
    related_skills: [github-pr-workflow, github-auth, github-repo-management]
---

# Patch Port Protocol — from external `.patch` to GitHub PR

End-to-end recipe for taking a `.patch` file (Slack attachment, mail body, format-patch from a different machine) and shipping it as a GitHub PR. Encodes the 7 traps that bite every time, in the order they bite.

## When to use this skill

- User attaches a `*.patch` file in Slack and says "apply this", "port this", "push this as PR", "review and merge", "create PR from this"
- User pastes a `git format-patch` output in chat
- The patch's base SHA may not match the local fork's HEAD (very common)
- Multiple checkouts of the target repo exist on this machine

## The 7 traps (read once, in order)

| # | Trap | Symptom |
|---|------|---------|
| 1 | **Misrouted patch** — from a different fork entirely | `git am` fails "base SHA not found"; base SHA is from Snapchat-internal `$USER@snapchat.com` or other private org |
| 2 | **Multi-canonical-repo** — the repo has 2+ checkouts with different HEADs | Applied patch on wrong checkout; PR diff shows unrelated drift |
| 3 | **Auth-vs-baked-in-user mismatch** — `~/repos/.../.git/config` has a different GitHub user than `gh auth status` | Push gets 403 even though `gh pr view` shows your account has admin |
| 4 | **Stale lock files** — prior AO spawn left `.git/worktrees/<name>/HEAD.lock` | `git worktree remove` errors out; `git am` can't run |
| 5 | **Drifted patch context** — patch was authored against an older HEAD than `origin/main` | `git apply --check` fails on `origin/main` but succeeds on the fork's actual HEAD |
| 6 | **LFS auth failed** — `$USER-af:***` baked-in token can't fetch LFS | `git worktree add` aborts partway through with "Smudge error: Bad credentials" |
| 7 | **Misnamed branch collision** — prior session created a branch with the same name | `git worktree add -b <branch>` errors "branch already exists" |

Every patch-port session hits at least 2-3 of these. The recipe below navigates them in order.

---

## Phase 1: Triage (do this BEFORE applying anything)

### 1a. Read the patch + any companion docs

If the user attached a `GUIDE.md` / `README.md` alongside the `.patch`, **read those first**. They typically encode the patch author's intent, base SHA, and known limits.

```bash
# Download all attachments (Slack uses SLACK_USER_TOKEN, bot token lacks files:read)
curl -fsS -H "Authorization: Bearer $SLACK_USER_TOKEN" \
    "https://files.slack.com/files-pri/T.../<file>" -o guide.md
cat guide.md
```

### 1b. Verify the patch's provenance (trap #1)

```bash
# Extract the base SHA from the patch header
PATCH=/path/to/patch.diff
grep -E '^From [0-9a-f]{40}' "$PATCH"
# → "From a550011829fad078895d31f85b9af591b74f161a Mon Sep 17..."

# Extract the author email
grep -E '^From: ' "$PATCH"
# → "From: jleechan2015 <jleechan2015@users.noreply.github.com>"  ← good
# → "From: Jeffrey Lee-Chan <$USER@snapchat.com>"              ← Snapchat-internal; misroute

# Verify the base SHA exists on the target repo
gh api repos/<owner>/<repo>/commits/<base-sha>
# → 200 OK with commit message  ← patch IS for this repo
# → 422 No commit found         ← patch is from a different fork; STOP

# Verify the patch's target files exist on the target repo
for f in $(grep -E '^diff --git' "$PATCH" | awk '{print $3}' | sed 's|b/||'); do
    gh api repos/<owner>/<repo>/contents/$f --jq '.name' 2>&1 | head -1
done
# → filename + size            ← file exists on target; patch can apply
# → 404 Not Found              ← file is from a different fork; STOP
```

**If base SHA 422s OR target files 404**, the patch is misrouted. STOP. Post a status message with the proof; don't fabricate a port. Don't waste budget trying to make it fit.

### 1c. Discover all canonical locations of the target repo (trap #2)

```bash
# Find every checkout on this machine
find ~ -maxdepth 6 -type d -name "<repo-name>" 2>/dev/null | \
    grep -E '\.git$|^~' | sort -u

# For each candidate, capture HEAD + dirty-status + auth
for d in <candidate-paths>; do
    cd "$d"
    echo "=== $d ==="
    echo "HEAD: $(git rev-parse --short HEAD)"
    echo "branch: $(git branch --show-current)"
    echo "uncommitted: $(git status --short | wc -l)"
    echo "origin: $(git remote get-url origin 2>/dev/null | sed 's|://[^@]*@|://***@|')"
done
```

**Decision tree** (default per `pr-branch-from-main.mdc` and SOUL.md `dark-factory-canonical-locations` COMMIT pattern):

1. `~/projects/<repo>` canonical, on origin/main → **USE THIS**
2. `~/repos/<owner>/<repo>` on a fork-divergent HEAD (e.g. `eae7413` vs `8fc167899`) → **CAN USE for patch port IF patch base SHA matches its HEAD**
3. `~/repos/<other-owner>/<repo>` or `~/projects_other/<other>/<repo>` → **NOT this repo; do NOT touch**
4. `~/.worktrees/<repo>/<legacy>` → **LEGACY; do NOT touch unless user asks**

Persist this discovery to a `## COMMIT:` block in `~/.hermes/workspace/SOUL.md` if the repo has multiple locations — see SOUL.md line 548 `dark-factory-canonical-locations` for the template.

---

## Phase 2: Apply the patch

### 2a. Pick the right checkout + create a clean worktree (traps #4, #6, #7)

```bash
# Clean up any stale worktree state from prior sessions
git worktree prune
rm -f /path/to/repo/.git/worktrees/<name>/HEAD.lock
git branch -D <branch-name> 2>/dev/null

# Create fresh worktree at the patch's base SHA
WORKTREE=/tmp/<repo>-patch-worktree
rm -rf "$WORKTREE" 2>/dev/null
GIT_LFS_SKIP_SMUDGE=1 git worktree add "$WORKTREE" -b <branch> <base-sha>
# LFS_SKIP_SMUDGE bypasses "Smudge error: Bad credentials" when
# the baked-in LFS token ($USER-af:***) can't fetch LFS objects
```

### 2b. Apply with `git apply`, NOT `git am` (trap #5)

```bash
cd "$WORKTREE"
git apply --check /path/to/patch.diff
echo "exit=$?"  # exit 0 = OK, non-zero = context drift
```

**Why `git apply` over `git am`:**

- `git am` requires the base SHA to be reachable from your current branch. When the patch was authored on a different fork's commit graph, `git am` errors immediately.
- `git apply` only requires the target files to exist. It works on any base that has the same target files, regardless of commit-graph ancestry.

If `git apply --check` fails on the chosen base, try a different canonical checkout (per Phase 1c). If it fails on ALL bases, the patch context has drifted — run `git apply --3way --check` for 3-way merge fallback.

### 2c. Commit

```bash
git apply /path/to/patch.diff
git add -A
# Use the patch's Subject line as the commit message
MSG=$(grep -E '^Subject: \[PATCH' /path/to/patch.diff | head -1 | sed 's/^Subject: \[PATCH\] //')
git commit -m "$MSG"
```

---

## Phase 3: Push + PR (trap #3)

### 3a. Diagnose auth — `gh auth status` wins over baked-in `.git/config`

```bash
gh auth status
# → "Logged in to github.com account jleechan2015"  ← USE THIS
# → "Active account: jleechan2015"                  ← USE THIS
```

```bash
# Show what user the local repo's baked-in URL uses
git remote get-url origin | grep -oE '://[^:]+:'
# → "://$USER-af:"    ← MISMATCH; baked-in user differs from gh auth
# → "://jleechan2015:"   ← matches gh auth; can push as-is
```

**The trap:** `~/repos/<owner>/<repo>/.git/config` often has a token baked in for a DIFFERENT GitHub user (e.g. `$USER-af:***`) than the one with admin on the org (e.g. `jleechan2015`). The `$USER-af` token gets 403 on push. Don't waste cycles trying to fix the wrong token.

### 3b. The CORRECT push recipe (verified 2026-07-20 on PR #407)

```bash
# 1. Drop the baked-in user — switch to unauthed URL
git remote set-url origin https://github.com/<owner>/<repo>.git

# 2. Wire gh as the credential helper (uses the ACTIVE gh auth user)
gh auth setup-git

# 3. Push (no terminal prompt; gh supplies the token)
GIT_TERMINAL_PROMPT=0 git push -u origin <branch>
```

Verify after push:
```bash
gh pr view <branch> --json author --jq '.author.login'
# → "jleechan2015"  ← correct
```

### 3c. Open the PR

```bash
~/.hermes/scripts/gh-safe-publish pr create --base main --head <branch> \
    --title '<conventional-commit title>' \
    --body-file /path/to/body.md
```

The PR body should explicitly document:
- **Base SHA note** if the branch isn't on `origin/main` (e.g. "branch rooted at `eae7413`, 39 commits behind `origin/main`"). This forces the reviewer to decide: merge as-is, or have you rebase + resolve conflicts.

---

## Phase 4: Test + report

Run the patch's expected test set:

```bash
cd "$WORKTREE"
python3 -m pytest <tests-mentioned-in-guide> -q
```

Compare against the patch author's claimed baseline. If your count differs, that's a real signal — investigate before pushing the PR.

---

## Phase 5: Status to user (always)

End-state report MUST include:

- **PR URL** with clickable link
- **Branch + commit SHA** (so reviewer can verify the push landed)
- **Test result** (e.g. "59/59 passed, matches guide.md expected")
- **Auth used** (e.g. "author: jleechan2015 per gh pr view")
- **Base-SHA note** if applicable (so reviewer knows what they're diffing against)
- **Memory used** citation per SOUL.md `Response guardrail` rule (2)

---

## Anti-patterns (forbidden)

1. **Don't `git am` first.** Always `git apply --check`. `git am` is for clean forks-of-forks; external patches almost never satisfy its base-SHA requirement.
2. **Don't push with the baked-in user.** Cross-check `gh auth status` first; if they differ, the baked-in user is the WRONG account.
3. **Don't blindly `git apply` on `origin/main`.** Verify the patch's base SHA against the fork's actual HEAD first; if they don't match, you may apply on the wrong base.
4. **Don't trust patch author email alone.** `jleechan2015@users.noreply.github.com` is trustworthy; `$USER@snapchat.com` is internal-Snapchat misroute. Check the org the email belongs to.
5. **Don't fabricate a port** when the patch is misrouted. Post the proof (422 from gh api, 404 from gh repo view) and ask the user which repo they meant.
6. **Don't skip the multi-canonical-repo discovery.** On Mac with ~30 repos, the chance the user has ≥2 checkouts of any given repo is high. The 6-line scan in Phase 1c takes 30 seconds and prevents a 30-minute "applied on the wrong fork" recovery.

---

## Pitfall log (filled from real incidents)

| Date | Incident | Resolution | Encoded as |
|------|----------|------------|------------|
| 2026-07-20 | First patch was Snapchat-internal `$USER@snapchat.com`; base SHA 422'd on dark-factory | Stopped, posted proof, closed bead + issue | Phase 1b provenance check |
| 2026-07-20 | 5 AO harnesses failed to spawn worker on dark-factory | Pivoted to inline-port + push | Phase 3 push-recipe |
| 2026-07-20 | `$USER-af:***` baked into `.git/config` got 403 on push | Switched to `gh auth setup-git` + jleechan2015 | Phase 3a-3b |
| 2026-07-20 | `git am` failed because base SHA `a5500118` not in local clone | Switched to `git apply` (doesn't need base SHA reachable) | Phase 2b |
| 2026-07-20 | Patch context drifted on `origin/main` post-#297 + #301; applied cleanly on fork HEAD `eae7413` | Documented base-SHA note in PR body | Phase 1c multi-canonical + Phase 3c PR body |

---

## Companion references

- `references/example-session-2026-07-20.md` — full transcript of the port phase (Phases 1-5), including the misroute discovery, the 5 AO-harness failure sequence, the `$USER-af` 403 trap, and the initial PR #407 push.
- `references/example-session-phase-6-bring-to-green-2026-07-21.md` — the same session's bring-to-green phase (Phase 6): rebase onto origin/main with conflict resolution in 2 files, inline `/advice` subagent fan-out as Gate-3 substitute for rate-limited CodeRabbit, audit-chain correctness fixes, and pre-existing skeptic-gate infra failure attribution via `br create`.
