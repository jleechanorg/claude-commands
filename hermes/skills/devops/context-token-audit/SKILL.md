---
name: context-token-audit
description: Read and report token usage stats from Hermes gateway logs. Use when asked "how many tokens", "token breakdown", "context size", "what's using my context", or any question about token/component breakdown in the current session or across recent sessions.
---

# Context Token Audit

Read actual token usage from Hermes gateway logs to report precise breakdown of context components.

## Log Location

```
~/.hermes_prod/logs/gateway.log
```

## Relevant Log Pattern

The gateway logs token stats with this format:
```
⏱️  Elapsed: 0.21s  Context: 4 msgs, ~14,339 tokens
```

Also contains per-message headers when sending to the LLM API:
```
DEBUG anthropic._base_client: Request options: ...'content': None, 'json_data': {'max_tokens': 131072, 'messages': [...]
```

## How to Read Tokens

### Single Session Token Count

```bash
grep -E "^   ⏱" ~/.hermes_prod/logs/gateway.log | tail -10 | grep -oE "Context: [0-9]+ msgs, ~[0-9,]+ tokens"
```

Returns most recent sessions with msg count and token estimate.

### Historical Token Distribution

```bash
grep -E "^   ⏱" ~/.hermes_prod/logs/gateway.log | awk '{print $NF}' | sed 's/[^0-9]//g' | sort -n | uniq -c | sort -rn | head -20
```

### Per-Session Range

```bash
grep -E "^   ⏱" ~/.hermes_prod/logs/gateway.log | grep -oE "[0-9]+ msgs, ~[0-9,]+ tokens" | sort -t: -k3 -rn | head -20
```

## Estimated Context Composition (for reporting)

When reporting token breakdown, use these known proportions from analysis:

| Component | Approx % | Notes |
|---|---|---|
| Tool definitions | ~45% | 35 tools with full JSON schemas |
| System prompt framework | ~18% | Fixed instruction structure |
| SOUL.md + AGENTS.md | ~25-27% | Combined policy files |
| Skills list (metadata only) | ~6% | 130+ entries, names + descriptions |
| Session context + profiles | ~4% | Slack thread, user profile, memory |
| TOOLS.md | <1% | Local setup notes |

**Note:** Skill content (`SKILL.md` files) loads on-demand via `skill_view()`, not pre-loaded. Only the skill metadata (name + description) is in the baseline context.

## Reporting Format

When asked "what's in my context" or "token breakdown":

1. Run the gateway log grep commands above
2. Report the observed token count for current session
3. Explain the composition using the estimated percentages above
4. Highlight which component dominates (usually tool definitions at ~45%)

## Caveats to State

- The `~NN,NNN tokens` figure is an **estimate** from the gateway, not the model's own count
- Actual tokenization varies by provider/model (GLM vs Claude vs GPT)
- The breakdown percentages are from analysis, not measured per-component
- Full file contents (SOUL.md, AGENTS.md) are only partially visible in the initial context load — the gateway may truncate large files