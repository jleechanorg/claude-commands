# 2026-06-25 — verify-before-upstream-claim (anti-pattern card)

**Bug class:** Fill-the-gap-from-training-data + claim-without-verification + tool-blindness.
**Channel:** Slack `C0ALSKLU9KM`, thread `1782382574.896179`.
**Trigger phrases:** "wait mine shouldn't be python I have an older fork", "What is this sub folder", "You have slack mcp".

## The three failures (in the same thread)

### 1. Hallucinated local path — `~/.hermes/agent-orchestrator/` (Python)

**What the agent said:** *"Compared to the Python agent-orchestrator you've been running locally (the `~/.hermes/agent-orchestrator/` we use)..."*

**Reality:** `~/.hermes/agent-orchestrator/` does not exist. The Python AO under `~/.hermes/` is `~/.hermes/ao_runner/` (a thin runner shim — `cli.py`, `runner.py`, `config.py`, `launchd.py`). The real source of truth for the user is the TypeScript fork `jleechanorg/agent-orchestrator`, cloned at `~/projects/agent-orchestrator-684-thread-ts/`.

**Root cause:** Filled the gap from training-data memory of "Python `agent-orchestrator`" instead of running `ls -d ~/.hermes/agent-orchestrator/`.

### 2. Assumed upstream rewrite = fork rewrite

**What the agent said:** *"Upstream AgentWrapper/agent-orchestrator went TypeScript → Go... Your fork is still on the older TS architecture."*

**Reality:** Upstream did go TS → Go. The user's fork (`jleechanorg/agent-orchestrator`) is indeed still TS — but the agent never asked or verified. It conflated "upstream changed" with "your fork matches the change," and then asserted the fork's state without checking. The user had to correct: *"mine shouldn't be python I have an older fork."*

**Root cause:** When the user has a fork of an upstream project, never assume the fork tracks upstream. Run `gh api repos/<owner>/<repo>/languages` (and `--json primaryLanguage`) for the fork, in the same turn as the claim.

### 3. "I can't fetch Slack URLs"

**What the agent said:** *"I don't have access to Slack thread URLs from this runtime — I can't fetch that link."*

**Reality:** The runtime exposes `mcp__slack__conversations_replies` (and other Slack MCP tools). The user had to remind: *"You have slack mcp."*

**Root cause:** Defaulted to "I can't fetch external URLs" without first checking which tools the runtime exposes. The same trap recurs with `mcp__playwright-mcp__*` (browser) and `mcp__slack__*` (threads/channels/users).

## The class-level rule (paste-able as pre-action gate)

Before any claim about an upstream repo's state, a local path on this machine, or a thread/channel/message on a connected platform, **run the actual verification command in the same turn and cite its output.** Do not fill the gap from training-data memory. Do not say "I can't fetch that" for tools the runtime exposes.

### Pre-flight gate (verbatim, copy into the response before the claim)

```bash
# Upstream / fork repo state
gh api repos/<owner>/<repo>/languages | jq '. | to_entries | map({lang: .key, bytes: .value})'

# Local path
ls -d <path> 2>&1

# Slack thread
mcp__slack__conversations_replies channel_id=<C> thread_ts=<ts> limit=20
```

If you can't run any of those in the current runtime, **say so explicitly with the blocker** — "Slack MCP not exposed in this runtime" or `gh` returns 403 — rather than guessing.

## Why this is class-level, not project-specific

Every repo the user touches has the same trap: a fork can lag upstream, a local path can be renamed, a tool's capability changes per runtime. The verification habit is the fix, not anything specific to `agent-orchestrator`.

## Cross-references

- **Umbrella skill:** `agent-agent-mistakes/SKILL.md` step 4 (Pre-Action Verify).
- **Skillify anti-pattern that names this exact drift:** `skillify/SKILL.md` → "Anti-Pattern: Claiming 'DONE' Without Re-Running The Test Suite" and "Anti-Pattern: Claiming 'DONE' For Staging AND Prod Without `ls`-Verifying Both".
- **Related skill:** `root-cause-first` (engineer the verify-first habit into the prompt rather than adding checks around an unverified claim).