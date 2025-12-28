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

**Checksum usability requirement:** `.sha256` files must reference the **local basename**
(e.g., `evidence.json`), not a nested path like `artifacts/run_.../evidence.json`.
This ensures `sha256sum -c` works when run from the evidence directory.

### Evidence Package Consistency (NEW)

**Single-run attribution:** If a bundle contains multiple runs, the docs **must**
name the exact run directory used for claims (e.g., `run_YYYYMMDD...`). Claims
must be traceable to one run only.

**Doc ↔ data alignment:** Any item lists in methodology/evidence **must** be
derived from actual test inputs or `game_state_snapshot.json`. Hardcoded or
handwritten lists are invalid.

**Threshold capture:** If pass/fail depends on thresholds (e.g.,
`min_narrative_items`), those values must be recorded in `evidence.json` or the
methodology so reviewers can verify the criteria.

**Environment claims:** Only claim env vars that are read from the actual
environment during the run (or omit them).

**Unsupported claims:** CI status, Copilot analysis, or external validations
must include their own evidence artifacts, otherwise omit those claims.

**Bug-fix classification:** If a bundle labels a change as "new feature" to
avoid before/after evidence, it must include a justification. Otherwise, for
bug-fix claims, include a pre-fix reproduction and a post-fix run.


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

**Canonical format** (use `/savetmp` command):

```
/tmp/<repo>/<branch>/<work>/<timestamp>/
├── README.md              # Package manifest with git provenance
├── README.md.sha256
├── methodology.md         # Testing methodology documentation
├── methodology.md.sha256
├── evidence.md            # Evidence summary with metrics
├── evidence.md.sha256
├── notes.md               # Additional context, TODOs, follow-ups
├── notes.md.sha256
├── metadata.json          # Machine-readable: git_provenance, timestamps
├── metadata.json.sha256
└── artifacts/             # Copied evidence files (test outputs, logs, etc.)
    └── <copied files with checksums>
```

**Usage:**
```bash
python .claude/commands/savetmp.py "<work-name>" \
  --methodology "Testing approach description" \
  --evidence "Results summary" \
  --notes "Follow-up notes" \
  --artifact /path/to/test/output
```

**Legacy format** (still valid for specialized tests):

```
/tmp/{feature}_api_tests_v{N}/
├── full_evidence_transcript.txt   # Human-readable log
├── api_completion_test.json       # Structured test results
├── api_completion_test.json.sha256
├── post_process_analysis.json     # Validation/regression checks
├── post_process_analysis.json.sha256
└── evidence_capture.sh            # Reproducible script
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

**Lightweight Prompt Tracking (for high-volume tests):**

When full text capture is impractical (>50KB per response), use the lightweight alternative:
- `debug_info.system_instruction_files`: List of prompt files loaded (e.g., `["prompts/master_directive.md", "prompts/game_state_instruction.md"]`)
- `debug_info.system_instruction_char_count`: Total character count of combined prompts

This proves which prompts were used without the ~100KB overhead per response. The file list provides provenance while keeping evidence bundles manageable.

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

### For New Feature Claims

New features don't require "before" evidence since there's no prior behavior to compare.
Instead, prove:
- Feature works as specified (test results with pass/fail counts)
- Correct prompts/code were used (`system_instruction_files` or code paths)
- State changes correctly (game_state snapshots, database records)

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

## Documentation-Data Alignment (Lessons from equipc Review)

When generating evidence documentation (methodology, evidence summary, notes), these rules prevent common mismatches:

### 1. Derive All Claims from Actual Data

**Never hardcode documentation content.** Generate it from source data:

```python
# ❌ BAD - Hardcoded claim
methodology = "WORLDAI_DEV_MODE=true"

# ✅ GOOD - Read from actual environment
dev_mode = os.environ.get("WORLDAI_DEV_MODE", "not set")
methodology = f"WORLDAI_DEV_MODE: {dev_mode}"
```

### 2. Warn on Missing/Dropped Data

**Silent drops hide real mismatches.** Track and report edge cases:

```python
# ❌ BAD - Silently skip missing items
items = [registry[id] for id in seeds if id in registry]

# ✅ GOOD - Track and warn
missing_ids = []
items = []
for id in seeds:
    if id in registry:
        items.append(registry[id])
    else:
        missing_ids.append(id)
if missing_ids:
    notes += f"WARNING: Missing IDs: {missing_ids}"
```

### 3. Display Denominators Must Match Totals

**"Found X/Y (need Z)" must use correct Y.** Common mistake: using min_required as denominator:

```python
# ❌ BAD - Misleading: "4/2 (need 2)" suggests 200% match
stats_col = f"{found}/{min_required} (need {min_required})"

# ✅ GOOD - Clear: "4/4 (need 2)" shows 4 of 4 found, 2 was minimum
stats_col = f"{found}/{len(total_required)} (need {min_required})"
```

### 4. Avoid Unverifiable Scope Claims

**Don't claim "bug fix" vs "new feature" unless explicit.** These are product decisions:

```python
# ❌ BAD - Makes unverifiable claim
methodology += "## New Feature (Not Bug Fix)\nThis is a new feature..."

# ✅ GOOD - Stick to verifiable facts
methodology += "## Test Scope\nValidates equipment display functionality."
```

### 5. Always Check Subprocess Return Codes

**Subprocess output alone doesn't prove success.** Check returncode:

```python
# ❌ BAD - Ignores failures
result = subprocess.run(cmd, capture_output=True)
print(result.stdout)

# ✅ GOOD - Warns on failure
result = subprocess.run(cmd, capture_output=True)
print(result.stdout)
if result.returncode != 0:
    print(f"WARNING: Command exited with code {result.returncode}")
```

### 6. Single Run Attribution

**Evidence bundles must reference exactly ONE test run.** Ambiguous artifact scope breaks traceability:

```python
# ❌ BAD - Copies entire directory with multiple runs
--artifact /path/to/all_runs/

# ✅ GOOD - Copies specific run only
--artifact /path/to/all_runs/run_20251227T051227_953691
```

## Anti-Patterns

- **"Tests pass" without evidence type** - Mock tests passing ≠ production working
- **Health endpoint only** - Proves server is up, not that features work
- **Endpoint existence** - tools/list returning tools ≠ tools executing correctly
- **Assuming mock = real** - Mock data is fabricated; production data is evidence
- **Assertions without command output** - "Exit code 0" without showing the command
- **Timestamp gaps** - Server captured at T, test run at T+1hr breaks provenance
- **Summary/raw mismatch** - Automated counts that don't match raw data
- **Hardcoded env claims** - Claiming WORLDAI_DEV_MODE=true without reading os.environ
- **Silent data drops** - Skipping missing items without warning hides mismatches
- **Wrong denominators** - Display showing "4/2" when there are 4 total items

## When to Stop and Ask

If you're about to:
- Run mock mode for production validation → STOP, use real mode
- Claim "tests pass" without specifying mode → STOP, clarify mode
- Skip actual execution evidence → STOP, collect real evidence
- Trust health checks as feature validation → STOP, test actual features

## Self-Contained Evidence Files

Evidence JSON files must use **relative paths** for portability:

```json
// ❌ BAD - Absolute paths break when bundle is moved
{
  "artifacts_dir": "/tmp/worktree_worker7/dev123/e2e_test",
  "output_file": "/tmp/worktree_worker7/dev123/results.json"
}

// ✅ GOOD - Relative paths work anywhere
{
  "artifacts_dir": "./artifacts",
  "output_file": "./results.json"
}
```

**Post-processing requirement:** After copying test output into a bundle:
1. Validate all embedded paths are relative
2. If absolute paths exist, update them to be bundle-relative
3. Or document the original source location separately

## Single Checksum Layer

Evidence bundles must have **exactly one layer** of checksums:

| Strategy | When to Use |
|----------|-------------|
| Per-file `.sha256` | Simple bundles, few files |
| Root `checksums.sha256` | Complex bundles, many files |
| **NEVER both** | Causes `.sha256.sha256` pollution |

**When packaging artifacts that already have checksums:**

```bash
# Use --clean-checksums with /savetmp
python .claude/commands/savetmp.py "work-name" \
  --artifact /path/to/source \
  --clean-checksums  # Removes existing .sha256 before packaging
```

**Manual cleanup if needed:**

```bash
# Remove all .sha256 files from artifact source before copying
find /path/to/source -name "*.sha256" -delete

# Then create fresh checksums at bundle level
cd /bundle/root
find . -type f ! -name "*.sha256" -exec sha256sum {} \; > checksums.sha256
```

## PR Mode for Full Diff Capture

When creating evidence for a PR, use `--pr-mode` to capture the full diff:

```bash
# Default: uses upstream or last commit (may miss PR context)
python .claude/commands/savetmp.py "evidence-name" --artifact ./results

# PR mode: always uses origin/main...HEAD (full PR diff)
python .claude/commands/savetmp.py "evidence-name" --artifact ./results --pr-mode
```

**Why this matters:**
- Default mode captures `HEAD~1..HEAD` (last commit only)
- After merging main, this shows merge changes, not PR changes
- PR mode always captures `origin/main...HEAD` (full PR diff)

## Related Standards

- `CLAUDE.md` - Three Evidence Rule (lines 110-113)
- `generatetest.toml` - Mock mode prohibition (lines 433-441)
- `end2end-testing.md` - Test mode commands (/teste, /tester, /testerc)
- `browser-testing-ocr-validation.md` - OCR evidence for visual claims
