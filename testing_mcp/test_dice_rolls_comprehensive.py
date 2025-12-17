#!/usr/bin/env python3
"""Comprehensive dice roll tests for all LLM providers.

Tests native two-phase tool calling across:
- Cerebras (GLM-4.6, Qwen-3)
- OpenRouter (Llama 3.1)
- Gemini (2.0-flash native, 3-pro code_execution)

Run with:
    cd testing_mcp && python test_dice_rolls_comprehensive.py

Or test specific provider:
    python test_dice_rolls_comprehensive.py --provider cerebras
    python test_dice_rolls_comprehensive.py --provider gemini
    python test_dice_rolls_comprehensive.py --provider openrouter
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# CRITICAL: Set TESTING=false to use real APIs
os.environ["TESTING"] = "false"

from mvp_site import constants
from mvp_site.llm_providers import cerebras_provider, gemini_provider, openrouter_provider

EVIDENCE_DIR = Path(__file__).parent / "evidence" / "dice_rolls"

# Test scenarios for comprehensive dice roll validation
TEST_SCENARIOS = {
    "combat_attack": {
        "name": "Combat Attack Roll",
        "prompt": """You are a D&D 5e Game Master. The player character Aric the Fighter (STR 16, +5 attack bonus) attacks a goblin (AC 15) with his longsword.

Player action: "I attack the goblin with my longsword!"

You MUST use the roll_attack tool to roll the attack and damage. The longsword does 1d8+3 damage.
Respond in JSON with: narrative, dice_rolls (array of roll results), entities_mentioned.""",
        "expected_tool": "roll_attack",
        "system": "You are a D&D 5e Game Master. ALWAYS use dice rolling tools for combat.",
    },
    "skill_check": {
        "name": "Skill Check Roll",
        "prompt": """You are a D&D 5e Game Master. The player character Lyra the Rogue (DEX 18, +7 Stealth) is trying to sneak past sleeping guards.

Player action: "I try to sneak past the guards without waking them."

You MUST use the roll_skill_check tool to make a Stealth check. The DC is 15.
Respond in JSON with: narrative, dice_rolls (array of roll results), entities_mentioned.""",
        "expected_tool": "roll_skill_check",
        "system": "You are a D&D 5e Game Master. ALWAYS use dice rolling tools for skill checks.",
    },
    "saving_throw": {
        "name": "Saving Throw Roll",
        "prompt": """You are a D&D 5e Game Master. A dragon breathes fire on the player character Theron the Paladin (CON 14, +2 save bonus). Theron must make a DC 18 Constitution saving throw to take half damage.

Player action: "I brace myself against the dragon fire!"

You MUST use the roll_saving_throw tool to make the Constitution save. The DC is 18.
Respond in JSON with: narrative, dice_rolls (array of roll results), entities_mentioned.""",
        "expected_tool": "roll_saving_throw",
        "system": "You are a D&D 5e Game Master. ALWAYS use dice rolling tools for saving throws.",
    },
    "generic_dice": {
        "name": "Generic Dice Roll",
        "prompt": """You are a D&D 5e Game Master. The party is determining initiative order for combat.

Player action: "I roll for initiative!"

You MUST use the roll_dice tool to roll 1d20+2 for initiative.
Respond in JSON with: narrative, dice_rolls (array of roll results), entities_mentioned.""",
        "expected_tool": "roll_dice",
        "system": "You are a D&D 5e Game Master. ALWAYS use dice rolling tools.",
    },
}

# Provider configurations
PROVIDERS = {
    "cerebras": {
        "models": ["zai-glm-4.6", "qwen-3-235b-a22b-instruct-2507"],
        "strategy": "native_two_phase",
        "test_fn": "test_cerebras",
    },
    "openrouter": {
        "models": ["meta-llama/llama-3.1-70b-instruct"],
        "strategy": "native_two_phase",
        "test_fn": "test_openrouter",
    },
    "gemini": {
        "models": ["gemini-2.0-flash", "gemini-3-pro-preview"],
        "strategy": "mixed",  # 2.0 uses native_two_phase, 3.0 uses code_execution
        "test_fn": "test_gemini",
    },
}


def ensure_evidence_dirs():
    """Create evidence directories."""
    for provider in PROVIDERS:
        (EVIDENCE_DIR / provider).mkdir(parents=True, exist_ok=True)


def validate_dice_rolls(response_text: str, expected_tool: str) -> dict:
    """Validate that response contains proper dice roll results."""
    result = {
        "has_dice_rolls": False,
        "dice_count": 0,
        "dice_rolls": [],
        "validation_errors": [],
    }

    # Try to parse as JSON
    try:
        data = json.loads(response_text)
        dice_rolls = data.get("dice_rolls", [])
        if dice_rolls:
            result["has_dice_rolls"] = True
            result["dice_count"] = len(dice_rolls)
            result["dice_rolls"] = dice_rolls
    except json.JSONDecodeError:
        # Check for dice notation in raw text
        import re

        dice_pattern = r"\d+d\d+(\+\d+)?\s*=\s*\d+"
        matches = re.findall(dice_pattern, response_text, re.IGNORECASE)
        if matches:
            result["has_dice_rolls"] = True
            result["dice_count"] = len(matches)

    # Validation checks
    if not result["has_dice_rolls"]:
        result["validation_errors"].append("No dice rolls found in response")

    if result["dice_count"] == 0:
        result["validation_errors"].append("dice_rolls array is empty")

    return result


def test_cerebras(model_name: str, scenario: dict) -> dict:
    """Test Cerebras model with native_two_phase strategy."""
    print(f"\n  Testing {model_name} - {scenario['name']}...")

    try:
        response = cerebras_provider.generate_content_with_native_tools(
            prompt_contents=[scenario["prompt"]],
            model_name=model_name,
            system_instruction_text=scenario["system"],
            temperature=0.7,
            max_output_tokens=4000,
        )

        text = response.text if hasattr(response, "text") else str(response)
        validation = validate_dice_rolls(text, scenario["expected_tool"])

        return {
            "success": validation["has_dice_rolls"],
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": "native_two_phase",
            "response_text": text,
            "validation": validation,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": "native_two_phase",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def test_openrouter(model_name: str, scenario: dict) -> dict:
    """Test OpenRouter model with native_two_phase strategy."""
    print(f"\n  Testing {model_name} - {scenario['name']}...")

    try:
        response = openrouter_provider.generate_content_with_native_tools(
            prompt_contents=[scenario["prompt"]],
            model_name=model_name,
            system_instruction_text=scenario["system"],
            temperature=0.7,
            max_output_tokens=4000,
        )

        text = response.text if hasattr(response, "text") else str(response)
        validation = validate_dice_rolls(text, scenario["expected_tool"])

        return {
            "success": validation["has_dice_rolls"],
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": "native_two_phase",
            "response_text": text,
            "validation": validation,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": "native_two_phase",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def test_gemini(model_name: str, scenario: dict) -> dict:
    """Test Gemini model with appropriate strategy."""
    print(f"\n  Testing {model_name} - {scenario['name']}...")

    # Gemini 3 uses code_execution, Gemini 2 uses native_two_phase
    use_code_execution = model_name in constants.MODELS_WITH_CODE_EXECUTION

    try:
        if use_code_execution:
            response = gemini_provider.generate_content_with_code_execution(
                prompt_contents=[scenario["prompt"]],
                model_name=model_name,
                system_instruction_text=scenario["system"],
                temperature=0.7,
                safety_settings=[],
                json_mode_max_output_tokens=4000,
            )
            strategy = "code_execution"
        else:
            response = gemini_provider.generate_content_with_native_tools(
                prompt_contents=[scenario["prompt"]],
                model_name=model_name,
                system_instruction_text=scenario["system"],
                temperature=0.7,
                safety_settings=[],
                json_mode_max_output_tokens=4000,
            )
            strategy = "native_two_phase"

        # Extract text from Gemini response
        text = ""
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text

        validation = validate_dice_rolls(text, scenario["expected_tool"])

        return {
            "success": validation["has_dice_rolls"],
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": strategy,
            "response_text": text,
            "validation": validation,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "scenario": scenario["name"],
            "strategy": "code_execution" if use_code_execution else "native_two_phase",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def run_provider_tests(provider_name: str, scenarios: list[str] | None = None) -> dict:
    """Run all tests for a specific provider."""
    provider = PROVIDERS[provider_name]
    test_fn = globals()[provider["test_fn"]]

    results = {"provider": provider_name, "models": {}, "summary": {"passed": 0, "failed": 0}}

    scenarios_to_run = scenarios or list(TEST_SCENARIOS.keys())

    for model_name in provider["models"]:
        print(f"\n{'=' * 60}")
        print(f"Testing {provider_name.upper()} - {model_name}")
        print("=" * 60)

        model_results = []
        for scenario_key in scenarios_to_run:
            scenario = TEST_SCENARIOS[scenario_key]
            result = test_fn(model_name, scenario)
            model_results.append(result)

            # Save individual evidence
            safe_model = model_name.replace("/", "_").replace(":", "_")
            evidence_file = EVIDENCE_DIR / provider_name / f"{safe_model}_{scenario_key}.json"
            with open(evidence_file, "w") as f:
                json.dump(result, f, indent=2)

            if result["success"]:
                results["summary"]["passed"] += 1
                print(f"    ✅ PASS: {scenario['name']}")
            else:
                results["summary"]["failed"] += 1
                error = result.get("error", result.get("validation", {}).get("validation_errors", []))
                print(f"    ❌ FAIL: {scenario['name']} - {error}")

        results["models"][model_name] = model_results

    return results


def main():
    parser = argparse.ArgumentParser(description="Comprehensive dice roll tests")
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()) + ["all"],
        default="all",
        help="Provider to test (default: all)",
    )
    parser.add_argument(
        "--scenario",
        choices=list(TEST_SCENARIOS.keys()),
        action="append",
        help="Specific scenario to test (can be repeated)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Comprehensive Dice Roll Tests - Real API")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Evidence directory: {EVIDENCE_DIR}")

    ensure_evidence_dirs()

    all_results = {}
    total_passed = 0
    total_failed = 0

    providers_to_test = list(PROVIDERS.keys()) if args.provider == "all" else [args.provider]

    for provider_name in providers_to_test:
        results = run_provider_tests(provider_name, args.scenario)
        all_results[provider_name] = results
        total_passed += results["summary"]["passed"]
        total_failed += results["summary"]["failed"]

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    for provider_name, results in all_results.items():
        passed = results["summary"]["passed"]
        failed = results["summary"]["failed"]
        total = passed + failed
        icon = "✅" if failed == 0 else "❌"
        print(f"  {icon} {provider_name.upper()}: {passed}/{total} passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} passed")

    # Save overall summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "results": all_results,
        "total_passed": total_passed,
        "total_failed": total_failed,
    }
    summary_file = EVIDENCE_DIR / "comprehensive_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nEvidence saved to: {EVIDENCE_DIR}/")
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
