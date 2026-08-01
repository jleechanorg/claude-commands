# Sessions Recap — claude-commands-export-superset

This is the cumulative cross-session learning log that backs the parent SKILL.md. Each entry is a
real session where the workflow ran and a new pitfall emerged.

## Session 20260701_132226_9e44cc1d — "Export commands superset audit"

**Task:** "Run /exportcommands and lets ensure it does the superset of ~/.claude/ and your-project.com commands skill etc"

**Outcome:** Audited the export script's union-merge behavior; identified that `~/.claude/commands/exportcommands.sh` (466 lines) did NOT include `~/.hermes/{skills,commands}` — only `CLAUDE_DIRS=(commands skills hooks agents scripts)` and `ROOT_DIRS=(orchestration automation ralph)`. The hermes surface was an undocumented gap.

**Lesson that became Pitfall 3:** the live hermes-aware version lives in `your-project.com/.claude/commands/exportcommands.sh`, not in `~/.claude/commands/`. Future sessions must run from WA.

## Session 20260702_123042_e1667fed — "PR Export Status Update"

**Task:** "Did this work? Do we have a /green PR and reviewed by /advice for export?"

**Outcome:** Identified that PR #8135 (in $GITHUB_REPOSITORY, NOT jleechanorg/claude-commands) was the hermes-superset PR. Pushed live, CI in flight, awaiting CodeRabbit + Bugbot + Skeptic. **Did NOT** actually merge — left local commit on `agento/export-superset-hermes` branch. Set up a 20m cron `4a40893d6256` to check status.

**Lesson that became Pitfall 1:** always re-check state — when the cron fired, #8135 had moved to CHANGES_REQUESTED (CodeRabbit flagged nits), and PR #325/#326 didn't exist yet. Iterated inline to fix the nits.

## Session 20260702_123356_c6348166 — "/meta skill define"

**Task (adjacent, not directly this workflow):** "Let's define a skill called /meta..." → created `harness-postmortem` skill for fixing agent behavior failures. Not directly part of the export workflow but consumed by it — agents that fail to drive-to-green on export PRs now have a meta-skill to fix their behavior.

## Session 20260706_123359_ab6c8817 — "Exportcommands Supersets Verification"

**Task:** "Run /exportcommands from the your-project.com repo and confirm it does superset of .claude in the repo and ~/.claude/ and does hermes skills/commands as welll and confirm it has /launchd"

**Outcome:** Confirmed PR #8135 was MERGED on 2026-07-04 23:57:52 UTC. Identified that a follow-up PR #319 (`export-curated-20260707-055543`) had been auto-created but CLOSED not merged. The /launchd surface was incidental (shipped via generic glob, not as a named surface).

**Lesson that became a memory:** the public `jleechanorg/claude-commands:main` HEAD now has a stream of merged work but **no merged export PR after #8135 was merged on the WA side**. Public repo is stale w.r.t. user's current local `~/.claude/`.

## Session 20260713_22:50_XXXX — "Export / supersede / fresh export"

**Task:** "lets consolidate the PRs into one claude-commands PR and /green and get /advice to approve and fix any serious issues fullrun"

**Outcome:**
- Verified that #325 and #326 had been MERGED by the user 8 min before the task started (mid-task pivot). Original consolidation plan was obsolete.
- PR #324 was on a stale base (`a30c037`, 3 days old); rebase audit revealed 0 truly-new files + 183 outdated files + 8+ `backup/` security-leak files.
- Posted supersession comment #4963569181 on #324 (the "Pitfall 8 template" used here).
- Ran fresh `/exportcommands` from `~/your-project.com` → PR #327 (`export-20260713-155353`, 66 files, +7,436/−19).
- Discovered bot rate-limit faux-green: CodeRabbit + Cursor Bugbot + Codex connector all posted "rate limit reached" comments while status webhooks showed `success`.
- Documented the rate-limit timeout per `coderabbit-slow-bot-policy` (Pitfall 4 recipe).

**Net learnings distilled into Pitfalls 1–9 of the parent SKILL.md (v1.0.0).**

## Session 20260713_23:30_XXXX — "Remove archive from PR + patch exportcommands"

**Task:** "lets remove the archive from the PR and modify /exportcommands to stop exporting it"

**Outcome:**
- PR #327 was open with 66 files, 61 of which were `_archive/_removed-*` + `_archive/{loose-md,_archived_loose_md}/` content the user did NOT want shipped.
- Track A: patched `~/.claude/commands/exportcommands.sh` with 3 exclude additions (global find, project find, root-dir rsync). Verified with `bash -n` and a fixture-based find smoke test (1 file kept / 3 expected — archive paths correctly filtered at both top-level and nested levels).
- Track B: cloned branch in fresh worktree, `git rm -rf` 61 archive files, `git restore --source=<MAIN_SHA> --staged --worktree --` 4 files that had been content-modified by the export's `perl -pi -e` filters (restoring them to main's exact bytes), `git commit --amend --no-edit` to fold the restorations into the cleanup commit, `git push --force-with-lease origin HEAD:refs/heads/export-20260713-155353`.
- Final PR: 5 files (the actual incremental: `/harness --optimize`, `/slackbots`, `/social` draft-only, plus the 2 backing skills). `+119 / −11`. `git secret guard` clean. CodeRabbit SUCCESS on new HEAD `afe98ef`. Mergeable clean. Zero inline review comments.
- Posted follow-up PR comment summarizing the cleanup + script patch.

**Pitfalls discovered that became Pitfall 10 (5th archetype: cleanup-PR + script-patch):**
- The export script has zero exclude logic for content categories — `_archive/`, `_archive/_removed-*/`, `_archived_loose_md/` etc all get shipped.
- Patching `exportcommands.sh` needs 3 separate exclude surfaces (global find, project find, root-dir rsync). The find clauses share enough string overlap that `patch` tool requires unique surrounding context.
- The cleanup-PR workflow has a non-obvious trap: 4 of the 61 "archive" files were content-modified by the export's filters — `git rm` of those would delete files that already exist on main. Must use `git restore --source=<MAIN_SHA>` (NOT `git checkout HEAD~1 --`) to keep main's exact bytes.
- Byte-identity verification via `git hash-object --stdin` is mandatory before committing; trailing-newline mismatches silently change content.
- `git commit --amend --no-edit` is the right tool to fold restorations into the cleanup commit.
- `git push --force-with-lease` (vs `--force`) is the safe pattern for force-pushing personal branches.
- Posting a follow-up PR comment after cleanup is durable record + may retrigger CodeRabbit review (bot rate limit window shifts between pushes).

**This session promoted Pitfall 10 from "implied" to "explicit" in the parent SKILL.md (v1.1.0).**

## Cross-session invariants (won't change without explicit user approval)

1. The export target is `jleechanorg/claude-commands` (per `target_repo` constant in the script).
2. The branch naming is `export-YYYYMMDD-HHMMSS` (local PT timezone).
3. The export superset is `~/.claude/{commands,skills,hooks,agents,scripts}` + `~/.hermes/{skills,commands}` + project's `.claude/{...}` + repo-root `{orchestration,automation,ralph}` + a sample of `workflows/`.
4. The script auto-pushes + auto-opens the PR; the agent's job is to drive the auto-opened PR to green and supersede any STALE prior PRs.
5. Content filters strip `$GITHUB_REPOSITORY` → `$GITHUB_REPOSITORY`, `your-project.com` → `your-project.com`, etc. — specific patterns before general (otherwise general would consume specific).
6. `git secret guard` runs in-script as the ONLY security pre-check.

## Cross-session anti-patterns (do not repeat)

1. **Plan-before-state-recheck.** A previous session built a 3-PR consolidation plan that was obsolete 60s after the user pivot. Always re-run `gh pr list` + `gh api branches/main` after every user message.
2. **File-list audit instead of byte-identity audit.** Counting file names that "exist in both" tells you nothing — you must compare actual bytes. A 200-file PR with all-empty SHA256=empty files would pass a file-list audit and fail a byte-identity audit.
3. **Assuming "mergeable_state: clean" means "the PR is mergeable."** It means the merge-button is enabled — not that the bots have reviewed. Bot reviews come through `pulls/<N>/reviews` (an empty array = no real review).
4. **Trusting bot status webhooks without checking bodies.** CodeRabbit posts `state: success` even when its body says "Review limit reached." Always fetch the comment body and grep for the telltale phrases.
5. **Closing the STALE PR before the new fresh-export PR is verified clean.** Always post the supersession comment, leave STALE open, close only after the new one is green.
6. **NEW: `git rm` of files that already exist on main.** The export's content filters may modify files that main already has by ~30 bytes (trailing newline, etc.). Removing those wholesale will delete them from main on merge. Use `git restore --source=<MAIN_SHA>` to keep main's exact bytes.
7. **NEW: `git checkout HEAD~1 -- <file>` as a "restore to before cleanup."** This restores the export-PR's pre-cleanup version, not main's original. Only `git restore --source=<MAIN_SHA>` ensures zero net diff vs main.
8. **NEW: trusting `git diff` byte counts on a `git restore`.** Restored files show as `+0 / -N` in the diff because the bytes are identical — but the file still appears in the PR's file list. Always verify the PR's `changed_files` count via REST after the force-push.
9. **NEW: `bash -n` as the only verification of a script patch.** Sufficient for syntax; insufficient for semantic correctness. Run a real `find` against a fixture with the unwanted category present, confirm only the expected files come through.
10. **NEW: bare `git push --force` on a personal branch.** Use `--force-with-lease` — refuses the push if the remote has been updated by anyone else since your last fetch. Free safety net.