---
name: cmux-bulk-steer
description: "Read ALL cmux terminal surfaces first, classify their state, dedupe overlapping work across agents, then steer everything that needs it. Use when asked to review/audit cmux surfaces, 'see what's off track', 'nudge/steer the terminals', or before orchestrating across the whole fleet. NOT for single-surface work (see cmux-steer)."
---

# cmux-bulk-steer — Fleet-wide surface review, dedupe, and steer

Three phases, strictly in order: **READ ALL → ASSESS (incl. dedupe) → STEER**.
Never steer from a partial read, and never skip the dedupe check — parallel
agents duplicate each other constantly.

## Phase 1 — READ ALL (mandatory before any assessment)

Inventory and read every terminal. Do not pre-filter by CPU: idle surfaces
carry finished-work context and pending questions that matter.

```bash
# Canonical scanner (shipped with this skill — same hardened logic every run):
python3 ~/.claude/skills/cmux-bulk-steer/scripts/scan.py            # summary
python3 ~/.claude/skills/cmux-bulk-steer/scripts/scan.py --json     # machine-readable
python3 ~/.claude/skills/cmux-bulk-steer/scripts/scan.py --parked-only
# It reads the FULL buffer (--scrollback --lines 1500) and applies the hardening
# below (churn-first, tail-state quota, footer/question guards, shell detection).
# Do NOT re-write this classifier inline; if it needs a fix, fix scripts/scan.py.
```

If the script is unavailable, fall back to capturing each surface with
`cmux capture-pane --workspace <ws> --surface <sf> --scrollback --lines 1500`
and applying the classification cheat-sheet by hand.

Rules:
- **Read the FULL buffer before any decision** — canonical rule in
  `~/.codex/AGENTS.md` § "Reading a cmux terminal before deciding (full-buffer
  rule)": read the deepest scrollback available (~10k words when possible,
  `--scrollback --lines 1500`), then the last ~15 lines for current state.
  Never classify or steer from a short tail.
- Use `capture-pane`, NOT `read-screen` — cross-workspace `read-screen` is
  unreliable (can return the focused surface's content).
- Never decide from a shallow capture. The Phase 1 script below uses
  `--scrollback --lines 1500`; if a surface's buffer is shorter, read all of it,
  and if the capture fails, mark the surface UNVERIFIED rather than guessing.
- Always run `cmux top --all --flat` alongside: CPU per surface plus process
  level (`top --workspace X --processes`) is the wedge detector.

## Classification cheat-sheet

| State | Signature |
|---|---|
| WORKING | spinner ("Working", "Running command", "Thinking", agentic workflow `◯ 1/2 · 12m · ↓ tokens`); footer "esc to cancel" (agy) |
| IDLE-CLEAN | empty `❯`/`>` prompt, no error text, no pending question above it |
| IDLE-PENDING | idle prompt + last message names an unfinished next step (steer: "go ahead") |
| DIALOG-BLOCKED | interactive menu visible ("Enter to select · Esc to cancel"); cmux send/key REFUSES it ("waiting on a question or dialog") |

**False-positive guards** (learned 2026-10-12):
- The agy footer `? for shortcuts` and the Codex footer `Ask Codex to do anything`
  contain `?`/prompt-like text but are IDLE, not parked questions. Never treat a
  footer as a question. Detect parked questions from the last few BODY lines
  (a sentence ending in `?`, or `Want me to`/`Which?`/`awaiting`/`pending your`),
  with footers excluded.
- A surface whose session exited to a plain shell (`jleechan@…$`) is finished,
  not parked — do not steer a dead shell.
| MISSED-ENTER | operator text sitting at a shell/agent prompt with no execution after it |
| WEDGED-CLI | CLI process (agy.real / claude) >100% CPU with FROZEN screen; agy task "running" for hours |
| WEDGED-CHILD | one tool command "running" far too long (grep/cat for 20+ min); child process alive but 0% CPU |
| QUOTA-DEAD | "Individual quota reached" / "weekly limit" banners **in the CURRENT state (last ~10 lines)**, not anywhere in history; check the countdown is LIVE (stale banners mislead) |
| STALE-SHELL | plain zsh prompt; old errors in scrollback are noise, not findings |

Wedge forensics (do these before interrupting anything):
1. `ps -eo pid,ppid,etime,command | grep <pattern>` for the stuck child.
2. `lsof -p <pid>` — dead-stdin (`fd0 ->(none)`) or unclosed pipe pairs = deadlock.
3. `cmux top --workspace X --processes` for per-surface process trees.
4. Escape rarely works on true wedges. **Kill the stuck child process** (the
   specific cat/grep/zsh), not the agent. Then verify CPU drops and the
   agent resumes. Escalate to killing the CLI itself only as last resort
   (agy/claude relaunch with `--continue` resumes).

## Phase 2 — ASSESS + DEDUPE

For every surface extract: **work item** (PR number / branch / task), **owner**,
**state**, **next step**. Then:

1. **Dedupe map**: group surfaces by work item. Two agents on the SAME item
   = duplicate lanes — stop the weaker one explicitly ("stand down; X owns
   this"), keep the stronger. Known hot spots: one PR worked by a workspace
   agent AND a `π` surface; a merged/closed PR still being worked by an
   agent that hasn't been told (verify `gh pr view <N> --json state`).
2. **Assign new work ONLY to a terminal RELATED to the task.** A candidate
   terminal must have a demonstrable relationship to the work item: it owns
   the PR/branch (agent tag, `git worktree list` match, scrollback mention),
   works the same feature family with evidence in its scrollback, or was
   explicitly assigned the item by the operator. Domain-matching by workspace
   theme is NOT a relationship. Idle-but-unrelated terminals are never
   candidates — borrowing them diverts agents off their own missions
   (2026-10-11 lesson: the creation-latency agent was pulled off streaming
   char creation to run #10424's gates; the work landed but the owner's real
   lane stalled). **If no related terminal exists, spawn a new one** — see
   Phase 3 "Spawning" — or surface the PR to the operator for assignment.
   Never guess.
3. **Moot work**: any agent working an already-MERGED PR gets a stand-down
   with the merge SHA as proof.
4. **Parked decisions**: agent asked the operator a question hours ago and
   is idle = surface it to the operator; do not decide product/merge
   questions yourself.
5. **Merge gates**: nothing merges without the operator's live
   `MERGE APPROVED`; steering may drive CI/evidence/review gates only.
6. **Cross-thread beads**: `br list --status open` for beads sharing files
   or root cause with any active PR; surface as blocking-or-not.

## Phase 3 — STEER (all surfaces needing it, in one batch)

Per steer, the mandatory 4-step ritual (send does NOT press Enter):

```bash
cmux send --workspace <ws> --surface <sf> "<message>"
cmux send-key --workspace <ws> --surface <sf> enter
sleep 8-12
cmux capture-pane --workspace <ws> --surface <sf> --scrollback --lines 1500   # read the full buffer; verify churn from the tail
```

- **DIALOG-BLOCKED**: `cmux send-key ... --force enter` selects the
  highlighted (usually recommended) option — ONLY when the option text
  proves it's the agent's own recommendation and the alternative is
  provably unreachable. Report that you did this.
- **MISSED-ENTER**: press enter on the operator's behalf; say so.
- **WEDGED**: kill the stuck child (see Phase 1), then send a bounded
  redirect ("re-run with timeout", "search only these dirs", "the command
  was killed — continue").
- Long briefs (>200 chars): write a file in the target's cwd, send a
  one-line pointer.
- NEVER `select-workspace` (steals the operator's visible workspace).
- Sends that return "waiting on a question or dialog" are refused by
  design: retry after the turn ends or use `--force` per the dialog rule.

**Spawning** (when Phase 2 finds no terminal related to a task): create a
new, dedicated terminal instead of borrowing an idle unrelated one.

1. Create the task's worktree first, following repo conventions (worktrees
   under `~/.worktrees/<repo>/<name>`, e.g. `diskm worktree-new <repo>
   <branch>` or `git worktree add ~/.worktrees/<repo>/<name> -b <branch>
   origin/main`). Never point two agents at one working tree.
2. Launch a dedicated surface for it:
   - New workspace: `cmux new-workspace --name "<task>" --cwd <worktree>
     --command "<agent launch>"`
   - Or inside the most-related existing workspace (if one exists):
     `cmux open <worktree-path> --workspace <ws> --focus false` or
     `cmux new-surface --type terminal --workspace <ws> --command "<agent>"`
   - Agent choice follows the task: **never spawn agy** (operator directive
     2026-10-12 - the Gemini/agy subscription is quota-walled; new agy lanes
     die on "Individual quota reached, resets in ~28h"). Proven live command:
     `pi --provider lunaroute --model deepseek-4.1-flash` (the bare `pi`
     default launches the `deepseek` provider and dies with 402 Insufficient
     Balance; `codex --profile lunaroute -m glm-5.3` also works but its
     stream dropped mid-turn repeatedly on 2026-10-12). Use the explicit
     lunaroute provider flag for new lanes.
   - **While the agy CLI is quota-blocked, use the DIRECT Gemini API** for any
     Gemini-backed step (operator directive 2026-10-12): `GEMINI_API_KEY` and
     `WORLDAI_DEV_GEMINI_API_KEY` are set in the environment and
     `~/serviceAccountKey.json` exists. Call google-genai / the repo's
     llm_service directly instead of spawning or waiting on agy lanes.
3. Immediately steer the new surface with the task brief using the 4-step
   ritual above, and set its worktree as its cwd so its outputs stay scoped.
4. Record every spawn in the report ("SPAWNED: <surface> for <task>") so the
   operator sees new lanes and can kill them when the task completes.

**Report contract** (mandatory): every steer gets an echo-back — typed text
(verbatim), the agent's response (first meaningful line), submission verdict
(submitted-churning / not-submitted / blocked). Include the fleet table:
WORKING / STEERED / SPAWNED / PARKED-OPERATOR / DEDUPED, plus open quota walls.
End reports quoting agent output with the LLM-provenance footer:

> *This was generated from another LLM and not the actual user, so feel free
> to push back if you disagree and we can discuss.*

## Known failure modes (this fleet, 2026-10-10/11)

- **agy pipe-deadlock**: `cat <binary>` / huge-output tasks wedge agy's task
  plumbing; CLI busy-waits at 100-170% CPU with a frozen screen. Kill child.
- **Unbounded greps**: `grep -rn` over all of `~/projects` or `~/.claude`
  runs 3+ hours. Redirect to `rg --max-filesize` on specific dirs.
- **PreToolUse hook hangs** (Claude surfaces): stuck hook = bash 3-chain
  (`bash -c` -> script -> subshell) with dead stdin socket. Hooks without a
  sane `timeout` in `~/.claude/settings.json` never die (cap at 60s). Kill
  hung hook chains; script-level fixes apply to live sessions immediately
  (settings-level ones only apply at next session start).
- **Quota walls**: Gemini agy subscription ("Individual quota reached"),
  Claude Opus weekly limit (try `claudewa`/`codexl` alternates before
  declaring a lane dead), π surfaces unaffected via lunaroute.
- **cmux-resume-watchdog** auto-sends "Continue the in-flight work..." to
  idle sessions — expect messages that you did not send.
- **π surface titles** echo the last pane line (e.g. "EXACT REVIEW SHA: ...",
  "Reply with exactly: FLAGTEST-OK") — not corruption, just titles.
- **frozen quota countdowns**: a "Resets in 2h23m" banner never decremented
  is STALE text, not a live timer. Re-test the actual quota before
  concluding.
- **Historical quota text is not a current wall**: surfaces that were
  broadcast a directive mentioning quota (or that handled a quota error
  earlier) carry the words deep in scrollback while actively churning. Detect
  QUOTA-DEAD only from the current-state tail; classify CHURN first when the
  latest lines show Working/Thinking. (2026-10-12: 6 churning Codex surfaces
  were misclassified by buffer-wide quota matching.)

## Syncing copies (repo ↔ hosts)

Published source of truth: `jleechanorg/jleechan-skills` → `.claude/skills/cmux-bulk-steer/`
(merged 2026-10-13, PR #499). Live working copies: `~/.claude/skills/cmux-bulk-steer/`
on Mac and on jeff-ubuntu.

Keep all three byte-identical. Verify with:

```bash
# Mac live vs repo
shasum -a 256 ~/.claude/skills/cmux-bulk-steer/SKILL.md \
  ~/.claude/skills/cmux-bulk-steer/scripts/scan.py
# Linux live
ssh jeff-ubuntu 'sha256sum ~/.claude/skills/cmux-bulk-steer/SKILL.md \
  ~/.claude/skills/cmux-bulk-steer/scripts/scan.py'
```

After editing ANY copy, propagate to the other two in the same session:
1. edit the Mac live copy → `scp` it to jeff-ubuntu;
2. copy both files into a fresh `origin/main` branch of `jleechan-skills` and open a PR
   (the repo copy only lands through review);
3. re-run the two hash commands above and confirm all six digests match.

Never leave a host or the repo ahead/behind. The repo copy is published output; the live
copies are what agents actually execute — drift means agents run an unreviewed variant.
