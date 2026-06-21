---
description: Switch the main thread to the Fable (latest Claude) model with strict token-economy discipline. Heavily use Haiku/Sonnet subagents; reserve the main model for hardest reasoning only.
type: workflow
execution_mode: immediate
---

# /fable

## Purpose

Activate the **Fable** mode for the current session:

1. **Main thread = Fable (latest Claude).** Use it only for the hardest reasoning: novel architecture, root-cause analysis, ZFC / RCF / leveling reviews, cross-PR synthesis, multi-step planning, anything where the prompt is "figure out what to do."
2. **Subagent defaults = Haiku-first, Sonnet for implementation.** Reserve Fable-quality reasoning for the main thread and the small set of subagent roles that genuinely need it.
3. **Token economy is a first-class constraint.** Goal: best outcomes AND best $/token. A 3× cheaper model that produces equivalent output is the right tool.

This command is a session-level contract. Once invoked, the rules below apply to every subsequent turn in the session.

## What /fable does NOT do

- Does not change `~/.claude/settings.json` or any persistent config. It is a session-mode declaration, not a config edit.
- Does not auto-spawn subagents. Subagent use follows the routing table below; you still decide when to spawn.
- Does not bypass safety or rigor. Fail-closed, /es, /green, evidence standards are all still required — they are CHEAPER to follow than to skip.

## The 3-tier routing table (apply per-call)

| Task shape | Subagent / tier | Rationale |
|---|---|---|
| Read-only Grep / Glob / Read / LS on a single file | **Haiku** | Pattern matching; 3× cheaper, comparable quality |
| Multi-file read-only synthesis (e.g., `/ms`, `/perp`, /e sweeps) | **Haiku + JSON schema** | Schema-forcing makes Haiku output reliable for aggregation |
| Single targeted Edit / Write (the obvious fix) | **Sonnet** | Implementation needs moderate judgment |
| Multi-file refactor, pair-coder, test writing | **Sonnet** | Pair-coder's full-context role |
| Subagent that must reason about novel bugs or design | **Fable (escalate)** | Only escalate when Haiku/Sonnet demonstrably fail |
| **Adversarial review, root-cause-first, ZFC / leveling, architecture pivot, cross-PR synthesis, multi-step planning** | **Fable (MAIN THREAD)** | "Figure out what to do" territory — this is where main-model reasoning pays for itself |

**Rule of thumb:** if you can write the agent's prompt as "do exactly X to file Y" → Haiku or Sonnet. If the prompt is "figure out what to do" → Fable.

## Token-economy rules (apply to ALL tiers)

1. **No re-reading files you've already read in this session.** The harness tracks file state.
2. **No re-running /ms, /history, /e sweeps that already ran.** Cache the result inline; reference by ID.
3. **Use offset/limit on Read for large files.** Default `$PROJECT_ROOT/world_logic.py` (421KB) → always Grep-first, never Read-whole.
4. **Bead lookups via `br` CLI only.** Never read `.beads/issues.jsonl` directly.
5. **Parallel independent work in a single message.** Sequential execution of independent work is a performance anti-pattern.
6. **Prefer `Grep` tool over `grep` in Bash.** Save Bash for OS-level operations.
7. **When context grows, compact proactively.** The session can summarize; do not let it thrash.

## Failure modes to avoid

- **Haiku hallucination on nuanced prompts.** If a Haiku agent returns output that doesn't match the expected schema or seems off, escalate to Sonnet. Do NOT accept low-quality output just to save tokens.
- **Sonnet pair-coder over-extension.** Pair-coder/verifier roles benefit from the full Sonnet context window. Do not use Haiku for those.
- **Fable overuse.** If you find yourself writing Fable-quality prompts for trivial edits, you are burning tokens. Step down to Sonnet/Haiku.
- **Subagent result-dumping.** A subagent's final message IS the return value. Do not re-summarize it in the main thread unless the synthesis itself is the deliverable.

## When /fable is the wrong choice

- **Single-file typo fix.** Just Edit it. No mode switch needed.
- **Pure conversation / clarification.** Stay on whatever model is active; /fable is overkill.
- **A session that needs persistent main-model reasoning throughout.** If 80% of the session is "figure out" prompts, /fable is correct. If only 20% is, consider /sonnet or default instead.

## Cross-references

- Skill: `~/.claude/skills/parallel-subagents/` (when to fan out)
- Skill: `~/.claude/skills/zero-framework-cognition/SKILL.md` (the "hardest stuff" that Fable is reserved for)
- Skill: `~/.claude/skills/root-cause-first/SKILL.md` (RCF = Fable territory)
- Hook: `~/.claude/hooks/rtk.sh` (token-savings on shell commands; always-on, not /fable-specific)
- Global policy: `~/.claude/CLAUDE.md` (large file discipline, parallel subagents, bead lookup rules)

## Invocation

User types `/fable` (with or without arguments). Response is:

```
Genesis Coder, Prime Mover,

[/fable active] Main thread = Fable. Subagents = Haiku-first, Sonnet for implementation. Fable reserved for: novel architecture, RCF, ZFC/leveling, cross-PR synthesis, multi-step planning. Token economy rules in effect. No re-reads, no re-sweeps, no file-whole reads, parallel-where-independent.

<resume prior work or begin new task>
```

If `$ARGUMENTS` follows `/fable`, treat them as the task to begin.
