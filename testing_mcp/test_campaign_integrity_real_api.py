#!/usr/bin/env python3
"""Campaign Integrity tests against an MCP server (local or preview).

These tests validate the Campaign Integrity Guidelines:
- Milestone Leveling (no "speedrun" jumps)
- Social HP (NPC resistance to persuasion)
- Resource Attrition (spell slot/resource tracking)
- Attunement Economy (configurable item limits)

Run (local MCP already running):
    cd testing_mcp
    python test_campaign_integrity_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically; requires `gcloud` access to Secret Manager):
    cd testing_mcp
    python test_campaign_integrity_real_api.py --start-local
"""

# ruff: noqa: PLR0912, PLR0915, DTZ005

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.campaign_utils import (
    create_campaign,
    process_action,
)
from lib.model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)
from lib.mcp_client import MCPClient

EVIDENCE_DIR = Path(__file__).parent / "evidence" / "campaign_integrity"


# Test scenarios for campaign integrity validation
TEST_SCENARIOS: list[dict[str, Any]] = [
    # Milestone Leveling Tests
    {
        "name": "Milestone Leveling - Single Arc Level Up",
        "category": "milestone_leveling",
        "description": "Verify that completing a story arc provides reasonable level progression (1-3 levels)",
        "user_input": (
            "I have just completed a major story arc by defeating the bandit lord "
            "and saving the village. Award me experience and level up my character."
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": ["level", "Level", "experience", "XP"],
            "forbidden_patterns": [
                r"level\s*(\d{3,})",  # 3+ digit levels (100+)
                r"level\s*[5-9]\d",  # Excessive level jumps (50-99)
            ],
        },
    },
    {
        "name": "Milestone Leveling - Epic Campaign High Level",
        "category": "milestone_leveling",
        "description": "Verify epic campaigns can exceed Level 20 with DM approval",
        "user_input": (
            "My Level 20 Fighter has completed an epic quest to defeat a god. "
            "As the DM, grant me an epic boon or advancement beyond Level 20."
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": ["boon", "epic", "advancement", "power", "ability", "Level"],
        },
    },
    # Social HP Tests
    {
        "name": "Social HP - King Persuasion Resistance",
        "category": "social_hp",
        "description": "Verify that high-authority NPCs resist immediate persuasion",
        "user_input": (
            "I approach the King and roll a 28 on Persuasion (natural 20 + 8). "
            "I ask him to hand over his crown and abdicate the throne to me."
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": [
                "impressed",
                "consider",
                "audience",
                "listen",
                "intrigued",
                "won't",
                "cannot",
                "impossible",
                "refuse",
                "guards",
            ],
            "forbidden_patterns": [
                r"hands you the crown",
                r"abdicates immediately",
                r"gives you the throne",
                r"you\s+are\s+now\s+king",
                r"crowns?\s+you",
                r"hands?\s+over\s+(the\s+)?(crown|throne)",
                r"abdicates\b",
                r"you\s+take\s+the\s+throne",
            ],
        },
    },
    {
        "name": "Social HP - Commoner Quick Persuasion",
        "category": "social_hp",
        "description": "Verify that low-authority NPCs can be persuaded more easily",
        "user_input": (
            "I ask the tavern keeper to give me a free drink, rolling a 15 on Persuasion."
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": ["drink", "ale", "mug", "serves", "pours", "offers"],
        },
    },
    # NPC Hard Limits Tests
    {
        "name": "NPC Hard Limits - Paladin Oath",
        "category": "npc_hard_limits",
        "description": "Verify NPCs maintain inviolable beliefs despite high rolls",
        "user_input": (
            "I roll a 30 on Persuasion (natural 20 + 10 modifiers) to convince "
            "the Paladin of Devotion to break his oath and murder an innocent child."
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": [
                "refuses",
                "never",
                "cannot",
                "oath",
                "sacred",
                "impossible",
                "horrified",
                "attacks",
                "draws weapon",
            ],
            "forbidden_patterns": [
                r"agrees to kill",
                r"kills the child",
                r"breaks.*oath.*willingly",
                r"agrees",
                r"accepts your request",
                r"will do it",
                r"does it without hesitation",
            ],
        },
    },
    # Resource Attrition Tests
    {
        "name": "Resource Attrition - Spell Slot Tracking",
        "category": "resource_attrition",
        "description": "Verify spell slots are tracked when cast",
        "user_input": (
            "As a Level 5 Wizard with 4 first-level, 3 second-level, and 2 third-level spell slots, "
            "I cast Fireball (3rd level) and Magic Missile (1st level). "
            "What spell slots do I have remaining?"
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": ["slot", "remaining", "expended", "used", "left"],
        },
    },
    # Attunement Economy Tests
    {
        "name": "Attunement Economy - Standard Limit",
        "category": "attunement_economy",
        "description": "Verify standard campaigns mention attunement limits",
        "user_input": (
            "I find 5 magical items that require attunement: Ring of Protection, "
            "Cloak of Elvenkind, Boots of Speed, Flame Tongue sword, and Amulet of Health. "
            "How many can I attune to at once?"
        ),
        "validation": {
            "type": "narrative_check",
            "expect_any": ["attune", "three", "3", "limit", "choose", "select"],
        },
    },
]


def extract_narrative(result: dict[str, Any]) -> str:
    """Return narrative text using the same fallbacks as validation."""

    narrative = result.get("narrative") or result.get("response") or ""
    if narrative:
        return str(narrative)

    content = result.get("content") or []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                narrative += str(item["text"])

    return narrative


def validate_result(
    result: dict[str, Any], scenario: dict[str, Any], narrative: str | None = None
) -> list[str]:
    """Validate a test result against expected patterns."""
    errors: list[str] = []

    if result.get("error"):
        errors.append(f"server returned error: {result['error']}")
        return errors

    # Get narrative response (reuse passed-in narrative when available)
    narrative = narrative if narrative is not None else extract_narrative(result)

    if not narrative:
        errors.append("no narrative response received")
        return errors

    validation = scenario.get("validation", {})
    val_type = validation.get("type")

    if val_type == "narrative_check":
        # Check for expected patterns (at least one must match)
        expect_any = validation.get("expect_any", [])
        if expect_any:
            found_any = any(pat.lower() in narrative.lower() for pat in expect_any)
            if not found_any:
                errors.append(
                    f"expected narrative to contain one of {expect_any}, "
                    f"got: {narrative[:200]}..."
                )

        # Check for forbidden patterns (none should match)
        forbidden = validation.get("forbidden_patterns", [])
        for pattern in forbidden:
            if re.search(pattern, narrative, re.IGNORECASE):
                errors.append(
                    f"narrative contained forbidden pattern '{pattern}': {narrative[:200]}..."
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Campaign Integrity tests (no direct provider calls)"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --start-local (0 = random free port)",
    )
    # NOTE: Mock mode removed - these tests ALWAYS use real services
    # This is a "real API" test file - mocks defeat the purpose
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Enable enhanced evidence capture (checksums, provenance).",
    )
    parser.add_argument(
        "--evidence-dir",
        default=str(EVIDENCE_DIR),
        help="Directory to store evidence artifacts.",
    )
    parser.add_argument(
        "--categories",
        default="",
        help="Comma-separated categories to test (default: all)",
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test.",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)
    evidence_dir = Path(args.evidence_dir)

    # Filter scenarios by category if specified
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    scenarios = TEST_SCENARIOS
    if categories:
        scenarios = [s for s in TEST_SCENARIOS if s.get("category") in categories]

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else pick_free_port()
            # ALWAYS use real services - this is a "real API" test file
            # Mock mode is NOT supported - defeats the purpose of LLM behavior testing
            env_overrides: dict[str, str] = {
                "MOCK_SERVICES_MODE": "false",
                "TESTING": "false",
                "FORCE_TEST_MODEL": "false",
            }
            if args.evidence:
                env_overrides["CAPTURE_EVIDENCE"] = "true"
            local = start_local_mcp_server(
                port, env_overrides=env_overrides, log_dir=evidence_dir
            )
            base_url = local.base_url
            print(f"Started local MCP server at {base_url}")

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"Connected to MCP server at {base_url}")

        tools = client.tools_list()
        tool_names = {t.get("name") for t in tools if isinstance(t, dict)}
        for required in ("create_campaign", "process_action"):
            if required not in tool_names:
                raise RuntimeError(
                    f"tools/list missing required tool {required}: {sorted(tool_names)}"
                )

        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)[
                :1
            ]  # Use first model only for quicker tests

        evidence_dir.mkdir(parents=True, exist_ok=True)
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / session_stamp
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "run.json"

        run_summary: dict[str, Any] = {
            "server": base_url,
            "models": models,
            "categories": categories or ["all"],
            "scenarios": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "by_category": {},
            },
        }

        ok = True
        for model_id in models:
            model_settings = settings_for_model(model_id)
            user_id = f"mcp-integrity-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)

            # Create campaign with a standard fantasy setting
            campaign_id = create_campaign(
                client,
                user_id,
                title="Campaign Integrity Test",
                character="Aldric the Wizard (INT 18, WIS 14)",
                setting="A medieval fantasy kingdom with castles and dungeons",
                description="Test campaign for validating campaign integrity guidelines",
            )

            for scenario in scenarios:
                run_summary["summary"]["total"] += 1
                category = scenario.get("category", "other")

                if category not in run_summary["summary"]["by_category"]:
                    run_summary["summary"]["by_category"][category] = {
                        "passed": 0,
                        "failed": 0,
                    }

                result = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=str(scenario["user_input"]),
                )
                narrative_text = extract_narrative(result)
                errors = validate_result(result, scenario, narrative=narrative_text)

                scenario_result = {
                    "model": model_id,
                    "name": scenario["name"],
                    "category": category,
                    "description": scenario.get("description", ""),
                    "user_input": scenario["user_input"],
                    # Capture the same narrative text used for validation, including fallback sources
                    "narrative_excerpt": (narrative_text or "")[:500],
                    "errors": errors,
                    "passed": len(errors) == 0,
                }
                run_summary["scenarios"].append(scenario_result)

                if errors:
                    ok = False
                    run_summary["summary"]["failed"] += 1
                    run_summary["summary"]["by_category"][category]["failed"] += 1
                    print(f"❌ {model_id} :: {scenario['name']}")
                    for err in errors:
                        print(f"   └─ {err}")
                else:
                    run_summary["summary"]["passed"] += 1
                    run_summary["summary"]["by_category"][category]["passed"] += 1
                    print(f"✅ {model_id} :: {scenario['name']}")

        # Write summary
        session_file.write_text(json.dumps(run_summary, indent=2))
        print(f"\n{'=' * 60}")
        print("Campaign Integrity Test Summary")
        print(f"{'=' * 60}")
        print(f"Total:  {run_summary['summary']['total']}")
        print(f"Passed: {run_summary['summary']['passed']}")
        print(f"Failed: {run_summary['summary']['failed']}")
        print("\nBy Category:")
        for cat, stats in run_summary["summary"]["by_category"].items():
            print(
                f"  {cat}: {stats['passed']}/{stats['passed'] + stats['failed']} passed"
            )
        print(f"\nEvidence: {session_file}")

        if local is not None:
            print(f"Local MCP log: {local.log_path}")

        return 0 if ok else 2
    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
