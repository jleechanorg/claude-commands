---
name: cmux-goal
description: Set Claude Code's builtin /goal for yourself (the running session) via the cmux socket CLI — types the /goal command into your own composer so the Stop hook + purple UI indicator activate. Use when the user asks you to set your own goal, when /ironclad step 3 needs the builtin set, or when a mission should be Stop-hook-enforced without asking the user to type it.
---

> **Terminal-reading rule (canonical):** before any classification, assessment, or steer of a
> cmux surface, read the surface's FULL available history (~10k words when possible;
> `cmux capture-pane --scrollback --lines 1500`), then the last ~15 lines for current state.
> Never decide from a short tail. Canonical text: `~/.codex/AGENTS.md` section
> "Reading a cmux terminal before deciding (full-buffer rule)".

> **No workspace selection (mandatory):** never run `cmux select-workspace`, `workspace.select`, `workspace-action --action focus`, or any command that selects/focuses/switches a workspace or surface — it steals the operator's active window. Read headless with `cmux capture-pane --workspace <ws> --surface <sf> --scrollback --lines <n>`; never `cmux read-screen` for a targeted read (it returns the focused surface's content, so it cannot read a named surface — the 2026-10-18 measurement recorded below did show it does not change the selection, but it still cannot target). `cmux send`/`send-key --workspace <ws> --surface <sf>` is allowed and must not select.

> **Headless only (measured, 2026-10-18; evidence `/tmp/spicy-search/cmux/focus-test.md`):** `capture-pane` / `read-screen` / `cmux send`+`send-key` / `surface.send_text` were measured NOT to change the operator's selected workspace; always pass `--focus false` to `new-surface`/`new-workspace`; never `select-workspace`/`focus`; do not create/close workspaces/surfaces on the live desktop without asking. Canonical rule: `~/.claude/skills/cmux-steer/SKILL.md` § "Headless only".

## ⚠️ Submit Discipline (MANDATORY — read this before every cmux steer)

`cmux send` does **NOT** press Enter. This is the #1 recurring cmux failure mode
(verified 2026-07-16: user explicitly flagged "you always forget to send" after the
fable iOS pivot bootstrap). The submit ritual below is a hard contract for every
send to a cmux surface. Skip ANY step and the message sits in the input buffer
without ever reaching the agent.

**Supersedes the 4-step form (measured 2026-10-20).** The 2026-07-16 **4-step**
ritual (type → `send-key enter` → wait → verify) is now counted as a **3-step**
ritual below: the measured preferred send folds typing and Enter into one action
(`cmux send … && cmux send-key … enter`, or a socket `surface.send_text` whose
`text` ends in the literal `\n`). Both forms still work — a standalone
`send-key enter` is never wrong — but the ritual is counted as three steps because
type+Enter is one measured action. Canonical owner of the ritual and of the general
newline rule: `~/.claude/skills/cmux-steer/SKILL.md` § "The submit ritual" and
§ "`cmux send` newline rule".

### The submit ritual — 3 steps (supersedes the 2026-07-16 4-step ritual)

```bash
# STEP 1 — Type + Enter as ONE action. `&&` chain is the preferred CLI form;
#          the socket form needs a LITERAL trailing \n (type + Enter in one call).
cmux send --workspace workspace:N --surface surface:M "/goal <single-line condition>" \
  && cmux send-key --workspace workspace:N --surface surface:M enter
# Socket equivalent (only when the CLI is unavailable):
#   printf '{"method":"surface.send_text","params":{"surface_id":"<uuid>","text":"/goal <cond>\\n"}}\n' | nc -U -w 3 "${CMUX_SOCKET_PATH:-$HOME/.local/state/cmux/cmux.sock}"
# `OK surface:M` / `ok:true` only prove socket acceptance, NOT submission.

# STEP 2 — Wait 5-15 seconds for the agent to start processing.
sleep 8

# STEP 3 — Verify with churning label (THE ONLY definitive proof).
cmux capture-pane --workspace workspace:N --surface surface:M --lines 25
# Look for one of:
#   - "Working (Xs • esc to interrupt)"
#   - "Forming… (Xs · thinking)"
#   - "Precipitating… (Xs · ↓ tokens)"
#   - "Brewed / Churned / Cooked for Xm"
# If you see ANY active churning label → SUBMITTED.
# If the text is still sitting at the ❯ prompt → NOT submitted: apply
#   "Repair, never re-type" below (one bare Enter, re-capture). Never re-send the text.
# If "Stopped" / "Done" / nothing → no churn, investigate.
```

### NEWLINE TRAP — the dominant failure of this skill (measured 2026-10-20)

Operator-caught twice on 2026-10-20 (the `lvl up` notice at 10:04 AM and the
`world` `/goal` at 12:10 PM). A `/goal` typed with a **real newline** anywhere
before the end — a multi-line condition, an interpolated multi-line `$VAR`, a
heredoc, or `$(cat file)` output whose file ends in `\n` — leaves the text parked
in the composer with **the cursor resting on a blank line beneath it**, and it
never submits. That blank-line-with-cursor signature is the tell.

Rules that make this reliable: the condition MUST be one line (no literal
newlines, no heredoc, no `$(cat …)`); keep the `/goal` line under ~180 characters
and push the overflow into the bead; never wrap it in `$( … )` whose output
carries trailing whitespace. General owner for every cmux send, not just `/goal`:
`~/.claude/skills/cmux-steer/SKILL.md` § "`cmux send` newline rule".

### Repair, never re-type (measured 2026-10-20)

If a capture still shows the `/goal` text at the `❯` composer, or shows the
blank-line-with-cursor signature, send **one** `cmux send-key --surface "$SURFACE" enter`
and re-capture. Do not resend the text — a second send concatenates a duplicate
`/goal` line into the same buffer.

### Success criterion (measured 2026-10-20, Claude Code)

The composer footer shows `◎ /goal active (Nm)` — or the harness prints `Goal set: …`.
An empty composer, a socket `ok:true`, or a churning label left over from a previous
turn is NOT proof. Then capture the target surface's full history and tail; if it is
generating, wait until idle and capture again (text typed during generation can sit
in the composer). Send, wait 5–15 s, capture, and apply the criterion above. Text
disappearing, socket `ok:true`, an earlier turn's churning label, or the send call
returning are not confirmation.

### ⚠️ Output Contract — typed text + terminal response (MANDATORY)

Every reply that reports a `cmux send` action MUST include, in the same reply:

1. **The exact text that was typed** — verbatim copy of the string passed to `cmux send`.
2. **The cmux terminal response** — verbatim transcript of what `cmux capture-pane` returned AFTER the `cmux send-key enter` settle window
   (typically 5-15s). Specifically, the agent's first action after absorption.
3. **Submission status** — explicit verdict: "submitted (churning label X)",
   "not submitted (text still at ❯ prompt)", or "blocked (no churn, retried N times)".

**Treat as not working until we see a response.** A reply that does NOT include
both the typed text AND a terminal response is invalid evidence that the
steer landed. The operator cannot distinguish a successful send from a failed
send that left text in the input buffer.

Canonical contract + echo-back template: `~/.hermes/skills/cmux/references/output-contract-mandatory.md`.

### ⚠️ LLM-Provenance Caveat (MANDATORY footer)

Every reply that quotes cmux output, terminal text, or agent actions produced
by another LLM (the worker agent OR the assistant's own synthesis of agent
output) MUST end with this verbatim footer:

> *This was generated from another LLM and not the actual user, so feel free
> to push back if you disagree and we can discuss.*

Full caveat rules + scope: `~/.hermes/skills/cmux/references/output-contract-mandatory.md` § "LLM-Provenance Caveat".

### Echo-back proof (MANDATORY)

Every cmux steering action MUST be followed by an **echo-back proof** in the same
turn or the immediate next turn to your operator (Slack thread, terminal reply,
or whichever channel triggered the steer). The proof MUST follow the template
in `~/.hermes/skills/cmux/references/output-contract-mandatory.md` and include
the typed text + terminal response + submission status, not just the
churning label.

> ◀ sent to surface:55 (LEFT/claudec) at <HH:MM:SS PT> — typed: "<first 80 chars>";
> response: "<first 80 chars of the churning label or first agent line>"; status:
> submitted (churning label "Forming… 9s · ↓ 4.9k tokens").

**Banned** (these are the failure modes the user keeps flagging):
- "I sent the message" (no Enter proof)
- "The agent should have received it" (no churning label)
- `cmux send` with no follow-up `cmux send-key enter` (or the literal `\n` socket form)
- A real newline in the send argument — it parks the text in the composer (2026-10-20)
- Re-sending text after a non-submit instead of one bare `send-key enter`
- Focusing or selecting a surface to send; always target with explicit `--workspace`/`--surface`

### Worktree-pointer strategy for long briefs

For task briefs >200 chars (e.g. orchestrating iOS app pivot, multi-PR review),
do NOT paste the full text into the input. Write the brief to a file in the
agent's cwd (e.g. `.cmux-<task>-brief.md`) and send a 1-2 line pointer. This
avoids the autocompleter contamination pitfall where shell-style tokens inside
long text trigger tab completion mid-stream. For `/goal` specifically, the
one-line condition rule above still applies — the pointer technique covers the
overflow, not the submitted line.

### Canonical reference

Full recipe + edge cases + the 2026-06-25 worked example live at:
`~/.hermes/skills/cmux/references/send-submit-proof-2026-06-25.md`

This rule was added 2026-07-16 after the fable iOS pivot bootstrap surfaced
"you always forget to send" / "make sure you press submit and the work starts
on the cmux input" (Slack ts 1784185650.528089). Apply it uniformly to every
cmux-touching skill.

# cmux-goal — set the builtin /goal for yourself

**Why this exists:** Claude Code's builtin `/goal <condition>` installs a session-scoped Stop hook (keeps the model working until the condition holds) and lights the purple goal indicator — but builtins are processed only from the composer, and the model has no direct tool for them. When the session runs inside cmux, the socket CLI can type into the session's OWN composer, so the model can set its own goal. Runtime native goal tools are preferred whenever available in the active environment; verify persisted state directly. The cmux composer socket typing mechanism is a fallback for Claude Code sessions where native tool support is unavailable. Proven live 2026-07-12 (DK2D mission; user: "I wanted you to use the builtin goal and set it yourself").

## Procedure

**Step 0 — Context pass, ALWAYS FIRST, unconditional (user directive 2026-07-19, re-affirmed 2026-07-21 after this step was skipped despite existing in prose form).** Before anything else — before even checking cmux hosting — run BOTH, invoked as their own Skill calls (not folded into later prose you might skim past):
   - `/ms <goal keywords>` (memory_search) — memories often hold measured contracts, prior exit criteria, and known traps for exactly this goal.
   - `/history <goal keywords>` — prior attempts, their failure modes, and what's already in flight.
   This applies EVERY time `/cmux-goal` is invoked, even standalone with no other context — the whole point is that invoking this skill alone is enough to ground the goal in real prior work. Do not skip this because you believe you already "have context" from the current conversation; other sessions/machines may hold relevant state this one doesn't.

1. **Query existing goal and choose mechanism:** Query whether an active goal already exists (e.g. inspect runtime goal state or check `/goal active`) before attempting to install one. If an existing goal matches the intended objective, continue execution without replacement (never clear or replace an existing goal without an explicit user request). If a different goal is active, preserve it unless the user explicitly authorizes replacement or has explicitly cleared it. If a new goal is needed, wait until Step 2 has hardened the condition, then choose the mechanism for the active environment: use the runtime's native goal API/tool directly when one is available (for example Codex `create_goal`), rather than printing a `/goal` line or asking the user to paste it. Only when no native goal mechanism is available should Claude Code confirm cmux hosting with `cmux identify` (which must return a `caller` block with `surface_ref`). If `cmux` is missing or has no caller block, prepare the exact `/goal ...` command as the final fallback. Goal setup failure does not halt an already-authorized mission or claim an active goal; report the warning and continue authorized execution.
2. **Compose the condition.** ALWAYS invoke the `ironclad` skill to harden exit criteria — binary, executable, externally anchored (prefer an EXISTING checker/script/gate as the anchor when one exists), anti-gaming, iterate-until; the bead carries the full criteria superset — the builtin gets the short literal condition. Fold in anything concrete Step 0 surfaced (prior traps, measured contracts, in-flight work on other machines). Keep it short (the UI truncates); avoid shell-hostile characters; single-quote it. **The condition must also be ONE LINE** (see "NEWLINE TRAP") — under ~180 characters, with any overflow pushed into the bead.
   - **CI-check criteria must not silently mean "poll forever."** If any criterion depends on a remote CI system ("zero failing checks", "N-green", "gate passes"), state in the condition (or the bead) that a slow/backlogged/flaky CI run does NOT block progress by itself: per `~/.claude/CLAUDE.md` § "Slow/backlogged CI runners — run locally + post proof, don't just wait", when a check is stuck 10min+ past its normal runtime, run the equivalent test locally instead of re-polling, and treat a real local pass (with command + output + timestamp + git SHA, explicitly labeled "local run — CI still pending") as satisfying that sub-criterion until CI catches up. Repo-specific local-run invocation contracts live in `~/.claude/skills/testing-infrastructure/SKILL.md` — read it for the exact command shape (don't guess). This prevents the goal from trapping the session in an unbounded retry/poll loop against a shared, externally-contended resource (see `~/.claude/skills/ironclad/SKILL.md` § "Verify the structural precondition BEFORE the first grind" — CI capacity is exactly this class of external producer/blocker).
3. **Create goal once (if needed):** If an existing matching goal was confirmed in Step 1, continue without recreation or replacement. If creating a new goal and the active environment provides a native goal tool, invoke that native tool once with the hardened condition and retain its returned goal identifier/objective for verification. Do not substitute a printed `/goal` command when the native tool is callable. For Claude Code fallback via cmux composer socket typing, type + Enter as ONE measured action (preferred form, no escaping surface, no UUID resolution):
   ```bash
   SURFACE=surface:<N>
   cmux send --surface "$SURFACE" "/goal <single-line condition>" \
     && cmux send-key --surface "$SURFACE" enter
   ```
   Raw socket fallback only when the CLI is unavailable — the `\n` must be the literal two-character escape, never a real newline:
   ```bash
   SURFACE_UUID=$(cmux identify --id-format uuids | python3 -c "import json,sys; print(json.load(sys.stdin)['caller']['surface_id'])")
   SOCK="${CMUX_SOCKET_PATH:-$HOME/.local/state/cmux/cmux.sock}"
   printf '{"method":"surface.send_text","params":{"surface_id":"%s","text":"/goal <condition text>\\n"}}\n' "$SURFACE_UUID" | nc -U -w 3 "$SOCK"
   ```
   **Submission is a separate gate from typing** — apply § "The submit ritual", § "NEWLINE TRAP", and § "Repair, never re-type" above; the general rule is owned by `~/.claude/skills/cmux-steer/SKILL.md` § "`cmux send` newline rule".
4. **Verify persisted query, not tool-layer:** verify persisted state directly. For a native goal tool, query the runtime again and confirm the goal is active and its objective matches the hardened condition (not merely that the tool returned successfully). For cmux, require harness confirmation such as "Goal set: ..." / "A session-scoped Stop hook is now active", or the measured composer footer `◎ /goal active (Nm)`; `OK surface:N` is only the tool layer. If no confirmation arrives via cmux, check whether another prompt was mid-flight (your text may have appended to it) and retry once — one bare `send-key enter` first, per "Repair, never re-type". If setup still does not succeed, proceed with the authorized mission without halting; do not falsely claim an active goal.
5. Acknowledge briefly and keep working — the goal-exit-criteria UserPromptSubmit hook (if installed) auto-injects ironclad hardening on top.

## Cautions

- `/goal clear` / `/goal active` are also typeable this way, but **never clear or replace an existing goal** without an explicit user request.
- Setup failure does not halt an authorized mission: if goal installation fails, do not stop work or claim an active goal; log the setup failure and continue authorized execution.
- Sending text mid-generation appends to the composer; prefer sending while otherwise idle at the end of your turn.
- Works for any builtin in principle; scope this skill to /goal — self-typing other builtins needs its own justification.
- Related: `ironclad` skill (criteria hardening), `~/.claude/hooks/goal-exit-criteria.sh` (hardening hook), memory `reference_builtin_goal_exit_criteria_hook`.
