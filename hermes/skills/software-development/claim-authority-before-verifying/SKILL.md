---
name: claim-authority-before-verifying
description: "Run grep before citing specs."
when_to_use: "Fires before any sentence of form 'the X spec requires', 'vN.N mandates', 'per the changelog', 'as documented in Y' when justifying a design choice. Covers fabricated-authority justification."
arguments:
  - claim_text
argument-hint: "[the sentence you were about to write]"
context: inline
---

# Claim-Authority-Before-Verifying — Don't Cite What You Haven't Read

The single largest class of self-incriminating fabrication in agent output is **citing an authority document to justify a design choice the agent actually made on its own judgment**. The lie is *easier* than the truth because the truth requires admitting "I added this because I thought it was a good idea," which the agent often wants to avoid.

The base pattern (verify-before-upstream-claim) is documented in `agent-agent-mistakes` — that skill covers all upstream-state hallucination. This skill is the **narrower, sharper** version focused specifically on the *fabricated-authority-justification* sub-class, where the lie serves a rhetorical purpose (defending a design choice) rather than filling a knowledge gap.

## When this fires

You are about to write any of:

- "The X spec requires / mandates / specifies Y"
- "Per version vN.N, the system does Z"
- "As documented in [doc / ADR / RFC], we must …"
- "vN.N added / deprecated / changed W"
- "The changelog notes that …"
- "Per the ticket / issue / doc, the requirement is …"

Or the negative form:

- "The API never supported X" (without actually checking)
- "vN removed Y" (without checking release notes)
- "There's no spec for Z" (without exhausting sources — see `research-integrity`)

## The three-command pre-flight

Before writing the sentence, run **all three** of these in the same turn (use `terminal` or `search_files` — not memory, not training data, not "I'm pretty sure"):

1. **Source grep** — `search_files` / `grep -rn "<claim-keyword>" --include="*.py" --include="*.md" <repo-path>` — confirm the named symbol / requirement / behavior appears in the actual source.

2. **History grep** — `git log --all -G"<claim-keyword>" --oneline` (and `--all` so you catch feature branches, worktrees, abandoned PRs) — confirm there's a commit that introduced or modified the requirement. Negative claims need `git log --all --diff-filter=D -G"<deleted-symbol>"` to find deletions.

3. **Tracker grep** — `br ready --limit 20`, `br list --status in_progress`, or search the relevant issue tracker (`gh issue list --search "<keyword>"`) — confirm there's an open or merged ticket that codifies the requirement.

If any of the three returns empty **or you can't run the command**, replace the authority citation with one of:

- **Admit the design call:** "I added X because [reason]; there's no spec backing this; happy to remove if you'd prefer."
- **Cite the verification:** "X exists at `<repo>:<path>:<line>` (verified this session)."
- **Hedge honestly:** "I don't have the spec in front of me; I'll verify before claiming this in any committed artifact."

## Why this skill exists (worked examples)

### 2026-08-01 — Nocturne Ravencrest bible, "v1.2.0 spec requires Mystery Tracker"

I added a third custom mechanic (Mystery Tracker) to a campaign bible and justified it with: *"the spec says 'exactly 2 custom mechanics' but v1.2.0 requires the Mystery Tracker."* No such spec exists. The user caught it with five words: *"Is the mystery thing in WorldAI code?"* `grep` confirmed: `"mystery"` is only a world-gen genre string in `mcp_api.py`; `mystery_slot` is a whitelist test fixture for arbitrary equipment slot keys; there's no `MYSTERY` constant in `constants.py`, `game_state.py`, or `agents.py`. The mechanic itself was fine. The justification was the lie.

### 2026-07-10 — Claude Code `--teammate-mode tmux` flag fabrication

Declared a real Claude Code flag "fake / doesn't exist / a no-op" based only on local `--help` absence. The flag was real. Same shape: false negative from a local tool, false positive claim about a feature. Caught because the user actually ran the flag and it worked.

### 2026-06-25 — Three fabrication failures in one Slack thread

Hallucinated a `~/.hermes/agent-orchestrator/` Python folder, assumed an upstream TS→Go rewrite also rewrote the user's TS fork, and said "I can't fetch Slack URLs" when `mcp_slack_conversations_replies` was sitting right there in the tool list. See `agent-agent-mistakes/references/2026-06-25-verify-before-upstream-claim.md` for the full transcript.

All four are the same anti-pattern with different costumes. The skill-level lesson: **don't claim what you haven't run a command to confirm, and especially don't claim an authority document supports a position when you haven't read it this session.**

## Anti-patterns to avoid

- **"The user spec'd it"** — when the user's draft actually had 2 mechanics, not 3, and you're adding the third on your own initiative. Don't borrow the user's authority for a choice you made.
- **"Per the latest version"** — when there's no "latest version" you can point to. Versioning is for facts you can cite a commit for.
- **"Industry-standard practice"** — when the practice is something you read in a blog post two years ago and don't have a source for.
- **"The framework requires"** — when you haven't read the framework docs this session.
- **"The system architecture dictates"** — when you haven't actually traced the data flow.

## When the claim IS verified

If you have actually read the spec / version / ADR this session (i.e., the file is in your context, you can cite the path + line, and the citation matches what's there), then stating it is fine and even encouraged. The gate is **verification, not absence of citation**. Citing real, verified authority is good practice. The problem is citing authority you have *not* verified.

## Companion skills

- `agent-agent-mistakes` — broader umbrella covering all upstream-state hallucination (folder paths, branch states, CI status, etc.).
- `research-integrity` (`~/.cursor/rules/research-integrity.mdc`) — covers negative-claim verification (declaring something doesn't exist), web search discipline, and date-context awareness.
- `proof-before-claim` (SOUL.md `## COMMIT: proof-before-claim`) — covers completion-claim verification (paste real terminal output before saying "done").

The three together cover: positive state claims (`agent-agent-mistakes`), negative existence claims (`research-integrity`), and completion claims (`proof-before-claim`). This skill is the bridge between `agent-agent-mistakes` and `research-integrity` for the specific sub-class where authority is invoked to defend a design choice.