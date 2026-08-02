# Stale `.agent_prompt_<branch>.txt` Worktree Recovery (2026-07-30)

## The class

`git worktree add <path> -b <branch> origin/main` does **not** give you a
clean slate when the parent directory has prior Hermes-agent state from
unrelated sessions. Claude Code's runtime detects the
`.agent_prompt_<other-branch>.txt` marker left by a prior session and
binds the new worker's CWD + prompt identity to that old string, NOT
the new worktree.

## Verified worked example: gemini-flash-vs-luna-compare task (2026-07-30)

- Intended: `git worktree add /tmp/gemini-luna-compare -b feat/gemini-flash-vs-luna-compare origin/main`
- Actual: the worker initialized `/private/tmp/gemini-luna-compare-new/`
  instead. The `/tmp/gemini-luna-compare/` dir had `worker_brief.md`
  but **zero evidence files** — the worker was working out of a
  different worktree, one polluted with a stale
  `.agent_prompt_pr-2162-gemini-3-upgrade..txt` from a prior session.

## Detection (mandatory after every `git worktree add`)

```bash
ls -la <intended-path>/        # MUST show real evidence files
ls -la /private/tmp/ | grep <topic>   # look for sister dirs the worker may have created
cat <worktree>/.agent_prompt_*.txt 2>/dev/null | head -3   # check whose prompt it actually loaded
```

If the worker created `.agent_prompt_<old-branch>.txt` in a DIFFERENT
path than the one you intended, the worker rebound to the old prompt
and is working in the wrong worktree.

## Fix — two recipes

### Recipe A: pre-create worktree, then explicitly point the worker

Before `git worktree add`, clean the parent dir:

```bash
rm -f .agent_prompt_*.txt
git worktree add <path> -b <branch> origin/main
```

### Recipe B: parent finishes the report from the worktree state directly

If the worker already burned `--max-turns` writing to the wrong
worktree, **don't re-dispatch.** The parent session reads
`<wrong-worktree>/evidence/` directly and writes the
`comparison_report.md` itself. Verified on 2026-07-30: parent wrote a
165-line comparison_report.md with all 6 verdict rows from
`/private/tmp/gemini-luna-compare-new/evidence/` in one turn, no
re-dispatch. (Combined with the v1.8.1 "research+reproduction" sizing
table — `--max-turns 50` is too small for 6 evidence rows + API
probes + report; budget 60-80.)

### Recipe C: use a path that's unlikely to collide

`/private/tmp/wt-<topic>` is the canonical safe path on macOS because
`.agent_prompt_*.txt` files don't get cross-linked from `/tmp/`
sessions. Avoid `/tmp/<topic>` as the primary worktree path on
multi-session days; use it only for scratch + brief files.

## Anti-pattern

Trusting `git worktree add <path>` to give you a clean slate when the
parent dir has prior session state. Same failure class as session
`20260722_155550_273bd3e1` (3rd sibling, "Stale prompt artefact in
worktree" / `SESSION_INCOMPLETE_HANDLE`).
