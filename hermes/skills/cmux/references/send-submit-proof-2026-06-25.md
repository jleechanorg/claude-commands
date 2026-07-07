# cmux Send → Submit → Proof — The Recurring Failure Mode (2026-06-25)

**Status:** Verified recipe for the single most common cmux steer failure
(class: "forgot to press Enter" / "I told the agent but it didn't get the message").

**Trigger phrases that mean the user is referencing this class:**
- "you always forget to send"
- "did you press send"
- "the agent didn't get it"
- "why isn't the worker doing X"
- "show me proof you sent it"
- "what did the agent actually receive"

**Why this skill reference exists:** the main `cmux/SKILL.md` already documents
the send+enter+verify pattern across multiple sub-patterns ("⚠️ Preflight",
"Idle-agent prompt contamination", "Should I steer now or wait?"). This file
consolidates the **canonical 4-step ritual** with one explicit "this is the #1
recurring failure mode" framing, so the next session doesn't have to dig
through 3 sub-sections to remember the rule.

## The 4-step ritual (NEVER skip a step)

```bash
export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock
# Resolve real socket first; see drift-aware-steer-recipe.md

# STEP 1 — Type the text. Returns OK (socket acceptance ONLY — not proof).
cmux send --workspace workspace:N --surface surface:M "your message"
# Output: "OK surface:M workspace:N"
# ↓ THIS IS NOT PROOF OF SUBMISSION. It only proves the socket accepted the bytes.

# STEP 2 — Press Enter. `cmux send` does NOT auto-press Enter.
cmux send-key --workspace workspace:N --surface surface:M enter
# Output: "OK surface:M workspace:N"

# STEP 3 — Wait 5-15 seconds for the agent to start processing.
sleep 8

# STEP 4 — Verify with churning label (THE ONLY definitive proof).
cmux read-screen --workspace workspace:N --surface surface:M --lines 25
# Look for one of:
#   - "Working (Xs • esc to interrupt)"
#   - "Brewed for Xs"
#   - "Churned for Xm Ys"
#   - "Precipitating… (Xs · thinking)"
#   - "Fixing drift on PR #N… (Xs · ↓ 5.1k tokens)"
# If you see ANY active churning label → SUBMITTED.
# If you see the message text still sitting at the ❯ prompt → NOT submitted,
#   repeat step 2 (or send Escape + clear + re-send shorter).
# If you see "Stopped" / "Done" / nothing → no churn, investigate.
```

**Step 1 alone is wrong ~80% of the time** when an agent is idle at the `❯`
prompt. The user's verbatim frustration from the 2026-06-09 incident was
*"Wait it's still not sent wtf undoing"* — same failure shape that burned
5 sessions since then.

## Why each step exists (don't try to "optimize" them away)

### Step 1 (`send`) — types text, returns `OK`
- `OK surface:M workspace:N` is **socket-acceptance only**, not "agent received."
- The agent may be in any state (idle, churn-running, mid-Edit on another file).
- Text may sit in the input buffer un-submitted forever.
- The cmux skill's "Common mistakes" section in `references/cli-cheatsheet.md`
  documents this explicitly under the `send` row.

### Step 2 (`send-key enter`) — presses Enter to submit
- `cmux send` does NOT auto-press Enter. This is the **#1 documented behavior**
  in `cli-cheatsheet.md` and the most-violated rule.
- Historical breakage (2026-06-09): on some socket builds, `send-key` rejected
  every key with `invalid_params: Unknown key`. Workaround then was to send a
  literal CR (`printf '\r'`) via `cmux send`. **Verified 2026-06-23**: on the
  current `/tmp/cmux-debug-may-18.sock` socket, `send-key enter` works. Always
  try `send-key` first; fall back to the `\r` workaround if it fails.
- If `send-key enter` returns `OK`, that is **also socket-acceptance only**.
  Don't stop here either.

### Step 3 (sleep) — give the agent time to start churning
- 5s is too short for a healthy Claude Code agent to react.
- 8-15s is the sweet spot for a normal agent.
- 30s for one mid-thought on a 50+ minute run.
- 60s if the agent just finished a previous task and is starting a new turn.

### Step 4 (churn label) — the only definitive proof
- An active churning label proves the agent's REPL is processing your message.
- Spinner with "esc to interrupt" + a counter advancing = submitted and running.
- Token counter advancing (`↓ 5.1k tokens`) = even better proof; the model API
  is actively streaming the response.

**Anti-pattern:** "I sent the message and got OK, the agent must have it."
This is the failure mode the user is repeatedly calling out. **OK is not proof.**
**Churn is proof.** Don't claim "I sent it" without step 4 evidence.

## What "stuck" looks like (the steer landed but worker didn't act)

| Symptom | Diagnosis | Fix |
|---|---|---|
| Message text visible at prompt but no churn | Not submitted (step 2 missed) | `send-key enter` again |
| `API Error: Unable to connect to API (ConnectionRefused)` | Worker-side CLI auth problem, not a steer problem | Investigate the worker's API key, not the cmux call |
| `You've hit your session limit · resets <time>` | Claude session rate limit | Wait for reset or open a new surface |
| Worker reverts to a previous task | Worker absorbed but decided your task was out of scope | Re-steer with verification-first framing (see SKILL.md "Should I steer now or wait?") |
| Spinner label frozen at the same time for >5 min | Genuinely stuck | Press Escape, then re-steer or accept the stall |

## The worktree-pointer strategy for long briefs (avoids autocompleter contamination)

**The problem:** when the worker is idle at `❯`, Claude Code's autocompleter
fires on long pastes and injects garbage into the buffer. Symptom: the prompt
buffer ends up with both your text AND trailing hallucinated text like
`also i always need intent classifier started up` (2026-06-23 PR #7848 incident,
816-char paste into idle Opus session, Opus read past it but burned ~12k tokens).

**The fix:** write the long brief to a file in the worktree, then send a SHORT
1-2 line pointer to the file. The agent reads the file with its native
`Read` tool, which is bulletproof.

```bash
# 1. Write the brief to a file in the worker's cwd (or anywhere readable)
cat > $HOME/projects/worktree_X/agy-next-steps.md <<'EOF'
# Tasks for the worker

1. ...
2. ...
3. ...

## Stop conditions
- Report back here when done
- Do NOT merge — human gate only
EOF

# 2. Send a SHORT pointer (1-2 lines, ≤ 200 chars ideally)
cmux send --workspace workspace:N --surface surface:M \
  "Read $HOME/projects/worktree_X/agy-next-steps.md and execute tasks 1-5 in order. Report back when done."

# 3. Press Enter + verify churn
cmux send-key --workspace workspace:N --surface surface:M enter
sleep 8
cmux read-screen --workspace workspace:N --surface surface:M --lines 25
```

**Why this beats a long cmux paste:**
- No autocompleter contamination risk (the file content is read via tool, not pasted)
- Audit trail in the file (anyone can `cat` it later)
- Easy to revise the brief before sending (just edit the file, don't re-paste)
- The cmux send stays short, matching the cmux skill's documented 1-2 line idle-paste rule

**Verified 2026-06-25 (agy worker steer):** wrote `agy-next-steps.md` (3.2KB),
sent 13-word pointer, agent read the file, loaded 4 skills, created a bead,
started task 1 — all confirmed via churning label `Working (1m 37s • esc to interrupt)`.

## Worked transcript (the exact 4-step sequence I used, 2026-06-25)

```
$ cmux --socket /private/tmp/cmux-debug-may-18.sock send \
    --workspace workspace:72 --surface surface:239 \
    "Read $HOME/projects/worktree_misc23423r23r2/agy-next-steps.md and execute tasks 1-5 in order from that file. Report back here when done."
OK surface:239 workspace:72                          # ← step 1: socket acceptance, NOT proof

$ cmux --socket /private/tmp/cmux-debug-may-18.sock send-key \
    --workspace workspace:72 --surface surface:239 enter
OK surface:239 workspace:72                          # ← step 2: socket accepted Enter, NOT proof

$ sleep 8 && cmux --socket /private/tmp/cmux-debug-may-18.sock read-screen \
    --workspace workspace:72 --surface surface:239 --lines 25
... Working (12s • esc to interrupt) ...              # ← step 4: DEFINITIVE PROOF

$ sleep 15 && cmux --socket /private/tmp/cmux-debug-may-18.sock read-screen \
    --workspace workspace:72 --surface surface:239 --lines 30
... Working (41s • esc to interrupt) · 1 background terminal running ... 
                                                       # ← proof of sustained work
```

The agent then continued for another ~1 minute, eventually hitting
`Working (1m 37s • esc to interrupt)` while it owned the work.

## Failure-mode catalogue (so future-you can pattern-match fast)

| Date | Surface | Failure | Fix that worked |
|---|---|---|---|
| 2026-06-09 | workspace:16 surface:140 | `send-key` rejected all keys | `printf '\r'` via `cmux send` |
| 2026-06-19 | workspace:16 surface:23 | First `send` didn't auto-submit | Manual `send-key enter` after the fact |
| 2026-06-20 | workspace:1 surface:1 | Recon only, **no steer sent at all** | (No fix — transcript ended before steer) |
| 2026-06-23 | workspace:28 surface:60 | 816-char paste + autocompleter contamination | Shorter steer; accept ~12k token burn |
| 2026-06-16 | wa-2369 AO spawn | `ao send` "auto-submit" claim doesn't hold for fresh spawns | Explicit `tmux send-keys Enter` |
| 2026-06-25 | workspace:72 surface:239 | None — used the 4-step ritual + worktree-pointer | (This session, the success case) |

## The user's framing — "you always forget to send"

When the user invokes this phrase, they're not complaining about one specific
incident — they're invoking a **class of failure that has burned them 5+ times
in 30 days**. The right response is:

1. **Acknowledge the class**, not just this incident.
2. **Show the 4-step ritual executing** in real-time (so they can see Enter pressed).
3. **Show the churn proof** in the response (`Working (12s • esc to interrupt)`).
4. **Offer to update the cmux skill** with the lesson if a new pitfall emerged.

The skill update is **proactive**, not reactive. The user is testing whether
the agent remembers the lesson. Don't make them remind you.

## Related references

- `references/cli-cheatsheet.md` → "Common mistakes" section: "Assuming
  `cmux send` presses Enter. It does not. Always follow with `cmux send-key enter`."
- `references/drift-aware-steer-recipe.md` → the dual-channel steer (PR comment
  + cmux pointer) for verification-first cases.
- `references/send-key-broken-workarounds.md` → historical `send-key` breakage
  + workaround recipes.
- Main `SKILL.md` → "Idle-agent prompt contamination" sub-pattern (same theme).