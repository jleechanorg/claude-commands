"""Evidence capture and provenance utilities per evidence-standards.md.

This module provides evidence capture functions that comply with
.claude/skills/evidence-standards.md requirements.

Canonical evidence structure:
    /tmp/<repo>/<branch>/<work>/<timestamp>/
    ├── README.md              # Package manifest with git provenance
    ├── README.md.sha256
    ├── methodology.md         # Testing methodology documentation
    ├── methodology.md.sha256
    ├── evidence.md            # Evidence summary with metrics
    ├── evidence.md.sha256
    ├── metadata.json          # Machine-readable: git_provenance, timestamps
    ├── metadata.json.sha256
    ├── request_responses.jsonl # Raw request/response payloads (LLM behavior proof)
    ├── request_responses.jsonl.sha256
    └── artifacts/             # Copied evidence files (test outputs, logs, etc.)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_evidence_dir(test_name: str) -> Path:
    """Get evidence directory following /tmp/<repo>/<branch>/<test_name> pattern.

    Per evidence-standards.md, evidence should be saved in /tmp subdirectory.

    Args:
        test_name: Name of the test (e.g., "relationship_reputation")

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
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


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
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=str(PROJECT_ROOT),
            timeout=10,
            capture_output=True,
        )
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
        "PORT",
        "FIREBASE_PROJECT_ID",
        "GEMINI_API_KEY",  # Masked
    ]
    env_vars: dict[str, Any] = {}
    overrides = server_env_overrides or {}
    for var in env_vars_to_capture:
        # Prefer server_env_overrides (explicit server config) over os.environ (test runner)
        value = overrides.get(var) if var in overrides else os.environ.get(var)
        if value and ("KEY" in var or "CREDENTIALS" in var):
            env_vars[var] = f"[SET - {len(value)} chars]"  # Mask sensitive values
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
    provenance["timestamp"] = datetime.now(timezone.utc).isoformat()

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

    Args:
        evidence_dir: Directory to create bundle in.
        test_name: Name of the test for documentation.
        provenance: Git and server provenance dict from capture_provenance().
        results: Test results dict to save as run.json.
        request_responses: Optional list of request/response captures.
        methodology_text: Optional custom methodology text.
        server_log_path: Path to server log file to copy to artifacts.
        isolation_info: Optional dict describing test isolation design.
            Example: {"total_campaigns": 12, "shared_campaign": 1, "isolated_tests": 11,
                      "reason": "State-sensitive tests require fresh campaigns"}

    Returns:
        Dict mapping file types to their paths.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = evidence_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    bundle_timestamp = datetime.now(timezone.utc).isoformat()
    files: dict[str, Path] = {}

    # 1. README.md - Package manifest
    readme_content = f"""# Evidence Package: {test_name}

## Package Manifest
- **Test Name:** {test_name}
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
    write_with_checksum(evidence_dir / "README.md", readme_content)
    files["readme"] = evidence_dir / "README.md"

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
    write_with_checksum(evidence_dir / "methodology.md", methodology_text)
    files["methodology"] = evidence_dir / "methodology.md"

    # 3. evidence.md - Evidence summary
    scenarios = results.get("scenarios", [])
    passed = sum(1 for s in scenarios if not s.get("errors"))
    failed = len(scenarios) - passed

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

    evidence_content = f"""# Evidence Summary: {test_name}

## Test Results
- **Total Scenarios:** {len(scenarios)}
- **Passed:** {passed}
- **Failed:** {failed}
- **Pass Rate:** {passed / len(scenarios) * 100 if scenarios else 0:.1f}%
{isolation_note}
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
        if scenario.get("relationship_updates"):
            evidence_content += f"- **Relationship Updates:** {list(scenario['relationship_updates'].keys())}\n"
        if scenario.get("reputation_updates"):
            evidence_content += f"- **Reputation Updates:** Yes\n"

    evidence_content += f"""
## Provenance Chain
- **Git HEAD:** `{provenance.get('git_head', 'unknown')}`
- **Test Timestamp:** `{bundle_timestamp}`
- **Server PID:** `{provenance.get('server', {}).get('pid', 'unknown')}`
"""
    write_with_checksum(evidence_dir / "evidence.md", evidence_content)
    files["evidence"] = evidence_dir / "evidence.md"

    # 4. metadata.json - Machine-readable
    metadata = {
        "test_name": test_name,
        "bundle_timestamp": bundle_timestamp,
        "provenance": provenance,
        "summary": {
            "total_scenarios": len(scenarios),
            "passed": passed,
            "failed": failed,
        },
    }
    write_with_checksum(
        evidence_dir / "metadata.json",
        json.dumps(metadata, indent=2),
    )
    files["metadata"] = evidence_dir / "metadata.json"

    # 5. request_responses.jsonl - Raw payloads (if provided)
    if request_responses:
        save_request_responses(evidence_dir, request_responses)
        files["request_responses"] = evidence_dir / "request_responses.jsonl"

    # 6. run.json - Test results
    save_evidence(evidence_dir, results, "run.json")
    files["results"] = evidence_dir / "run.json"

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

    return files
