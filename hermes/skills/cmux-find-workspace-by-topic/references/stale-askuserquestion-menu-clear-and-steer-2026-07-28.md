# Stale AskUserQuestion Menu → Clear-and-Steer Recipe (2026-07-28)

## What this is

When a Claude Code worker is sitting at a stale **AskUserQuestion** 4-option blocking menu from a *prior* mission — and the user asks you to steer it to a *new* mission — the prompt is occupied by the menu. You cannot send a new steer until the menu is dismissed. **Pressing Enter without picking a choice DOES dismiss the menu** (Esc also works, and is what Claude Code's UI calls "cancel the question"). Either path lands the agent at an empty `❯` prompt where the steer can be absorbed.

**Verified 2026-07-28, $GITHUB_REPOSITORY PR #8489 (`feat/levelup-lean-auto-apply-v25`):**
- Operator asked to steer w4/s80 toward `/green` + `/er` + `/advice` on PR #8489
- Agent was sitting at a 4-option menu about **PR #8328** (god-mode), which was **already MERGED + green** at `8d5aadec7c` (2026-07-18T05:58:33Z)
- The menu was a stale recap from a prior session — the choices were moot for the new mission
- Pressed `cmux send-key escape` → menu dismissed → empty `❯` prompt → sent verification-first steer → agent absorbed it (`· Doing… 36s · ↓ 230 tokens`)

## When this fires (trigger)

- User asks you to steer a cmux worker to a new goal
- `cmux read-screen` shows a Claude Code AskUserQuestion selector (numbered list 1-4 + "Type something" + "Chat about this" + "Enter to select · ↑/↓ to navigate · Esc to cancel")
- The menu's content references a DIFFERENT PR / context than the user's current ask
- Live GitHub state (verified via `gh pr view` / `gh api`) shows the menu's referenced PR is already MERGED, CLOSED, or otherwise terminal

## The 5-step ritual (extends the 4-step send→submit→proof ritual)

```bash
SOCK=/tmp/cmux-debug-dev-fork.sock       # canonical socket
WS=4                                       # workspace ref (e.g., "bulk: levelup + quicks")
SURF=80                                    # surface ref (the one you want to steer)

# STEP 0 — Read surface to confirm the menu state (NOT the empty ❯ state)
cmux --socket "$SOCK" read-screen \
  --workspace workspace:$WS --surface surface:$SURF --lines 30 \
  | tail -30
# Look for: "Enter to select · ↑/↓ to navigate · Esc to cancel"
# If present → menu is blocking, you cannot steer until it's dismissed.

# STEP 1 — Press Esc to dismiss the menu (does NOT pick a choice)
cmux --socket "$SOCK" send-key \
  --workspace workspace:$WS --surface surface:$SURF escape

# STEP 2 — Wait 2-3 seconds for the agent to process the dismissal
sleep 3

# STEP 3 — Verify the prompt is now empty
cmux --socket "$SOCK" read-screen \
  --workspace workspace:$WS --surface surface:$SURF --lines 10 \
  | tail -10
# Look for: empty `❯` + a "User declined to answer questions" recap line
# If you see the recap but NO menu → safe to send the steer.
# If the menu is still there → Esc didn't take, retry once.

# STEP 4 — Send the verification-first steer (use the worktree-pointer strategy
#          for briefs >200 chars)
cmux --socket "$SOCK" send \
  --workspace workspace:$WS --surface surface:$SURF \
  "<your verification-first steer — see cmux-find-workspace-by-topic SKILL.md
   for the canonical template>"

# STEP 5 — Send Enter + verify churn label (same as the standard 4-step ritual)
cmux --socket "$SOCK" send-key --workspace workspace:$WS --surface surface:$SURF enter
sleep 8
cmux --socket "$SOCK" read-screen \
  --workspace workspace:$WS --surface surface:$SURF --lines 25 \
  | tail -25
# Look for: "Working…", "Doing…", "Forming…", "Cooked for Xs", any active
# churning label + token counter → SUBMITTED.
```

## Verification-first steer recipe (companion)

When the user asks to drive a PR to `/green` / `/er` / `/advice`, and the agent is at a stale menu from a *different* (possibly merged) PR, the steer should:

1. **Acknowledge** the prior work the agent was on ("saw you were triaging PR #X")
2. **State live GitHub state** of the menu's referenced PR (e.g., "PR #X is MERGED + green at SHA Y")
3. **State the user's NEW mission** clearly with verbs ("drive PR #Z to /green + /er + /advice")
4. **List the current CI failures** at HEAD (paste the `gh pr checks` output)
5. **Prescribe the action sequence** (`/green` first, then `/er`, then `/advice`; or whatever the user asked for)
6. **Hold the design contract** intact (cite the governing design doc + bead ID)
7. **DO NOT list**: "want me to apply this?" — that re-creates the menu
8. **DO list**: report-back expectations (green outcome + /er bundle URL + /advice verdict + final SHA)

For >200 char briefs, write to a file in the agent's cwd (e.g., `.cmux-pr<num>-steer-<date>.md`) and send a 1-2 line pointer per the worktree-pointer strategy.

## Why "Esc" and not "Enter"

If you press Enter on an unselected menu, Claude Code picks the first option (default-selected). If the first option is "Stop here — accept current state", you'll have accidentally told the agent to stop. **Esc is the safe choice** because it explicitly cancels the question without picking any option.

Alternative: press the down-arrow keys enough times to highlight the option that matches the user's intent, THEN press Enter. But this requires the operator's intent to map cleanly to one of the 4 options — when the menu is from a different PR entirely, none of the options match. **Esc is canonical** for the stale-menu case.

## Anti-patterns

- ❌ **Don't pick option 1 (or any option) without reading it** — if the menu is from a different PR, the options may not match the user's intent at all. Picking the wrong one creates more work than dismissing.
- ❌ **Don't `cmux send` before Esc** — the new text lands AFTER the menu in the scrollback; the agent's next action still depends on the menu state. The menu will re-block on the next turn anyway.
- ❌ **Don't trust the menu's recap as the agent's current state** — the menu is a static choice list, not the agent's live context. The agent may have moved on; only the empty `❯` (or an active churning label) is the live state.
- ❌ **Don't press `Esc` and immediately verify with `read-screen` at 0s** — Claude Code's menu-dismissal animation takes ~2s. Always `sleep 3` before reading.

## Companion references

- `cmux-find-workspace-by-topic/SKILL.md` — the 4-step send→submit→proof ritual (apply the 5-step variant when a stale menu is present)
- `cmux/SKILL.md` — the parent cmux skill, including the "Should I steer now or wait?" rule
- `finish-the-job` — when the steer IS the user's goal and you need to drive to PR-merged end-state (the verification-first steer IS a Phase 0 + Phase 3 combined action)
