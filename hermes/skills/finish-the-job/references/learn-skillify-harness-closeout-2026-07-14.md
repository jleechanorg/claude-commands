# Learn + skillify + harness + /newb closeout pattern (added 2026-07-14)

## Trigger

When the user message contains **two or more of** `/learn`, `/skillify`, `/harness`, `/newb`, "fresh worktree", or "close the loop" in the same turn, they are asking for the **full closeout loop**, not a single action.

Verified trigger from Slack thread C09GRLXF9GR/p1784083166 (2026-07-14, jleechanorg/claude-commands PR #321 → #329 incident):

> "this isnt a clean PR from origin main why do you kee pscrewiing this up? /learn and /skillify and dont we ahvr a fresh worktree skill or instrucitons to use /newb? lets run /harness and then fix it"

The user named FOUR actions in one message. The expected end-state is the user getting back proof that all four landed, not one.

## The four actions in order

1. **`/learn`** — persist the durable lesson.
   - Write `~/.claude/projects/<project-key>/memory/feedback_<date>_<slug>.md`
   - Append to `~/roadmap/learnings-<YYYY-MM>.md`
   - Create + close a bead in `.beads/issues.jsonl` so future agents can discover via `br search`
   - If `~/llm_wiki` is available, write the raw source copy + index entry per `learn` skill

2. **`/skillify`** — capture the reusable workflow.
   - Load `skillify` skill; verify SKILL.md frontmatter + Contract + Phases + Output Format
   - Add 11-item completeness items (tests, scripts, RESOLVER entry, E2E smoke, trigger eval, check-resolvable)
   - If updating an existing umbrella (e.g. `pr-cleanup-replay`), extend with new phase or pitfall; do NOT create a parallel skill
   - If creating a new umbrella, name it at the CLASS level (e.g. "learn-skillify-harness-closeout" NOT "fix-pr-321-2026-07-14")

3. **`/harness`** — mechanical enforcement.
   - Load `harness-engineering` skill (or `agent-harness-engineering` from hermes-imports)
   - Add `## COMMIT: <rule-name>` block to SOUL.md with Trigger/Action/Why/Files
   - Update RESOLVER.md with new trigger phrases on the same line as the `## <skill>` heading
   - Add overlay doc (`docs/agent/<topic>.md`) for the project-local discovery path
   - Add contract test that locks the rule in place

4. **`/newb` / fresh-worktree verify** — confirm clean operation.
   - Load `using-git-worktrees` skill
   - Apply Step 0 (Detect Existing Isolation) + Step 1 (Create Isolated Workspace via `git worktree add -b <branch> origin/main`)
   - Verify the worktree is at `origin/main` HEAD before edits; verify diff vs `origin/main` is the load-bearing change
   - If the user asked "do we have a fresh worktree skill?" — surface the existing skill (`~/.claude/skills/tessl__using-git-worktrees/SKILL.md`) AND its gap (no `## Phase -1` prevention gate for "never push onto a non-owned PR head from inside a worktree")

## Why all four must land

Running only `/learn` captures the lesson in memory but not as a reusable workflow.
Running only `/skillify` captures the workflow but does not persist the incident-class.
Running only `/harness` adds mechanical checks but has no memory anchor explaining WHY.
Running only `/newb` confirms clean state but does not lock in the anti-pattern prevention.

The four together produce a closed loop:
- Memory captures WHAT happened and WHY (lesson)
- Skill captures HOW to do the class of work (workflow)
- Harness captures WHERE the mechanical enforcement lives (rule)
- Worktree verifies the agent operated correctly THIS time (proof)

Next session encountering a similar incident will (a) find the memory entry, (b) load the skill, (c) trip the harness rule, (d) verify against the worktree contract.

## Verified outputs from this session (PR #329 closeout)

| Action | Artifact | Verification |
|---|---|---|
| `/learn` | `~/.claude/projects/-Users-$USER-claude-commands/memory/feedback_2026-07-14_feedback-pr-push-onto-someone-elses-pr-head-pollution.md` (3948 bytes) | `wc -c` |
| `/learn` | `~/roadmap/learnings-2026-07.md` updated (153856 bytes) | `ls -la` |
| `/learn` | Bead `$USER-4a9` created + closed | `br show $USER-4a9 --json` |
| `/skillify` | `pr-cleanup-replay/SKILL.md` Phase -1 added (39 new lines) | `grep -c "Phase -1"` = 1 |
| `/skillify` | `pr-cleanup-replay` RESOLVER entry updated with prevention triggers | `grep "never push onto someone"` |
| `/skillify` | 3 new contract tests added (5 → 8 passing) | `pytest tests/` → 8 passed |
| `/skillify` | `references/gitleaks-pre-push-hook-bypass.md` written | `test -f` |
| `/harness` | `## COMMIT: never-push-onto-someone-elses-pr-head` added to SOUL.md (5 lines) | `grep -c "## COMMIT: never-push"` = 1 |
| `/harness` | Overlay doc `docs/agent/anti-patterns.md` created (2077 bytes) | `ls -la` |
| `/newb` | Clean worktree `cc-sidekick-checkpoint-clean` branched from `origin/main` (`4ca7ca2d5`) | `git rev-parse origin/main` |
| `/newb` | Polluted worktree `cc-pr321-checkpoint` reset to legitimate head `286311a97` | `git reset --hard` + `--force-with-lease` push |
| All four | PR #329 open with 1 commit / 5 files / +427/-691 branched from `origin/main` | `gh api .../pulls/329` |

## Anti-pattern (do not run partial closeout)

The user's 2026-07-14 trigger named FOUR actions. A previous version of this skill (pre-1.4.0) had the agent picking ONE (e.g. just `/skillify` or just `/learn`). The result was:

- Memory captured the lesson in one file but no contract test locked it
- Skill captured the workflow but no SOUL.md `## COMMIT:` enforced it
- Harness rule existed but no memory entry anchored it to the incident class
- Worktree was clean but no RESOLVER entry routed the next session to it

Net: the next session encountering a similar anti-pattern had to re-derive all four artifacts from scratch. The 1.4.0 update embeds this reference so future sessions read it once and execute all four in sequence.

## Tool-load order at session-start

```python
# Parallel fan-out at session-start
delegate_task(context="...", goal="load pr-cleanup-replay skill", toolsets=["file"])
delegate_task(context="...", goal="load skillify skill", toolsets=["file"])
delegate_task(context="...", goal="load learn skill", toolsets=["file"])
delegate_task(context="...", goal="load harness-engineering skill", toolsets=["file"])
delegate_task(context="...", goal="load using-git-worktrees skill", toolsets=["file"])
```

Then sequence: learn → skillify → harness → worktree-verify.