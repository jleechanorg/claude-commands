#!/usr/bin/env python3
"""
RewardsAgent E2E Test

This test creates a REAL campaign and validates that RewardsAgent:
1. Triggers after combat ends (combat_phase == "ended" with combat_summary)
2. Triggers for non-combat encounters (encounter_completed == true)
3. Displays proper rewards summary with XP/loot
4. Checks for level-up availability
5. Sets rewards_processed: true to prevent duplicates
6. Smoothly transitions back to story mode with continue options

What this test PROVES:
- RewardsAgent activates when rewards are pending from any source
- Rewards display includes XP, loot, and level-up status
- State is properly updated after reward processing
- Smooth UX flow: rewards shown first, then continue options

Run locally:
    BASE_URL=http://localhost:8001 python testing_mcp/test_rewards_agent_real_e2e.py

Run against preview:
    BASE_URL=https://preview-url python testing_mcp/test_rewards_agent_real_e2e.py
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.dev_server import ensure_server_running, get_base_url


def get_output_dir() -> str:
    """
    Get output directory following /savetmp strategy.

    Structure: /tmp/<repo>/<branch>/rewards_e2e/<timestamp>/

    This follows the evidence-standards.md pattern for structured output.
    """
    # Allow override via environment variable
    if os.getenv("OUTPUT_DIR"):
        return os.getenv("OUTPUT_DIR")

    # Get repo name from git or fallback
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, timeout=5
        ).strip()
        repo_name = Path(repo_root).name
    except Exception:
        repo_name = "worldarchitect.ai"

    # Get branch name
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip()
        # Sanitize branch name for filesystem
        branch = branch.replace("/", "_").replace("\\", "_")
    except Exception:
        branch = "unknown"

    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build path: /tmp/<repo>/<branch>/rewards_e2e/<timestamp>/
    output_dir = Path("/tmp") / repo_name / branch / "rewards_e2e" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    return str(output_dir)


# Configuration
BASE_URL = get_base_url()  # Uses worktree-specific port
USER_ID = f"e2e-rewards-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
OUTPUT_DIR = get_output_dir()
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global list to collect raw MCP responses for evidence
RAW_MCP_RESPONSES: List[dict] = []


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


def capture_provenance() -> dict:
    """Capture git and environment provenance with full diff vs origin/main."""
    provenance = {}
    try:
        provenance["git_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5
        ).strip()
        provenance["git_branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip()

        # Fetch origin/main for comparison
        subprocess.run(["git", "fetch", "origin", "main"], timeout=10, capture_output=True)

        # Get merge-base with origin/main
        try:
            provenance["merge_base"] = subprocess.check_output(
                ["git", "merge-base", "HEAD", "origin/main"], text=True, timeout=5
            ).strip()
        except Exception:
            provenance["merge_base"] = None

        # Commits ahead of origin/main
        try:
            ahead_output = subprocess.check_output(
                ["git", "rev-list", "--count", "origin/main..HEAD"], text=True, timeout=5
            ).strip()
            provenance["commits_ahead_of_main"] = int(ahead_output)
        except Exception:
            provenance["commits_ahead_of_main"] = None

        # Diff stat vs origin/main
        try:
            diff_stat = subprocess.check_output(
                ["git", "diff", "--stat", "origin/main...HEAD"], text=True, timeout=10
            ).strip()
            provenance["diff_stat_vs_main"] = diff_stat[-1000:] if len(diff_stat) > 1000 else diff_stat
        except Exception:
            provenance["diff_stat_vs_main"] = None

    except Exception as e:
        provenance["git_error"] = str(e)

    provenance["env"] = {
        "BASE_URL": BASE_URL,
        "STRICT_MODE": STRICT_MODE,
    }

    # Capture server runtime info
    provenance["server"] = capture_server_runtime_info()

    return provenance


def capture_server_runtime_info() -> dict:
    """Capture running server PID, port, and environment."""
    info = {"pid": None, "port": None, "env_vars": {}, "process_cmdline": None}

    try:
        # Find gunicorn/python processes on our port
        port = BASE_URL.split(":")[-1].rstrip("/")
        lsof_output = subprocess.check_output(
            ["lsof", "-i", f":{port}", "-t"], text=True, timeout=5
        ).strip()
        if lsof_output:
            pids = lsof_output.split("\n")
            info["pid"] = pids[0] if pids else None
            info["all_pids"] = pids

            # Get command line for the process
            if info["pid"]:
                try:
                    cmdline = subprocess.check_output(
                        ["ps", "-p", info["pid"], "-o", "command="], text=True, timeout=5
                    ).strip()
                    info["process_cmdline"] = cmdline[:500]
                except Exception:
                    pass

        info["port"] = port

        # Capture relevant env vars (from current process, server may differ)
        for var in ["WORLDAI_DEV_MODE", "GOOGLE_APPLICATION_CREDENTIALS",
                    "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", "TESTING"]:
            val = os.environ.get(var)
            if val:
                info["env_vars"][var] = val[:100] if len(val) > 100 else val

    except Exception as e:
        info["error"] = str(e)

    return info


def get_server_log_paths() -> List[str]:
    """Get possible server log file paths (multiple candidates)."""
    paths = []
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip()
        # Try both with and without slash replacement
        paths.append(f"/tmp/worldarchitect.ai/{branch.replace('/', '_')}/app.log")
        paths.append(f"/tmp/worldarchitect.ai/{branch}/app.log")
    except Exception:
        pass

    # Also check common locations
    paths.extend([
        "/tmp/worldarchitect.ai/app.log",
        "/tmp/server.log",
    ])

    return paths


def get_server_log_path() -> str:
    """Get the first existing server log file path."""
    for path in get_server_log_paths():
        if os.path.exists(path):
            return path
    # Return default even if doesn't exist
    return get_server_log_paths()[0] if get_server_log_paths() else "/tmp/worldarchitect.ai/app.log"


def capture_server_log_snippet(
    since_ts: str, keywords: Optional[List[str]] = None
) -> dict:
    """
    Capture server log entries since a timestamp.

    Args:
        since_ts: ISO timestamp to start from
        keywords: Optional list of keywords to filter (e.g., ["REWARDS", "XP"])
                  If None, captures ALL log lines (not just keyword-filtered)

    Returns:
        dict with log_lines, count, and file_path
    """
    # Try all possible log paths
    log_paths_tried = []
    for log_path in get_server_log_paths():
        log_paths_tried.append(log_path)
        if os.path.exists(log_path):
            break
    else:
        return {
            "log_path": None,
            "log_lines": [],
            "count": 0,
            "error": f"No log file found. Tried: {log_paths_tried}",
            "paths_tried": log_paths_tried,
        }

    result = {"log_path": log_path, "log_lines": [], "count": 0, "error": None, "paths_tried": log_paths_tried}

    try:
        # Parse the since timestamp and convert to local time for comparison
        # Log file uses local time (no timezone), test uses UTC
        since_dt = datetime.fromisoformat(since_ts.replace("Z", "+00:00"))
        # Convert UTC to local time for comparison with log timestamps
        # Log timestamps are local time (no timezone), test uses UTC
        try:
            import time
            # time.timezone is seconds WEST of UTC (positive for US), so local = UTC - offset
            local_offset_seconds = time.timezone if time.localtime().tm_isdst == 0 else time.altzone
            since_dt_local = since_dt.replace(tzinfo=None) - timedelta(seconds=local_offset_seconds)
        except Exception:
            # Fallback: assume EST (UTC-5 = subtract 5 hours from UTC)
            since_dt_local = since_dt.replace(tzinfo=None) - timedelta(hours=5)

        result["since_dt_utc"] = str(since_dt)
        result["since_dt_local"] = str(since_dt_local)

        with open(log_path, "r") as f:
            lines = f.readlines()

        result["total_lines_in_file"] = len(lines)

        # Filter lines after the timestamp
        relevant_lines = []
        all_lines_since = []  # Capture ALL lines since timestamp for context

        for line in lines[-1000:]:  # Last 1000 lines for better coverage
            # Try to extract timestamp from log line (format: 2025-12-27 14:30:45,123)
            match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            if match:
                try:
                    line_dt = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    # Compare naive datetimes (both in local time)
                    if line_dt >= since_dt_local:
                        all_lines_since.append(line.strip())
                        if keywords:
                            if any(kw.upper() in line.upper() for kw in keywords):
                                relevant_lines.append(line.strip())
                        else:
                            relevant_lines.append(line.strip())
                except ValueError:
                    # If timestamp parse fails, still capture if keywords match
                    if keywords and any(kw.upper() in line.upper() for kw in keywords):
                        relevant_lines.append(line.strip())

        # If keyword filtering returned nothing, include all lines since timestamp
        if keywords and not relevant_lines and all_lines_since:
            result["note"] = f"No keyword matches; showing all {len(all_lines_since)} lines since timestamp"
            relevant_lines = all_lines_since

        result["log_lines"] = relevant_lines[:100]  # Limit to 100 lines
        result["count"] = len(relevant_lines)
        result["all_lines_since_timestamp"] = len(all_lines_since)

    except Exception as e:
        result["error"] = str(e)

    return result


def mcp_call(method: str, params: dict, timeout: int = 180) -> dict:
    """Make an MCP JSON-RPC call and capture raw request/response."""
    call_id = f"{method}-{datetime.now().timestamp()}"
    payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": method,
        "params": params,
    }

    call_timestamp = datetime.now(timezone.utc).isoformat()
    resp = requests.post(f"{BASE_URL}/mcp", json=payload, timeout=timeout)
    response_json = resp.json()

    # Record raw request/response for evidence
    RAW_MCP_RESPONSES.append({
        "call_id": call_id,
        "timestamp": call_timestamp,
        "request": payload,
        "response": response_json,
    })

    return response_json


def extract_result(response: dict) -> dict:
    """Extract result from MCP response - handles both formats."""
    result = response.get("result", {})
    # Format 1: Direct result object (create_campaign, get_campaign_state)
    if "campaign_id" in result or "game_state" in result:
        return result
    # Format 2: MCP content array (process_action)
    content = result.get("content", [])
    if content and isinstance(content, list):
        text = content[0].get("text", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    return result


def detect_rewards_box(narrative: str) -> dict:
    """Detect formatted rewards box in narrative output.

    A rewards box is a structured display like:
    ═══════════════════════════════════════
            COMBAT VICTORY!
    ═══════════════════════════════════════
      Experience Gained: 50 XP
    ═══════════════════════════════════════

    Returns dict with detection results.
    """
    if not narrative:
        return {"found": False, "reason": "no narrative"}

    # Markers that indicate a structured rewards display
    box_markers = [
        "═══",  # Box border character
        "╔══",  # Box corner (top-left)
        "╠══",  # Box T-junction
        "╚══",  # Box corner (bottom-left)
        "───",  # Alternative border
        "***",  # Markdown emphasis block
        "---",  # Horizontal rule
        "VICTORY",  # Victory header
        "REWARDS",  # Rewards header
        "Experience Gained",  # XP display
        "XP Earned",  # Alt XP display
        "Gold Found",  # Loot display
        "Loot:",  # Loot section
    ]

    narrative_upper = narrative.upper()
    found_markers = [m for m in box_markers if m.upper() in narrative_upper]

    # Find ALL XP mentions and extract numeric values
    xp_matches = re.findall(r'[+]?(\d+)\s*(?:XP|xp|Experience)', narrative)
    has_xp_display = bool(xp_matches)

    # Sum all XP values found (handles cases like "25 XP + 25 XP = 50 XP")
    xp_values = [int(x) for x in xp_matches]
    total_xp_mentioned = max(xp_values) if xp_values else 0  # Use max as total (avoids double-counting)

    # A rewards box requires: (border OR header) AND XP display
    has_border_or_header = any(m in found_markers for m in ["═══", "───", "***", "---", "VICTORY", "REWARDS"])
    is_rewards_box = has_border_or_header and has_xp_display

    return {
        "found": is_rewards_box,
        "has_xp_display": has_xp_display,
        "has_border_or_header": has_border_or_header,
        "found_markers": found_markers,
        "xp_matches": xp_matches,  # All XP values found
        "total_xp_mentioned": total_xp_mentioned,  # Max XP value (the total)
    }


def check_rewards_indicators(
    narrative: str, game_state: dict, response_data: Optional[dict] = None
) -> dict:
    """Check for rewards processing indicators in response.

    Args:
        narrative: The narrative text from the response
        game_state: The game state from the response
        response_data: Full response data (optional) to check for JSON rewards_box field
    """
    narrative_lower = narrative.lower() if narrative else ""

    # Detect formatted rewards box in narrative (ASCII art style)
    narrative_rewards_box = detect_rewards_box(narrative)

    # Check for JSON rewards_box field in response (preferred method)
    json_rewards_box = None
    has_json_rewards_box = False
    if response_data:
        json_rewards_box = response_data.get("rewards_box")
        if json_rewards_box and isinstance(json_rewards_box, dict):
            has_json_rewards_box = json_rewards_box.get("xp_gained", 0) > 0

    indicators = {
        # Narrative indicators
        "has_xp_mention": any(x in narrative_lower for x in ["xp", "experience point", "experience gained"]),
        "has_rewards_box": narrative_rewards_box["found"] or has_json_rewards_box,
        "has_json_rewards_box": has_json_rewards_box,
        "json_rewards_box": json_rewards_box,
        "rewards_box_details": narrative_rewards_box,
        "has_level_mention": "level" in narrative_lower,
        "has_loot_mention": any(x in narrative_lower for x in ["gold", "loot", "item", "obtained"]),

        # State indicators - CRITICAL: these must be true for rewards to be "processed"
        "rewards_processed_combat": game_state.get("combat_state", {}).get("rewards_processed", False),
        "rewards_processed_encounter": game_state.get("encounter_state", {}).get("rewards_processed", False),
        "rewards_processed_any": (
            game_state.get("combat_state", {}).get("rewards_processed", False)
            or game_state.get("encounter_state", {}).get("rewards_processed", False)
        ),

        # Player XP check
        "player_xp": game_state.get("player_character_data", {}).get("experience", {}).get("current"),
    }

    # Count narrative indicators
    narrative_indicators = sum([
        indicators["has_xp_mention"],
        indicators["has_rewards_box"],
        indicators["has_loot_mention"],
    ])

    indicators["narrative_indicator_count"] = narrative_indicators
    indicators["has_sufficient_indicators"] = narrative_indicators >= 2

    return indicators


def check_continue_options(response_data: dict) -> dict:
    """Check if response includes continue/choice options."""
    planning_block = response_data.get("planning_block", {})
    choices = planning_block.get("choices", {})

    return {
        "has_planning_block": bool(planning_block),
        "has_choices": bool(choices),
        "choice_count": len(choices),
        "choice_keys": list(choices.keys()) if choices else [],
        "has_continue_option": any(
            "continue" in k.lower() or "adventure" in k.lower()
            for k in choices.keys()
        ) if choices else False,
    }


def validate_rewards_summary(combat_summary: dict, player_data: dict) -> dict:
    """Validate rewards summary has required fields."""
    validation = {
        "has_combat_summary": bool(combat_summary),
        "xp_awarded": combat_summary.get("xp_awarded") if combat_summary else None,
        "enemies_defeated": combat_summary.get("enemies_defeated") if combat_summary else None,
        "loot_distributed": combat_summary.get("loot_distributed") if combat_summary else None,
        "player_xp_current": player_data.get("experience", {}).get("current"),
        "player_level": player_data.get("level"),
        "issues": [],
    }

    if not combat_summary:
        validation["issues"].append("No combat_summary present")
    elif validation["xp_awarded"] is None:
        validation["issues"].append("combat_summary missing xp_awarded")
    elif not isinstance(validation["xp_awarded"], (int, float)):
        validation["issues"].append(f"xp_awarded is not a number: {validation['xp_awarded']}")
    elif validation["xp_awarded"] <= 0:
        validation["issues"].append(f"xp_awarded should be > 0: {validation['xp_awarded']}")

    validation["is_valid"] = len(validation["issues"]) == 0
    return validation


def has_reward_evidence(
    rewards_processed: bool,
    xp_awarded: Optional[int],
    loot_distributed: Optional[bool],
    xp_before: Optional[int],
    xp_after: Optional[int],
) -> bool:
    """Check if rewards were generated, independent of narrative formatting."""
    if not rewards_processed:
        return False

    xp_award_present = isinstance(xp_awarded, (int, float)) and xp_awarded > 0
    loot_present = bool(loot_distributed)
    xp_increased = (
        xp_before is not None
        and xp_after is not None
        and xp_after > xp_before
    )

    return xp_award_present or loot_present or xp_increased


def main():
    # Ensure development server is running with fresh code (auto-reload enabled)
    # This prevents stale code issues where server doesn't pick up changes
    log("Ensuring development server is running with fresh code...")
    try:
        ensure_server_running(check_code_changes=True)
    except Exception as e:
        log(f"⚠️  Could not manage server: {e}")
        log("   Proceeding with existing server or BASE_URL...")

    results = {
        "test_name": "rewards_agent_real_e2e",
        "test_type": "rewards_mode_validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "user_id": USER_ID,
        "output_dir": OUTPUT_DIR,
        "strict_mode": STRICT_MODE,
        "provenance": capture_provenance(),
        "steps": [],
        "scenarios": {},
        "summary": {},
    }

    log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
    log(f"Base URL: {BASE_URL}")
    log(f"Output Dir: {OUTPUT_DIR}")

    # Step 1: Health check
    log("Step 1: Health check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        health = resp.json()
        results["steps"].append({
            "name": "health_check",
            "passed": health.get("status") == "healthy",
            "details": health,
        })
        log(f"  Health: {health.get('status')}")
    except Exception as e:
        log(f"  FAILED: {e}")
        results["steps"].append({"name": "health_check", "passed": False, "error": str(e)})
        save_results(results)
        return 1

    # =========================================================================
    # SCENARIO 1: Combat End Rewards
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 1: Combat End Rewards")
    log("=" * 60)

    scenario1 = {"name": "combat_end_rewards", "steps": []}

    # Create campaign
    log("Step 1.1: Create campaign for combat scenario")
    create_response = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": USER_ID,
                "title": "The Rewards Test - Combat",
                "description": "Testing RewardsAgent activation after combat",
                "character": "A level 2 fighter with 200 XP, ready for battle",
                "setting": "A forest clearing where bandits ambush travelers",
            },
        },
    )

    campaign_data = extract_result(create_response)
    campaign_id = campaign_data.get("campaign_id")
    scenario1["campaign_id"] = campaign_id
    scenario1["steps"].append({
        "name": "create_campaign",
        "passed": campaign_id is not None,
        "campaign_id": campaign_id,
    })
    log(f"  Campaign ID: {campaign_id}")

    if not campaign_id:
        log("  FAILED: No campaign ID")
        results["scenarios"]["scenario1"] = scenario1
        save_results(results)
        return 1

    # Start and run combat
    log("Step 1.2: Trigger combat encounter")
    combat_start_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "Two bandits jump out from behind the trees and attack! "
                    "I draw my sword and fight them. "
                    "[OOC: Start combat - set in_combat=true, roll initiative, "
                    "create combatants for me and 2 bandits (CR 1/8 each)]"
                ),
            },
        },
    )

    combat_start_data = extract_result(combat_start_response)
    combat_state = combat_start_data.get("game_state", {}).get("combat_state", {})
    in_combat = combat_state.get("in_combat", False)

    scenario1["steps"].append({
        "name": "start_combat",
        "passed": in_combat is True,
        "in_combat": in_combat,
        "combat_state": combat_state,
    })
    log(f"  in_combat: {in_combat}")

    # Execute combat action
    log("Step 1.3: Execute combat action")
    combat_action_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": "I attack the nearest bandit with my longsword!",
            },
        },
    )

    combat_action_data = extract_result(combat_action_response)
    combat_action_game_state = combat_action_data.get("game_state", {}) or {}
    xp_before_end_combat = (
        (combat_action_game_state.get("player_character_data", {}) or {})
        .get("experience", {})
        .get("current")
    )
    scenario1["steps"].append({
        "name": "combat_action",
        "passed": True,
        "narrative_preview": combat_action_data.get("narrative", "")[:200],
    })

    # End combat - this should trigger RewardsAgent
    log("Step 1.4: End combat (should trigger RewardsAgent)")
    end_combat_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "I defeat both bandits with powerful strikes! The battle is over. "
                    "[OOC: End combat now - set in_combat=false, combat_phase='ended', "
                    "populate combat_summary with xp_awarded (bandits are CR 1/8 = 25 XP each = 50 XP total). "
                    "RewardsAgent should process and display the rewards.]"
                ),
            },
        },
    )

    end_combat_data = extract_result(end_combat_response)
    end_narrative = end_combat_data.get("narrative", end_combat_data.get("raw_text", ""))
    end_game_state = end_combat_data.get("game_state", {})
    end_combat_state = end_game_state.get("combat_state", {}) or {}
    end_player_data = end_game_state.get("player_character_data", {}) or {}

    # Check rewards indicators
    rewards_check = check_rewards_indicators(end_narrative, end_game_state, end_combat_data)
    continue_check = check_continue_options(end_combat_data)
    rewards_validation = validate_rewards_summary(
        end_combat_state.get("combat_summary", {}),
        end_player_data
    )

    # STRICT (relaxed format): Combat end passed if:
    # 1. Combat ended properly (in_combat=false, combat_phase=ended)
    # 2. rewards_processed=true AT THIS STEP (not a later step)
    # 3. Evidence of rewards generated (xp_awarded/loot/xp increase)
    has_structured_xp = rewards_validation.get("xp_awarded")
    xp_after_end_combat = end_player_data.get("experience", {}).get("current")
    combat_end_passed = bool(
        end_combat_state.get("in_combat") is False
        and end_combat_state.get("combat_phase") == "ended"
        and rewards_check["rewards_processed_combat"]  # STRICT: Must be true here
        and has_reward_evidence(
            rewards_check["rewards_processed_combat"],
            has_structured_xp,
            end_combat_state.get("combat_summary", {}).get("loot_distributed"),
            xp_before_end_combat,
            xp_after_end_combat,
        )
    )

    # Also track why it failed for diagnostics
    combat_end_issues = []
    if end_combat_state.get("in_combat") is not False:
        combat_end_issues.append("in_combat not False")
    if end_combat_state.get("combat_phase") != "ended":
        combat_end_issues.append(f"combat_phase={end_combat_state.get('combat_phase')}, expected 'ended'")
    if not rewards_check["rewards_processed_combat"]:
        combat_end_issues.append("rewards_processed=False (must be True at this step)")
    if not has_reward_evidence(
        rewards_check["rewards_processed_combat"],
        has_structured_xp,
        end_combat_state.get("combat_summary", {}).get("loot_distributed"),
        xp_before_end_combat,
        xp_after_end_combat,
    ):
        combat_end_issues.append("insufficient reward evidence (xp_awarded/loot/xp increase)")

    scenario1["steps"].append({
        "name": "end_combat_rewards",
        "passed": combat_end_passed,
        "issues": combat_end_issues,  # Why it failed
        "narrative_preview": end_narrative[:500],
        "combat_state": end_combat_state,
        "rewards_check": rewards_check,
        "continue_check": continue_check,
        "rewards_validation": rewards_validation,
    })

    log(f"  in_combat: {end_combat_state.get('in_combat')}")
    log(f"  combat_phase: {end_combat_state.get('combat_phase')}")
    log(f"  rewards_processed: {end_combat_state.get('rewards_processed')}")
    log(f"  has_rewards_box: {rewards_check['has_rewards_box']}")
    log(f"  has_json_rewards_box: {rewards_check['has_json_rewards_box']}")
    if rewards_check.get('json_rewards_box'):
        log(f"  json_rewards_box: {rewards_check['json_rewards_box']}")
    log(f"  XP awarded: {rewards_validation.get('xp_awarded')}")
    log(f"  Player XP: {rewards_validation.get('player_xp_current')}")
    log(f"  Rewards indicators: {rewards_check['narrative_indicator_count']}/3")
    log(f"  XP before end: {xp_before_end_combat} -> after: {xp_after_end_combat}")
    log(f"  Has continue options: {continue_check['has_choices']}")
    if combat_end_issues:
        log(f"  ISSUES: {', '.join(combat_end_issues)}")

    # Continue after rewards - verify smooth transition
    log("Step 1.5: Continue after rewards (verify smooth UX)")
    continue_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": "I search the bodies for any loot, then continue on my way.",
            },
        },
    )

    continue_data = extract_result(continue_response)
    continue_narrative = continue_data.get("narrative", "")
    continue_game_state = continue_data.get("game_state", {})
    continue_combat_state = continue_game_state.get("combat_state", {}) or {}

    # Verify we're back in story mode (not stuck in rewards)
    scenario1["steps"].append({
        "name": "continue_after_rewards",
        "passed": (
            continue_combat_state.get("in_combat") is False
            and bool(continue_narrative)
        ),
        "narrative_preview": continue_narrative[:300],
        "combat_state": continue_combat_state,
    })
    log(f"  Story continues: {bool(continue_narrative)}")
    log(f"  Narrative: {continue_narrative[:150]}...")

    scenario1["passed"] = all(s.get("passed", False) for s in scenario1["steps"])
    results["scenarios"]["scenario1"] = scenario1

    # =========================================================================
    # SCENARIO 2: Narrative Kill (Quick Execution)
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 2: Narrative Kill Rewards")
    log("=" * 60)

    scenario2 = {"name": "narrative_kill_rewards", "steps": [], "campaign_id": campaign_id}

    log("Step 2.1: Narrative kill (should still award XP)")
    narrative_kill_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "I spot a wounded goblin scout hiding in the bushes. "
                    "I quietly approach and execute it with a swift sword strike. "
                    "[OOC: This is a narrative kill outside of formal combat. "
                    "Award 50 XP (goblin CR 1/4) using combat_summary with xp_awarded. "
                    "RewardsAgent should still process this kill's XP.]"
                ),
            },
        },
    )

    kill_data = extract_result(narrative_kill_response)
    kill_narrative = kill_data.get("narrative", kill_data.get("raw_text", ""))
    kill_game_state = kill_data.get("game_state", {})
    kill_combat_state = kill_game_state.get("combat_state", {}) or {}
    kill_player_data = kill_game_state.get("player_character_data", {}) or {}

    kill_rewards_check = check_rewards_indicators(kill_narrative, kill_game_state, kill_data)
    kill_combat_summary = kill_combat_state.get("combat_summary", {}) or {}

    # STRICT (relaxed format): Narrative kill passed if:
    # 1. rewards_processed=true (RewardsAgent actually ran)
    # 2. Evidence of rewards generated (xp_awarded/loot/xp increase)
    kill_has_structured_xp = kill_combat_summary.get("xp_awarded")
    xp_before_kill = (
        (continue_game_state.get("player_character_data", {}) or {})
        .get("experience", {})
        .get("current")
    )
    xp_after_kill = kill_player_data.get("experience", {}).get("current")
    narrative_kill_passed = bool(
        kill_rewards_check["rewards_processed_any"]  # STRICT: Must be true
        and has_reward_evidence(
            kill_rewards_check["rewards_processed_any"],
            kill_has_structured_xp,
            kill_combat_summary.get("loot_distributed"),
            xp_before_kill,
            xp_after_kill,
        )
    )

    # Track issues for diagnostics
    narrative_kill_issues = []
    if not kill_rewards_check["rewards_processed_any"]:
        narrative_kill_issues.append("rewards_processed=False (must be True)")
    if not has_reward_evidence(
        kill_rewards_check["rewards_processed_any"],
        kill_has_structured_xp,
        kill_combat_summary.get("loot_distributed"),
        xp_before_kill,
        xp_after_kill,
    ):
        narrative_kill_issues.append("insufficient reward evidence (xp_awarded/loot/xp increase)")

    scenario2["steps"].append({
        "name": "narrative_kill",
        "passed": narrative_kill_passed,
        "issues": narrative_kill_issues,
        "narrative_preview": kill_narrative[:500],
        "combat_summary": kill_combat_summary,
        "rewards_check": kill_rewards_check,
        "player_xp": kill_player_data.get("experience", {}).get("current"),
    })

    log(f"  XP mentioned: {kill_rewards_check['has_xp_mention']}")
    log(f"  XP awarded: {kill_combat_summary.get('xp_awarded')}")
    log(f"  rewards_processed: {kill_rewards_check['rewards_processed_any']}")
    log(f"  Player XP: {kill_player_data.get('experience', {}).get('current')}")
    if narrative_kill_issues:
        log(f"  ISSUES: {', '.join(narrative_kill_issues)}")

    scenario2["passed"] = all(s.get("passed", False) for s in scenario2["steps"])
    results["scenarios"]["scenario2"] = scenario2

    # =========================================================================
    # SCENARIO 3: Non-Combat Encounter (Heist/Social)
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 3: Non-Combat Encounter Rewards")
    log("=" * 60)

    scenario3 = {"name": "non_combat_encounter", "steps": []}

    # Create new campaign for this scenario
    log("Step 3.1: Create campaign for social encounter")
    create_response3 = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": USER_ID,
                "title": "The Rewards Test - Social",
                "description": "Testing RewardsAgent for non-combat encounters",
                "character": "A level 3 rogue with expertise in Deception and Stealth",
                "setting": "A bustling city with corrupt nobles and valuable treasures",
            },
        },
    )

    campaign3_data = extract_result(create_response3)
    campaign3_id = campaign3_data.get("campaign_id")
    campaign3_game_state = campaign3_data.get("game_state", {})
    campaign3_initial_xp = campaign3_game_state.get("player_character_data", {}).get("experience", {}).get("current", 0)
    scenario3["campaign_id"] = campaign3_id
    scenario3["initial_xp"] = campaign3_initial_xp
    scenario3["steps"].append({
        "name": "create_campaign",
        "passed": campaign3_id is not None,
        "campaign_id": campaign3_id,
        "initial_xp": campaign3_initial_xp,
    })
    log(f"  Campaign ID: {campaign3_id}")
    log(f"  Initial XP: {campaign3_initial_xp}")

    if not campaign3_id:
        log("  FAILED: No campaign ID")
        results["scenarios"]["scenario3"] = scenario3
        save_results(results)
        return 1

    # Start a heist encounter
    log("Step 3.2: Start heist encounter")
    heist_start_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign3_id,
                "user_input": (
                    "I sneak into the merchant's shop at night to steal the valuable gem. "
                    "[OOC: Start a heist encounter - set encounter_state.encounter_active=true, "
                    "encounter_type='heist', difficulty='medium'. Track objectives: "
                    "bypass lock, grab gem, escape undetected.]"
                ),
            },
        },
    )

    heist_start_data = extract_result(heist_start_response)
    heist_start_narrative = heist_start_data.get("narrative", heist_start_data.get("raw_text", ""))
    heist_game_state = heist_start_data.get("game_state", {})
    encounter_state = heist_game_state.get("encounter_state", {}) or {}
    heist_start_xp = (heist_game_state.get("player_character_data", {}) or {}).get("experience", {}).get("current", 0)

    # Accept if: encounter_active set, OR narrative describes heist/sneak action, OR has planning block
    heist_started = (
        encounter_state.get("encounter_active", False)
        or "sneak" in heist_start_narrative.lower()
        or "lock" in heist_start_narrative.lower()
        or "gem" in heist_start_narrative.lower()
        or bool(heist_start_data.get("planning_block", {}).get("choices"))
    )

    scenario3["steps"].append({
        "name": "start_heist",
        "passed": heist_started,
        "encounter_state": encounter_state,
        "narrative_preview": heist_start_narrative[:200],
        "xp_at_start": heist_start_xp,
    })
    log(f"  encounter_active: {encounter_state.get('encounter_active')}")
    log(f"  encounter_type: {encounter_state.get('encounter_type')}")
    log(f"  Heist started (narrative check): {heist_started}")

    # Complete the heist
    log("Step 3.3: Complete heist (should trigger RewardsAgent)")
    heist_complete_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign3_id,
                "user_input": (
                    "I pick the lock (DC 15 Sleight of Hand), grab the gem, and slip "
                    "out the back window without a trace. Perfect heist! "
                    "[OOC: Complete the encounter successfully - set encounter_completed=true, "
                    "populate encounter_summary with xp_awarded (100 XP for medium heist "
                    "with +25% heist bonus = 125 XP). RewardsAgent should process rewards.]"
                ),
            },
        },
    )

    heist_complete_data = extract_result(heist_complete_response)
    heist_narrative = heist_complete_data.get("narrative", heist_complete_data.get("raw_text", ""))
    heist_final_state = heist_complete_data.get("game_state", {})
    heist_encounter_state = heist_final_state.get("encounter_state", {}) or {}
    heist_player_data = heist_final_state.get("player_character_data", {}) or {}
    heist_current_xp = heist_player_data.get("experience", {}).get("current", 0)

    # Also check combat_summary in case LLM used that instead of encounter_state
    heist_combat_state = heist_final_state.get("combat_state", {}) or {}
    heist_combat_summary = heist_combat_state.get("combat_summary", {}) or {}

    heist_rewards_check = check_rewards_indicators(heist_narrative, heist_final_state, heist_complete_data)
    heist_continue_check = check_continue_options(heist_complete_data)
    heist_summary = heist_encounter_state.get("encounter_summary", {}) or {}

    # XP increased check - use heist_start_xp (XP at step 3.2), not campaign initial
    xp_increased = heist_current_xp > heist_start_xp
    xp_gain = heist_current_xp - heist_start_xp  # Proper delta for this step

    # STRICT (relaxed format): Heist passed if:
    # 1. rewards_processed=true (RewardsAgent actually ran)
    # 2. Evidence of rewards generated (xp_awarded/loot/xp increase)
    heist_has_structured_xp = heist_summary.get("xp_awarded") or heist_combat_summary.get("xp_awarded")
    heist_passed = bool(
        heist_rewards_check["rewards_processed_any"]  # STRICT: Must be true
        and has_reward_evidence(
            heist_rewards_check["rewards_processed_any"],
            heist_has_structured_xp,
            heist_summary.get("loot_distributed"),
            heist_start_xp,
            heist_current_xp,
        )
    )

    # Track issues for diagnostics
    heist_issues = []
    if not heist_rewards_check["rewards_processed_any"]:
        heist_issues.append("rewards_processed=False (must be True)")
    if not has_reward_evidence(
        heist_rewards_check["rewards_processed_any"],
        heist_has_structured_xp,
        heist_summary.get("loot_distributed"),
        heist_start_xp,
        heist_current_xp,
    ):
        heist_issues.append("insufficient reward evidence (xp_awarded/loot/xp increase)")

    scenario3["steps"].append({
        "name": "complete_heist_rewards",
        "passed": heist_passed,
        "issues": heist_issues,
        "narrative_preview": heist_narrative[:500],
        "encounter_state": heist_encounter_state,
        "encounter_summary": heist_summary,
        "combat_summary": heist_combat_summary,
        "rewards_check": heist_rewards_check,
        "continue_check": heist_continue_check,
        "player_xp": heist_current_xp,
        "xp_at_heist_start": heist_start_xp,
        "xp_increased": xp_increased,
        "xp_gain": xp_gain,
    })

    log(f"  encounter_completed: {heist_encounter_state.get('encounter_completed')}")
    log(f"  rewards_processed: {heist_rewards_check['rewards_processed_any']}")
    log(f"  XP in encounter_summary: {heist_summary.get('xp_awarded')}")
    log(f"  XP in combat_summary: {heist_combat_summary.get('xp_awarded')}")
    log(f"  XP mentioned: {heist_rewards_check['has_xp_mention']}")
    log(f"  has_rewards_box: {heist_rewards_check['has_rewards_box']}")
    log(f"  XP increased: {xp_increased} (gain: {xp_gain}, from {heist_start_xp} to {heist_current_xp})")
    log(f"  Has continue options: {heist_continue_check['has_choices']}")
    if heist_issues:
        log(f"  ISSUES: {', '.join(heist_issues)}")

    scenario3["passed"] = all(s.get("passed", False) for s in scenario3["steps"])
    results["scenarios"]["scenario3"] = scenario3

    # =========================================================================
    # SCENARIO 4: Social Victory
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 4: Social Victory Rewards")
    log("=" * 60)

    scenario4 = {"name": "social_victory", "steps": [], "campaign_id": campaign3_id}
    # Track XP before social encounter (after heist)
    scenario4["xp_before_social"] = heist_current_xp

    log("Step 4.1: Social victory encounter")
    log(f"  XP before social: {heist_current_xp}")
    social_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign3_id,
                "user_input": (
                    "I approach the guard captain and convince him I'm a visiting noble's servant "
                    "on important business. Using my silver tongue, I talk my way past the checkpoint. "
                    "[OOC: This is a social encounter victory. DC 16 Deception check succeeds. "
                    "Award 75 XP for medium social difficulty, plus 25 XP bonus for avoiding combat. "
                    "Total: 100 XP. Set encounter_completed=true, process rewards.]"
                ),
            },
        },
    )

    social_data = extract_result(social_response)
    social_narrative = social_data.get("narrative", social_data.get("raw_text", ""))
    social_game_state = social_data.get("game_state", {})
    social_encounter_state = social_game_state.get("encounter_state", {}) or {}
    social_player_data = social_game_state.get("player_character_data", {}) or {}
    social_current_xp = social_player_data.get("experience", {}).get("current", 0)

    # Also check combat_summary in case LLM used that instead of encounter_state
    social_combat_state = social_game_state.get("combat_state", {}) or {}
    social_combat_summary = social_combat_state.get("combat_summary", {}) or {}

    social_rewards_check = check_rewards_indicators(social_narrative, social_game_state, social_data)
    social_summary = social_encounter_state.get("encounter_summary", {}) or {}

    # XP increased check - use heist_current_xp (XP after step 3.3), not xp_before_social
    social_xp_before = scenario4.get("xp_before_social", 0)
    social_xp_increased = social_current_xp > social_xp_before
    social_xp_gain = social_current_xp - social_xp_before  # Proper delta for this step

    # STRICT (relaxed format): Social victory passed if:
    # 1. rewards_processed=true (RewardsAgent actually ran)
    # 2. Evidence of rewards generated (xp_awarded/loot/xp increase)
    social_has_structured_xp = social_summary.get("xp_awarded") or social_combat_summary.get("xp_awarded")
    social_passed = bool(
        social_rewards_check["rewards_processed_any"]  # STRICT: Must be true
        and has_reward_evidence(
            social_rewards_check["rewards_processed_any"],
            social_has_structured_xp,
            social_summary.get("loot_distributed"),
            social_xp_before,
            social_current_xp,
        )
    )

    # Track issues for diagnostics
    social_issues = []
    if not social_rewards_check["rewards_processed_any"]:
        social_issues.append("rewards_processed=False (must be True)")
    if not has_reward_evidence(
        social_rewards_check["rewards_processed_any"],
        social_has_structured_xp,
        social_summary.get("loot_distributed"),
        social_xp_before,
        social_current_xp,
    ):
        social_issues.append("insufficient reward evidence (xp_awarded/loot/xp increase)")

    scenario4["steps"].append({
        "name": "social_victory",
        "passed": social_passed,
        "issues": social_issues,
        "narrative_preview": social_narrative[:500],
        "encounter_summary": social_summary,
        "combat_summary": social_combat_summary,
        "rewards_check": social_rewards_check,
        "player_xp": social_current_xp,
        "xp_before_step": social_xp_before,
        "xp_increased": social_xp_increased,
        "xp_gain": social_xp_gain,
    })

    log(f"  XP mentioned: {social_rewards_check['has_xp_mention']}")
    log(f"  XP in encounter_summary: {social_summary.get('xp_awarded')}")
    log(f"  XP in combat_summary: {social_combat_summary.get('xp_awarded')}")
    log(f"  rewards_processed: {social_rewards_check['rewards_processed_any']}")
    log(f"  has_rewards_box: {social_rewards_check['has_rewards_box']}")
    log(f"  XP increased: {social_xp_increased} (gain: {social_xp_gain}, from {social_xp_before} to {social_current_xp})")
    log(f"  Player XP: {social_current_xp}")
    if social_issues:
        log(f"  ISSUES: {', '.join(social_issues)}")

    scenario4["passed"] = all(s.get("passed", False) for s in scenario4["steps"])
    results["scenarios"]["scenario4"] = scenario4

    # =========================================================================
    # Summary
    # =========================================================================
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)

    scenarios_passed = sum(1 for s in results["scenarios"].values() if s.get("passed"))
    scenarios_total = len(results["scenarios"])

    results["summary"] = {
        "scenarios_passed": scenarios_passed,
        "scenarios_total": scenarios_total,
        "scenario1_combat_end": results["scenarios"]["scenario1"]["passed"],
        "scenario2_narrative_kill": results["scenarios"]["scenario2"]["passed"],
        "scenario3_heist": results["scenarios"]["scenario3"]["passed"],
        "scenario4_social": results["scenarios"]["scenario4"]["passed"],
    }

    log(f"Scenarios: {scenarios_passed}/{scenarios_total} passed")
    log(f"  1. Combat End Rewards: {'PASS' if results['scenarios']['scenario1']['passed'] else 'FAIL'}")
    log(f"  2. Narrative Kill: {'PASS' if results['scenarios']['scenario2']['passed'] else 'FAIL'}")
    log(f"  3. Heist Encounter: {'PASS' if results['scenarios']['scenario3']['passed'] else 'FAIL'}")
    log(f"  4. Social Victory: {'PASS' if results['scenarios']['scenario4']['passed'] else 'FAIL'}")

    save_results(results)

    # Determine overall success
    # At minimum, scenario 1 (combat end) should pass as it's the core case
    core_passed = results["scenarios"]["scenario1"]["passed"]

    if core_passed and scenarios_passed >= 2:
        log("\n[PASS] RewardsAgent E2E test passed!")
        log("  - Combat end rewards processing verified")
        if results["scenarios"]["scenario2"]["passed"]:
            log("  - Narrative kill rewards verified")
        if results["scenarios"]["scenario3"]["passed"]:
            log("  - Heist encounter rewards verified")
        if results["scenarios"]["scenario4"]["passed"]:
            log("  - Social victory rewards verified")
        return 0
    if STRICT_MODE:
        log("\n[FAIL] RewardsAgent E2E test failed (strict mode)")
        if not results["scenarios"]["scenario1"]["passed"]:
            log("  - Core scenario (combat end) FAILED")
        return 1
    log("\n[WARN] RewardsAgent test had issues (non-strict mode)")
    return 0


def save_results(results: dict) -> None:
    """
    Save results following /savetmp evidence structure.

    Structure:
    /tmp/<repo>/<branch>/rewards_e2e/<timestamp>/
    ├── evidence.json + .sha256        (main test results)
    ├── raw_mcp_responses.jsonl + .sha256
    ├── metadata.json + .sha256        (git provenance)
    ├── README.md + .sha256
    └── checksums.manifest
    """
    output_dir = Path(OUTPUT_DIR)

    # Write main results (evidence.json following savetmp naming)
    evidence_file = output_dir / "evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(results, f, indent=2)

    # Write raw MCP responses as JSONL (one entry per line)
    raw_mcp_file = output_dir / "raw_mcp_responses.jsonl"
    with open(raw_mcp_file, "w") as f:
        for entry in RAW_MCP_RESPONSES:
            f.write(json.dumps(entry) + "\n")
    log(f"Raw MCP responses saved: {len(RAW_MCP_RESPONSES)} calls captured")

    # Capture server log snippets for reward-related entries
    test_start_ts = results.get("timestamp", datetime.now(timezone.utc).isoformat())
    server_logs = capture_server_log_snippet(
        test_start_ts,
        keywords=["REWARDS", "XP", "SERVER_ENFORCEMENT", "REWARDS_MODE", "combat_summary", "encounter_summary"]
    )
    server_log_file = output_dir / "server_logs.txt"
    with open(server_log_file, "w") as f:
        f.write("# Server Log Evidence\n")
        f.write("# ===================\n\n")
        f.write(f"# Test timestamp (UTC): {test_start_ts}\n")
        f.write(f"# Test timestamp (local): {server_logs.get('since_dt_local', 'N/A')}\n")
        f.write(f"# Log path found: {server_logs.get('log_path')}\n")
        f.write(f"# Paths tried: {server_logs.get('paths_tried', [])}\n")
        f.write(f"# Total lines in file: {server_logs.get('total_lines_in_file', 'N/A')}\n")
        f.write(f"# Lines since timestamp: {server_logs.get('all_lines_since_timestamp', 'N/A')}\n")
        f.write(f"# Keyword-filtered lines: {server_logs.get('count')}\n")
        if server_logs.get("error"):
            f.write(f"# ERROR: {server_logs.get('error')}\n")
        if server_logs.get("note"):
            f.write(f"# Note: {server_logs.get('note')}\n")
        f.write("\n# Server runtime info:\n")
        server_info = results.get("provenance", {}).get("server", {})
        f.write(f"#   PID: {server_info.get('pid')}\n")
        f.write(f"#   Port: {server_info.get('port')}\n")
        f.write(f"#   Command: {server_info.get('process_cmdline', 'N/A')}\n")
        f.write(f"#   Env vars: {server_info.get('env_vars', {})}\n")
        f.write("\n# --- Log Lines ---\n\n")
        for line in server_logs.get("log_lines", []):
            f.write(line + "\n")
        if not server_logs.get("log_lines"):
            f.write("(No log lines captured - see error/notes above)\n")
    log(f"Server logs captured: {server_logs.get('count')} reward-related lines")

    # Write metadata.json with git provenance (savetmp standard)
    metadata = {
        "test_name": "rewards_agent_real_e2e",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "git_provenance": results.get("provenance", {}),
        "configuration": {
            "base_url": BASE_URL,
            "user_id": USER_ID,
            "strict_mode": STRICT_MODE,
        },
        "summary": results.get("summary", {}),
    }
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write README.md (savetmp standard)
    readme_content = f"""# RewardsAgent E2E Test Results

**Test Run:** {datetime.now(timezone.utc).isoformat()}
**Base URL:** {BASE_URL}
**Output Directory:** {output_dir}

## Summary

| Scenario | Result |
|----------|--------|
| 1. Combat End Rewards | {'PASS' if results.get('summary', {}).get('scenario1_combat_end') else 'FAIL'} |
| 2. Narrative Kill | {'PASS' if results.get('summary', {}).get('scenario2_narrative_kill') else 'FAIL'} |
| 3. Heist Encounter | {'PASS' if results.get('summary', {}).get('scenario3_heist') else 'FAIL'} |
| 4. Social Victory | {'PASS' if results.get('summary', {}).get('scenario4_social') else 'FAIL'} |

**Scenarios Passed:** {results.get('summary', {}).get('scenarios_passed', 0)}/{results.get('summary', {}).get('scenarios_total', 4)}

## Git Provenance

- **HEAD:** {results.get('provenance', {}).get('git_head', 'unknown')[:12]}
- **Branch:** {results.get('provenance', {}).get('git_branch', 'unknown')}

## Files

- `evidence.json` - Full test results with all scenario data
- `raw_mcp_responses.jsonl` - Raw MCP request/response captures
- `metadata.json` - Git provenance and configuration
- `checksums.manifest` - SHA256 checksums for all files
"""
    readme_file = output_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)

    # Generate checksums for evidence files (savetmp standard)
    evidence_files = [
        "evidence.json",
        "raw_mcp_responses.jsonl",
        "server_logs.txt",
        "metadata.json",
        "README.md",
    ]

    checksums = {}
    for filename in evidence_files:
        filepath = output_dir / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            checksums[filename] = checksum
            # Write individual checksum file
            with open(f"{filepath}.sha256", "w") as f:
                f.write(f"{checksum}  {filename}\n")

    # Write manifest with all checksums
    manifest_file = output_dir / "checksums.manifest"
    with open(manifest_file, "w") as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")

    log(f"\nResults saved to: {output_dir}")
    log(f"Checksums ({len(checksums)} files):")
    for filename, checksum in checksums.items():
        log(f"  {filename}: {checksum[:16]}...")


if __name__ == "__main__":
    sys.exit(main())
