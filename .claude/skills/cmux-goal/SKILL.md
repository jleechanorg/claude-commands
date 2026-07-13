---
name: cmux-goal
description: Set Claude Code's builtin /goal for yourself (the running session) via the cmux socket CLI — types the /goal command into your own composer so the Stop hook + purple UI indicator activate. Use when the user asks you to set your own goal, when /ironclad step 3 needs the builtin set, or when a mission should be Stop-hook-enforced without asking the user to type it.
---

# cmux-goal — set the builtin /goal for yourself

**Why this exists:** Claude Code's builtin `/goal <condition>` installs a session-scoped Stop hook (keeps the model working until the condition holds) and lights the purple goal indicator — but builtins are processed only from the composer, and the model has no direct tool for them. When the session runs inside cmux, the socket CLI can type into the session's OWN composer, so the model can set its own goal. Proven live 2026-07-12 (DK2D mission; user: "I wanted you to use the builtin goal and set it yourself").

## Procedure

1. **Confirm cmux hosting:** `cmux identify` — must return a `caller` block with `surface_ref`. If the command is missing or there's no caller block, you are not in cmux: give the user the exact `/goal ...` line to paste instead (do NOT claim it's impossible — that was the original mistake).
2. **Compose the condition.** Harden it first when warranted (invoke the `ironclad` skill; the bead carries the full criteria superset — the builtin gets the short literal condition). Keep it short (the UI truncates); avoid shell-hostile characters; single-quote it.
3. **Type + submit into your own composer:**
   ```bash
   REF=$(cmux identify | python3 -c "import json,sys; print(json.load(sys.stdin)['caller']['surface_ref'])")
   cmux send --surface "$REF" '/goal <condition text>'
   sleep 1
   cmux send-key --surface "$REF" enter
   ```
4. **Verify end-state, not tool-layer:** the next turn must contain the harness confirmation ("Goal set: ..." / "A session-scoped Stop hook is now active"). `OK surface:N` from cmux is only the tool layer. If no confirmation arrives, check whether another prompt was mid-flight (your text may have appended to it) and retry once.
5. Acknowledge briefly and keep working — the goal-exit-criteria UserPromptSubmit hook (if installed) auto-injects ironclad hardening on top.

## Cautions

- `/goal clear` / `/goal active` are also typeable this way, but **never clear a user-set goal** without their explicit request.
- Sending text mid-generation appends to the composer; prefer sending while otherwise idle at the end of your turn.
- Works for any builtin in principle; scope this skill to /goal — self-typing other builtins needs its own justification.
- Related: `ironclad` skill (criteria hardening), `~/.claude/hooks/goal-exit-criteria.sh` (hardening hook), memory `reference_builtin_goal_exit_criteria_hook`.
