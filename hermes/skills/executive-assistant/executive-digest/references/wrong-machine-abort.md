# Wrong-Machine Abort — Operator-Scoped Skill

**Added 2026-07-24 after `executive-digest` cron fired on a non-Gonto Hermes host.**

## The trap

`executive-digest` is hard-coded to one operator:

- Workspace path: `~/executive-assistant-skills/`
- Config file: `~/executive-assistant-skills/config/user.json` (operator name, both Gmail addresses, WhatsApp number, Hermes workspace path)
- Required CLIs: `gog`, `mcporter`, `todoist-cli`
- Style/state dir: `{workspace}/style/DIGEST_RULES.md`
- Delivery channel: WhatsApp (with Slack DM to a named Chief of Staff)

A cron / launchd job that says "executive-assistant sweep" or `/exec-digest` can be installed on **any** machine the Hermes agent has access to. Without a preflight gate, the agent's first action is "read `user.json`". If the file doesn't exist, the agent proceeds with whatever fallback it can invent. Result: a fabricated digest posted to an arbitrary channel — or, worse, sent to whatever WhatsApp/email address was hand-typed into a request.

## The correct shape

**Gate FIRST, read SECOND.** The preflight block in `SKILL.md §0` runs four machine checks:

1. `~/executive-assistant-skills/config/user.json` exists
2. Required CLIs on PATH
3. Workspace dir from config exists
4. `style/DIGEST_RULES.md` exists

Each failure returns a distinct exit code (11/12/13/14) so the abort message can name the exact missing piece.

## The honest-skip contract

When the gate fails:

- ✅ Post a status-only abort notice (trigger phrase + which check failed + two remediation paths).
- ✅ Use the configured fallback channel (default `#ai-general`).
- ✅ Update `digest-state.json` `lastRun` so the cron doesn't loop-storm.
- ❌ Do NOT invent a "nothing to report today" digest.
- ❌ Do NOT read `user.json` "just to see what's there" — that path leads to partial reads with broken assumptions.
- ❌ Do NOT call `gog`/`mcporter`/`todoist-cli` against the wrong operator's accounts. (They would either 401 or — worse — succeed against a misconfigured account that was a leftover from another install.)

## Generalizing the pattern

This is the **operator-scoped skill** failure mode. Any skill that hard-codes a specific user's email, phone, workspace, or accounts MUST ship with a preflight gate. Class members:

- `executive-digest` (Gonto, WhatsApp)
- `email-drafting` (Gonto, Gmail accounts m@gon.to / gonto@hypergrowthpartners.com)
- `daily-task-prep` (operator-specific Todoist)
- any skill that reads `~/executive-assistant-skills/config/user.json`

For skill authors: add a §0 preflight to any skill that depends on a non-Hermes operator config. The pattern is:

```bash
test -f "$HOME/<operator-workspace>/config/user.json" \
  || { echo "ABORT: ...not found"; exit 11; }
# ...additional machine checks
```

Then a "wrong-machine abort path" subsection that names the fallback channel and the SILENT-suppression carve-out explicitly.

## References

- SOUL.md `slack-channel-routing-policy` — `#ai-general` is the default fallback for system-initiated messages.
- SOUL.md `proof-before-claim` — don't fabricate a digest to satisfy the cron delivery contract.
- SOUL.md `always-skillify-after-non-trivial-work` — the trigger that should have produced this skill update originally.

## Incident log

| Date | Host | Trigger | Failure | Resolution |
|---|---|---|---|---|
| 2026-07-24 16:01 PT | non-Gonto Hermes | "Executive assistant sweep" cron | Skill missing workspace + config | Posted abort notice to `#ai-general` via xoxp fallback (MCP bot identity returned `not_in_channel`); SKILL.md §0 preflight gate added. |
