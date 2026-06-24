---
name: advice
description: Token-efficient second opinion slash command /advice. Extracts decision point + artifact (≤150 lines), then fans out in parallel: (1) Opus subagent reviewer with fallback chain codex→agy→cursor, (2) /research on the decision topic, (3) /secondo multi-model opinion. Use instead of advisor() which ships the full conversation uncached.
---

# /advice — Token-Efficient Second Opinion

**Replaces `advisor()`. Never call advisor() — use this instead.**

## When invoked

`/advice [optional: specific question]` — invoked manually or automatically at a decision point.

## Step 1: Extract the artifact

From the current conversation, extract:
- **Decision** (3–5 sentences): what specifically needs a second opinion — be concrete about constraints and tradeoffs
- **Artifact** (≤150 lines): the relevant code, plan, error, diff, or architecture sketch — nothing unrelated

If no specific question was passed, infer from most recent context. If relevant context exceeds 150 lines, summarize the excess into 2–3 sentences prepended before the artifact.

## Step 2: Fan out three reviewers in parallel

Spawn all three in a single message:

---

**Reviewer A — Fallback chain (try in order, stop at first success):**

**A1 — Opus subagent (primary):** Spawn an Agent:
```
You are a senior engineer giving a focused second opinion.

DECISION:
[decision, 3–5 sentences]

ARTIFACT:
[≤150 lines]

Return exactly:
VERDICT: [recommended approach, one line]
REASONING: [3–4 sentences]
RISK: [main risk, one sentence]
CONFIDENCE: [high / medium / low]
```

**A2 — cursor (fallback if A1 errors):**
```bash
cursor agent -p --force "Senior engineer second opinion.\n\nDECISION:\n[decision]\n\nARTIFACT:\n[artifact]\n\nReturn VERDICT, REASONING (3-4 sentences), RISK, CONFIDENCE."
```

**A3 — agy (fallback if A2 errors):**
```bash
agy --print --dangerously-skip-permissions "Senior engineer second opinion.\n\nDECISION:\n[decision]\n\nARTIFACT:\n[artifact]\n\nReturn VERDICT, REASONING (3-4 sentences), RISK, CONFIDENCE."
```
Note: agy is the Antigravity CLI (reads CLAUDE.md on startup like any CC session, but starts fresh — no current conversation history). Independent perspective, slightly slower than cursor.

**A1.1 — `claude -p` (first-class choice when invoked outside Claude Code; fallback if A3 errors):**
```bash
claude -p --dangerously-skip-permissions "Senior engineer second opinion.\n\nDECISION:\n[decision]\n\nARTIFACT:\n[artifact]\n\nReturn VERDICT, REASONING (3-4 sentences), RISK, CONFIDENCE."
```
Note: Same Claude Code context inheritance as agy. For a cleaner isolated call: add `--cwd /tmp`.

If all options fail, note "Reviewer A unavailable" in the synthesis table.

---

**Reviewer B — Research:**

Invoke `/research [decision topic distilled to 6 words]`

---

**Reviewer C — Secondo:**

Invoke `/secondo` with the decision + artifact (same text as Reviewer A).

---

## Step 3: Synthesize

Present:

```
| Reviewer  | Verdict              | Key concern         | Confidence |
|-----------|----------------------|---------------------|------------|
| A (source)| ...                  | ...                 | high/med/low |
| Research  | [consensus finding]  | [main caveat]       | —          |
| Secondo   | ...                  | ...                 | —          |
```

- 2+ agree → state recommended path, proceed
- All three diverge → surface disagreement, ask user which axis matters most (speed / safety / cost)

## Token budget

| Reviewer | Tokens sent |
|---|---|
| Reviewer A | Decision + artifact ≈ 1,500–2,500 tokens |
| /research | Web queries only |
| /secondo | Decision + artifact ≈ 1,500–2,500 tokens |
| **Total** | **~5,000 tokens vs ~80,000–140,000 for advisor()** |

**96–97% fewer input tokens** per review cycle.

## Fallback chain summary

| Priority | CLI | When |
|---|---|---|
| A1 | Claude subagent (Opus) | Primary (inside Claude Code) |
| A1.1 | `claude -p --dangerously-skip-permissions` | First-class choice when invoked outside Claude Code; fallback if A3/agy errors |
| A2 | `cursor agent -p --force` | Opus unavailable |
| A3 | `agy --print --dangerously-skip-permissions` | cursor errors |

Note: codex removed — gpt-4.5 unsupported with ChatGPT account + quota exhausted as of 2026-06-24.
