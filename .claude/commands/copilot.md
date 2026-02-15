---
description: /copilot - Orchestrated PR Comment Processing
type: llm-orchestration
execution_mode: llm-driven
---

# /copilot - Orchestrated PR Comment Processing

**Autonomous PR comment analysis, categorization, fixes, and response posting**

## ⚡ EXECUTION WORKFLOW

**When /copilot is invoked, YOU (Claude) must execute these steps:**

### Step 1: Launch Orchestration Agent

Execute the copilot orchestration script:

```bash
python3 .claude/scripts/copilot_execute.py [PR_NUMBER]
```

**This launches an autonomous orchestration agent that:**
- Fetches and analyzes all PR comments via `/commentfetch`
- Checks CI status via `/gstatus`
- Categorizes comments (CRITICAL/BLOCKING/IMPORTANT/ROUTINE)
- Generates comprehensive responses for ALL comments
- Posts consolidated summary comment via `/commentreply`
- Verifies 100% coverage via `/commentcheck`
- Pushes changes via `/pushl` if needed

The orchestration agent follows detailed instructions in `.codex/skills/copilot-pr-processing/SKILL.md` and runs autonomously without stopping to ask questions.

---

## Command Usage

```bash
/copilot [PR_NUMBER]
```

**Examples:**
```bash
# Auto-detect PR from current branch
/copilot

# Explicit PR number
/copilot 5368
```

## Arguments

- `PR_NUMBER` (optional): PR number to process - auto-detected from current branch if omitted

## Configuration

**Environment Variables:**

- **`COPILOT_USE_PAIR`** (default: `false`): Enable /pair integration for automated fixing
  - When `true`: CRITICAL/BLOCKING comments trigger /pair sessions for implementation + verification
  - /pair sessions use dual-agent (coder + verifier) approach with automated testing

- **`COPILOT_PAIR_MIN_SEVERITY`** (default: `CRITICAL`): Minimum severity level to trigger /pair
  - Options: `CRITICAL`, `BLOCKING`, `IMPORTANT`, `ROUTINE`
  - Severity hierarchy: CRITICAL > BLOCKING > IMPORTANT > ROUTINE

- **`COPILOT_PAIR_IMPORTANT`** (default: `false`): Include IMPORTANT comments in /pair processing
  - When `true`: IMPORTANT comments also trigger /pair (in addition to CRITICAL/BLOCKING)

- **`COPILOT_AGENT_CLI`** (default: `codex`): Agent CLI to use for orchestration
  - Options: `codex`, `claude`, `gemini`, `cursor`
  - Falls back through chain if primary not available

- **`COPILOT_PAIR_CODER`** (default: `claude`): CLI for /pair coder agent

- **`COPILOT_PAIR_VERIFIER`** (default: `codex`): CLI for /pair verifier agent

- **`COPILOT_PAIR_TIMEOUT`** (default: `600`): Timeout in seconds for /pair sessions

**Example Usage:**
```bash
# Enable /pair integration with default settings
export COPILOT_USE_PAIR=true
/copilot 5368

# Use /pair for BLOCKING+ with custom CLIs
export COPILOT_USE_PAIR=true
export COPILOT_PAIR_MIN_SEVERITY=BLOCKING
export COPILOT_PAIR_CODER=gemini
export COPILOT_PAIR_VERIFIER=claude
/copilot 5368
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  /copilot Command Execution                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. ORCHESTRATION LAUNCH                                      │
│     └─> Spawn autonomous agent via .claude/scripts/copilot_execute.py│
│                                                               │
│  2. PHASE 0: Comment Fetch & CI Analysis                      │
│     ├─> /commentfetch - Fetch all PR comments                │
│     └─> /gstatus - Check CI status and merge state           │
│                                                               │
│  3. PHASE 1: Comment Categorization                           │
│     ├─> Analyze comment content and severity                 │
│     └─> Categorize: CRITICAL/BLOCKING/IMPORTANT/ROUTINE      │
│                                                               │
│  4. PHASE 2: Response Generation                              │
│     ├─> Generate responses for ALL comments                  │
│     ├─> ACTION_ACCOUNTABILITY protocol                        │
│     └─> Create responses.json with metadata                  │
│                                                               │
│  5. PHASE 3: Consolidated Comment Posting                     │
│     ├─> /commentreply - Post single summary comment          │
│     └─> Acknowledges all automated reviewer feedback         │
│                                                               │
│  6. PHASE 4: Coverage Verification                            │
│     ├─> /commentcheck - Verify 100% comment coverage         │
│     └─> Ensure no comments missed                            │
│                                                               │
│  7. PHASE 5: Push Changes                                     │
│     └─> /pushl - Push any fixes or responses to PR           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Workflow Phases

### Phase 0: Data Collection
- Fetch all PR comments (inline, general, review, copilot)
- Check CI status and identify failing checks
- Load PR context and branch information

### Phase 1: Analysis & Categorization
- **CRITICAL**: Security vulnerabilities, production blockers
- **BLOCKING**: Test failures, CI issues, merge conflicts
- **IMPORTANT**: Performance concerns, architectural issues
- **ROUTINE**: Style suggestions, documentation, minor improvements

### Phase 2: Response Generation
- Analyze every comment (bot + human)
- Generate ACTION_ACCOUNTABILITY responses
- Document: action_taken, files_modified, commit, verification
- Create responses.json with all metadata

### Phase 3: Consolidated Response
- Post single summary comment to PR
- Acknowledge all automated reviewers (Cursor Bugbot, CodeRabbit, Copilot, GitHub Actions)
- Provide high-level summary of changes and fixes
- Reference specific commits where fixes were applied

### Phase 4: Coverage Verification
- Verify 100% comment coverage (80/80, etc.)
- Ensure consolidated comment posted successfully
- Check for any missed or unacknowledged feedback

### Phase 5: Completion
- Push responses and any fixes to PR
- Update PR status
- Mark workflow complete

## Comment Coverage Protocol

**100% Reply Rate Mandate:**
- ALL comments require responses (bot + human)
- ONLY exception: `[AI responder]` tagged comments (our own responses)
- Bot comments (CodeRabbit, Copilot, Cursor Bugbot) are NOT optional
- Consolidated summary comment addresses all feedback

## Integration with Other Commands

- `/commentfetch` - Fetch PR comments
- `/gstatus` - Check PR CI status
- `/commentreply` - Post responses
- `/commentcheck` - Verify coverage
- `/pushl` - Push changes
- `/fixpr` - Fix specific CI failures (if needed)

## Orchestration vs Direct Execution

**Key Principle:** /copilot spawns an orchestration agent that executes autonomously. You (Claude in the main session) should NOT execute the workflow directly - instead, launch the agent and let it run.

**Correct Pattern:**
```bash
# You run this ONE command:
python3 .claude/scripts/copilot_execute.py 5368

# Agent handles all phases autonomously
```

**Incorrect Pattern (Don't Do This):**
```bash
# DON'T manually execute each command yourself:
/commentfetch 5368
/gstatus
# ... analyzing comments manually ...
# ... generating responses manually ...
/commentreply ...
```

## Agent Instructions

The orchestration agent receives detailed instructions from `.codex/skills/copilot-pr-processing/SKILL.md` including:
- Comprehensive comment analysis protocol
- ACTION_ACCOUNTABILITY response format
- Priority-based processing queues
- Error handling and retry logic
- Test execution and verification procedures

## Success Criteria

A /copilot execution is successful when:
- ✅ All PR comments fetched and analyzed
- ✅ Consolidated summary comment posted
- ✅ 100% comment coverage verified (via /commentcheck)
- ✅ CI status checked and documented
- ✅ Changes pushed to PR (if applicable)
- ✅ Orchestration agent exits cleanly

## Error Handling

If orchestration fails:
- Check agent logs in orchestration output
- Review `.codex/skills/copilot-pr-processing/SKILL.md` for requirements
- Verify MCP tools available (commentfetch, commentreply, commentcheck)
- Check PR exists and is accessible via `gh` CLI
- Retry with explicit PR number if auto-detection failed

---

**Protocol Version:** 5.0 (Orchestrated Execution)
**Last Updated:** 2026-02-12
