--- 
description: /generatetest - Evidence-Based Test Generator (Real Mode Only)
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately.**
**This is NOT documentation - these are COMMANDS to execute right now.**

**MANDATORY**: Read `.claude/skills/evidence-standards.md` before generating any test code.
This ensures generated tests follow current evidence standards.

## 🚨 CORE PRINCIPLES

**REAL MODE ONLY**: All generated tests use real local servers, real databases, nothing mocked.
**EVIDENCE-FIRST**: Tests generate evidence bundles directly to `/tmp/<repo>/<branch>/<work>/<timestamp>/`.
**USE SHARED LIBRARIES**: ALWAYS use `testing_mcp/lib/` utilities - NEVER reimplement test infrastructure.
**FREE-FORM INPUT**: Accept natural language like "for this PR make sure the equipment logic works".

## 🔧 MANDATORY: USE SHARED LIBRARY UTILITIES

**⚠️ CRITICAL RULE**: ALWAYS use functions from `testing_mcp/lib/` - NEVER reimplement them.

### Available Shared Utilities

| Module | Functions | Purpose |
|--------|-----------|---------|
| **`lib/evidence_utils.py`** | `get_evidence_dir(test_name)` | Get `/tmp/<repo>/<branch>/<test_name>` path |
| | `capture_provenance(base_url, server_pid=None)` | Capture git + server provenance |
| | `save_evidence(evidence_dir, data, filename)` | Save with SHA256 checksum |
| | `write_with_checksum(path, content)` | Write file with checksum |
| | `create_evidence_bundle(evidence_dir, ...)` | Create complete evidence bundle |
| | `save_request_responses(evidence_dir, pairs)` | Save request/response JSONL |
| **`lib/mcp_client.py`** | `MCPClient(base_url, timeout)` | MCP JSON-RPC client |
| | `client.tools_call(tool_name, args)` | Call MCP tool |
| **`lib/campaign_utils.py`** | `create_campaign(client, user_id, ...)` | Create campaign via MCP |
| | `process_action(client, user_id, campaign_id, ...)` | Process player action |
| | `get_campaign_state(client, user_id, campaign_id)` | Get game state |
| | `ensure_game_state_seed(client, user_id, campaign_id)` | Seed basic game state |
| **`lib/server_utils.py`** | `start_local_mcp_server(port)` | Start local test server |
| | `pick_free_port(start)` | Find available port |
| | `DEFAULT_EVIDENCE_ENV` | Environment vars for evidence capture |
| **`lib/model_utils.py`** | `settings_for_model(model_id)` | Get model-specific settings |
| | `update_user_settings(client, user_id, settings)` | Update user model settings |
| **`lib/narrative_validation.py`** | `validate_narrative_quality(narrative)` | Validate narrative structure |
| | `extract_dice_notation(text)` | Extract dice rolls from text |

### Required Import Pattern

```python
#!/usr/bin/env python3
"""Generated test - uses shared lib utilities."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ✅ MANDATORY: Import from shared libraries
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    get_evidence_dir,
    save_evidence,
    create_evidence_bundle,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import create_campaign, process_action
from testing_mcp.lib.model_utils import settings_for_model, update_user_settings

# ❌ NEVER reimplement these functions in the test file
```

### What You MUST NOT Reimplement

**❌ FORBIDDEN - These already exist in `lib/`:**
- `def capture_provenance()` → Use `lib/evidence_utils.capture_provenance()`
- `def get_evidence_dir()` → Use `lib/evidence_utils.get_evidence_dir()`
- `def save_evidence()` → Use `lib/evidence_utils.save_evidence()`
- `def write_with_checksum()` → Use `lib/evidence_utils.write_with_checksum()`
- `def create_campaign()` → Use `lib/campaign_utils.create_campaign()`
- `def process_action()` → Use `lib/campaign_utils.process_action()`
- Custom MCP client code → Use `lib/mcp_client.MCPClient`

**✅ REQUIRED Pattern:**
```python
# Get evidence directory
evidence_dir = get_evidence_dir("my_test_name")

# Capture provenance
provenance = capture_provenance(base_url="http://localhost:8001")

# Create campaign
client = MCPClient(base_url)
campaign_id = create_campaign(
    client,
    user_id="test-user",
    title="Test Campaign",
)

# Process action
response = process_action(
    client,
    user_id="test-user",
    campaign_id=campaign_id,
    user_input="I attack the goblin",
)

# Save evidence
save_evidence(evidence_dir, test_results, "results.json")
```

**Benefits of Using Shared Libraries:**
1. **Automatic standards compliance** - Evidence follows `.claude/skills/evidence-standards.md`
2. **Zero maintenance burden** - Updates benefit all tests automatically
3. **Consistent behavior** - All tests use identical evidence structure
4. **Reduced duplication** - No need to copy/paste utility code
5. **Single source of truth** - Centralized in `testing_mcp/lib/`

## 📁 OUTPUT LOCATIONS

| Output Type | Default Location | Override Flag |
|-------------|------------------|---------------|
| **Test files** | `testing_mcp/` | `--test-dir <path>` |
| **Evidence** | `/tmp/<repo>/<branch>/<work>/iteration_NNN/` | `--evidence-dir <path>` |

**Versioning (v1.1.0+):** Evidence bundles now use iteration-based directories:
- Each run creates `iteration_001/`, `iteration_002/`, etc.
- `latest` symlink points to most recent iteration
- `metadata.json` includes `run_id`, `iteration`, `bundle_version`

## 🚨 EXECUTION WORKFLOW

### Phase 1: Parse Free-Form Input

**Action Steps:**
1. Extract test focus from natural language input (e.g., "equipment logic", "dice rolls", "campaign creation")
2. Identify PR context if mentioned (e.g., "for this PR" → analyze current branch changes)
3. Determine test type: MCP integration, browser automation, or hybrid
4. Generate descriptive `work_name` for evidence directory

**Example Parsing:**
```
Input: "for this PR make sure the equipment logic works"
→ Focus: equipment logic
→ Context: current PR/branch changes
→ Type: MCP integration (equipment = game state)
→ work_name: equipment_validation
```

### Phase 2: Generate Test File

**Action Steps:**
1. Create test file in `testing_mcp/test_<focus>.py` (or custom `--test-dir`)
2. Include self-contained evidence generation (methodology, evidence, notes)
3. Add `--work-name` CLI argument (evidence saving is mandatory, no flag needed)
4. Always start fresh local server with free port (unless `--server` provided)
5. Ensure test uses REAL servers (no mocks, no test mode)

**Generated Test Structure:**
```python
#!/usr/bin/env python3
"""
Generated by /generatetest - Evidence-Based Test
Focus: [extracted focus]
Work Name: [work_name]

REAL MODE ONLY - No mocks, no test mode
Evidence standards: .claude/skills/evidence-standards.md
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ✅ MANDATORY: Use shared library utilities
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_evidence,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import create_campaign, process_action
from testing_mcp.lib.model_utils import settings_for_model, update_user_settings

# Test configuration
WORK_NAME = "[work_name]"
DEFAULT_MODEL = "gemini-3-flash-preview"  # Pin model to avoid fallback noise

# ✅ MANDATORY: Import server utilities for fresh server startup
from testing_mcp.lib.server_utils import start_local_mcp_server, pick_free_port

# ❌ REMOVED: get_next_iteration() - use lib/evidence_utils.get_evidence_dir() instead
# ❌ REMOVED: get_evidence_dir() - use lib/evidence_utils.get_evidence_dir() instead
# ❌ REMOVED: capture_git_provenance() - use lib/evidence_utils.capture_provenance() instead
# ❌ REMOVED: write_with_checksum() - use lib/evidence_utils.write_with_checksum() instead
# ❌ REMOVED: save_evidence() - use lib/evidence_utils.create_evidence_bundle() instead


def run_tests(server_url: str) -> list:
    """Run actual tests against real server - implement test logic here."""
    client = MCPClient(server_url)
    user_id = f"test-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Pin model to avoid fallback noise
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    # Test implementation - example
    results = []
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Test Campaign",
    )

    response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I attack the goblin",
    )

    # Validate response and record result
    passed = "narrative" in response and response["narrative"]
    errors = [] if passed else ["Failed to process action"]
    results.append({
        "name": "basic_action",
        "passed": passed,
        "errors": errors,
        "campaign_id": campaign_id,
        "details": "Action processed successfully" if passed else "Failed to process action",
    })

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-name", default=WORK_NAME)
    parser.add_argument("--server", help="Optional: use existing server URL (default: start fresh)")
    args = parser.parse_args()

    # ✅ MANDATORY: Always start fresh local server with free port
    local_server = None
    server_url = args.server
    
    if not server_url:
        # Start fresh server on free port
        port = pick_free_port()
        print(f"🚀 Starting fresh local MCP server on port {port}...")
        local_server = start_local_mcp_server(port)
        server_url = local_server.base_url
        
        # Wait for server to be ready
        client = MCPClient(server_url)
        client.wait_healthy(timeout_s=30.0)
        print(f"✅ Server ready at {server_url}")

    try:
        # Run tests against REAL server
        results = run_tests(server_url)

        # ✅ MANDATORY: Always save evidence (no optional flag)
        evidence_dir = get_evidence_dir(args.work_name)
        server_pid = local_server.pid if local_server else None
        provenance = capture_provenance(server_url, server_pid=server_pid)

        # Create evidence bundle using shared lib
        bundle_files = create_evidence_bundle(
            evidence_dir=evidence_dir,
            test_name=args.work_name,
            results={"scenarios": results, "summary": {"total_scenarios": len(results)}},
            provenance=provenance,
            server_log_path=local_server.log_path if local_server else None,
        )

        print(f"📦 Evidence bundle created: {evidence_dir}")
        print(f"   Files: {len(bundle_files)} with checksums")
    finally:
        # Clean up local server if we started it
        if local_server:
            print("🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
```

### Phase 3: Add Evidence Standards Compliance

**Action Steps:**
1. Include git provenance capture (HEAD, origin/main, changed files)
2. Add server environment capture (process info, ports, env vars)
3. Derive ALL documentation from actual data (never hardcode)
4. Track missing/dropped data with warnings
5. Check subprocess return codes

**Evidence Standards Checklist (from `.claude/skills/evidence-standards.md`):**
- [ ] Git provenance: HEAD commit, origin/main, changed files (via `capture_git_provenance()`)
- [ ] Server environment: PID, port, env vars (via `capture_server_runtime()`)
- [ ] Checksums: SHA256 for ALL evidence files including JSONL and server logs
- [ ] Timestamp synchronization: collect all evidence in one pass
- [ ] Documentation-Data alignment: derive claims from actual data
- [ ] Centralized utilities: use `lib/evidence_utils.py`
- [ ] Raw capture: use `DEFAULT_EVIDENCE_ENV` from `server_utils.py` for automatic raw LLM capture
- [ ] JSONL file: create `request_responses.jsonl` with full request/response pairs
- [ ] Server logs: copy to `artifacts/server.log` with checksum
- [ ] Evidence mode: document capture approach with `evidence_mode` field

### Phase 4: Verify Real Mode

**Action Steps:**
1. Confirm server is running on expected port
2. Verify WORLDAI_DEV_MODE setting
3. Ensure NO mock imports or test mode flags
4. Validate API responses are from real server

**🚨 MOCK MODE = INVALID EVIDENCE**:
- ❌ FORBIDDEN: `TESTING=true`, mock imports, fake services
- ❌ FORBIDDEN: Hardcoded responses or placeholder data
- ✅ REQUIRED: Real local server, real database, real API responses

## 📋 REFERENCE DOCUMENTATION

# /generatetest - Evidence-Based Test Generator

**Purpose**: Generate self-contained tests with built-in evidence generation

**Usage**: `/generatetest <free-form description>`

**Examples:**
```bash
/generatetest for this PR make sure the equipment logic works
/generatetest validate dice roll integrity in combat
/generatetest test campaign creation flow end-to-end
```

## 🔍 TEST TYPE DETECTION

**Automatic Detection from Free-Form Input:**

| Keywords | Test Type | Example Input |
|----------|-----------|---------------|
| `equipment`, `inventory`, `items`, `game_state` | MCP Integration | "equipment logic works" |
| `dice`, `roll`, `combat`, `damage` | MCP Integration | "dice rolls are fair" |
| `campaign`, `create`, `firebase` | MCP Integration | "campaign creation flow" |
| `browser`, `ui`, `page`, `click` | Browser Automation | "landing page loads correctly" |
| `login`, `oauth`, `auth` | Browser + Auth | "login flow works" |

**Default**: MCP Integration (most common for this project)

## 📊 GENERATED TEST REQUIREMENTS

Every generated test MUST include:

### 1. Evidence Generation - Use Shared Lib
```python
# ❌ FORBIDDEN: Custom evidence generation
# def save_evidence(...):
#     """DON'T implement this - it exists in lib/evidence_utils.py"""

# ✅ REQUIRED: Use lib utilities
from testing_mcp.lib.evidence_utils import create_evidence_bundle

# Generate evidence bundle
evidence_dir = get_evidence_dir("my_test")
provenance = capture_provenance(server_url)

bundle_files = create_evidence_bundle(
    evidence_dir=evidence_dir,
    test_name="my_test",
    results=test_results,
    provenance=provenance,
    server_url=server_url,
)
# Bundle automatically includes:
# - README.md, methodology.md, evidence.md, notes.md
# - run.json with scenarios
# - metadata.json with git provenance
# - SHA256 checksums for all files
```

### 2. CLI Arguments
```python
parser.add_argument("--work-name", default="<auto_generated>")
parser.add_argument("--server", help="Optional: use existing server URL (default: start fresh)")
# Note: Evidence saving is MANDATORY - no flag needed
```

### 3. Real Mode Verification
```python
def verify_real_mode(server_url):
    """Verify server is real, not mocked."""
    response = requests.get(f"{server_url}/health")
    assert response.status_code == 200
    assert "mock" not in response.text.lower()
```

### 4. Model Settings Forcing
```python
from lib.model_utils import settings_for_model, update_user_settings

DEFAULT_MODEL = "gemini-3-flash-preview"

# Pin model at test start to avoid fallback noise
update_user_settings(
    client,
    user_id=user_id,
    settings=settings_for_model(DEFAULT_MODEL),
)
```

### 5. Request/Response Capture (MANDATORY for behavior claims)
```python
from lib.evidence_utils import save_request_responses

# Track all MCP tool calls
request_responses: list[dict] = []

# After each action, capture request/response pair
request_responses.append({
    "request": {"tool": "process_action", "user_id": user_id, ...},
    "response": action_response,
})

# Save to JSONL at end
save_request_responses(evidence_dir, request_responses)
```

**Minimal inline helper if not using evidence_utils:**
```python
def save_request_responses(evidence_dir: Path, pairs: list[dict]):
    """Write request/response pairs to JSONL with checksum."""
    jsonl_path = evidence_dir / "request_responses.jsonl"
    with jsonl_path.open("w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    # Generate checksum
    sha256 = hashlib.sha256(jsonl_path.read_bytes()).hexdigest()
    (evidence_dir / "request_responses.jsonl.sha256").write_text(
        f"{sha256}  request_responses.jsonl\n"
    )
```

### 6. Server Runtime Artifacts (REQUIRED for integration claims)
```python
import subprocess

def capture_server_artifacts(evidence_dir: Path, port: int, server_pid: int | None):
    """Capture server runtime state for evidence."""
    artifacts_dir = evidence_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    # lsof - what's listening on the port
    try:
        lsof_output = subprocess.check_output(
            ["lsof", "-i", f":{port}", "-P", "-n"],
            stderr=subprocess.STDOUT, text=True
        )
        (artifacts_dir / "lsof_output.txt").write_text(lsof_output)
    except subprocess.CalledProcessError:
        pass

    # ps - process info
    if server_pid:
        try:
            ps_output = subprocess.check_output(
                ["ps", "-p", str(server_pid), "-o", "pid,ppid,user,etime,command"],
                stderr=subprocess.STDOUT, text=True
            )
            (artifacts_dir / "ps_output.txt").write_text(ps_output)
        except subprocess.CalledProcessError:
            pass
```

### 7. Git Provenance Capture - Use Shared Lib
```python
# ❌ FORBIDDEN: Custom git provenance capture
# def capture_git_provenance():
#     """DON'T implement this - it exists in lib/evidence_utils.py"""

# ✅ REQUIRED: Use lib utility
from testing_mcp.lib.evidence_utils import capture_provenance

# Capture git + server provenance
provenance = capture_provenance(
    base_url="http://localhost:8001",
    server_pid=None,  # Optional - will auto-detect if not provided
)

# Returns:
# {
#     "git_head": "abc123...",
#     "git_branch": "feature/xyz",
#     "git_origin_main": "def456...",
#     "changed_files": ["file1.py", "file2.py"],
#     "server_url": "http://localhost:8001",
#     "server_pid": 12345,
#     "lsof_output": "...",  # What's listening on the port
#     "ps_output": "...",     # Process info
# }
```

> The shared lib version handles missing remotes, detached HEADs, and filters empty
> strings from changed_files automatically. It also captures server runtime state.

## 🚨 EVIDENCE STANDARDS COMPLIANCE

From `.claude/skills/evidence-standards.md`:

| Requirement | Implementation |
|-------------|----------------|
| **Derive claims from data** | `os.environ.get()`, not hardcoded strings |
| **Warn on missing data** | Track `missing_item_ids` list, add to notes |
| **Correct denominators** | `found/total (need min)`, not `found/min` |
| **Check return codes** | `if result.returncode != 0: warn()` |
| **Single run attribution** | Evidence bundle references ONE test run |
| **Git provenance** | HEAD, origin/main, changed files |
| **Checksums** | SHA256 via `write_with_checksum()` helper |
| **Self-contained** | No external script dependencies |
| **Per-scenario campaign_id** | Include `campaign_id` for each scenario in run.json |
| **Model matrix** | Test multiple models when behavior varies by provider |
| **Pass quality** | Track `pass_type: "strong"/"weak"` in results |
| **Partial state handling** | Check field presence, not just truthiness |
| **Scenario forcing** | Use high HP + explicit instructions to prevent shortcuts |

## 🔬 ADVANCED PATTERNS (from dice_rolls_comprehensive.py)

### Per-Scenario Campaign Isolation

When scenarios can pollute each other's context (e.g., LLM continuing previous combat):

```python
for scenario in TEST_SCENARIOS:
    # Create fresh campaign per scenario to avoid context pollution
    scenario_campaign_id = create_campaign(client, user_id)
    ensure_game_state_seed(client, user_id=user_id, campaign_id=scenario_campaign_id)

    result = process_action(client, campaign_id=scenario_campaign_id, ...)

    # Include campaign_id in evidence for log traceability
    run_summary["scenarios"].append({
        "name": scenario["name"],
        "campaign_id": scenario_campaign_id,  # ← Required
        ...
    })
```

### Model Matrix Testing

Test across multiple providers when behavior varies:

```python
DEFAULT_MODEL_MATRIX = [
    "gemini-3-flash-preview",      # code_execution strategy
    "qwen-3-235b-a22b-instruct",   # native_two_phase strategy
]

for model_id in models:
    model_settings = settings_for_model(model_id)
    # Run scenarios for each model...
```

### dice_audit_events Schema (for dice/RNG evidence)

```python
{
    "source": "code_execution" | "server_tool",
    "label": "Stealth Check",
    "notation": "1d20+1",
    "rolls": [10],
    "modifier": 1,
    "total": 11,
    "dc": 12,                    # Required for skill/save
    "dc_reasoning": "...",       # Required - proves DC set before roll
    "success": false             # Required for skill/save
}
```

### Pass Quality Classification

Track evidence strength in results:

```python
# Define pass criteria with quality levels
strong_pass = primary_condition and secondary_condition
weak_pass = primary_condition and not secondary_condition
passed = primary_condition  # Core requirement

result = {
    "status": "PASS" if passed else "FAIL",
    "pass_type": "strong" if strong_pass else ("weak" if weak_pass else "fail"),
    "primary_condition": primary_condition,
    "secondary_condition": secondary_condition,
}

# Output for evidence
if strong_pass:
    print("✅ TEST PASSED (STRONG): All conditions met")
elif weak_pass:
    print("✅ TEST PASSED (WEAK): Core proven, secondary not met")
else:
    print("❌ TEST FAILED: Core requirement not proven")
```

### Partial State Update Handling

APIs return only changed fields. Handle missing fields correctly:

```python
# ❌ BAD - Treats missing field as False
still_active = response.get("state", {}).get("active") is True

# ✅ GOOD - Check field presence with fallback
state = response.get("state", {})
if "active" in state:
    still_active = state["active"] is True
elif state.get("round_number") is not None:
    # Partial update with progress indicator - still active
    still_active = True
else:
    # Fall back to previous known state
    still_active = previous_state.get("active", False)
```

### LLM Scenario Forcing

Prevent LLM shortcuts with explicit constraints:

```python
# ❌ BAD - LLM may resolve in 1-2 actions
SCENARIO = "Fight the enemies"

# ✅ GOOD - Forces extended scenario
SCENARIO = """You face a Boss (CR 5, HP 120) with two Guards (HP 59 each).
This encounter CANNOT be resolved in fewer than 3 rounds.
DO NOT end prematurely. All enemies fight to the death."""
```

### Statistical Validation

For RNG-dependent features, include distribution tests:

```python
# Distribution test
for notation in ("1d6", "1d20"):
    rolls = [roll_dice(notation) for _ in range(200)]
    stats = {"count": len(rolls), "min": min(rolls), "max": max(rolls), "mean": sum(rolls)/len(rolls)}
    assert abs(stats["mean"] - expected_mean) < tolerance
```

## 🔧 PRIORITY MATRIX

```
🚨 CRITICAL: Blocks core functionality, data corruption risk
⚠️ HIGH: Significant degradation, wrong behavior
📝 MEDIUM: Minor issues, cosmetic problems
ℹ️ LOW: Documentation, edge cases
```

**Stop Rule**: 🚨 CRITICAL → Stop testing, fix immediately, verify, resume

## ✅ COMPLETION CRITERIA

- [ ] Test file created in `testing_mcp/` (or custom dir)
- [ ] Self-contained evidence generation (no external dependencies)
- [ ] **Fresh local server started** with free port (unless --server provided)
- [ ] **Evidence ALWAYS saved** (no optional flag)
- [ ] Real mode verified (no mocks, no TESTING=true)
- [ ] Git provenance captured
- [ ] All results derived from actual data
- [ ] Missing data tracked with warnings
- [ ] **run.json includes scenarios array** with campaign_id and errors
- [ ] **Model settings pinned** via update_user_settings()
- [ ] **request_responses.jsonl captured** for behavior claims
- [ ] **Server artifacts collected** (lsof, ps) for integration claims