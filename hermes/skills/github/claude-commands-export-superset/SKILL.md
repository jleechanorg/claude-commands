---
name: claude-commands-export-superset
description: |
  Audit, rebase, supersede, and ship the jleechanorg/claude-commands export pipeline.
  Five-session playbook covering consolidation, supersession, fresh export, AND the
  cleanup-PR + script-patch archetype (Pitfall 10) for excluding content categories like
  `_archive/` that should never have shipped. v1.2.0 adds Pitfalls 11 + 12 covering
  cross-vendor re-sync staleness (vendored copy drifts from upstream between exports)
  and content-filter rewrites BODY-but-not-FILENAMES (install scripts that reference
  filter-rewritten filenames break at install time). Triggers on "consolidate the open
  claude-commands PRs", "fresh /exportcommands", "remove the archive from the PR and
  modify /exportcommands to stop exporting it", "supersede #N", "edit the export to
  exclude _archive/", "the cmux-goal pair isn't on main", "re-sync the vendored
  watchdog", "stale cmux_resume_watchdog in the export", "install script fails
  with no such file", "com.$USER.cmux-resume-watchdog.plist not found", etc.
  Encodes twelve pitfalls.
version: 1.2.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [github, claude-commands, export, supersession, rebase, audit, drive-pr-to-green, exclude-paths, script-patch, vendoring, cross-vendor-sync] 
    related_skills: [drive-pr-to-green, github-pr-automation-debug, github-pr-workflow, patch-tool-safe-editing]
---

# claude-commands-export-superset

Audit, rebase, supersede, and ship the `jleechanorg/claude-commands` export pipeline. This is the
canonical workflow when the user wants "the latest `~/.claude/` shipped" — multiple sessions have
hit this same task with subtle differences (open PRs vary, some already merged, some still stale,
sometimes the auto-opened PR contains content the user wants excluded), and the playbook below
locks in the four most common pitfalls PLUS the 5th-archetype cleanup workflow discovered 2026-07-13.

## Trigger

Any of these messages should fire this skill:

- "consolidate the open claude-commands PRs" / "consolidate #N/#M/#O into one PR"
- "fresh /exportcommands and check the PRs"
- "the export is stale / has new content since last run"
- "see what else is needed / what's incremental" (mid-task state re-check)
- "supersede #N" / "close #N as superseded"
- "remove the archive from the PR and modify /exportcommands to stop exporting it"
- "/exportcommands [from ~/your-project.com]"
- "the cmux-goal / ironclad pair isn't on main yet"
- "the latest commands/skills aren't in jleechanorg/claude-commands"
- "edit the export to exclude _archive/" / "stop exporting archive paths"

## Pitfall 1 — Always re-check current state BEFORE planning (added 2026-07-13)

The user may have merged some PRs mid-task, or some may have closed, between your first `gh pr list`
and your final action. **Re-run the state-recency check after every user message and after every
OOB directive**, not just at session start. Specifically:

```bash
# Step 0 of every task in this class — re-run on any pivot
HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/pulls?state=open&per_page=20&sort=created&direction=desc' \
  --jq '[.[] | {n: .number, title: .title, state: .state, headRefName: .head.ref, headSha: .head.sha, baseSha: .base.sha, mergeable: .mergeable, mergeable_state: .mergeable_state, additions: .additions, deletions: .deletions, commits: .commits}]'

# Also verify main SHA right now (not from earlier in the session)
HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/branches/main' \
  --jq '{sha: .commit.sha, lastCommit: .commit.commit.message, lastCommitDate: .commit.commit.author.date}'
```

Verified 2026-07-13: an earlier session plan started "consolidate #324/#325/#326 into one PR." A
mid-task user OOB ("i just merged some of those PRs") revealed that #325 and #326 had already
landed on main at `337dc6d7` 8 minutes before the task. The original plan was obsolete; the
correct response was to (a) supersede #324 as no-longer-net-new, (b) run a fresh
`/exportcommands` for the incremental, (c) close the original 3-PR plan entirely.

**Anti-pattern:** building a consolidation strategy on stale state. Even if your first `gh pr list`
returned 3 open PRs, a user pivot 60s later may have already merged 2 of them. Always re-verify.

## Pitfall 2 — `mergeable_state: dirty` on a stale-base PR means BASE != main (added 2026-07-13)

When you see `mergeable_state: dirty` or `mergeable: false` on a PR, the FIRST diagnostic is
**base vs main comparison**, not the file list. The PR may simply be 200+ commits behind main
because it was cut before several merges.

```bash
# Verify the staleness
HOME=$HOME GH_TOKEN="" gh api 'repos/<owner>/<repo>/pulls/<N>' \
  --jq '{baseSha: .base.sha, headSha: .head.sha, baseRef: .base.ref, mergeable: .mergeable, mergeable_state: .mergeable_state}'

HOME=$HOME GH_TOKEN="" gh api 'repos/<owner>/<repo>/branches/main' \
  --jq '{main: .commit.sha}'

# If baseSha != main, the PR is stale. Three options:
#   1. git merge origin/main into the PR branch (merge-commit pattern, preserves N-commit history)
#   2. git rebase origin/main onto the PR branch (cleaner history, but replays N commits)
#   3. Compare file content vs current main — if no truly-new content, supersede without merging
```

For the `claude-commands` export PRs specifically, the **third option is often correct**: the
PR's "content" is `cp` from `~/.claude/`, and if `~/.claude/` hasn't changed since the branch was
cut, the rebase just produces duplicate work.

Verified 2026-07-13: PR #324 (`add-cmux-goal-ironclad-thin-commands`) had `mergeable_state: dirty`,
base `a30c037` (3 days stale), 300 files vs current main, 200 commits. On rebase audit:
- 0 truly net-new files (excluding `backup/`, `.beads/`, `.agentloop/`)
- 183 files where #324 had older content (main was ~4× larger in those paths)
- 42 files in main but not in #324 (came from #325/#326 merges)

Conclusion: #324 was obsolete and would re-introduce the `backup/` security leak it pre-dated.
Right action: **supersede, do not rebase**.

## Pitfall 3 — `~/.claude/commands/exportcommands.sh` is NOT the canonical version (added 2026-07-13)

Two scripts coexist:

| Path | Version | Hermes superset? |
|---|---|---|
| `~/.claude/commands/exportcommands.sh` (466 lines) | Original 2024-06 version | ❌ NO — `CLAUDE_DIRS=(commands skills hooks agents scripts)` only |
| `your-project.com/.claude/commands/exportcommands.sh` | Live (per `export-commands-orchestration-contract`) | ✅ YES — adds `HERMES_DIRS=(skills commands)` (PR #8135) |

The "live" version lives in the your-project.com repo and is the one you want for `/exportcommands`
runs targeting `jleechanorg/claude-commands`. The global one still ships, but its hermes surface
is missing.

**Run recipe (verified 2026-07-13):**

```bash
# Run from your-project.com so the hermes-aware union-merge fires
cd ~/your-project.com
HOME=$HOME PROJECT_ROOT=$HOME/your-project.com \
  bash $HOME/.claude/commands/exportcommands.sh

# Output structure (script writes to stdout in this exact shape):
#   ▶ Cloning jleechanorg/claude-commands...
#   ✅ commands (global-only:N  project-only:N  identical:N  auto-resolved:N)
#   ✅ skills (...)  ✅ hooks (...)  ✅ agents (...)  ✅ scripts (...)
#   ✅ orchestration  ✅ automation  ✅ ralph  ✅ workflows
#   ✅ Filters applied
#   ▶ Scanning for leaked paths...
#   ▶ Updating README.md via Claude...
#   ⚠️  Claude CLI failed — keeping existing README unchanged   ← safe to ignore if non-blocking
#   git secret guard: scanning outgoing range <BASE>..<HEAD> for refs/heads/export-YYYYMMDD-HHMMSS
#   ✅ Export complete!
#      PR: https://github.com/jleechanorg/claude-commands/pull/<N>
#      Branch: export-YYYYMMDD-HHMMSS
```

**Branch naming is deterministic:** `export-YYYYMMDD-HHMMSS` (local PT timezone). The PR
auto-opens via the script's `gh pr create --head <branch> --base main` step.

**Per-file byte-identity audit** (not file-list audit) is the correct delta test:

```bash
# For each file in the diff, fetch main's content and branch's content and compare bytes
git show origin/main:<path>     # main's version
git show origin/<branch>:<path>  # branch's version
# If identical → no net change
# If branch has older/smaller content → obsolete
# If branch has net-new content → genuinely incremental
```

## Pitfall 4 — Bot rate-limit faux-green on the auto-opened export PR (added 2026-07-13)

The export script's auto-opened PR almost always posts **CodeRabbit status = success** BUT with
**body = "Review limit reached"**. Same for Cursor Bugbot with **"Bugbot couldn't run - usage limit
reached"**. These are NOT real reviews — they're webhook-level "success" statuses the bot posted
to clear the queue without doing work.

**Verification recipe (every time the export script's auto-PR is involved):**

```bash
# 1. Get the bot comments
HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/issues/<N>/comments?per_page=10' \
  --jq '[.[] | select(.user.login | test("coderabbitai|cursor|chatgpt-codex-connector"; "i")) | {login: .user.login, body: .body[:200]}]'

# 2. Match for the rate-limit telltales
#   coderabbitai[bot]: contains "Review limit reached" or "rate limited"
#   cursor[bot]: contains "Bugbot couldn't run" or "usage limit reached"
#   chatgpt-codex-connector[bot]: contains "Codex usage limits"
# If any of these phrases appears → status=success is FAUX. Document in the PR with a comment
# citing coderabbit-slow-bot-policy from SOUL.md and proceed with the merge anyway.

# 3. Also check the actual review state (not the status webhook)
HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/pulls/<N>/reviews' \
  --jq '[.[] | {state: .state, login: .user.login, submitted_at: .submitted_at}]'
# Empty array = no real review was submitted = faux-green.
```

**Pattern (verified 2026-07-13, PR #327):** all three bots posted rate-limit comments within 60s
of each other at PR creation; the status webhooks all showed `success`; the actual review array
was empty. Per `coderabbit-slow-bot-policy` in SOUL.md, this is non-blocking after ONE once-per-head
review attempt. Document the timeout in a PR comment with the same phrases the bots used, then
proceed with the green-check + human-merge handoff.

## Pitfall 5 — `git secret guard` output IS the security pre-check (added 2026-07-13)

The export script runs `git secret guard` on the outgoing range and prints to stdout. Look for:

```
git secret guard: scanning outgoing range <BASE>..<HEAD> for refs/heads/<BRANCH>
```

A line WITHOUT a `FAIL` after it = clean. A line WITH `FAIL` or `WARNING` = block the PR until
resolved. This is the ONLY security check the script does — there's no pre-commit hook or
workflow gate. If the script's stdout doesn't show this line at all, run `git secret scan
<BASE>..<HEAD>` yourself before pushing.

## Pitfall 6 — `localexportcommands.md` and `exportcommands.md` are DOCS, not scripts (added 2026-07-13)

Three documents live in `~/.claude/commands/`:

| File | Role |
|---|---|
| `exportcommands.sh` (466 lines, 19.1K) | **The script.** Invoked by `/exportcommands`. |
| `exportcommands.md` (45.1K) | **Operator doc** — explains what `/exportcommands` does, full superset spec, hermes-deploy-pipeline relationship. |
| `localexportcommands.md` (23.2K) | **Local-only doc** — variant for projects that want to skip the global union and ship only their own `.claude/` dir. |
| `exportcommands.py` (96.4K) | Companion Python (alternative entry point; not invoked by `/exportcommands`). |
| `tests/test_exportcommands.py` | Contract tests for the Python entry. |

When users say "/exportcommands", they mean the **bash script**, not the docs or the Python.

## Pitfall 7 — The auto-opened PR has no `.github/workflows/` (verified 2026-07-13)

`jleechanorg/claude-commands` has CI at `./workflows/*.yml`, NOT at `.github/workflows/`. Earlier
`gh api .github/workflows` returns 404 — that's expected. The CI is:

- `workflows/coderabbit-ping-on-push.yml` (CodeRabbit webhook ping)
- `workflows/claude-code.yml` (some Claude Code integration)
- `workflows/claude-processor.yml`
- Plus 30+ others

When driving an export PR to green, **don't look for `.github/workflows/`**. The "green" check
on this repo is:
- `mergeable_state: clean` (REST pulls endpoint)
- `statusCheckRollup` empty (no GH Actions runs on the export PR's head)
- Real bot reviews OR documented rate-limit timeout per Pitfall 4

## Pitfall 8 — Supersession comment template (verified 2026-07-13)

When posting a supersession comment on a STALE PR (before closing), include:

1. **Base staleness evidence** — the SHA the PR branched from and main's current SHA.
2. **Per-file diff math** — total files, net-new, modified, main-only counts.
3. **Why it's superseded** — concrete examples (empty files, security-leak files, files where
   main has 4× the content).
4. **Forward path** — where the incremental went instead (the new fresh-export PR).
5. **Co-Authored-By** — Claude Code attribution.

```markdown
## Closing as superseded — consolidation audit findings

After the merges of [PR #325](...) and [PR #326](...) landed on `main` @ `<MAIN_SHA>`,
this PR's value collapsed. Detailed audit:

### Diff math
- Total files in #N: **<N>** (vs current main)
- Files in #N *only* (not in main): **<X>** truly net-new (excluding `backup/`, `.beads/`, ...)
- Files *modified* in #N vs main: **<Y>**
- Files in main but not in #N: **<Z>** (came from #N+1/#N+2 merges)

For the <Y> files where #N differs from current main, main has ~<M> MB of content vs #N's ~<m> MB.
- `<file_a>`, `<file_b>` in this PR are **empty files**; main has the real implementations.
- 29 `workflows/*.yml` files predate the `security(backup)` gitignore; rebase reintroduces leaks.

### Security incident this PR still contains
`backup/<HOSTNAME>/...` — <N> files. The original 2026-07-12 home-config snapshot leak that
prompted the `security: gitignore backup/` commit. **Merging would re-introduce that leak.**

### Recommendation
- **`<key feature>` is on main** (via [<PR>](...) merge <DATE>).
- All remaining valuable content is **already represented** in main via #N+1+#N+2.

Closing as superseded.

🤖 Generated with [Claude Code](https://claude.com/claude-code). Co-Authored-By: Claude <noreply@anthropic.com>
```

## Pitfall 9 — `/exportcommands` from a non-main branch (verified 2026-07-13)

The export script uses `git rev-parse --show-toplevel` to detect `PROJECT_ROOT`, NOT
`--abbrev-ref HEAD`. So it works from any branch. BUT — if you're on `feat/issue-8084` with N
uncommitted files, those files don't affect the export (uncommitted = not in worktree), but the
export still uses the WORKTREE'S HEAD for diff calculations.

**Recipe:** if you want a "true diff vs prior export", check out the branch that matches the
prior export's source state, run `/exportcommands` from there, then post the diff against the
prior PR's branch. Verified 2026-07-13: running from `feat/issue-8084` produced PR #327 (66 files,
+7,436/−19) — clean against current main `337dc6d7`. Branch mismatch didn't corrupt anything
because the union-merge ignores branch identity.

## Pitfall 11 — Vendored-source re-sync staleness (verified 2026-08-01, PR #38 → #40)

When the export bundles source files (Python scripts + tests) that originated in
a DIFFERENT upstream repo (e.g. `user_scope/scripts/cmux_resume_watchdog.py`
re-shipped as `your-project.com/.claude/skills/cmux-resume-watchdog/cmux_resume_watchdog.py`),
the export's snapshot has a *second* decay axis the existing 10 pitfalls don't
cover: **the vendored copy can drift from upstream between export runs**. The
signal is the bug-by-bug re-discovery cycle:

1. Run `/exportcommands` from your-project.com → snapshot of `cmux_resume_watchdog.py` from this exact moment lands in the export branch.
2. Meanwhile, `user_scope` main advances (a real bug fix lands: 3 new quota regex anchors, 10 new network patterns).
3. Live daemon on this machine is now running the upstream HEAD (auto-pulled by launchd), but the vendored copy in `your-project.com` (and downstream in `claude-commands`) is still pre-fix.
4. The **first /advice review** returns "vendored copy is stale, missing 13 patterns". Round-trip fix: re-copy from upstream, re-sync both PRs.
5. **Second /advice review** returns "vendored test file uses `REPO_ROOT = Path(__file__).resolve().parents[1]`" — but in the vendored location the script lives in `parents[0]`. **Every test fails on `importlib.SpecNotFound`.** Round-trip fix: patch REPO_ROOT in the vendored copy only.
6. **Web-advice review** independently catches a fixture leak (`"$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"` in a `Surface()` test fixture) that survived the SUBS filter because the regex `s|\bjleechan\b|$USER|g` rewrote `$USER` but the hostname + project path survived verbatim.

The cure (recipe, 2026-08-01):

```bash
# Phase A — re-sync the script AND its sibling test file
cp $HOME/projects/<upstream>/scripts/<script>.py \
   $HOME/.worktrees/<export-wt>/.claude/skills/<skill>/<script>.py
cp $HOME/projects/<upstream>/tests/test_<script>.py \
   $HOME/.worktrees/<export-wt>/.claude/skills/<skill>/test_<script>.py

# Phase B — fix REPO_ROOT in the test file if it was authored for upstream's
# tree layout (parents[N]) but the vendored location has a different depth.
# Common case: upstream test does Path(__file__).resolve().parents[1] / "scripts" / X
# → vendored test needs Path(__file__).resolve().parent / X

# Phase C — grep both files for fixture-style literals that the SUBS regex
# won't catch (usernames, hostnames, project paths). Replace with placeholders.
# Per SUBS spec (lines 220-260 of exportcommands.sh), `\bjleechan\b` is rewritten
# to `$USER`, but `$USER@<hostname>` is rewritten only on the prefix half.
# Always run:
rg -n '\bjleechan\b|@.*-macbook-pro|~/projects/[^/]+/' \
   $HOME/.worktrees/<export-wt>/.claude/skills/<skill>/

# Phase D — run the test suite IN THE VENDORED LOCATION, not upstream
cd $HOME/.worktrees/<export-wt>/.claude/skills/<skill>/
~/.local/orch-venv/bin/python3 -m pytest test_<script>.py -q
# Expect: same pass count as upstream, but RUN from this dir so the REPO_ROOT
# lookup targets the vendored layout.

# Phase E — only after test D passes, amend + force-push the export branches
git add .claude/skills/<skill>/<script>.py .claude/skills/<skill>/test_<script>.py
git commit --amend --no-edit
git push --force-with-lease=<expected_old_sha> origin HEAD
# Mirror to downstream (claude-commands export branch):
cd $HOME/.worktrees/<downstream-wt>
cp ... same files ...
git add ... same files ...
git commit -m "feat(skills/<skill>): re-sync from <upstream> PR #N"
git push origin HEAD
```

Three anti-patterns the recipe explicitly avoids:

- ❌ **Re-running `/exportcommands`** to "refresh" the vendored copy — the export script does a UNION-MERGE of all skill files; if upstream's file is functionally newer than the export's, the union-merge may not even detect the change because the export's content filters rewrite upstream's bytes too. Re-run is the wrong tool.
- ❌ **Patching only the script** (not the test file). The test file's `REPO_ROOT` resolution depends on the file's position in the vendored tree, which differs from upstream's tree. Always ship both files together.
- ❌ **Trusting the SUBS regex to filter fixture leaks**. The regex is fine-grained for `$USER` standalone but mechanically blind to the surrounding context (`$USER@<host>`, `~/projects/<path>/`). Always run the Phase C leak grep after every re-sync.

**The cross-vendor re-sync is a three-PR pipeline** (verified 2026-08-01):
- Upstream: `jleechanorg/user_scope` PR #40 — canonical fix lands here.
- Source-side: `$GITHUB_REPOSITORY` PR #8681 — re-sync the vendored copy + force-push.
- Downstream: `jleechanorg/claude-commands` PR #346 — mirror the re-sync + push.

All three PRs must move together or the merge decouples. Force-push only to branches you own; use `gh pr view --json headRefName,author` to verify branch ownership before each `--force-with-lease=<expected_old_sha>`.

## Pitfall 12 — Content-filter regex rewrites BODY but not FILENAMES (verified 2026-08-01, install_cmux_resume_watchdog.sh)

The export's `perl -pi -e 's|...|...|g'` SUBS regexes rewrite CONTENT of filtered files in place. Filenames are NOT filtered. This is a sharp edge when an install script or shell wrapper does *both*:

1. Defines a `LABEL=com.<githubuser>.<skill>` constant in CONTENT (gets filter-rewritten to `LABEL=com.$USER.<skill>`).
2. References `$SKILL_DIR/$LABEL.<ext>` to find a sibling file on disk (FILENAME on disk is NOT rewritten — still `com.<githubuser>.<skill>.<ext>`).

**Symptom** (verified 2026-08-01, `install_cmux_resume_watchdog.sh:18`): script does `sed -e "s|@HOME@|$HOME|g" ... "$SKILL_DIR/$LABEL.plist.template"` where `$LABEL` is post-filter `com.$USER.cmux-resume-watchdog` but the shipped template file is `com.$USER.cmux-resume-watchdog.plist.template`. The `set -euo pipefail` script aborts on `ls` returning empty — and **the install is broken for every downstream user**, not just the bad commit author.

**Three cure recipes**, pick the one that matches the install script's structure:

```bash
# Recipe A — rename the file to be filter-stable (drop the user-name prefix).
#   Before: com.$USER.cmux-resume-watchdog.plist.template
#   After:  cmux-resume-watchdog.plist.template
# Pros: zero install-script changes needed (the file path becomes predictable).
# Cons: doesn't help if the script reaches for files by user-derived names.

# Recipe B — use @PLACEHOLDER@ in the file's CONTENT and `sed "s|@PLACEHOLDER@|$LABEL|g"`
# in the installer. The export's SUBS regex is non-greedy on `@` so `@LABEL@`,
# `@DEST@`, `@HOME@` survive the filter intact.
# Pros: any user-derived token can be parameterized without filter breakage.
# Cons: the install script must explicitly run the sed pass; a literal-substitute
#   installer will break.

# Recipe C — pick a vendor-neutral name that doesn't contain the github username.
#   com.localhost.<skill>           — stable across users; macOS launchd accepts
#                                     labels with localhost domain; no filter
#                                     rewrite is needed even if the content
#                                     mentions the literal string.
#   com.example.<skill>             — same idea
# Pros: zero filter interaction at all.
# Cons: many users' machines already have a com.<their-actual-github-user>.<skill>
#   entry in /Library/LaunchAgents, so first install requires explicit bootout
#   of the old label.
```

**Detection recipe** (run BEFORE every export of a skill that has shell installers):

```bash
# For every shell/script file in the staged export, list every reference to a
# github-username-prefixed file path:
HOME=$HOME git -C $HOME/.worktrees/<export-wt> diff --name-only \
  --diff-filter=AM HEAD~1..HEAD | grep -E '\.(sh|bash|zsh|fish)$' | while read f; do
    echo "=== $f ==="
    grep -nE "com\\.\\w+|com\\.\\\$USER|/\\\$LABEL/\\\$|\\\$SKILL_DIR/\\\$LABEL" "$f"
  done
# Each "Yes I do" hit → apply Recipe A, B, or C above.
```

**The mental model:** filter rewrites apply to *content*. Any cross-reference between
a content-managed variable (like `LABEL=...`) and a filesystem name is a latent
breakage waiting for a fresh export on a different host. Audit every `ls $X`,
`@file_template`, `$CONFIG_DIR/...` reference for this property before pushing.

## Pitfall 10 — The 5th archetype: cleanup-PR + script-patch workflow (added 2026-07-13)

The export script has **no exclude logic for content categories**. It's a copy-everything
union-merge. A fresh export will ship every file under `~/.claude/skills/_archive/`,
`~/.claude/skills/_archived_loose_md/`, `.beads/`, etc. — local history-keeping surfaces that
should never reach the public `jleechanorg/claude-commands` repo.

When the user says *"remove the archive from the PR and modify /exportcommands to stop exporting
it"*, the correct response is a two-track atomic edit:

### Track A — patch `exportcommands.sh` so future runs skip the category

The script has TWO union-merge surfaces plus an rsync for root-level dirs. Each needs its own
exclude:

```bash
# Surface 1: union_dir() global find — add to the `\( -not -path ... \)` block
\( -not -path '*/_archive/*' \) \

# Surface 2: union_dir() project find — same exclude, different anchor context
\( -not -path '*/_archive/*' \) \

# Surface 3: rsync block for orchestration/automation/ralph — add to --exclude list
--exclude='_archive/' \
--exclude='*/_archive' \
```

The script's `find` calls have ~25 lines of `--not -path` clauses between them — use unique
surrounding context (e.g. the `union_dir()` body or `while IFS= read -r -d '' f; do` lines) to
disambiguate. After patching, run `bash -n ~/.claude/commands/exportcommands.sh` to confirm syntax.

**Smoke-test the patch** before pushing: extract the union_dir function and run it against a
fixture with files in both `_archive/` and non-`_archive/` paths. Confirm the count of returned
files matches the expected (non-archive) total.

### Track B — amend the auto-opened PR to drop the unwanted content

In a fresh worktree of the PR branch:

```bash
# 1. Get the diff-list and identify files in the unwanted category
HOME=$HOME git -C ~/worktrees/<branch> diff --name-only --diff-filter=AM HEAD~1..HEAD \
  | grep '<unwanted-category-pattern>' > /tmp/rm_files.txt

# 2. git rm the matching files
HOME=$HOME git -C ~/worktrees/<branch> rm -rf $(cat /tmp/rm_files.txt)

# 3. Commit and force-push
HOME=$HOME git -C ~/worktrees/<branch> commit -F <commit-message-file>
HOME=$HOME git -C ~/worktrees/<branch> push --force-with-lease origin \
  HEAD:refs/heads/<branch>
```

### CRITICAL — distinguish "files I ADDED" vs "files main already had"

The auto-opened PR may include files that **already existed on main** (in modified form, because
the export's content filters changed them by ~30 bytes). Removing those files wholesale will
make them disappear from main on merge, which is wrong.

**Recipe to keep main's version intact** while still removing only the unwanted category:

```bash
# For each "already-on-main" file the script modified, restore it to main's exact bytes
git restore --source=<MAIN_SHA> --staged --worktree -- <file-path>

# Verify byte identity before committing
git show <MAIN_SHA>:<file> | git hash-object --stdin
cat <file> | git hash-object --stdin
# Both SHAs must match — if they differ by even 1 byte, the content-filter stripped a trailing newline
```

**Don't use `git checkout HEAD~1 -- <file>`** — that restores to the export-PR's modified version
(before the cleanup), not to main's original. `git restore --source=<MAIN_SHA>` is the only path
that ensures zero net diff vs main.

### Final shape

After Track A + Track B, the PR diff shrinks from "all categories" to "the actual incremental
the user wanted". Verified 2026-07-13 with PR #327: original 66 files → 5 files after the
cleanup. The 5-file PR contained exactly `/harness --optimize` flag, new `/slackbots` command,
`/social` draft-only semantics, plus the two backing skill files.

**Always close by posting a follow-up PR comment** that summarizes the cleanup (what was
removed, why, what the script patch prevents) — this is the durable record for future sessions
and audit trails. CodeRabbit may now actually review the PR (since the bot rate limit resets
on push), so the post-cleanup push is also your chance to retrigger a real review.

## The full sequence (execute in order, no pauses)

### Phase 0 — Re-check state (Pitfall 1)

```bash
HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/pulls?state=open&per_page=20' \
  --jq '[.[] | {n: .number, title: .title, baseSha: .base.sha, mergeable: .mergeable, mergeable_state: .mergeable_state, headRefName: .head.ref, headSha: .head.sha, files: .changed_files, additions: .additions, deletions: .deletions, commits: .commits}]'

HOME=$HOME GH_TOKEN="" gh api 'repos/jleechanorg/claude-commands/branches/main' \
  --jq '{main: .commit.sha, lastCommit: .commit.commit.message, lastCommitDate: .commit.commit.author.date}'
```

If main advanced past the open PRs' bases, reclassify each open PR as:
- **FRESH** — baseSha == main → drive to green directly
- **STALE** — baseSha < main → run Pitfall 2 audit (base audit + content audit)
- **CLEANUP_NEEDED** — auto-opened export PR with files in unwanted categories → Pitfall 10
- **AUTO-MERGED** — `state: closed, mergedAt: <recent>` → already in main, no action
- **CLOSED-UNMERGED** — `state: closed, mergedAt: null` → archive, don't reopen

### Phase 1 — Content audit on each STALE PR (Pitfall 2 + 3)

For each STALE PR, in a fresh clone:

```bash
git clone https://github.com/jleechanorg/claude-commands.git /tmp/<purpose>-audit
cd /tmp/<purpose>-audit
git fetch origin <branch>
git checkout -B audit/<pr-n> origin/<branch>

# Per-file byte identity check (not just name overlap)
python3 <<'PY'
import subprocess, os, time
# ... fetch main's content + branch's content for each file in diff, compare bytes
PY
```

The output is one of:
- **0 truly new files + N outdated files + security-leak files** → supersede
- **<10 truly new files + 0 outdated** → rebase + merge (preserves the unique work)
- **Many new files, all in `.claude/` not in `backup/` etc** → rebase + merge
- **Many new files in unwanted categories (`_archive/`, etc.)** → Pitfall 10 cleanup-PR + script-patch

If supersede, post a detailed audit comment per the Pitfall 8 template.

### Phase 2 — Run fresh /exportcommands (Pitfall 3 + 5)

```bash
cd ~/your-project.com
HOME=$HOME PROJECT_ROOT=$HOME/your-project.com \
  bash $HOME/.claude/commands/exportcommands.sh
```

Capture:
- Branch name (`export-YYYYMMDD-HHMMSS`)
- Commit SHA
- PR number (auto-opened)
- `git secret guard` line (must be clean)
- File count / additions / deletions

### Phase 2.5 — (Optional) Cleanup-PR + script-patch (Pitfall 10)

If the auto-opened PR contains content the user wants excluded:

1. Patch `~/.claude/commands/exportcommands.sh` (Track A) with the 3 exclude additions.
2. Run `bash -n` to confirm syntax + a smoke-test fixture to confirm `find` no longer
   picks up files in the unwanted category.
3. In a fresh worktree, `git rm` the unwanted files, `git restore --source=<MAIN_SHA>` the
   already-on-main files that the script's content filters modified (Track B).
4. `git commit --amend` to fold the restorations into the cleanup commit (or new commit).
5. `git push --force-with-lease origin HEAD:refs/heads/<branch>`.
6. Verify the PR's file list via REST: must show exactly the categories you want.

### Phase 3 — Drive the new PR to green (Pitfall 4 + 7)

```bash
# REST (GraphQL is rate-limited; use REST for state)
HOME=$HOME GH_TOKEN="" gh api "repos/jleechanorg/claude-commands/pulls/<N>" \
  --jq '{mergeable: .mergeable, mergeable_state: .mergeable_state, headSha: .head.sha, baseSha: .base.sha, changed_files: .changed_files, additions: .additions, deletions: .deletions}'

# Bot faux-green check
HOME=$HOME GH_TOKEN="" gh api "repos/jleechanorg/claude-commands/issues/<N>/comments?per_page=10" \
  --jq '[.[] | {login: .user.login, body: .body[:150]}] | map(select(.login | test("coderabbit|cursor|chatgpt-codex"; "i")))'

# Status webhook (often shows success despite no real review)
HOME=$HOME GH_TOKEN="" gh api "repos/jleechanorg/claude-commands/commits/<HEAD_SHA>/status" \
  --jq '{state: .state, contexts: [.statuses[] | {context: .context, state: .state}]}'
```

If bots rate-limited → post a documentation comment per the template in Pitfall 4 (cite
`coderabbit-slow-bot-policy` from SOUL.md, ping `@coderabbitai` to retrigger, set a 2h SLA).

If bots substantive and CHANGES_REQUESTED → fix inline (the export script's content is generated,
not authored, so fixes are usually trivial content adjustments — re-run the script).

If bots substantive and APPROVED → ready to merge.

### Phase 4 — Supersede any STALE PR (Pitfall 8)

Do NOT close the STALE PR before the new fresh-export PR is verified clean. Close order matters:
if you close #324 first and the new export PR turns out to be wrong, you've burned your reference
state. Post the supersession comment, leave the PR open until the new one is green, then close.

### Phase 5 — Final reply (Slack thread + PR description)

Same shape as `drive-pr-to-green` Step 10 — single reply with PR URL, gate-by-gate verdicts, and
the per-PR supersession receipts. Cite each bot's rate-limit timeout in the reply so the user
knows why a "green" PR has no real review. If Phase 2.5 ran, include the script-patch path
(`~/.claude/commands/exportcommands.sh` line ranges + before/after file count) so the user can
see the durable prevention fix.

## References

- `references/sessions-recap.md` — session-by-session audit of what was learned across 2026-07-01, 2026-07-02, 2026-07-06, 2026-07-13 (1st cleanup session)
- `references/cleanup-archetype-recipe.md` — detailed Track A (script-patch) + Track B (PR cleanup) workflow with the 5-file vs 66-file PR case study
- `references/exportcommands-sh-contract.md` — full content-filter + union-merge spec extracted from the live script
- `references/cross-vendor-resync-recipe.md` — Pitfall 11 deep-dive: the three-bug cycle (stale source → REPO_ROOT break → fixture leak) when an exported skill bundles code from a different upstream repo, with verified recipe (Phases A-F)
- `references/routing-eval.jsonl` — `{intent, expected_skill, ambiguous_with?}` fixture for skill resolver routing evals

## Resolver Trigger Entry

For the resolver, the heading line MUST contain the user-typed trigger phrases on the same line as the `##` heading. Add this entry to `~/.hermes/skills/RESOLVER.md` (the canonical resolver graph):

```markdown
## claude-commands-export-superset — consolidate claude-commands PRs, run fresh /exportcommands, cleanup-PR + script-patch to exclude categories, supersede stale PRs, drive to green
triggers: consolidate the open claude-commands PRs, fresh /exportcommands and check the PRs, the export is stale, see what else is needed / what's incremental, supersede #N, /exportcommands from ~/your-project.com, the cmux-goal / ironclad pair isn't on main, the latest commands/skills aren't in jleechanorg/claude-commands, run a fresh export of my claude config, audit the open export PRs, close #N as superseded, remove the archive from the PR and modify /exportcommands to stop exporting it, edit the export to exclude _archive/, stop exporting archive paths, drop the archive from this PR
```

## Skills Index / Discovery

This skill is referenced by / related to:

- `drive-pr-to-green` — general PR-to-green workflow; we use it for the new export PR's Phase 3 (faux-green detection)
- `github-pr-automation-debug` — explains the bot-authoring pattern; useful for the Phase 3 bot rate-limit faux-green check
- `github-pr-workflow` — low-level `gh pr` helpers used throughout Phases 0–4
- `patch-tool-safe-editing` — relevant for the script-patch phase (Pitfall 10 Track A); the union-merge script has 3 surfaces with shared `\( -not -path ... \)` patterns that require unique surrounding context to disambiguate

The class is distinct from those because:
1. The export script's auto-opened PR has **specific union-merge semantics** that other PRs don't (Pitfall 3, 5)
2. The `mergeable_state: dirty` audit is **content-driven** not just branch-driven (Pitfall 2)
3. The bot faux-green pattern shows up **reliably on every auto-opened export PR** (Pitfall 4)
4. Supersession is a **first-class action** in this workflow, unlike other PR workflows
5. Cleanup-PR + script-patch is the 5th archetype for content categories that should never have shipped (Pitfall 10)