---
description: Launch dual-agent pair programming with LLM brainstorming and background monitoring
argument-hint: '[--coder-cli <cli>] [--verifier-cli <cli>] "task description"'
type: llm-orchestration
execution_mode: llm-driven
---

# /pair - Orchestrated Dual-Agent Pair Programming

**Flexible dual-agent orchestration with background monitoring**

## ⚡ EXECUTION WORKFLOW

**When /pair is invoked, YOU (Claude) must execute these steps:**

### Step 1: Brainstorm with /superpowers
Use `/superpowers:brainstorm` to analyze the task and create a comprehensive plan:
- Break down the implementation requirements
- Identify test verification criteria
- Define success metrics
- Plan the coder/verifier coordination strategy

### Step 2: Review and Refine Plan
Review the brainstorm results and refine as needed to ensure:
- Clear implementation steps for coder agent
- Specific verification criteria for verifier agent
- Communication protocol between agents
- Iteration strategy until both agents agree work is complete

### Step 3: Launch Python Orchestration
Execute the pair programming session:

```bash
python3 scripts/pair_execute.py "$TASK_DESCRIPTION"
```

**This launches the full pair programming session with:**
- Coder agent for implementation (default: Claude) - long-running tmux session
- Verifier agent for testing (default: Codex) - long-running tmux session
- MCP Mail for agent coordination (mcp__agentmail__* tools) - REQUIRED
- Beads MCP for state tracking (mcp__beads__* tools) - REQUIRED
- Background monitor observing progress (does NOT orchestrate messages)

---

## Command Usage

```bash
/pair "Task description"
/pair --coder-cli <cli> --verifier-cli <cli> "Task description"
```

**Examples:**
```bash
# Default: Claude coder + Codex verifier
/pair "Add user authentication with JWT tokens"

# Custom: Gemini coder + Claude verifier
/pair --coder-cli gemini --verifier-cli claude "Fix the pagination bug"

# Same CLI for both: Claude + Claude pair
/pair --coder-cli claude --verifier-cli claude "Implement dark mode toggle"

# Codex + Codex pair
/pair --coder-cli codex --verifier-cli codex "Refactor user service"
```

## Arguments

- `task`: Task description in quotes (REQUIRED)
- `--coder-cli`: CLI for coder agent (default: claude) - Options: claude, codex, gemini, cursor
- `--verifier-cli`: CLI for verifier agent (default: codex) - Options: claude, codex, gemini, cursor
- `--brainstorm`: Run brainstorm phase before launching agents
- `--max-iterations`: Maximum monitor iterations (default: 10)
- `--interval`: Monitor check interval in seconds (default: 60)
- `--no-monitor`: Skip background monitor (agents only)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    /pair Command Execution                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. BRAINSTORM PHASE (Optional: /superpowers:brainstorm)         │
│     └─> Generate comprehensive task plan via /superpowers        │
│                                                                  │
│  2. ORCHESTRATION PHASE (Flexible CLI Selection)                 │
│     ├─> Coder Agent (--coder-cli) - implements the solution      │
│     │   Options: claude*, codex, gemini, cursor                  │
│     │                                                            │
│     └─> Verifier Agent (--verifier-cli) - verifies test results  │
│         Options: claude, codex*, gemini, cursor                  │
│         (* = default)                                            │
│                                                                  │
│  3. MONITORING PHASE (Background via pair_monitor.py)            │
│     └─> Checks agent progress every 1 minute                     │
│     └─> Max 10 iterations per agent                              │
│     └─> Coordinates via Beads MCP + MCP Mail                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Supported CLI Combinations

| Coder | Verifier | Use Case |
|-------|----------|----------|
| claude | codex | Default - Best reasoning + strong verification |
| claude | claude | Same model pair - consistent style |
| gemini | claude | Fast coding + thorough review |
| codex | codex | OpenAI ecosystem pair |
| cursor | claude | Cursor speed + Claude review |

## ITERATIVE WORKFLOW

**Key Concept:** Agents run independently in tmux sessions, coordinating via MCP Mail until BOTH agree work is complete.

### Architecture: Independent Agent Iteration

Both agents are **long-running processes** in tmux sessions:
- Each agent has its own event loop: work → send message → check inbox → work
- Agents poll MCP Mail for messages (mcp__agentmail__check_inbox)
- Agents continue iterating until they receive termination signal
- Monitor observes progress but does NOT orchestrate communication

**This is NOT exit-and-wake** - agents stay running and poll independently.

### Communication Flow

```
Coder Agent (tmux session)              Verifier Agent (tmux session)
    │                                            │
    ├─ Implement feature                         │
    ├─ Write tests                               │
    ├─ Commit changes                            │
    │                                            │
    ├─ mcp__agentmail__send_message ────────────>│
    │  (IMPLEMENTATION_READY)                    │
    │                                            │
    ├─ Loop: Check inbox every 30s              ├─ mcp__agentmail__check_inbox
    │  while True:                               ├─ Receive IMPLEMENTATION_READY
    │    msgs = check_inbox()                    ├─ Review code & run tests
    │    if msgs: break                          │
    │    sleep(30)                               ├─ mcp__agentmail__send_message
    │                                            │  (VERIFICATION_FAILED + feedback)
    │<─────────────────────────────────────────  │
    ├─ Receive VERIFICATION_FAILED               │
    ├─ Read feedback                             ├─ Loop: Check inbox every 30s
    ├─ Fix issues                                │  while True:
    ├─ Re-run tests                              │    msgs = check_inbox()
    │                                            │    if msgs: break
    ├─ mcp__agentmail__send_message ────────────>│    sleep(30)
    │  (IMPLEMENTATION_READY v2)                 │
    │                                            ├─ Receive IMPLEMENTATION_READY v2
    │                                            ├─ Re-verify
    │                                            ├─ All checks pass!
    │                                            │
    │<─────────────────────────────────────────  │
    ├─ Receive VERIFICATION_COMPLETE             ├─ mcp__agentmail__send_message
    ├─ Create PR                                 │  (VERIFICATION_COMPLETE)
    └─ Exit successfully                         └─ Exit successfully
```

**Both agents running concurrently** - monitor tracks them but doesn't deliver messages.

### Iteration Rules

1. **Coder Agent (Independent Loop):**
   - **STAYS RUNNING** in tmux session throughout entire workflow
   - Event loop:
     1. Implement feature, write tests, commit changes
     2. Update Beads status: mcp__beads__update (implementation → in_progress)
     3. Send message: mcp__agentmail__send_message(IMPLEMENTATION_READY)
     4. **Poll inbox** every 30s: `while True: msgs = mcp__agentmail__check_inbox(); if msgs: break; sleep(30)`
     5. Receive VERIFICATION_FAILED → read feedback, fix issues, goto step 1
     6. Receive VERIFICATION_COMPLETE → update Beads (done), create PR, exit
   - Agent decides when to exit (on VERIFICATION_COMPLETE or max iterations)
   - No external orchestration - agent is autonomous

2. **Verifier Agent (Independent Loop):**
   - **STAYS RUNNING** in tmux session throughout entire workflow
   - Event loop:
     1. **Poll inbox** every 30s for IMPLEMENTATION_READY
     2. Receive message → update Beads: mcp__beads__update (verification → in_progress)
     3. Review code, run tests, verify quality
     4. Send VERIFICATION_FAILED (with feedback) OR VERIFICATION_COMPLETE
     5. Update Beads status (blocked OR done)
     6. If sent FAILED: goto step 1 (wait for next implementation)
     7. If sent COMPLETE: exit successfully
   - Agent decides when to exit (on VERIFICATION_COMPLETE or max iterations)
   - No external orchestration - agent is autonomous

3. **Monitor (Observer, NOT Orchestrator):**
   - Tracks both agents via tmux session status
   - Checks Beads status for progress updates
   - **Does NOT deliver messages** - MCP Mail handles that
   - **Does NOT inject prompts** - agents iterate independently
   - Logs progress for user visibility
   - Terminates on: both agents exit, timeout (10 min wall time), or agent crash
   - Can send SIGTERM to agents on timeout (graceful shutdown)

**Iteration Counting:**
- Each agent tracks its own iteration count internally
- Monitor tracks wall time: max 10 minutes (configurable)
- Agents can exchange unlimited messages within that time window

### Termination Conditions

The session ends when the **first** of these occurs:

1. ✅ **Success:** Verifier sends VERIFICATION_COMPLETE
2. ⏱️ **Timeout:** 10 monitor iterations without progress (configurable via --max-iterations)
3. ❌ **Failure:** Agent exits with error code
4. 🛑 **Manual:** User kills session via `tmux kill-session` or Ctrl+C

### Error Recovery

**Agent crashes:** Session state preserved in `$SESSION_DIR`. Monitor detects missing tmux session and logs error. Manual restart: Re-run the same command.

**MCP Mail unavailable:** If mcp__agentmail__* tools fail, agents MUST exit with error. MCP Mail is REQUIRED for coordination.

**Beads MCP unavailable:** If mcp__beads__* tools fail, agents can continue but state tracking is lost. Beads is strongly recommended but not blocking.

**Monitor crashes:** Session continues independently. Restart monitor with same session ID to resume tracking.

---

## EXECUTION INSTRUCTIONS

**When /pair is invoked, execute these steps immediately:**

### Phase 1: Initialize Session

```bash
# Generate unique session ID
SESSION_ID="pair-$(date +%s)"
TASK_DESCRIPTION="$1"
CODER_CLI="${CODER_CLI:-claude}"
VERIFIER_CLI="${VERIFIER_CLI:-codex}"
TIMESTAMP=$(date -Iseconds)

# Create session directory for artifacts (cross-platform)
# Note: Python scripts use tempfile.gettempdir() for platform compatibility
# Cross-platform mktemp: GNU (Linux) vs BSD (macOS) compatibility
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # GNU mktemp (Linux)
    TEMP_BASE=$(mktemp -d)
else
    # BSD mktemp (macOS)
    TEMP_BASE=$(mktemp -d -t "pair_sessions")
fi
SESSION_DIR="${TEMP_BASE}/${SESSION_ID}"
mkdir -p "${SESSION_DIR}"

echo "🎯 Pair Session: ${SESSION_ID}"
echo "📋 Task: ${TASK_DESCRIPTION}"
```

### Phase 2: Brainstorm via /superpowers

**Use /superpowers:brainstorm slash command to generate a comprehensive task plan:**

1. **Run brainstorm command**:
```bash
# Option 1: Use /superpowers:brainstorm slash command (recommended)
# The slash command handles planning and task breakdown automatically

# Option 2: Direct MCP tool usage (for custom integrations)
# mcp__chrome-superpower__use_browser can be used for web-based brainstorming
```

2. **Generate task breakdown:**
- Implementation steps for coder agent
- Test verification criteria for verifier agent
- Success metrics for monitoring

3. **Store brainstorm results:**
```bash
# Save to session directory (note: unquoted EOF enables variable expansion)
cat > "${SESSION_DIR}/brainstorm_results.json" << EOF
{
  "session_id": "${SESSION_ID}",
  "task": "${TASK_DESCRIPTION}",
  "coder_instructions": "...",
  "verifier_instructions": "...",
  "success_criteria": [...],
  "max_iterations": 10
}
EOF
```

### Phase 3: Create Bead for State Tracking

**Register session with Beads (file-based or MCP):**

**Option 1: File-based (Current Implementation)**
```bash
# Create bead entry for this pair session
BEAD_ID="${SESSION_ID}"

# Ensure .beads directory exists before writing
mkdir -p .beads

# Write to beads tracking file
echo "{\"id\":\"${BEAD_ID}\",\"title\":\"Pair Session: ${TASK_DESCRIPTION}\",\"description\":\"Dual-agent pair programming session for: ${TASK_DESCRIPTION}\",\"status\":\"in_progress\",\"priority\":1,\"issue_type\":\"task\",\"created_at\":\"${TIMESTAMP}\",\"updated_at\":\"${TIMESTAMP}\"}" >> .beads/beads.left.jsonl
```

**Option 2: Beads MCP Server (Recommended if available)**
```bash
# Prerequisites: pip install beads-mcp
# The Beads MCP server provides these tools:
# - mcp__beads__create: Create new issues/tasks
# - mcp__beads__update: Update issue status, priority, design, notes
# - mcp__beads__list: List and query issues
# - mcp__beads__status: Query issue status

# MCP tools are used by agents automatically when the MCP server is configured
# Python implementation in scripts/pair_execute.py handles bead creation
```

**Beads MCP Server Setup:**
- **Installation**: `pip install beads-mcp` (version 0.38.0+)
- **Framework**: Uses FastMCP for Model Context Protocol communication
- **Storage**: Git-based (.beads/*.jsonl) with hash-based IDs (bd-a1b2)
- **Compatible with**: Claude Desktop, Cursor IDE, and MCP-compatible clients
- **Repository**: [steveyegge/beads](https://github.com/steveyegge/beads)

### Phase 4: Launch Coder Agent (Implementation)

**Use orchestration to spawn the coder agent:**

```bash
# Execute via orchestration framework
python3 orchestration/orchestrate_unified.py \
  --agent-cli "${CODER_CLI}" \
  --bead "${BEAD_ID}" \
  --mcp-agent "${CODER_CLI}-coder-${SESSION_ID}" \
  "$(cat <<EOF
${TASK_DESCRIPTION}

IMPORTANT: This is a PAIR SESSION.
Your role: IMPLEMENTATION

Instructions:
1. Implement the requested feature/fix
2. Write comprehensive tests
3. Send progress updates via MCP Mail to ${VERIFIER_CLI}-verifier-${SESSION_ID}
4. Commit changes but DO NOT create PR yet
5. Wait for verification from the verifier agent before final PR

MCP Mail Protocol:
- Send IMPLEMENTATION_READY when code is complete
- Include file list and test coverage in message body
- Use subject: IMPLEMENTATION_READY
EOF
)"
```

### Phase 5: Launch Verifier Agent (Verification)

**Spawn the verifier agent for test verification:**

```bash
# Launch verifier agent in parallel
python3 orchestration/orchestrate_unified.py \
  --agent-cli "${VERIFIER_CLI}" \
  --bead "${BEAD_ID}" \
  --mcp-agent "${VERIFIER_CLI}-verifier-${SESSION_ID}" \
  "$(cat <<EOF
Verify implementation for: ${TASK_DESCRIPTION}

IMPORTANT: This is a PAIR SESSION.
Your role: VERIFICATION

Instructions:
1. Wait for IMPLEMENTATION_READY message from ${CODER_CLI}-coder-${SESSION_ID}
2. Review the implementation files listed in the message
3. Run all tests: TESTING=true python -m pytest
4. Verify code quality and test coverage
5. Send VERIFICATION_COMPLETE or VERIFICATION_FAILED via MCP Mail

MCP Mail Protocol:
- Poll for IMPLEMENTATION_READY from ${CODER_CLI}-coder-${SESSION_ID}
- Send VERIFICATION_COMPLETE when tests pass
- Send VERIFICATION_FAILED with failure details if issues found
- Include test output in message body
EOF
)"
```

### Phase 6: Start Background Monitor

**Launch monitoring script as background process:**

```bash
# Start the pair monitor in background
nohup python3 scripts/pair_monitor.py \
  --session-id "${SESSION_ID}" \
  --coder-agent "${CODER_CLI}-coder-${SESSION_ID}" \
  --verifier-agent "${VERIFIER_CLI}-verifier-${SESSION_ID}" \
  --bead-id "${BEAD_ID}" \
  --max-iterations 10 \
  --interval 60 \
  > "${SESSION_DIR}/monitor.log" 2>&1 &

MONITOR_PID=$!
echo "${MONITOR_PID}" > "${SESSION_DIR}/monitor.pid"

echo "🔄 Background monitor started (PID: ${MONITOR_PID})"
echo "📋 Monitor log: ${SESSION_DIR}/monitor.log"
```

---

## MONITORING SCRIPT BEHAVIOR

The background monitor (`scripts/pair_monitor.py`) performs:

1. **Every 1 minute:**
   - Check Coder agent status via tmux
   - Check Verifier agent status via tmux
   - Query MCP Mail for coordination messages
   - Update bead with current status

2. **Iteration Counting with Progress Reset:**
   - Track iterations since last status change
   - **Reset counter to 0** when status changes (progress detected)
   - Only increment counter when status is unchanged (stagnation)
   - After 10 stagnant iterations, escalate to timeout

3. **Termination Conditions (first match wins):**
   - **Success:** Bead status becomes `completed` → exit cleanly
   - **Timeout:** 10 iterations without progress → send `SESSION_TIMEOUT` to both agents, update bead to `timeout`, exit
   - **Failure:** Agent tmux session crashes → log error, update bead to `failed`, exit

4. **Coordination via MCP:**
   - Beads: Track overall session state
   - MCP Mail: Facilitate agent-to-agent communication

**Cross-Platform:** Works on Linux, macOS, and Windows (via WSL or Git-Bash). Python scripts use `tempfile.gettempdir()` for portable temp directories.

---

## MCP MAIL PROTOCOL

> **Note:** MCP Mail integration is currently stubbed in `pair_monitor.py`. Use the
> status file fallback (`status.json`) until MCP Mail hooks are wired in.

### Message Types

| Subject | Sender | Receiver | Purpose |
|---------|--------|----------|---------|
| IMPLEMENTATION_READY | Coder | Verifier | Code complete, ready for verification |
| VERIFICATION_COMPLETE | Verifier | Coder | Tests pass, ready for PR |
| VERIFICATION_FAILED | Verifier | Coder | Issues found, needs fixes |
| PROGRESS_UPDATE | Either | Monitor | Status update for tracking |
| SESSION_COMPLETE | Monitor | Both | Session finished successfully |
| SESSION_TIMEOUT | Monitor | Both | Max iterations reached |

### Message Format

```json
{
  "to": "<agent_id>",
  "subject": "IMPLEMENTATION_READY",
  "body": {
    "session_id": "pair-1234567890",
    "phase": "implementation_complete",
    "files_changed": ["src/auth.py", "tests/test_auth.py"],
    "test_coverage": "85%",
    "status": "ready_for_verification"
  }
}
```

### MCP Implementation (Agent Mail MCP Server)

**Current Status**: The Python implementation in `scripts/pair_monitor.py` uses stub functions for MCP Mail. To enable real MCP coordination:

**Available MCP Tools:**
- `mcp__agentmail__register_agent` - Register agent with mail system
- `mcp__agentmail__send_message` - Send messages to other agents
- `mcp__agentmail__check_inbox` - Check for incoming messages
- `mcp__agentmail__list_messages` - List messages with filters
- `mcp__agentmail__whoami` - Get current agent ID
- `mcp__agentmail__mark_read` - Mark messages as read
- `mcp__agentmail__delete_messages` - Delete messages

**Integration Pattern:**
```python
# Replace stub functions in pair_monitor.py with:
def check_mcp_mail(agent_id: str, subject: str = None) -> list:
    """Check MCP mail for messages."""
    # Use mcp__agentmail__check_inbox tool
    # Filter by agent_id and optionally by subject
    return messages

def send_mcp_mail(to: str, subject: str, body: dict) -> bool:
    """Send MCP mail message."""
    # Use mcp__agentmail__send_message tool
    return success
```

**Fallback**: If MCP Mail server is unavailable, the monitor uses file-based coordination via `${SESSION_DIR}/status.json`

---

## BEADS STATE TRACKING

### Bead Status Values

| Status | Meaning |
|--------|---------|
| `in_progress` | Session active, agents working |
| `implementation` | Coder agent implementing |
| `verification` | Verifier agent verifying |
| `completed` | Both agents finished successfully |
| `failed` | Session failed, needs intervention |
| `timeout` | Max iterations exceeded |

### Bead Update Format

```bash
# Update bead status
jq --arg status "verification" '.status = $status | .updated_at = (now | todate)' .beads/beads.left.jsonl
```

---

## SUCCESS CRITERIA

A pair session is considered successful when:

1. ✅ Coder agent completes implementation
2. ✅ Verifier agent verifies tests pass
3. ✅ MCP Mail coordination messages exchanged
4. ✅ Bead updated to "completed" status
5. ✅ Monitor script exits cleanly

---

## ERROR HANDLING

### Agent Stuck

If an agent doesn't progress for 3+ iterations:
1. Monitor sends TIMEOUT_WARNING via MCP Mail
2. Bead status updated to "blocked"
3. User notified to check agent manually

### Max Iterations Exceeded

If 10 iterations reached without completion:
1. Monitor sends SESSION_TIMEOUT to both agents
2. Bead status updated to "timeout"
3. Session artifacts preserved for debugging

### Communication Failure

If MCP Mail fails:
1. Fall back to file-based coordination
2. Write status to `${SESSION_DIR}/status.json`
3. Agents poll this file as backup

---

## MANUAL INTERVENTION

### Check Agent Status

```bash
# View Coder agent
tmux attach -t ${CODER_CLI}-coder-${SESSION_ID}

# View Verifier agent
tmux attach -t ${VERIFIER_CLI}-verifier-${SESSION_ID}
```

### Check Monitor Log

```bash
# Monitor log location (Python scripts use platform temp directory)
# Find actual path: python3 -c "import tempfile; print(tempfile.gettempdir())"
tail -f "$(python3 -c 'import tempfile; print(tempfile.gettempdir())')/pair_sessions/${SESSION_ID}/monitor.log"
```

### Force Session Complete

```bash
# Update bead to completed
python3 -c "
import json
import sys
from pathlib import Path
from datetime import datetime

bead_id = '${SESSION_ID}'
beads_file = Path('.beads/beads.left.jsonl')

if beads_file.exists():
    # Read existing beads
    beads = []
    with open(beads_file, 'r') as f:
        for line in f:
            if line.strip():
                beads.append(json.loads(line))
    
    # Update matching bead
    updated = False
    for bead in beads:
        if bead.get('id') == bead_id:
            bead['status'] = 'completed'
            bead['updated_at'] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        # Write back updated beads
        with open(beads_file, 'w') as f:
            for bead in beads:
                f.write(json.dumps(bead) + '\n')
        print(f'✅ Bead {bead_id} marked as completed')
    else:
        print(f'⚠️ Bead {bead_id} not found')
        sys.exit(1)
else:
    print('⚠️ .beads/beads.left.jsonl not found')
    sys.exit(1)
"
```

### Kill Session

```bash
# Stop monitor
kill $(cat "$(python3 -c 'import tempfile; print(tempfile.gettempdir())')/pair_sessions/${SESSION_ID}/monitor.pid")

# Kill agent sessions
tmux kill-session -t ${CODER_CLI}-coder-${SESSION_ID}
tmux kill-session -t ${VERIFIER_CLI}-verifier-${SESSION_ID}
```

---

## IMPLEMENTATION NOTES

### Why Dual Agents?

- **Separation of concerns**: Dedicated implementation vs. verification
- **Flexible pairing**: Mix and match CLIs based on task needs
- **Redundancy**: One agent can catch gaps the other misses

### Why Background Monitoring?

- Non-blocking: Doesn't pause the main session
- Independent: Continues even if orchestrator exits
- Persistent: Can recover from transient failures

### Why Beads + MCP Mail?

- **Beads**: Persistent state across sessions
- **MCP Mail**: Real-time agent coordination
- **Dual approach**: Redundancy for reliability

---

## QUICK START

**Simplest invocation - defaults work out of the box:**

```bash
/pair "Add JWT authentication to the API"
```

This single command:
1. Brainstorms the task via `/superpowers`
2. Launches Claude coder agent (implements feature + tests)
3. Launches Codex verifier agent (runs tests, reviews code)
4. Starts background monitor (1min checks, 10 stagnation limit)
5. Coordinates via MCP Mail + Beads state tracking

**Custom CLI pairing:**

```bash
# Gemini implements, Claude verifies
/pair --coder-cli gemini --verifier-cli claude "Fix pagination bug"

# Same model pair (consistent style)
/pair --coder-cli claude --verifier-cli claude "Refactor auth module"
```

**Session complete when:** Verifier sends `VERIFICATION_COMPLETE` (all tests pass).

---

**Protocol Version:** 4.1 (Orchestrated Dual-Agent with Progress Reset)
**Last Updated:** 2026-01-10
