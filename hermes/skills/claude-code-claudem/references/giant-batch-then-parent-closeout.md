# Giant-batch-then-parent-closeout — wave-of-subagents → parent finishes mechanical

> **When this pattern fires:** A parent session dispatches **≥3 subagents in parallel** via `delegate_task` whose deliverable is a complete PR (or set of PRs) — file authoring + commit + push + PR open. The wave's individual subagents will hit the 600s runtime timeout during the mechanical closeout (file authoring is fast; commit + push + PR open is slow because each `cd` + `git add` + `git commit` + `git push` + `gh pr create` is a separate tool call). The compiled report arrives with `status=timeout` for every subagent even when 90% of the work landed.

## The pattern

1. **For each subagent in the wave, prompt it to commit + push + open PR in its final turns.** Workers that time out before committing leave diffs as untracked / un-staged files in the worktree — the parent session has to inspect and finish.
2. **When the wave consolidated result arrives with `status=timeout` for every task, do NOT re-dispatch.** Re-dispatch wastes another 600s re-doing the file work. The worktree edits are already there; the next worker will re-analyze the same files and burn another 600s. The parent session's closeout is faster AND avoids losing the worker's well-formed partial output.
3. **Inspect the diff state.** Run in the parent session (parallel terminal calls are fine):
   ```bash
   # For each subagent's worktree:
   git -C <wt> status -sb
   git -C <wt> log --oneline -5
   git -C <wt> ls-files --others --exclude-standard
   git -C <wt> diff --stat origin/main..HEAD
   ```
   - If `git status` shows untracked files + modified files + no new commit → the worker did the work but ran out of turns before commit. Parent finishes: `git add <files>` → `git commit -m "<subject>"` → `git push origin HEAD:refs/heads/<branch>` → `gh pr create …`.
   - If the worker DID commit + push → you're verifying, not closing out.
4. **Run focused tests in the parent session** after each PR push — this is the cheaper verification path than dispatching a "verify" subagent. The existing venv at `$HOME/projects/your-project.com/venv/bin/python` has every dep including `jsonschema`; `PYTHONPATH=.` is required because the worktree's `$PROJECT_ROOT/` is not on sys.path by default.
5. **Post the per-blocker reply comment on the PR** in the parent session — workers don't have permission to post to the user's Slack thread via MCP, but the parent session does. Use `gh pr comment <num> --repo <owner/repo> --body "<reply>"` (background process) — works without MCP.

## Live proof (2026-07-28)

5-subagent wave to ship a PR-A (generic shared contracts + AI mystery/internal-drive arcs) + PR #8661 (Spellblade fixes). 3 of 5 subagents timed out at 600s. `git status` on each worktree showed:

- **PR-A worktree** (`/private/tmp/wt-shared-contracts`): 6 shared contracts untracked + 3 Python files modified + AGENTS.md modified. Parent finished AGENTS.md rule + test file + commit + push + open PR.
- **PR #8661 worktree** (`/private/tmp/spellblade-prompts`): 1 new commit already pushed (`88f1665eb89`), 59 tests pass. Parent posted the per-blocker reply comment at `https://github.com/$GITHUB_REPOSITORY/pull/8661#issuecomment-5111586764`.
- **MBTI wiki** (`~/llm_wiki/wiki/`): 16 concept pages + 1 index + 16 raw HTML files (parent fetched the raw/ files since the worker skipped that step). Parent fixed the source-path reference from `sources/articles/mbti/` to `raw/articles/mbti/` across all 17 wiki files.

## Anti-patterns

- **Re-dispatching the timed-out subagent with a larger budget.** The worktree edits are already there; the next worker will re-analyze the same files and burn another 600s. The parent session's closeout is faster AND avoids losing the worker's well-formed partial output.
- **Waiting for the consolidated `delegate_task` result and reporting "all timed out, nothing done."** That's the wrong verdict. The work is mostly done; the closeout is the missing 10%.
- **Trying to merge the partial commits in this turn.** Don't merge — the commit is on a feature branch, parent session finishes the push, then `/green` + `/advice` + `/er` run separately.

## Sizing `--max-turns` for subagents in this pattern

Each subagent gets `--max-turns 20` for file authoring + 1 final commit + push attempt. The parent session absorbs the closeout. If the worker hasn't committed by turn 18, dispatch the parent closeout early rather than waiting for the 600s timeout.

`--max-turns` budget per worker shape:

| Worker shape | Recommended `--max-turns` |
|---|---|
| Single file authoring + commit + push | 15 |
| Multi-file authoring (3-8 files) + commit + push | 20 |
| Multi-file authoring + Python wiring + tests + commit + push | 30 |
| Multi-PR work (touch 2 worktrees) | 35 |

Each `Bash` tool call ≈ 1 turn. Each `git commit` + `git push` + `gh pr create` is 3 turns. Workers that need to read N files before writing N files burn the budget on reads — instruct them to write from the spec/brief without re-reading source files unless the spec is ambiguous.

## When the parent session's closeout also gets stuck

- If the parent session's `git commit` fails because the message exceeds the author limit or contains a disallowed character, retry with `git commit -m "short title" -m "longer body in second -m"`.
- If `git push` is blocked by branch protection on the PR branch, report the exact error and let the user unblock.
- If `gh pr create` fails because the branch already has a PR (e.g. the worker DID push before timing out), report the existing PR URL and let the parent session drive green/advice/er on it.
- If the parent session itself runs out of context window mid-closeout, stop and report the files-modified state with `git status` + `git diff --stat` — the next session can pick up the closeout.

## Why this beats re-dispatch

Two reasons:

1. **Latency.** Re-dispatch costs 600s of worker time + ~30s of parent overhead = ~10.5 min. Parent closeout after the wave is ~60s of inspection + the remaining mechanical steps. For a 5-subagent wave, parent closeout saves ~50 min total.
2. **Correctness.** The worker that timed out had the right context in its head (the brief, the file paths, the test names). Re-dispatch burns that context on re-orientation. The parent session already has the spec from the user's original message and the closeout is mechanical.
