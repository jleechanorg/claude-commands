---
name: copilot-pr-processing
description: "Run /copilot PR processing with ACTION_ACCOUNTABILITY outputs and optional /pair escalation for high-severity clusters."
---

# Copilot PR Processing

## Quick Start
1. Read `.claude/commands/copilot.md`.
2. Execute directly from the command spec (no orchestration wrapper).
3. Generate `/tmp/{repo}/{branch}/copilot/responses.json` before posting.

## Required References
1. `.claude/commands/copilot.md`
2. `.claude/commands/commentfetch.md`
3. `.claude/commands/_copilot_modules/commentfetch.py`
4. `.claude/commands/commentcheck.md`
5. `.claude/commands/commentreply.md`

## Core Rules
- Follow the 10-step workflow in copilot.md.
- Keep ACTION_ACCOUNTABILITY fields complete: `comment_id`, `reply_text`, `response`, `tracking_reason`, `files_modified`.
- Use `/pair` only for the high-volume/high-risk lane described below.

## Phase 3.5: Pair Programming Integration

### COMPREHENSIVE GUIDE

Use this phase when high-severity feedback volume justifies parallel coder/verifier execution.

#### Configuration
- `COPILOT_USE_PAIR=true|false`
- `COPILOT_PAIR_MIN_SEVERITY=BLOCKING`
- `COPILOT_PAIR_IMPORTANT=false`
- `COPILOT_PAIR_CODER=claude`
- `COPILOT_PAIR_VERIFIER=codex`
- `COPILOT_PAIR_TIMEOUT=600` (10-minute max; 600s)

#### Step 1: Trigger Detection
```python
def should_trigger_pair(critical_count: int, blocking_count: int, cfg: dict) -> bool:
    if str(cfg.get("COPILOT_USE_PAIR", "false")).lower() != "true":
        return False
    return (critical_count + blocking_count) >= 6
```

#### Step 2: Task Spec Generation
```python
def generate_pair_task_spec(pr_number: int, comments: list[dict]) -> str:
    lines = [f"Fix CRITICAL/BLOCKING review comments for PR #{pr_number}"]
    for c in comments:
        lines.append(f"- [{c['severity']}] {c['path']}:{c.get('line','?')} :: {c['body']}")
    return "\n".join(lines)
```

#### Step 3: Launch /pair Session
```python
def launch_pair(task_spec: str) -> list[str]:
    return [
    # Uses ralph-pair.sh (replaces legacy pair_execute.py, removed in PR #5834)
        "bash",
        "ralph/ralph-pair.sh",
        "run",
        "--max-iterations", "3",
        task_spec,
    ]
```

#### Step 4: Collect Result Signals
```python
def collect_pair_results(raw: dict) -> dict:
    return {
        "session_id": raw.get("session_id"),
        "status": raw.get("status", "unknown"),
        "duration_seconds": raw.get("duration_seconds", 0),
        "test_results": raw.get("test_results", []),
        "files_changed": raw.get("files_changed", []),
    }
```

#### Step 5: Merge Back Into Responses
```python
def enhance_response_with_pair_data(entry: dict, pair_data: dict) -> dict:
    entry["pair_metadata"] = {
        "session_id": pair_data.get("session_id"),
        "status": pair_data.get("status"),
        "duration_seconds": pair_data.get("duration_seconds"),
        "test_results": pair_data.get("test_results", []),
    }
    return entry
```

### Error Handling:
```python
from subprocess import TimeoutExpired

try:
    result = run_pair_session()
except TimeoutExpired:
    result = {"status": "timeout", "issues_found": ["pair timeout; fallback to inline fixes"]}
except Exception as exc:
    result = {"status": "failed", "issues_found": [str(exc)], "suggestions": ["continue inline"]}
```

```python
def fallback_inline_if_needed(pair_status: str) -> bool:
    return pair_status in {"timeout", "failed", "VERIFICATION_FAILED"}
```

```python
def classify_verifier_outcome(report: dict) -> str:
    if report.get("issues_found"):
        return "VERIFICATION_FAILED"
    if report.get("tests_passed"):
        return "VERIFICATION_COMPLETE"
    return "IMPLEMENTATION_READY"
```

```python
def build_pair_metadata(session_id: str, status: str, duration_seconds: int, test_results: list[str]) -> dict:
    return {
        "session_id": session_id,
        "status": status,
        "duration_seconds": duration_seconds,
        "test_results": test_results,
    }
```

```python
def send_message(payload: dict) -> None:
    # MCP Mail send_message call
    pass
```

```python
def check_inbox(session_id: str) -> list[dict]:
    # MCP Mail check_inbox call
    return []
```

## Codex as Verifier
Codex VERIFIER responsibilities:
- perform focused code review
- run tests and validate failures are resolved
- return `IMPLEMENTATION_READY`, `VERIFICATION_COMPLETE`, or `VERIFICATION_FAILED`
- provide actionable feedback with `issues_found` and concrete suggestions

## MCP Mail Protocol
Use MCP Mail tools for coder/verifier coordination:
- `send_message`
- `check_inbox`
- poll every 15-30s until terminal status

Example verifier payload:
```json
{
  "session_id": "pair-123",
  "status": "VERIFICATION_COMPLETE",
  "files_changed": [".claude/commands/copilot.md"],
  "issues_found": [],
  "suggestions": []
}
```

## Workflow Examples
**Example 1:**
- **Scenario**: 7 CRITICAL/BLOCKING comments in one PR Comment batch
- **Flow:** trigger /pair, run tests, merge pair_metadata back to responses

**Example 2:**
- **Scenario**: BLOCKING regression remains after first pass
- **Flow:** verifier returns `VERIFICATION_FAILED`; iterate once; rerun tests

**Example 3:**
- **Scenario**: /pair timeout at 600s
- **Flow:** timeout fallback to inline fix path; mark timeout context in tracking_reason

## Testing Instructions
- Run focused validator:
  - `pytest -q .codex/skills/copilot-pr-processing/tests/test_skill_md_pair_integration.py`
- Smoke-check command docs:
  - `python3 -m py_compile .claude/commands/_copilot_modules/commentfetch.py`

## Verification Checklist
- [ ] Requirements met for /pair activation threshold
- [ ] Requirements met for MCP Mail handoff fields
- [ ] Tests pass for skill documentation validators
- [ ] feedback includes issues_found and suggestions when failing
- [ ] pair_metadata includes session_id/status/duration_seconds/test_results

## Backward Compatibility
- If `COPILOT_USE_PAIR=false`, skip Phase 3.5 and continue inline.
- Existing non-pair `/copilot` runs remain valid.

## Outputs
- Comments: `/tmp/{repo}/{branch}/copilot/comments.json`
- Responses: `/tmp/{repo}/{branch}/copilot/responses.json`
