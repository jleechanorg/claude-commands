# wrong-target-removal-on-stop-X-from-Y — 2026-07-20 incident

**Phase 0 working class (added in harness-postmortem v0.5.0).** Triggered when the user
says "stop X from Y" or "stop X from giving me Z" and the agent removes the literal
noun X instead of the upstream source that actually produces Y.

## Originating incident

- **Thread:** `C0AJ3SD5C79` / parent `1784344760.053389` ("Lets stop mcp mail from giving these reports")
- **Symptom reported:** Cron EA-sweep brief appearing in user's DM (D0A418NEHHC), the bot
  `U0A4G7LDJ4R` (MCP Agent Mail) replying to threads with self-investigation reports.
- **What the agent did (wrong):** Removed the cron job `clawchief:ea-sweep-hourly`
  (job_id `a790a5b54e61`) because its name literally matched the user's "mcp mail"
  complaint via word-association.
- **What the user actually meant:** Keep the cron. STOP the MCP Agent Mail **agent**
  from passively listening to Slack threads and posting self-reports (the bot
  `U0A4G7LDJ4R` driven by `SLACK_APP_TOKEN=xapp-...`).
- **User feedback (verbatim):** "No keep the job you fucking idiot — I said mcp mail
  agent I don't want it passively listening to my threads."

## Root cause

The agent parsed "stop mcp mail from giving these reports" literally — "mcp mail"
became the noun to remove, "reports" became the symptom to stop. But the named noun
(`clawchief:ea-sweep-hourly` cron, or even MCP Agent Mail server the cron doesn't
depend on) was a downstream consumer; the actual source was a separate agent's
Socket-Mode listener doing MCP ingest → agent reply. The literal parse
mis-identified the target by an order of magnitude.

## Disambiguation recipe (Phase 0 pre-action check)

When the user says "stop X from Y" / "stop X from giving me Z" / "stop X from doing W":

1. **Identify the symptom noun** ("these reports", "that bot", "passively listening",
   "self-reports", "self-investigation"). This is what the user wants to STOP.
2. **Identify the named target X.** Usually a noun that sounds like a consumer
   (a cron, a workflow, a named task).
3. **Trace the data path** from X back to its source:
   - cron → script → MCP server → external API
   - Slack message → Socket-Mode listener → MCP message → agent reply → chat.postMessage
   - repo file → git push → webhook → downstream consumer
4. **Find the originating source** of the symptom noun. Common patterns:
   - "These reports" → a cron output → look for the cron that PRODUCES the output
     (NOT the cron that DELIVERS it).
   - "Passively listening" → a Socket-Mode listener or webhook subscriber → look
     for the service with the inbound API token.
   - "Self-reports" / "self-investigation" → an agent that picks up ingested
     messages and replies → look for the agent's MCP trigger, NOT the consumer cron.
5. **If provenance is unambiguous** (one clear source), fix at the source layer.
6. **If provenance is ambiguous**, surface ONE clarifying question: "I see two
   possible sources for Y — do you mean A (upstream producer) or B (downstream
   consumer)?" DO NOT silently remove the literal noun.

## Wrong-target signals to grep for (in the user's message + recent history)

- "passively listening" — almost always inbound Socket-Mode / webhook
- "self-reports" / "self-investigation" — almost always an agent reply loop
- "these reports" / "these emails" / "these notifications" — almost always a
  producer, not the named consumer
- "that bot" — almost always an agent identity, not the cron that delivered it

If the named target X sounds like a *consumer* (a cron, a delivery channel, a
notification path) and the symptom noun matches an *agent behavior* (passive
listening, self-investigation, bot reply), the target X is almost certainly the
wrong target.

## Correct fix (this incident)

Three-layer fix landed in second-pass session:

1. **Env overlay** `~/mcp_mail/.env.slack-off` with 6 disabling flags
   (`SLACK_ENABLED=false`, `SLACK_SYNC_ENABLED=false`, `SLACK_NOTIFY_ON_MESSAGE=false`,
   `SLACK_NOTIFY_ON_ACK=false`, `SLACK_SLACKBOX_ENABLED=false`, `SLACK_USE_BLOCKS=false`).
2. **Server boot path** `~/mcp_mail/scripts/run_server_with_token.sh` sources the
   overlay BEFORE any other env (including `~/.bashrc` exports) so the
   `SLACK_ENABLED=false` wins.
3. **Launchd plist** `~/Library/LaunchAgents/com.mcp.agent.mail.plist` has NO
   `SLACK_ENABLED` override in `<EnvironmentVariables>`.

Verification (14-gate contract test `~/tests/test_mcp_agent_mail_slack_off.py`):
overlay exists, 6 flags =false, run script sources overlay, plist has no override,
live process env has both flags false, MCP tools/list returns 200.

Companion SOUL.md `## COMMIT: mcp-agent-mail-no-passive-slack-listening` (added
in this session at line 512) hardcodes the trigger phrases ("stop MCP mail
listening", "stop MCP mail from echoing", "stop the bot from replying", "passively
listening") so the next session auto-loads this rule.

Companion skill `~/.hermes/skills/mcp-agent-mail-no-slack-bridge/SKILL.md` is the
canonical reference for the 3-layer fix + verification recipe + re-enable
procedure (operator-explicit `ENABLE MCP MAIL SLACK BRIDGE` only).

## Anti-pattern

**"Removed the named noun X because the user said stop X from Y."** Wrong 95% of
the time. The named noun is usually a downstream display path; the symptom is
upstream. Always trace before removing.

## Cross-references

- `harness-postmortem/SKILL.md` Phase 0 — `wrong-target-removal-on-stop-X-from-Y`
  working class.
- `~/.hermes/skills/mcp-agent-mail-no-slack-bridge/SKILL.md` — the canonical
  reference for the 3-layer fix.
- `~/.hermes/workspace/SOUL.md` — `## COMMIT: mcp-agent-mail-no-passive-slack-listening`
  (line 512) hardcodes trigger phrases.
- `~/tests/test_mcp_agent_mail_slack_off.py` — 14-gate contract test.