"""Evidence capture and provenance utilities per evidence-standards.md.

This module provides evidence capture functions that comply with
.claude/skills/evidence-standards.md requirements.

Canonical evidence structure:
    /tmp/<repo>/<branch>/<work>/
    ├── iteration_001/           # First test run (auto-incremented)
    │   ├── README.md            # Package manifest with git provenance
    │   ├── methodology.md       # Testing methodology documentation
    │   ├── evidence.md          # Evidence summary with metrics
    │   ├── metadata.json        # Machine-readable: git_provenance, timestamps
    │   ├── request_responses.jsonl # Raw request/response payloads
    │   └── artifacts/           # Copied evidence files
    ├── iteration_002/           # Second test run
    └── latest -> iteration_002  # Symlink to most recent

Evidence Format Version:
    EVIDENCE_FORMAT_VERSION = "1.1.0"
    - 1.0.0: Initial format with canonical bundle structure
    - 1.1.0: Added versioning (bundle_version, iteration, run_id)
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Evidence format versioning
EVIDENCE_FORMAT_VERSION = "1.1.0"  # Current bundle format version


def _get_next_iteration(work_dir: Path) -> tuple[int, Path]:
    """Get the next iteration number and path for an evidence bundle.

    Scans for existing iteration_NNN directories and returns the next number.

    Args:
        work_dir: Parent directory (e.g., /tmp/repo/branch/test_name/)

    Returns:
        Tuple of (iteration_number, iteration_path).
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    # Find existing iteration directories
    existing = []
    for entry in work_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("iteration_"):
            match = re.match(r"iteration_(\d+)", entry.name)
            if match:
                existing.append(int(match.group(1)))

    next_num = max(existing) + 1 if existing else 1
    iteration_dir = work_dir / f"iteration_{next_num:03d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    # Update 'latest' symlink
    latest_link = work_dir / "latest"
    if latest_link.is_symlink():
        latest_link.unlink()
    elif latest_link.exists():
        # Remove if it's a file/dir (shouldn't happen)
        if latest_link.is_dir():
            shutil.rmtree(latest_link)
        else:
            latest_link.unlink()
    latest_link.symlink_to(iteration_dir.name)

    return next_num, iteration_dir


def _generate_run_id(test_name: str, iteration: int) -> str:
    """Generate a unique run ID for this evidence bundle.

    Format: {test_name}-{iteration:03d}-{timestamp}
    Example: llm_guardrails_exploits-003-20260101T221620

    Args:
        test_name: Name of the test.
        iteration: Iteration number.

    Returns:
        Unique run ID string.
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{test_name}-{iteration:03d}-{timestamp}"


def get_evidence_dir(test_name: str, run_id: str | None = None) -> Path:
    """Get evidence directory following /tmp/<repo>/<branch>/<test_name>[/<run_id>] pattern.

    Per evidence-standards.md, evidence should be saved in /tmp subdirectory.

    Args:
        test_name: Name of the test (e.g., "relationship_reputation")
        run_id: Optional run identifier or timestamp for nested directories.

    Returns:
        Path to evidence directory.
    """
    repo_name = "worldarchitect.ai"
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
    except Exception:
        branch = "unknown"

    evidence_dir = Path("/tmp") / repo_name / branch / test_name
    if run_id:
        evidence_dir = evidence_dir / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


def capture_git_provenance(fetch_origin: bool = True) -> dict[str, Any]:
    """Capture git provenance for evidence bundles.

    Args:
        fetch_origin: If True, fetch origin/main before capturing.

    Returns:
        Dict with git_head, git_branch, merge_base, commits_ahead_of_main, diff_stat_vs_main,
        origin_main, and working_directory when available.
    """
    provenance: dict[str, Any] = {"working_directory": str(PROJECT_ROOT)}
    try:
        if fetch_origin:
            fetch = subprocess.run(
                ["git", "fetch", "origin", "main"],
                check=False,
                cwd=str(PROJECT_ROOT),
                timeout=10,
                capture_output=True,
                text=True,
            )
            provenance["git_fetch_origin_main"] = {
                "returncode": fetch.returncode,
                "stdout": (fetch.stdout or "").strip() or None,
                "stderr": (fetch.stderr or "").strip() or None,
            }
        provenance["git_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["git_branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["origin_main"] = subprocess.check_output(
            ["git", "rev-parse", "origin/main"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["merge_base"] = subprocess.check_output(
            ["git", "merge-base", "HEAD", "origin/main"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["commits_ahead_of_main"] = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "origin/main..HEAD"],
                cwd=str(PROJECT_ROOT),
                text=True,
                timeout=5,
            ).strip()
        )
        provenance["diff_stat_vs_main"] = subprocess.check_output(
            ["git", "diff", "--stat", "origin/main...HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=10,
        ).strip()
    except Exception as e:
        provenance["git_error"] = str(e)
    return provenance


def capture_server_runtime(port: int | str) -> dict[str, Any]:
    """Capture server runtime info (pid, command line, lsof/ps outputs) for a port."""
    info: dict[str, Any] = {
        "port": str(port),
        "pid": None,
        "process_cmdline": None,
        "lsof_output": None,
        "ps_output": None,
    }
    try:
        lsof_output = subprocess.check_output(
            ["lsof", "-i", f":{port}", "-P", "-n"],
            text=True,
            timeout=5,
        ).strip()
        info["lsof_output"] = lsof_output
        # Extract first pid if present
        pids = [
            line.split()[1]
            for line in lsof_output.splitlines()[1:]
            if line.strip()
        ]
        if pids:
            info["pid"] = pids[0]
            try:
                info["process_cmdline"] = subprocess.check_output(
                    ["ps", "-p", str(info["pid"]), "-o", "command="],
                    text=True,
                    timeout=5,
                ).strip()
                info["ps_output"] = subprocess.check_output(
                    ["ps", "-p", str(info["pid"]), "-o", "pid,user,etime,args"],
                    text=True,
                    timeout=5,
                ).strip()
            except Exception as e:
                print(f"⚠️ Failed to capture ps output for PID {info['pid']}: {e}", flush=True)
    except Exception as e:
        print(f"⚠️ Failed to capture server runtime info: {e}", flush=True)
    return info


def capture_server_health(server_url: str) -> dict[str, Any]:
    """Capture server /health response for provenance."""

    health_url = f"{server_url.rstrip('/')}/health"
    try:
        req = urllib.request.Request(health_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "url": health_url,
                "status_code": response.status,
                "response": data,
                "captured_at": datetime.now(UTC).isoformat(),
            }
    except urllib.error.HTTPError as e:
        return {
            "url": health_url,
            "status_code": e.code,
            "error": str(e),
            "captured_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        return {
            "url": health_url,
            "error": str(e),
            "captured_at": datetime.now(UTC).isoformat(),
        }


def capture_full_provenance(
    port: int | str,
    base_url: str,
    *,
    fetch_origin: bool = True,
) -> dict[str, Any]:
    """Capture full provenance including git + server + health."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git": capture_git_provenance(fetch_origin=fetch_origin),
        "server": capture_server_runtime(port),
        "health": capture_server_health(base_url),
        "base_url": base_url,
    }


def capture_provenance(
    base_url: str,
    server_pid: int | None = None,
    *,
    server_env_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Capture git and server provenance per evidence-standards.md.

    Required fields:
    - provenance.git_head
    - provenance.git_branch
    - provenance.merge_base
    - provenance.commits_ahead_of_main
    - provenance.diff_stat_vs_main
    - provenance.server.pid
    - provenance.server.port
    - provenance.server.process_cmdline

    Args:
        base_url: Server base URL.
        server_pid: Process ID of the server (if known).
        server_env_overrides: Env vars that were explicitly set on the server process.
            These take precedence over os.environ for accurate provenance capture.

    Returns:
        Provenance dict with all required fields.
    """
    provenance: dict[str, Any] = {}

    # Git provenance
    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "main"],
            check=False,
            cwd=str(PROJECT_ROOT),
            timeout=10,
            capture_output=True,
            text=True,
        )
        provenance["git_fetch_origin_main"] = {
            "returncode": fetch.returncode,
            "stdout": (fetch.stdout or "").strip() or None,
            "stderr": (fetch.stderr or "").strip() or None,
        }
        provenance["git_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["git_branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["merge_base"] = subprocess.check_output(
            ["git", "merge-base", "HEAD", "origin/main"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=5,
        ).strip()
        provenance["commits_ahead_of_main"] = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "origin/main..HEAD"],
                cwd=str(PROJECT_ROOT),
                text=True,
                timeout=5,
            ).strip()
        )
        provenance["diff_stat_vs_main"] = subprocess.check_output(
            ["git", "diff", "--stat", "origin/main...HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=10,
        ).strip()
    except Exception as e:
        provenance["git_error"] = str(e)

    # Server runtime info - capture all required env vars per evidence-standards.md
    # CRITICAL: Use server_env_overrides when available - these are the ACTUAL values
    # that were set on the server process, not the test runner's environment.
    port = base_url.split(":")[-1].rstrip("/")
    env_vars_to_capture = [
        "WORLDAI_DEV_MODE",
        "TESTING",
        "MOCK_SERVICES_MODE",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS",  # WorldAI-specific credentials
        "FIRESTORE_EMULATOR_HOST",  # Emulator vs real Firestore indicator
        "PORT",
        "FIREBASE_PROJECT_ID",
        "GEMINI_API_KEY",  # Masked
    ]
    env_vars: dict[str, Any] = {}
    overrides = server_env_overrides or {}
    for var in env_vars_to_capture:
        # Prefer server_env_overrides (explicit server config) over os.environ (test runner)
        value = overrides.get(var) if var in overrides else os.environ.get(var)
        if value and "KEY" in var:
            # Fully mask API keys
            env_vars[var] = f"[SET - {len(value)} chars]"
        elif value and "CREDENTIALS" in var:
            # For credential files, show filename only (not full path) for evidence traceability
            env_vars[var] = f"[SET - file:{pathlib.Path(value).name}]"
        else:
            env_vars[var] = value

    provenance["server"] = {
        "port": port,
        "pid": server_pid,
        "process_cmdline": None,
        "env_vars": env_vars,
        "lsof_output": None,
        "ps_output": None,
    }

    if server_pid:
        try:
            cmdline = subprocess.check_output(
                ["ps", "-p", str(server_pid), "-o", "command="],
                text=True,
                timeout=5,
            ).strip()
            provenance["server"]["process_cmdline"] = cmdline

            # Capture full ps output for evidence
            ps_full = subprocess.check_output(
                ["ps", "-p", str(server_pid), "-o", "pid,user,etime,args"],
                text=True,
                timeout=5,
            ).strip()
            provenance["server"]["ps_output"] = ps_full
        except Exception:
            pass

        # Capture lsof output for port evidence
        try:
            lsof_output = subprocess.check_output(
                ["lsof", "-i", f":{port}", "-P", "-n"],
                text=True,
                timeout=5,
            ).strip()
            provenance["server"]["lsof_output"] = lsof_output
        except Exception:
            pass

    # Use UTC timestamp with timezone for consistency
    provenance["timestamp"] = datetime.now(UTC).isoformat()

    return provenance


def save_evidence(
    evidence_dir: Path,
    data: dict[str, Any],
    filename: str = "run.json",
) -> tuple[Path, Path]:
    """Save evidence JSON with SHA256 checksum per evidence-standards.md.

    Args:
        evidence_dir: Directory to save evidence.
        data: Evidence data dict.
        filename: Output filename (default: run.json).

    Returns:
        Tuple of (evidence_file_path, checksum_file_path).
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_file = evidence_dir / filename
    evidence_file.write_text(json.dumps(data, indent=2))

    # Generate checksum per evidence-standards.md
    checksum_file = evidence_dir / f"{filename}.sha256"
    with open(evidence_file, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()
    checksum_file.write_text(f"{sha256_hash}  {filename}\n")

    return evidence_file, checksum_file


def write_with_checksum(filepath: Path, content: str) -> str:
    """Write file and create SHA256 checksum file.

    Per evidence-standards.md, all evidence files should have checksums.
    The .sha256 file uses the basename format for portability.

    Args:
        filepath: Path to write content to.
        content: String content to write.

    Returns:
        The SHA256 hash of the content.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)

    sha256_hash = hashlib.sha256(content.encode()).hexdigest()
    checksum_file = Path(str(filepath) + ".sha256")
    # Use basename only for portability (evidence-standards.md requirement)
    checksum_file.write_text(f"{sha256_hash}  {filepath.name}\n")

    return sha256_hash


def save_request_responses(
    evidence_dir: Path,
    captures: list[dict[str, Any]],
) -> tuple[Path, str]:
    """Save raw request/response payloads as JSONL per evidence-standards.md.

    Per evidence-standards.md section "For LLM/API Behavior Claims", evidence
    MUST capture the full request/response cycle.

    Args:
        evidence_dir: Directory to save evidence.
        captures: List of request/response dicts from MCPClient.get_captures_as_dict().

    Returns:
        Tuple of (file_path, sha256_hash).
    """
    filepath = evidence_dir / "request_responses.jsonl"

    lines = [json.dumps(c) for c in captures]
    content = "\n".join(lines) + "\n" if lines else ""

    sha256_hash = write_with_checksum(filepath, content)
    return filepath, sha256_hash


def create_evidence_bundle(
    evidence_dir: Path,
    *,
    test_name: str,
    provenance: dict[str, Any],
    results: dict[str, Any],
    request_responses: list[dict[str, Any]] | None = None,
    methodology_text: str | None = None,
    server_log_path: Path | None = None,
    isolation_info: dict[str, Any] | None = None,
    use_iteration: bool = True,
) -> dict[str, Path]:
    """Create a complete evidence bundle per evidence-standards.md canonical format.

    Creates:
        - README.md: Package manifest with git provenance
        - methodology.md: Testing methodology documentation
        - evidence.md: Evidence summary with metrics
        - metadata.json: Machine-readable provenance and timestamps
        - request_responses.jsonl: Raw request/response payloads (if provided)
        - run.json: Test results
        - artifacts/server.log: Copy of server log (if provided)
        - artifacts/lsof_output.txt: Port binding evidence
        - artifacts/ps_output.txt: Process info evidence

    All files get .sha256 checksum files.

    With use_iteration=True (default), creates versioned structure:
        /tmp/<repo>/<branch>/<test_name>/iteration_001/
        /tmp/<repo>/<branch>/<test_name>/iteration_002/
        /tmp/<repo>/<branch>/<test_name>/latest -> iteration_002

    Args:
        evidence_dir: Directory to create bundle in (or parent for iteration mode).
        test_name: Name of the test for documentation.
        provenance: Git and server provenance dict from capture_provenance().
        results: Test results dict to save as run.json.
        request_responses: Optional list of request/response captures.
        methodology_text: Optional custom methodology text.
        server_log_path: Path to server log file to copy to artifacts.
        isolation_info: Optional dict describing test isolation design.
            Example: {"total_campaigns": 12, "shared_campaign": 1, "isolated_tests": 11,
                      "reason": "State-sensitive tests require fresh campaigns"}
        use_iteration: If True, create iteration_NNN subdirectory (default: True).

    Returns:
        Dict mapping file types to their paths.
    """
    # Handle iteration-based directories
    if use_iteration:
        iteration_num, actual_evidence_dir = _get_next_iteration(evidence_dir)
        run_id = _generate_run_id(test_name, iteration_num)
    else:
        actual_evidence_dir = evidence_dir
        actual_evidence_dir.mkdir(parents=True, exist_ok=True)
        # Parse iteration number from directory name (e.g., "iteration_002" -> 2)
        dir_name = actual_evidence_dir.name
        match = re.match(r"iteration_(\d+)", dir_name)
        iteration_num = int(match.group(1)) if match else 1
        run_id = _generate_run_id(test_name, iteration_num)

    artifacts_dir = actual_evidence_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    bundle_timestamp = datetime.now(UTC).isoformat()
    files: dict[str, Path] = {}

    # 1. README.md - Package manifest
    readme_content = f"""# Evidence Package: {test_name}

## Package Manifest
- **Test Name:** {test_name}
- **Run ID:** `{run_id}`
- **Iteration:** {iteration_num}
- **Bundle Version:** {EVIDENCE_FORMAT_VERSION}
- **Collected At (UTC):** {bundle_timestamp}
- **Repository:** worldarchitect.ai
- **Branch:** {provenance.get('git_branch', 'unknown')}
- **Commit:** {provenance.get('git_head', 'unknown')}
- **Merge Base:** {provenance.get('merge_base', 'unknown')}
- **Commits Ahead of Main:** {provenance.get('commits_ahead_of_main', 0)}

## Git Provenance
```
{provenance.get('diff_stat_vs_main', 'No diff available')}
```

## Server Runtime
- **Port:** {provenance.get('server', {}).get('port', 'unknown')}
- **PID:** {provenance.get('server', {}).get('pid', 'unknown')}
- **Command:** {provenance.get('server', {}).get('process_cmdline', 'unknown')}

## Environment Variables
"""
    for var, val in provenance.get("server", {}).get("env_vars", {}).items():
        readme_content += f"- **{var}:** {val}\n"

    readme_content += """
## Files in This Bundle
- `README.md` - This manifest
- `methodology.md` - Testing methodology
- `evidence.md` - Evidence summary
- `metadata.json` - Machine-readable metadata
- `run.json` - Test results
- `request_responses.jsonl` - Raw request/response payloads (if present)
- `artifacts/` - Additional evidence files
"""
    write_with_checksum(actual_evidence_dir / "README.md", readme_content)
    files["readme"] = actual_evidence_dir / "README.md"

    # 2. methodology.md - Testing methodology
    if methodology_text is None:
        # Build isolation section if provided
        isolation_section = ""
        if isolation_info:
            isolation_section = f"""
## Test Isolation Design

**Multi-campaign architecture is BY DESIGN for test isolation.**

- **Total Campaigns:** {isolation_info.get('total_campaigns', 'unknown')}
- **Shared Campaign:** {isolation_info.get('shared_campaign', 0)} (reused across non-isolated tests)
- **Isolated Tests:** {isolation_info.get('isolated_tests', 0)} (each gets a fresh campaign)
- **Rationale:** {isolation_info.get('reason', 'State-sensitive tests require fresh campaigns to prevent context bleed')}

Isolated tests are marked with `isolated: True` in the test scenario definition.
Each isolated test creates its own campaign to ensure:
1. No state bleed from prior tests
2. Clean initial conditions for sensitive scenarios
3. Independent validation of state transitions
"""

        methodology_text = f"""# Methodology: {test_name}

## Test Type
Real API test against MCP server (not mock mode).

## Test Mode
- **TESTING env var:** {provenance.get('server', {}).get('env_vars', {}).get('TESTING', 'not set')}
- **Mode:** Real API calls via MCP HTTP JSON-RPC

## Execution Environment
- Server running at port {provenance.get('server', {}).get('port', 'unknown')}
- Process: {provenance.get('server', {}).get('process_cmdline', 'unknown')}
{isolation_section}
## Evidence Capture
- Raw request/response payloads captured for each MCP call
- Git provenance captured at test start
- Server runtime info captured via lsof/ps
- Raw LLM response text captured in server.log (artifacts/server.log)

## Validation Criteria
Test scenarios validate that:
1. MCP server processes actions correctly
2. State updates are returned as expected
3. No server errors occur
"""
    write_with_checksum(actual_evidence_dir / "methodology.md", methodology_text)
    files["methodology"] = actual_evidence_dir / "methodology.md"

    # 3. evidence.md - Evidence summary
    # Support both "scenarios" (list format) and "steps" (dict format)
    scenarios = results.get("scenarios", [])
    if not scenarios and "steps" in results:
        # Convert steps dict to scenarios list for evidence reporting
        steps_dict = results.get("steps", {})
        if not isinstance(steps_dict, dict):
            steps_dict = {}

        scenarios = []
        for step_name, step_data in steps_dict.items():
            if isinstance(step_data, dict):
                if step_data.get("success", True):
                    errors = []
                else:
                    errors_raw = step_data.get("errors")
                    if isinstance(errors_raw, list) and errors_raw:
                        errors = errors_raw
                    else:
                        msg = (
                            step_data.get("error")
                            or step_data.get("error_message")
                            or "Step failed"
                        )
                        errors = [msg]
            else:
                errors = [f"Invalid step data type: {type(step_data).__name__}"]
            scenarios.append({"name": step_name, "errors": errors})

    # Normalize scenarios for evidence reporting.
    # Canonical scenario schema is {"name": str, "errors": list[str], ...}.
    # For backward compatibility, also accept {"passed": bool} or {"success": bool}.
    normalized_scenarios: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            normalized_scenarios.append(
                {
                    "name": str(scenario),
                    "errors": [f"Invalid scenario type: {type(scenario).__name__}"],
                }
            )
            continue

        if "errors" in scenario:
            errors_val = scenario.get("errors")
            if errors_val is None:
                scenario["errors"] = []
            elif not isinstance(errors_val, list):
                scenario["errors"] = [str(errors_val)]
        else:
            passed_flag: bool | None = None
            if "passed" in scenario:
                passed_flag = bool(scenario.get("passed"))
            elif "success" in scenario:
                passed_flag = bool(scenario.get("success"))

            if passed_flag is True:
                scenario["errors"] = []
            elif passed_flag is False:
                msg = (
                    scenario.get("details")
                    or scenario.get("error")
                    or scenario.get("error_message")
                    or "Scenario failed"
                )
                scenario["errors"] = [msg] if isinstance(msg, str) else ["Scenario failed"]
            else:
                scenario["errors"] = [
                    "Missing 'errors' and no pass/fail flag ('passed' or 'success') provided"
                ]

        normalized_scenarios.append(scenario)

    scenarios = normalized_scenarios
    passed = sum(1 for s in scenarios if not s.get("errors"))
    failed = len(scenarios) - passed

    # Raw validation stats (LLM layer before post-processing)
    summary_data = results.get("summary", {})
    raw_passed = summary_data.get("raw_passed", 0)
    raw_total = summary_data.get("raw_total", 0)
    raw_pass_rate = summary_data.get("raw_pass_rate", "N/A")

    # Build isolation note if multi-campaign
    isolation_note = ""
    if isolation_info and isolation_info.get("total_campaigns", 1) > 1:
        isolation_note = f"""
## ⚠️ Multi-Campaign Isolation Note

This evidence bundle contains **{isolation_info.get('total_campaigns', 'unknown')} campaigns**:
- **1 shared campaign** for non-isolated tests (campaign_id in results)
- **{isolation_info.get('isolated_tests', 0)} isolated campaigns** for state-sensitive tests

**Why:** {isolation_info.get('reason', 'State-sensitive tests require fresh campaigns')}

**Claim Scoping:** Each scenario result below includes its `campaign_id`. Claims about
specific scenarios reference ONLY that scenario's campaign. Aggregate claims (e.g., "18/18 passed")
span all campaigns but each individual result is traceable to its campaign.
"""

    # Build raw validation note ONLY if raw and post rates actually differ
    raw_validation_note = ""
    post_passed = passed
    if raw_total > 0 and raw_passed != post_passed:
        if raw_passed < post_passed:
            # Post-processing rescued some raw failures
            raw_validation_note = f"""
## ⚠️ Raw LLM Layer Warning

**Post-processing is masking raw LLM failures.**

- **Raw Layer Pass Rate:** {raw_passed}/{raw_total} ({raw_pass_rate})
- **Post-Processing Pass Rate:** {post_passed}/{len(scenarios)} ({post_passed / len(scenarios) * 100 if scenarios else 0:.1f}%)

The raw LLM layer accepted some exploits that were blocked by server post-processing.
This means guardrail success depends on post-processing, not the LLM itself.
See `raw_warnings` in individual scenario files for details.
"""
        else:
            # raw_passed > post_passed: post-processing caught issues that raw missed
            raw_validation_note = f"""
## ⚠️ Post-Processing Detected Additional Issues

- **Raw Layer Pass Rate:** {raw_passed}/{raw_total} ({raw_pass_rate})
- **Post-Processing Pass Rate:** {post_passed}/{len(scenarios)} ({post_passed / len(scenarios) * 100 if scenarios else 0:.1f}%)

Post-processing detected issues (dm_notes, core_memories, state mutations) that
the raw narrative validation missed. See `errors` in individual scenario files.
"""

    evidence_content = f"""# Evidence Summary: {test_name}

## Test Results
- **Total Scenarios:** {len(scenarios)}
- **Post-Processing Passed:** {passed}
- **Post-Processing Failed:** {failed}
- **Post-Processing Pass Rate:** {passed / len(scenarios) * 100 if scenarios else 0:.1f}%
- **Raw LLM Layer Passed:** {raw_passed}/{raw_total} ({raw_pass_rate})
{raw_validation_note}{isolation_note}
## Scenario Results
"""
    for scenario in scenarios:
        status = "✅ PASS" if not scenario.get("errors") else "❌ FAIL"
        evidence_content += f"\n### {scenario.get('name', 'Unknown')}\n"
        evidence_content += f"- **Status:** {status}\n"
        # Add campaign_id for traceability
        if scenario.get("campaign_id"):
            evidence_content += f"- **Campaign ID:** `{scenario['campaign_id']}`\n"
        if scenario.get("errors"):
            evidence_content += f"- **Errors:** {scenario['errors']}\n"
        # Surface raw warnings prominently
        if scenario.get("raw_warnings"):
            evidence_content += f"- **⚠️ Raw Warnings:** {scenario['raw_warnings']}\n"
        if scenario.get("raw_errors"):
            evidence_content += f"- **Raw Response Issues:** {scenario['raw_errors']}\n"
        if scenario.get("relationship_updates"):
            evidence_content += f"- **Relationship Updates:** {list(scenario['relationship_updates'].keys())}\n"
        if scenario.get("reputation_updates"):
            evidence_content += "- **Reputation Updates:** Yes\n"

    # Handle both nested (capture_full_provenance) and flat (capture_provenance) structures
    git_head = 'unknown'
    server_pid = 'unknown'
    if isinstance(provenance, dict):
        if "git" in provenance:
            # Nested structure from capture_full_provenance
            git_head = provenance.get("git", {}).get("git_head", "unknown")
            server_pid = provenance.get("server", {}).get("pid", "unknown")
        else:
            # Flat structure from capture_provenance
            git_head = provenance.get("git_head", "unknown")
            server_pid = provenance.get("server", {}).get("pid", "unknown")

    evidence_content += f"""
## Provenance Chain
- **Git HEAD:** `{git_head}`
- **Test Timestamp:** `{bundle_timestamp}`
- **Server PID:** `{server_pid}`
"""
    write_with_checksum(actual_evidence_dir / "evidence.md", evidence_content)
    files["evidence"] = actual_evidence_dir / "evidence.md"

    # 4. metadata.json - Machine-readable with versioning + evidence standards
    # Evidence standards require: git_provenance, server, timestamp
    git_provenance: dict[str, Any] = {}
    server_runtime: dict[str, Any] | None = None
    if isinstance(provenance, dict):
        if "git" in provenance:
            git_provenance = provenance.get("git") or {}
            server_runtime = provenance.get("server")
        else:
            # Capture_provenance-style flat dict
            git_keys = [
                "git_head",
                "git_branch",
                "merge_base",
                "commits_ahead_of_main",
                "diff_stat_vs_main",
                "origin_main",
                "working_directory",
            ]
            git_provenance = {k: provenance.get(k) for k in git_keys if k in provenance}
            server_runtime = provenance.get("server")

    metadata = {
        "test_name": test_name,
        "run_id": run_id,
        "iteration": iteration_num,
        "bundle_version": EVIDENCE_FORMAT_VERSION,
        "timestamp": bundle_timestamp,
        "bundle_timestamp": bundle_timestamp,
        "git_provenance": git_provenance,
        "server": server_runtime,
        "provenance": provenance,
        "summary": {
            "total_scenarios": len(scenarios),
            "passed": passed,
            "failed": failed,
            # Raw LLM layer stats (if available)
            "raw_passed": raw_passed,
            "raw_total": raw_total,
            "raw_pass_rate": raw_pass_rate,
        },
    }
    write_with_checksum(
        actual_evidence_dir / "metadata.json",
        json.dumps(metadata, indent=2),
    )
    files["metadata"] = actual_evidence_dir / "metadata.json"

    # 5. request_responses.jsonl - Raw payloads (if provided)
    if request_responses:
        save_request_responses(actual_evidence_dir, request_responses)
        files["request_responses"] = actual_evidence_dir / "request_responses.jsonl"

    # 6. run.json - Test results
    save_evidence(actual_evidence_dir, results, "run.json")
    files["results"] = actual_evidence_dir / "run.json"

    # 7. artifacts/ - Supporting evidence files
    # Copy server log if provided
    if server_log_path and server_log_path.exists():
        dest_log = artifacts_dir / "server.log"
        shutil.copy2(server_log_path, dest_log)
        write_with_checksum(dest_log, dest_log.read_text())
        files["server_log"] = dest_log

    # Save lsof output if captured
    lsof_output = provenance.get("server", {}).get("lsof_output")
    if lsof_output:
        lsof_file = artifacts_dir / "lsof_output.txt"
        write_with_checksum(lsof_file, lsof_output)
        files["lsof_output"] = lsof_file

    # Save ps output if captured
    ps_output = provenance.get("server", {}).get("ps_output")
    if ps_output:
        ps_file = artifacts_dir / "ps_output.txt"
        write_with_checksum(ps_file, ps_output)
        files["ps_output"] = ps_file

    # Add iteration metadata to returned dict
    files["_bundle_dir"] = actual_evidence_dir
    files["_iteration"] = Path(str(iteration_num))  # Type-compatible placeholder
    files["_run_id"] = Path(run_id)  # Type-compatible placeholder

    print(f"📦 Evidence bundle created: {actual_evidence_dir}")
    print(f"   Run ID: {run_id}")
    print(f"   Iteration: {iteration_num}")
    print(f"   Bundle Version: {EVIDENCE_FORMAT_VERSION}")

    return files
