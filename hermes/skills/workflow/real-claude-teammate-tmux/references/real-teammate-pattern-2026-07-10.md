# Real teammate pattern — incident + fix transcript (2026-07-10)

## User signal (verbatim)

> Seems like /team-claude and /sidekick dont always start the real claude team
> invesitgate and use /advice to help inviestgate and /advice to sign off on a
> /rg solution where we truly do fresh repro and confirm fixed using tmux and
> just use sonnet models with claude code

(Same thread: C09GRLXF9GR, ts 1783707269.197099.)

## Root cause (verified)

`$HOME/.claude/commands/team-claude.md` and the `sidekick` skill at
`~/.claude/skills/sidekick/SKILL.md` had drifted into **pseudo-agent docs**:

- `team-claude.md` documented `Agent(subagent_type="claude-pair-coder", ...)`,
  `claude-pair-coder` / `claude-pair-verifier` subagent types, haiku scout
  lanes, `team_name=...`, and even asserted "no `TeamCreate` / `TaskCreate` /
  `TaskUpdate` / `SendMessage` exist in the Claude Code harness".
- `sidekick/SKILL.md` still referenced `TaskCreate`, `TaskList`, `TaskUpdate`,
  `SendMessage`, and `Agent` tool. The sidekick model was the literal
  string `claude-3-5-sonnet` (ages out when the CLI default rotates).
- Neither file mentioned the **real** Claude Code teammate primitive:
  `claude --model sonnet --teammate-mode tmux`.
- `/sidekick fable ...` was a documented (wrong) launch path.

Net effect: when invoked, both commands prompted Claude to call an `Agent(...)`
API shape that doesn't resolve to real teammates. Claude narrated a "team"
without starting any. Haiku scout lanes violated the user's "Sonnet only"
constraint even when a team did nominally start.

## Fix shape (what shipped in PR #321)

Repo: `jleechanorg/claude-commands`
Branch: `fix/real-claude-team-tmux`
PR: https://github.com/jleechanorg/claude-commands/pull/321
Commit: `286311a974ac3b4149ca39b16e33fe9d065910d1`
Live files mirrored: `~/.claude/commands/team-claude.md`,
`~/.claude/commands/sidekick.md`, `~/.claude/skills/sidekick/SKILL.md`.

### Changed files

| File | Change |
|---|---|
| `.claude/commands/team-claude.md` | Rewrote to require real `tmux new-session` launches running `claude --model sonnet --teammate-mode tmux`. Removed `claude-pair-coder` / `claude-pair-verifier` / haiku scout lanes / `team_name` / `TaskCreate` / `Agent(...)`. Added the four-check verification recipe and "Sonnet-only" hard rule. |
| `.claude/commands/sidekick.md` | Usage now Sonnet-only real tmux Claude Code sidekick. Dropped `/sidekick fable ...`. |
| `.claude/skills/sidekick/SKILL.md` | Spawn procedure rewritten to use STATE.md + `sidekick.prompt.md` + `tmux new-session` running `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p ...`. Removed `TaskCreate` / `TaskList` / `TaskUpdate` / `SendMessage` / `Agent` / `run_in_background` / `claude-3-5-sonnet` / `fable sidekick` references. |
| `tests/test_real_claude_team_contract.py` | NEW regression contract test. Asserts required real command is present AND forbidden pseudo-primitive strings are absent. |

## RED → GREEN proof (transcript)

```text
RED (before fix, fresh worktree at origin/main):
$ python3 -m pytest tests/test_real_claude_team_contract.py -q
FFF [100%]
FAILED ... test_team_claude_uses_real_tmux_claude_code_sonnet_only
  AssertionError: assert 'claude --model sonnet --teammate-mode tmux' in '...'
FAILED ... test_sidekick_uses_real_tmux_claude_code_and_keeps_state_file
  AssertionError: assert 'claude --model sonnet --teammate-mode tmux' in '...'

GREEN (after fix):
$ python3 -m pytest tests/test_real_claude_team_contract.py -q
... [100%]
3 passed in 0.14s
```

## Real tmux smoke (independent verification)

```text
$ tmux new-session -d -s rg-real-claude-team-proof-$$ \
  "cd $HOME/.hermes/state/worktrees/claude-commands && \
   claude --model sonnet --teammate-mode tmux \
   -p 'Reply exactly: real-claude-team-proof-ok' --max-turns 1; \
   rc=\$?; printf '\n[smoke exit=%s]\n' \"\$rc\"; exec bash"
$ tmux ls | grep '^rg-real-claude-team-proof-'
rg-real-claude-team-proof-13546: 1 windows (created Fri Jul 10 11:34:36 2026)
$ tmux capture-pane -t rg-real-claude-team-proof-13546 -p -S -80 | tail -8
real-claude-team-proof-ok
$ tmux kill-session -t rg-real-claude-team-proof-13546
```

The smoke proves the documented primitive (`claude --model sonnet
--teammate-mode tmux`) is the primitive that actually works on this machine,
not a fictional API.

## `/advice` Reviewer A sign-off (read-only fan-out)

```text
VERDICT: SIGN-OFF APPROVED
REASONING: All 7 CHECKS_REVIEWED passed:
  1. Static contract: 3/3 pytest green
  2. Forbidden-token grep: 0 hits in production files
  3. RED→GREEN regression: stash → 2 failed → stash pop → 3 passed
  4. Real tmux smoke (independent re-run): reviewer-a-confirmed captured
  5. /rg alias chain: rg → redgreen → Phase 1 RED + Phase 3 GREEN verified
  6. Diff inspection: all pseudo primitives removed, replaced with
     `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions`
  7. Environment: tmux 3.6a + claude 2.1.197 both installed
BLOCKERS: None
```

## Forbidden token list (audit pattern)

The contract test asserts the production files contain **none** of:

```text
TaskCreate  TaskList  TaskUpdate  SendMessage  TeamCreate
claude-pair-coder  claude-pair-verifier
model="haiku"  Agent(  team_name=  claude-3-5-sonnet  fable sidekick
```

And **all** of:

```text
claude --model sonnet --teammate-mode tmux
tmux new-session
tmux capture-pane
Sonnet-only
```

(The "Sonnet-only" string is the visible-name contract; the
`claude --model sonnet --teammate-mode tmux` command is the executable
contract.)

## Environment at the time

- `claude 2.1.197 (Claude Code)` — installed via `~/.local/bin/claude`
- `tmux 3.6a` — installed via `/opt/homebrew/bin/tmux`
- `claude auth status --text`: `Login method: Claude Max account` /
  `Email: $USER@gmail.com`
- Python 3.13.7 + pytest 9.0.3 (no project venv configured; used the
  orch-venv already on PATH)
- Working repo worktree:
  `~/.hermes/state/worktrees/claude-commands` (jleechanorg/claude-commands,
  origin/main at `d84faae2a684d4a8c09b40d26b3c6fa322c4fae9` after the
  branch was created)

## Things to copy verbatim into the next teammate-recipe fix

1. **Regression contract test skeleton** (in
   `templates/regression_contract_test.py`): a pytest that reads each
   production file as a string, asserts the real command is present, and
   asserts a forbidden-token list is absent. NO mocks, NO monkeypatching.
2. **The four-check verification recipe** (above): session + pane +
   capture + process. All four must pass before claiming "started".
3. **The `exec bash` tail** in the tmux wrapper. Without it the pane
   closes and you lose the launch evidence.
4. **The `/rg` + `/advice` sign-off workflow**: RED test on a fresh
   worktree at origin/main, then fix, then GREEN, then real tmux smoke,
   then forbidden grep, then `/advice` Reviewer A, then push + PR.
5. **Mirror the live `~/.claude/...` files** immediately after the PR
   opens. `jleechanorg/claude-commands` PRs land in
   `~/.hermes/state/worktrees/claude-commands/.claude/...` but the user's
   local slash-command resolution reads from `~/.claude/...`. Manual
   `cp -p` until install path catches up.

## What NOT to do (anti-patterns observed)

- **Don't trust the docs to be real.** The old `/team-claude` docs
  read like orchestration but were fiction. Always `git grep` for
  `Agent(` and `claude-pair-coder` first.
- **Don't skip the real tmux smoke.** A contract test that only checks
  strings can pass on docs that are correct in *language* but wrong in
  *execution*. Pair the contract with a real launch.
- **Don't add `--fallback-model` without asking.** The user explicitly
  pinned Sonnet. A silent fallback defeats the pin.
- **Don't conflate `--teammate-mode tmux` with `--tmux` (worktree
  flag).** `--tmux` is for creating a tmux session for a *worktree*.
  `--teammate-mode tmux` is for displaying *agent teammates* in tmux
  panes. They are independent flags. We use both: `--tmux` for the
  worktree (when applicable) and `--teammate-mode tmux` for the
  teammate display.
- **Don't hard-code `claude-3-5-sonnet` in the production docs.** Use
  `--model sonnet` (latest alias). The fixed string ages out.
