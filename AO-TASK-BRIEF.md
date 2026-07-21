# AO task brief — Fresh `/newb` completion of original claude-commands export work

## User's original words — preserve verbatim

Get all the original work I asked for done fresh from /newb

## Original work reconstructed from Slack

The original Slack root at `C09GRLXF9GR / 1783398704.258559` said:

> Make sure all the other slash commands and skills referenced here are in the Claude-commands repo too https://github.com/jleechanorg/claude-commands/blob/main/.claude/skills/swarm/SKILL.md

Then:

> Also some of this historical stuff or wip future work isn’t useful to the LLM let's cleanup locally and in Claude-commands

Jeffrey ultimately selected **safe subset only**, with the qualification that references may mention `bd` and `br` and say to use whatever the person has. Follow-up:

> Any slash commands referenced in that skill that arent in jleechanorg/claude-commands and lets ensure our local repo matches origin main too

Today Jeffrey clarified the durable end-state: do ALL original work fresh from `/newb`.

## Mandatory execution interpretation

Treat `/newb` as the contract in `/Users/jleechan/.claude/commands/newb.md`: a new isolated branch/worktree rooted at the latest `origin/main`. AO itself creates that fresh worktree; verify its start SHA equals fresh `origin/main` before edits. Do **not** reuse `/Users/jleechan/claude-commands`, which is dirty and on another branch.

Work only in the AO-created worktree. Do not push onto someone else's or a polluted PR head. Before push, run:

```bash
git fetch origin
git log --oneline origin/main..HEAD
git diff --shortstat origin/main...HEAD
git diff --check
git status --short --branch
```

All commits must match this scope and no merge commits / `.beads` drift / archive files may ride along.

## Current live facts (freshly verified 2026-07-14)

- `origin/main`: `4ca7ca2d5cdc425db19348aaefe4b1bd787ccf02` — merge of PR #327.
- Merged: PR #317, #325, #326, #327.
- Open clean PRs based on current main: PR #328 and PR #329.
- Open stale/polluted PRs: PR #323 (stale base `a30c037`, likely related docs) and PR #324 (200 commits, 3002 files, +670119/-24308, base `a30c037`, dirty).
- PR #324's stated load-bearing scope is only four files: thin command+skill pairs for `cmux-goal` and `ironclad`. Do not merge or amend the polluted branch.
- Local changes after current public main include at least today's command/skill state and existing open clean PRs. The goal is a fresh export/reconciliation, not blindly copying every local artifact.
- Bead: `jleechan-g8ca`.

## Required workflow

1. **Fresh-state proof**
   - Verify AO worktree is rooted at latest `origin/main` and save raw output.
   - Audit current open PR topology and author/branch ownership.

2. **Reconstruct and audit the original scope**
   - Read the current `~/.claude/skills/swarm/SKILL.md` and extract every actual slash-command / skill reference using semantic judgment, filtering false positives like model names and path fragments.
   - Check each reference against BOTH local `~/.claude/{commands,skills}` and current public `origin/main` in this repo.
   - Identify truly missing public commands/skills and any local/public byte drift relevant to the original ask.
   - Preserve the earlier safe cleanup outcome: remove stale non-actionable provenance/run IDs/SHAs only where that was the explicitly selected safe subset; allow `bd`/`br` language that tells users to use whichever their project has.

3. **Consolidate all still-load-bearing work cleanly**
   - Include the genuinely net-new intended contents of open clean PRs #328 and #329 if not already represented by a fresh authoritative export from local current state.
   - Salvage only the four load-bearing `cmux-goal` / `ironclad` files from polluted PR #324 if current local authoritative copies are still desired and not already on main.
   - Audit stale PR #323 against current local authoritative sidekick/swarm/team docs. Preserve only still-valid behavior; do not import stale contradictions or history.
   - Run the canonical `/exportcommands` pipeline if appropriate, but do not honor its old interactive confirmation gate: Jeffrey explicitly approved execution with this message. The authoritative export skill is `claude-commands-export-superset`; follow its archive exclusions and leak checks.
   - Create either one clean consolidated PR or a small set of clean, non-overlapping PRs when independent scopes require it. Prefer one clean fresh export PR if reviewability remains good. Every branch must be based on latest `origin/main`.

4. **Verification**
   - Run all repository contract tests relevant to exported commands/skills.
   - Add or update a focused contract test proving all actual references from swarm resolve in the repo and preventing future broken-reference drift. Do not use a brittle slash-token regex that misclassifies `/haiku` or path fragments.
   - Verify no `_archive`, backup, secret, `.beads` history drift, or unrelated files are included.
   - Run `/advice` Round 2 using an explicit **mid-tier Sonnet/Codex-Spark** reviewer lane after first push. Apply all substantive findings and re-run tests.
   - Drive each replacement PR to N-green: CI pass, mergeable, CodeRabbit APPROVED or documented real rate-limit exception, Bugbot zero errors, all substantive comments resolved; Evidence/Skeptic only if applicable to this docs/config repo.

5. **Supersession and final state**
   - Only after the replacement PR is pushed and verified remotely, post evidence comments and close obsolete/polluted PRs #323/#324/#328/#329 as superseded when their load-bearing content is fully represented. Do not close any PR whose unique work is not yet durably represented.
   - Update bead `jleechan-g8ca` with PR URL(s), pushed SHA(s), and exact status.
   - Final report must state one end-state, give full PR/commit URLs, exact gate status, fresh-base proof, diff scope, tests, `/advice` verdict, and any remaining human merge blocker.

## Model routing and worker constraints

Use the configured standard implementation model, not a top-tier model. Any reviewer/subagent spawn must explicitly set model tier: mini/haiku for mechanical audits; mid-tier Sonnet/Codex-Spark for implementation review and `/advice`; top tier only after a cheaper tier demonstrably fails, with the failure stated.

## Push requirement (mandatory)

After making and committing, run `git push origin <branch>` and only then stop. If you cannot push in the same session, leave a local commit ready and report exact commands. Verify `git rev-parse origin/<branch>` equals the pushed SHA. Open/update the GitHub PR before reporting completion. Do not stop at a local commit, plan, or diagnostic.
