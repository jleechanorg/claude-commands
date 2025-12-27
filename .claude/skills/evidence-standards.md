# Evidence Standards for All Testing and Verification

## Core Principle

**Evidence must prove what you claim.** Mock data cannot prove production behavior.

## Three Evidence Rule (from CLAUDE.md)

**MANDATORY for ANY integration claim:**

1. **Configuration Evidence**: Show actual config file entries enabling the behavior
2. **Trigger Evidence**: Demonstrate automatic trigger mechanism (not manual execution)
3. **Log Evidence**: Timestamped logs from automatic behavior (not manual testing)

## Mock vs Real Mode Decision Tree

Before running ANY test, answer:

| Question | If YES → |
|----------|----------|
| Testing production/preview server behavior? | MUST use real mode |
| Validating actual API responses? | MUST use real mode |
| Checking data integrity (dice, state, persistence)? | MUST use real mode |
| Proving a bug is fixed in production? | MUST use real mode |
| Development workflow validation only? | Mock mode acceptable |
| Unit testing isolated functions? | Mock mode acceptable |

## Mock Mode Prohibition

**MOCK MODE = INVALID EVIDENCE** for:
- Production server validation
- API integration claims
- Data integrity verification (dice rolls, state changes)
- Bug fix confirmation
- Performance claims
- Security validation

**Mock mode tests ONLY prove:**
- Code syntax is correct
- Function signatures work
- Basic logic flow (in isolation)

**Mock mode tests NEVER prove:**
- Production behavior
- Real API responses
- Actual data execution
- Integration correctness

## Evidence Collection Requirements

### Evidence Integrity (Checksums)

**ALL evidence files MUST have separate checksum files:**

```bash
# Generate checksums AFTER finalizing content
sha256sum evidence.json > evidence.json.sha256

# Verify checksums
sha256sum -c evidence.json.sha256
```

**Anti-pattern:** Embedding checksums inside JSON files (self-invalidating).

### Git Provenance Requirements

Every evidence bundle MUST capture:

```bash
git fetch origin main  # Ensure origin/main is current
git rev-parse HEAD     # Exact commit being tested
git rev-parse origin/main  # Base comparison point
git branch --show-current  # Branch name
git diff --name-only origin/main...HEAD  # Files changed
```

**Why:** Proves exactly what code was running during evidence capture.

### Server Environment Capture

For server-based evidence, capture:

```bash
# Process info
ps -eo pid,user,etime,args | grep "mvp_site\|python.*main"

# Listening ports
lsof -i :PORT -P -n | grep LISTEN

# Environment variables (sanitized)
# PID from above
lsof -p $PID 2>/dev/null | grep -E "^p|^fcwd|^n/"
```

**Required env vars to capture:**
- `WORLDAI_DEV_MODE`
- `PORT`
- `FIREBASE_PROJECT_ID`

### Evidence Directory Structure

Standard layout for evidence bundles:

```
/tmp/{feature}_api_tests_v{N}/
├── full_evidence_transcript.txt   # Human-readable log
├── api_completion_test.json       # Structured test results
├── api_completion_test.json.sha256
├── post_process_analysis.json     # Validation/regression checks
├── post_process_analysis.json.sha256
├── pip_freeze.txt                 # Python environment
├── pip_freeze.txt.sha256
├── evidence_capture.sh            # Reproducible script
└── run_api_completion_test.py     # Test runner
```

### For Production Claims

Evidence MUST include:
- Real server URL (not localhost for production claims)
- Actual API responses with timestamps
- Real data from database/logs
- Specific values that prove execution (e.g., dice roll results)

### For Prompt Enforcement Claims

If you claim a specific system instruction or enforcement block was included in a live LLM call:
- Capture runtime system instruction text from the actual request (debug output or logs)
- Tie it to the same execution that produced the response (timestamp + request/response evidence)
- Static code references alone are insufficient

**Runtime Capture Mechanism (WorldArchitect.AI):**

```bash
# Start server (system instruction capture is always enabled)
CAPTURE_SYSTEM_INSTRUCTION_MAX_CHARS=120000 \
WORLDAI_DEV_MODE=true \
PORT=8005 \
python -m mvp_site.main serve
```

The captured system instruction will appear in `debug_info.system_instruction_text` in API responses.

### For Integration Claims

Evidence MUST show:
- Configuration enabling the integration
- Automatic triggering (not manual invocation)
- Logs proving automatic execution with timestamps

### For Bug Fix Claims

Evidence MUST include:
- Reproduction of original bug (before fix)
- Same scenario with fix applied
- Different outcome proving fix works

### For LLM/API Behavior Claims

When proving LLM or API behavior, evidence MUST capture the full request/response cycle:

**Required captures:**
1. **Raw request payload** - The exact input sent to the API/LLM
2. **Raw response payload** - The exact output returned, before any parsing or transformation
3. **System instructions/prompts** - The full prompt text sent to the LLM (not just a reference to a file)
4. **Timestamps** - When each request was made and response received

**Why raw capture matters:**
- Parsed/transformed responses may hide LLM misbehavior
- System instruction files may differ from what was actually sent at runtime
- Summaries can mask edge cases or errors

**Capture format:**
```
request_responses.jsonl   # One JSON object per line, each containing:
{
  "timestamp": "ISO8601",
  "request": { ... full request ... },
  "response": { ... full response ... },
  "debug_info": {
    "system_instruction_text": "actual prompt sent",
    "raw_response_text": "LLM output before parsing"
  }
}
```

**Server configuration:**
- Enable full request/response logging in your server
- Set capture limits high enough to avoid truncation (e.g., 80K+ chars for LLM responses)
- Capture system instructions at runtime, not just file references

### For Test Result Portability

Test output files should be self-contained with embedded provenance:

```json
{
  "test_name": "feature_validation",
  "timestamp": "2025-12-27T05:00:00Z",
  "provenance": {
    "git_head": "abc123def456...",
    "git_branch": "feature-branch",
    "server_url": "http://localhost:8001"
  },
  "steps": [ ... ],
  "summary": { ... }
}
```

**Why embedded provenance:**
- Evidence bundle can be shared/moved without losing context
- Validates that test ran against claimed code version
- External provenance files can get separated from results

## Bulletproof Evidence Requirements (v3 Lessons)

These requirements elevate evidence from "probably correct" to "provably correct."

### Command Output with Exit Codes

**Assertions are not evidence.** Capture raw command output AND exit codes:

```bash
# ❌ BAD - Assertion only
echo "Fix commit is ancestor of test HEAD"

# ✅ GOOD - Raw output with exit code
echo "Command: git merge-base --is-ancestor $FIX_COMMIT $TEST_HEAD"
git merge-base --is-ancestor $FIX_COMMIT $TEST_HEAD
ANCESTRY_EXIT=$?
echo "Exit code: $ANCESTRY_EXIT"
echo "Interpretation: Exit 0 = TRUE (is ancestor), Exit 1 = FALSE (not ancestor), 128+ = error"
```

### Working Directory Anchor

**Every git command needs context.** Capture `pwd` to prove which repo:

```bash
echo "Working directory: $(pwd)"
echo "Git root: $(git rev-parse --show-toplevel)"
git rev-parse HEAD
```

### CI Checks Tied to HEAD SHA

**PR checks don't prove which commit was tested.** Link checks to specific SHA:

```bash
# Get the HEAD SHA being tested
HEAD_SHA=$(git rev-parse HEAD)

# Fetch check runs for that specific SHA
# Note: :owner/:repo is auto-inferred from git remote when run in a cloned repo
gh api repos/:owner/:repo/commits/$HEAD_SHA/check-runs \
  --jq '.check_runs[] | {name, status, conclusion, html_url}'
```

**Filter out placeholder checks:**
- Exclude checks with empty `html_url` or `completedAt = 0001-01-01T00:00:00Z`
- Exclude external links (e.g., `cursor.com`) that aren't GH Action runs

### Server-Process Git Linkage

**Server health ≠ server code version.** Tie gunicorn PID to its git state:

```bash
# Get gunicorn process listening on port 8005
PID=$(pgrep -f "gunicorn.*:8005" | head -1)

# Get its working directory (cross-platform)
if [ -L "/proc/$PID/cwd" ]; then
  SERVER_CWD=$(readlink -f "/proc/$PID/cwd")  # Linux
else
  SERVER_CWD=$(lsof -a -p "$PID" -d cwd 2>/dev/null | tail -1 | awk '{print $NF}')  # macOS
fi

# Verify git HEAD in server's working directory
git -C "$SERVER_CWD" rev-parse HEAD
```

### Timestamp Synchronization

**Spread-out timestamps break provenance chains.** Collect all evidence in one pass:

```bash
#!/bin/bash
# Single-pass evidence collection
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVIDENCE_DIR="/tmp/evidence_$(date +%s)"
mkdir -p "$EVIDENCE_DIR"

# Capture all state in rapid succession (< 60 seconds)
echo "Collection started: $TIMESTAMP" > "$EVIDENCE_DIR/log.txt"
curl -s http://localhost:8005/health >> "$EVIDENCE_DIR/server_state.txt"
git rev-parse HEAD >> "$EVIDENCE_DIR/git_state.txt"
# Run test
python test.py >> "$EVIDENCE_DIR/test_output.txt"
echo "Collection ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$EVIDENCE_DIR/log.txt"
```

### Summary vs Raw Data Consistency

**Automated summaries must match raw data.** Always verify:

```bash
# If summary says "Copilot comments: 4"
# Raw data MUST show 4 entries with user.login matching
# Example: raw data shows .user.login == "Copilot" (not "github-copilot[bot]")

# ❌ BAD - Exact match misses variations
jq '[.[] | select(.user.login == "github-copilot[bot]")]'  # Misses "Copilot"

# ✅ GOOD - Case-insensitive pattern matching
jq '[.[] | select(.user.login | test("copilot"; "i"))]'
```

## Anti-Patterns

- **"Tests pass" without evidence type** - Mock tests passing ≠ production working
- **Health endpoint only** - Proves server is up, not that features work
- **Endpoint existence** - tools/list returning tools ≠ tools executing correctly
- **Assuming mock = real** - Mock data is fabricated; production data is evidence
- **Assertions without command output** - "Exit code 0" without showing the command
- **Timestamp gaps** - Server captured at T, test run at T+1hr breaks provenance
- **Summary/raw mismatch** - Automated counts that don't match raw data

## When to Stop and Ask

If you're about to:
- Run mock mode for production validation → STOP, use real mode
- Claim "tests pass" without specifying mode → STOP, clarify mode
- Skip actual execution evidence → STOP, collect real evidence
- Trust health checks as feature validation → STOP, test actual features

## Related Standards

- `CLAUDE.md` - Three Evidence Rule (lines 110-113)
- `generatetest.toml` - Mock mode prohibition (lines 433-441)
- `end2end-testing.md` - Test mode commands (/teste, /tester, /testerc)
- `browser-testing-ocr-validation.md` - OCR evidence for visual claims
