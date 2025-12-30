#!/usr/bin/env python3
"""MCP test: LLM must provide EXPLICIT NUMERIC answers for force/resource counting.

This test reproduces a bug where users repeatedly ask "how many soldiers/spies do I have"
and the LLM responds with narrative prose that buries or omits the actual numbers.

Bug Pattern (from docs/debugging/Nocturne bg3 after (6).txt):
  User: "how many companions, spies, soldiers do I have now?"
  LLM: [500 words of prose mentioning names but NO COUNTS]
  User: "assess how many spies and soldiers I have"
  LLM: "seven elite combatants" buried in paragraph 3
  User: "how come you never answer how many spies/soldiers I have?"

Root Cause:
  LLM over-narrativizes data queries instead of leading with clear numbers.

Expected Behavior:
  When user asks "how many X", response MUST contain explicit numbers prominently.

Run (local MCP already running):
    cd testing_mcp
    python test_force_count_explicit_numbers.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_force_count_explicit_numbers.py --start-local --real-services

Run with evidence collection:
    cd testing_mcp
    python test_force_count_explicit_numbers.py --start-local --real-services --evidence
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.campaign_utils import create_campaign, process_action
from lib.mcp_client import MCPClient
from lib.model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

# =============================================================================
# CHARACTER SETUP - Military commander with known force composition
# =============================================================================

CHARACTER_COMMANDER = """
Nocturne the Ascendant Architect (Level 13 Bard, College of Whispers)
Race: Half-Elf
Attributes: STR 8, DEX 14, CON 12, INT 16, WIS 10, CHA 22 (+6)

Background: Noble (disgraced), now controls a shadow network

CURRENT MILITARY ASSETS (EXACT COUNTS):
=======================================
ELITE COMBATANTS (7 total):
- Silas the Vanguard Commander (1) - Veteran Fighter
- Morwen the Shadow (1) - Assassin
- Grave-Walker Twins (2) - Ranger specialists
- Kaelen (1) - Gloomstalker
- Vesper (1) - Shadow Monk
- Ghost Jax (1) - Arcane Trickster

STANDARD GUARDS (40 total):
- Mercenary guards at Highcliff Manor (40) - Basic security

SPY NETWORK (20 total):
- Informants across Baldur's Gate (20) - Intelligence gathering

COMPANIONS (3 total):
- Vaximus the Cryptographer (1) - Intellectual asset
- Elara (1) - Sister, non-combatant
- Lyra (1) - Sister, non-combatant

TOTAL FORCES SUMMARY:
- Elite combatants: 7
- Standard guards: 40
- Spies/Informants: 20
- Companions: 3
- GRAND TOTAL: 70 personnel

IMPORTANT: When asked about force counts, ALWAYS provide exact numbers first.
The player has repeatedly requested numerical breakdowns - honor this request.
"""

SETTING_SHADOW_EMPIRE = """
You are in the solar of Highcliff Manor, your shadow headquarters in Baldur's Gate.
Maps and ledgers cover the mahogany desk. Your network stretches across the city.
You have recently consolidated your power after several successful operations.

The player is reviewing their assets and wants a clear accounting of their forces.
They have explicitly requested numerical answers multiple times in the past.
"""

CHARACTER_NAMES = ["Silas", "Morwen", "Kaelen", "Vesper", "Jax", "Vaximus"]

# =============================================================================
# TEST SCENARIOS - Various ways users ask for force counts
# =============================================================================

FORCE_COUNT_SCENARIOS = [
    {
        "name": "Direct count request - how many soldiers",
        "user_input": "How many soldiers do I have?",
        "expected_numbers": {"guards": 40, "elite": 7},
        "minimum_numbers_in_response": 1,
        "first_sentence_number": True,  # Number should appear in first 2 sentences
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Direct count request - how many spies",
        "user_input": "How many spies do I have?",
        "expected_numbers": {"spies": 20},
        "minimum_numbers_in_response": 1,
        "first_sentence_number": True,
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Full force inventory request",
        "user_input": "List all my forces with exact numbers.",
        "expected_numbers": {"elite": 7, "guards": 40, "spies": 20},
        "minimum_numbers_in_response": 3,
        "first_sentence_number": False,  # List requests can take more sentences to enumerate
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Total count request",
        "user_input": "What is the total count of all my personnel?",
        "expected_numbers": {"total": 70},
        "minimum_numbers_in_response": 1,
        "first_sentence_number": True,
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Think request with count",
        "user_input": "Think. How many companions, spies, soldiers do I have now? What are my full faction resources?",
        "expected_numbers": {"elite": 7, "guards": 40, "spies": 20, "companions": 3},
        "minimum_numbers_in_response": 3,
        "first_sentence_number": True,  # ABSOLUTE PRECEDENCE: even "Think." prefix requires first-sentence numbers
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Assess forces request",
        "user_input": "Assess how many spies and soldiers I have.",
        "expected_numbers": {"spies": 20, "guards": 40, "elite": 7},
        "minimum_numbers_in_response": 2,
        "first_sentence_number": False,  # Assessment requests can take more sentences
        "character_names": CHARACTER_NAMES,
    },
    {
        "name": "Frustrated repeat request",
        "user_input": "Just tell me the NUMBER. How many soldiers and spies? Give me actual numbers, not prose.",
        "expected_numbers": {"spies": 20, "guards": 40, "elite": 7},
        "minimum_numbers_in_response": 2,
        "first_sentence_number": True,
        "character_names": CHARACTER_NAMES,
    },
]

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

PROSE_LENGTH_THRESHOLD = 500
"""Maximum characters allowed before flagging over-narrativizing when counts are absent."""

PROMINENCE_SENTENCE_LIMIT = 2
"""Number of leading sentences that must contain a number when prominence is required."""

NAME_DUMP_THRESHOLD = 3
"""Minimum distinct character names before flagging a name-dump without numbers."""

NARRATIVE_PREVIEW_CHARS = 150
"""Characters shown when previewing narratives in failures for readability."""

PROCESS_ACTION_TIMEOUT = 90.0
"""Timeout (seconds) for the process_action tool call in each scenario."""


def extract_numbers_from_text(text: str) -> list[int]:
    """Extract all numbers from text."""
    # Match digits, including numbers written as words for common counts
    digit_pattern = r"\b(\d+)\b"
    matches = re.findall(digit_pattern, text)
    numbers = [int(m) for m in matches]

    # Handle compound numbers like "forty-seven"
    compound_pattern = r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[-\s]?(one|two|three|four|five|six|seven|eight|nine)\b"
    tens = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }
    ones = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
    }
    text_lower = text.lower()
    for match in re.finditer(compound_pattern, text_lower):
        numbers.append(tens[match.group(1)] + ones[match.group(2)])

    # Remove compound segments to avoid double-counting components as single words
    text_for_words = re.sub(compound_pattern, " ", text_lower)

    # Also check for common number words
    word_numbers = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }
    for word, value in word_numbers.items():
        pattern = rf"\b{re.escape(word)}\b"
        if re.search(pattern, text_for_words):
            numbers.append(value)

    # Deduplicate while preserving order
    return list(dict.fromkeys(numbers))


def get_first_n_sentences(text: str, n: int = 2) -> str:
    """Get the first n sentences of text.

    Uses a simple approach that handles common abbreviations without
    variable-width lookbehinds (which Python's re module doesn't support).
    """
    if not text:
        return ""

    text = text.strip()

    # Protect common abbreviations by temporarily replacing their periods
    abbreviations = ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St."]
    protected = text
    for abbr in abbreviations:
        protected = protected.replace(abbr, abbr.replace(".", "<DOT>"))

    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r"(?<=[.!?])\s+", protected)

    # Take first n sentences and restore periods
    result = " ".join(sentences[:n])
    return result.replace("<DOT>", ".")


def validate_force_count_response(
    result: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Validate that LLM provided explicit numbers for force count queries.

    Returns (passed, errors) tuple.
    """
    errors: list[str] = []
    narrative = result.get("narrative") or ""

    if result.get("error"):
        errors.append(f"Server returned error: {result['error']}")
        return False, errors

    if not narrative:
        errors.append("No narrative returned - empty response")
        return False, errors

    # Extract numbers from response
    numbers_found = extract_numbers_from_text(narrative)

    # Check minimum numbers requirement
    min_numbers = scenario.get("minimum_numbers_in_response", 1)
    if len(numbers_found) < min_numbers:
        errors.append(
            f"NUMERIC RESPONSE FAILURE: Expected at least {min_numbers} numbers, "
            f"found {len(numbers_found)}. Numbers found: {numbers_found}"
        )

    # Check if expected numbers appear
    expected = scenario.get("expected_numbers", {})
    for category, expected_value in expected.items():
        if expected_value not in numbers_found:
            # Allow for some flexibility - maybe they split 47 into "40 guards + 7 elite"
            errors.append(
                f"MISSING COUNT: Expected '{category}' count of {expected_value} "
                f"not found in response. Numbers present: {numbers_found}"
            )

    # Check if number appears early (first 2 sentences)
    if scenario.get("first_sentence_number", False):
        first_sentences = get_first_n_sentences(narrative, PROMINENCE_SENTENCE_LIMIT)
        early_numbers = extract_numbers_from_text(first_sentences)
        if not early_numbers:
            errors.append(
                f"PROMINENCE FAILURE: No numbers in first 2 sentences. "
                f"User asked for count, but response buries numbers in prose. "
                f"First sentences: '{textwrap.shorten(first_sentences, width=NARRATIVE_PREVIEW_CHARS, placeholder='...')}'"
            )

    # Check for over-narrativizing patterns (prose without numbers)
    prose_length = len(narrative)
    if prose_length > PROSE_LENGTH_THRESHOLD and len(numbers_found) < 2:
        errors.append(
            f"OVER-NARRATIVIZING: Response is {prose_length} chars but only "
            f"{len(numbers_found)} numbers. User asked for counts, got prose."
        )

    # Specific anti-pattern: names without counts
    character_names = scenario.get("character_names", CHARACTER_NAMES)
    names_mentioned = sum(
        1 for name in character_names if name.lower() in narrative.lower()
    )
    if names_mentioned >= NAME_DUMP_THRESHOLD and len(numbers_found) < 2:
        errors.append(
            f"NAME-DUMP WITHOUT COUNTS: Response mentions {names_mentioned} character names "
            f"but only {len(numbers_found)} actual numbers. This is the exact bug pattern."
        )

    return len(errors) == 0, errors


def get_git_commit_hash() -> str:
    """Get current git commit hash."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()[:12] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_prompt_fingerprint() -> str:
    """Get hash of master_directive.md for provenance tracking."""
    try:
        import hashlib
        prompt_path = Path(__file__).parent.parent / "mvp_site" / "prompts" / "master_directive.md"
        if prompt_path.exists():
            content = prompt_path.read_text()
            return hashlib.sha256(content.encode()).hexdigest()[:16]
    except Exception:
        pass
    return "unknown"


def save_evidence(
    model_id: str,
    scenario_name: str,
    user_input: str,
    result: dict[str, Any],
    validation_errors: list[str],
    evidence_dir: Path,
) -> None:
    """Save test evidence to disk."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    safe_model = model_id.replace("/", "-").replace(":", "-")
    safe_scenario = (
        scenario_name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")
    )[:60]

    evidence_file = evidence_dir / f"{timestamp}_{safe_model}_{safe_scenario}.json"

    evidence = {
        "timestamp": timestamp,
        "model_id": model_id,
        "scenario_name": scenario_name,
        "user_input": user_input,
        "validation_passed": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "narrative": result.get("narrative", ""),
        "numbers_extracted": extract_numbers_from_text(result.get("narrative", "")),
        "dice_rolls": result.get("dice_rolls", []),
        "state_updates": result.get("state_updates", {}),
        "game_state": result.get("game_state", {}),
        # Provenance tracking
        "git_commit": get_git_commit_hash(),
        "prompt_fingerprint": get_prompt_fingerprint(),
    }

    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"  📁 Evidence saved: {evidence_file.name}")


def run_force_count_tests(
    client: MCPClient,
    model_id: str,
    scenarios: list[dict],
    evidence_dir: Path | None,
    created_campaigns: list[tuple[str, str]],
) -> tuple[int, int]:
    """Run force count scenarios and return (passed, total) counts."""
    passed_tests = 0
    total_tests = 0

    model_settings = settings_for_model(model_id)
    model_settings["debug_mode"] = True
    user_id = f"force-count-{model_id.replace('/', '-')}-{int(time.time())}"

    # Update user settings
    update_user_settings(client, user_id=user_id, settings=model_settings)

    # Create campaign with commander character using lib utility
    try:
        campaign_id = create_campaign(
            client,
            user_id,
            title="Force Count Validation Test",
            character=CHARACTER_COMMANDER,
            setting=SETTING_SHADOW_EMPIRE,
            description="Test campaign for validating numeric force count responses",
        )
    except RuntimeError as e:
        print(f"❌ Failed to create campaign: {e}")
        return 0, len(scenarios)

    print(f"   Campaign created: {campaign_id}")
    created_campaigns.append((user_id, campaign_id))

    # Run scenarios
    for scenario in scenarios:
        total_tests += 1
        scenario_name = scenario["name"]
        user_input = scenario["user_input"]

        print(f"\n   Testing: {scenario_name}")
        print(f'   Input: "{user_input[:60]}..."')
        print("   Expected: Explicit numeric counts")

        # Process action using lib utility
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            process_action,
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=user_input,
            mode="character",
        )
        try:
            result = future.result(timeout=PROCESS_ACTION_TIMEOUT)
        except TimeoutError:
            print(f"   ❌ FAILED: Timed out after {PROCESS_ACTION_TIMEOUT:.0f}s")
            executor.shutdown(wait=False, cancel_futures=True)
            continue
        except Exception:
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        else:
            executor.shutdown(wait=True, cancel_futures=True)

        # Validate result
        passed, validation_errors = validate_force_count_response(result, scenario)

        # Save evidence if requested
        if evidence_dir:
            save_evidence(
                model_id,
                scenario_name,
                user_input,
                result,
                validation_errors,
                evidence_dir,
            )

        # Report results
        if validation_errors:
            print(f"   ❌ FAILED: {scenario_name}")
            for error in validation_errors[:3]:  # Limit error output
                print(
                    f"      Error: {textwrap.shorten(error, width=100, placeholder='...')}"
                )
            narrative_preview = textwrap.shorten(
                result.get("narrative") or "",
                width=NARRATIVE_PREVIEW_CHARS,
                placeholder="...",
            )
            print(f'      Narrative start: "{narrative_preview}"')

            # Show what numbers were found
            numbers = extract_numbers_from_text(result.get("narrative", ""))
            print(f"      Numbers found: {numbers[:10]}")
        else:
            passed_tests += 1
            print("   ✅ PASSED: LLM provided explicit numeric counts")
            numbers = extract_numbers_from_text(result.get("narrative", ""))
            print(f"      Numbers found: {numbers[:5]}")

    return passed_tests, total_tests


def main() -> int:  # noqa: PLR0915 - orchestration CLI naturally long
    parser = argparse.ArgumentParser(
        description="MCP test: LLM must provide explicit numbers for force count queries"
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
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test. Defaults to Gemini+Qwen matrix.",
    )
    parser.add_argument(
        "--real-services",
        action="store_true",
        help="Use real API providers (requires API keys)",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Save detailed evidence files for each test",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    client: MCPClient | None = None
    created_campaigns: list[tuple[str, str]] = []
    base_url = str(args.server_url)

    try:
        # Start local MCP server if requested
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            env_overrides: dict[str, str] = {
                "MOCK_SERVICES_MODE": "false" if args.real_services else "true",
                "TESTING": "false",
                "FORCE_TEST_MODEL": "false",
                "FAST_TESTS": "false",
                "CAPTURE_EVIDENCE": "true",
            }
            local = start_local_mcp_server(port, env_overrides=env_overrides)
            base_url = local.base_url
            print(f"🚀 Local MCP server started on {base_url}")
            print(f"📋 Log file: {local.log_path}")

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"✅ MCP server healthy at {base_url}\n")

        # Parse model list
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        # Setup evidence directory if requested
        evidence_dir = None
        if args.evidence:
            evidence_dir = Path(__file__).parent / "evidence" / "force_count"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Evidence directory: {evidence_dir}\n")

        total_passed = 0
        total_tests = 0

        print("=" * 70)
        print("FORCE COUNT EXPLICIT NUMBERS TEST")
        print("=" * 70)
        print()
        print("This test validates that when users ask 'how many X do I have',")
        print("the LLM responds with EXPLICIT NUMBERS, not prose that buries counts.")
        print()

        for model_id in models:
            print(f"\n🤖 Testing model: {model_id}")
            print("-" * 50)

            passed, total = run_force_count_tests(
                client,
                model_id,
                FORCE_COUNT_SCENARIOS,
                evidence_dir,
                created_campaigns,
            )

            total_passed += passed
            total_tests += total

            print(f"\n   Model {model_id}: {passed}/{total} passed")

        # Final summary
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)
        print(f"Total: {total_passed}/{total_tests} tests passed")

        if total_passed < total_tests:
            print("\n⚠️  FORCE COUNT BUG REPRODUCED")
            print("The LLM is over-narrativizing count queries instead of")
            print("providing explicit numeric answers.")
            return 1
        print("\n✅ All force count tests passed - LLM provides explicit numbers")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        traceback.print_exc()
        return 1

    finally:
        # Cleanup campaigns
        if client and created_campaigns:
            print("\n🧹 Cleaning up test campaigns...")
            for user_id, campaign_id in created_campaigns:
                try:
                    client.tools_call(
                        "delete_campaign",
                        {"user_id": user_id, "campaign_id": campaign_id},
                    )
                except Exception as cleanup_err:
                    # Non-fatal: log cleanup issues but do not fail the test harness
                    print(f"   ⚠️ Cleanup failed for {campaign_id}: {cleanup_err}")

        # Stop local server
        if local:
            print("🛑 Stopping local MCP server...")
            local.stop()


if __name__ == "__main__":
    sys.exit(main())
