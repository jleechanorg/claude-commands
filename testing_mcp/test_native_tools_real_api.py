#!/usr/bin/env python3
"""Real API smoke tests for native two-phase tool calling across all providers.

This script tests that each provider properly handles dice rolls via native
tool calling, capturing evidence of the dice roll results.

IMPORTANT: This is NOT run in CI. Run manually with:
    cd testing_mcp && python test_native_tools_real_api.py

Requires API keys:
    - GEMINI_API_KEY for Gemini models
    - CEREBRAS_API_KEY for Cerebras models
    - OPENROUTER_API_KEY for OpenRouter models
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# CRITICAL: Set TESTING=false to use real APIs
os.environ["TESTING"] = "false"

from mvp_site import constants
from mvp_site.llm_providers import gemini_provider, cerebras_provider, openrouter_provider

# Evidence directory (relative to this script)
EVIDENCE_DIR = Path(__file__).parent / "evidence"

# Test prompt that should trigger dice rolls
COMBAT_PROMPT = """You are a D&D 5e Game Master. The player character Aric the Fighter is attacking a goblin with his longsword.

Player action: "I swing my longsword at the goblin!"

Important rules:
1. You MUST roll dice for the attack (d20 + modifier)
2. If hit, roll damage (1d8 + modifier for longsword)
3. Use the provided dice rolling tools

Respond with the combat outcome in JSON format with these fields:
- narrative: A vivid description of the combat action
- dice_rolls: Array of all dice rolled with results
- entities_mentioned: Array of entities involved
"""

SYSTEM_INSTRUCTION = """You are a Game Master for D&D 5e. Always use the dice rolling tools when combat or skill checks occur. Include all dice roll results in your response."""


def ensure_evidence_dirs():
    """Create evidence directories if they don't exist."""
    for provider in ["gemini", "cerebras", "openrouter"]:
        (EVIDENCE_DIR / provider).mkdir(parents=True, exist_ok=True)


def test_gemini_code_execution(model_name: str = "gemini-3-pro-preview"):
    """Test Gemini model with code_execution strategy (only works for Gemini 3+)."""
    print("\n" + "=" * 60)
    print(f"Testing {model_name} (code_execution strategy)")
    print("=" * 60)

    try:
        response = gemini_provider.generate_content_with_code_execution(
            prompt_contents=[COMBAT_PROMPT],
            model_name=model_name,
            system_instruction_text=SYSTEM_INSTRUCTION,
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=4000,
        )

        # Extract text from response
        text = ""
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text

        # Check for dice roll evidence
        has_dice = (
            "dice_rolls" in text.lower()
            or "rolled" in text.lower()
            or "d20" in text.lower()
        )

        # Save evidence
        evidence = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "strategy": "code_execution",
            "response_text": text,
            "has_dice_rolls": has_dice,
        }

        safe_name = model_name.replace("/", "_").replace(":", "_")
        evidence_file = EVIDENCE_DIR / "gemini" / f"{safe_name}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"Response length: {len(text)} chars")
        print(f"Contains dice rolls: {has_dice}")
        print(f"Evidence saved to: {evidence_file}")
        return has_dice

    except Exception as e:
        print(f"ERROR: {e}")
        safe_name = model_name.replace("/", "_").replace(":", "_")
        error_file = EVIDENCE_DIR / "gemini" / f"{safe_name}_error.txt"
        with open(error_file, "w") as f:
            f.write(str(e))
        return False


def test_gemini_native_tools(model_name: str = "gemini-2.0-flash"):
    """Test Gemini model with native_two_phase strategy."""
    print("\n" + "=" * 60)
    print(f"Testing {model_name} (native_two_phase strategy)")
    print("=" * 60)

    try:
        response = gemini_provider.generate_content_with_native_tools(
            prompt_contents=[COMBAT_PROMPT],
            model_name=model_name,
            system_instruction_text=SYSTEM_INSTRUCTION,
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=4000,
        )

        text = ""
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text

        has_dice = (
            "dice_rolls" in text.lower()
            or "rolled" in text.lower()
            or "d20" in text.lower()
        )

        evidence = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "strategy": "native_two_phase",
            "response_text": text,
            "has_dice_rolls": has_dice,
        }

        safe_name = model_name.replace("/", "_").replace(":", "_")
        evidence_file = EVIDENCE_DIR / "gemini" / f"{safe_name}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"Response length: {len(text)} chars")
        print(f"Contains dice rolls: {has_dice}")
        print(f"Evidence saved to: {evidence_file}")
        return has_dice

    except Exception as e:
        print(f"ERROR: {e}")
        safe_name = model_name.replace("/", "_").replace(":", "_")
        error_file = EVIDENCE_DIR / "gemini" / f"{safe_name}_error.txt"
        with open(error_file, "w") as f:
            f.write(str(e))
        return False


def test_cerebras_native_tools(model_name: str):
    """Test Cerebras model with native_two_phase strategy."""
    print("\n" + "=" * 60)
    print(f"Testing Cerebras {model_name} (native_two_phase strategy)")
    print("=" * 60)

    try:
        response = cerebras_provider.generate_content_with_native_tools(
            prompt_contents=[COMBAT_PROMPT],
            model_name=model_name,
            system_instruction_text=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=4000,
        )

        text = response.text if hasattr(response, "text") else str(response)

        has_dice = (
            "dice_rolls" in text.lower()
            or "rolled" in text.lower()
            or "d20" in text.lower()
        )

        evidence = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "strategy": "native_two_phase",
            "response_text": text,
            "has_dice_rolls": has_dice,
        }

        safe_name = model_name.replace("/", "_")
        evidence_file = EVIDENCE_DIR / "cerebras" / f"{safe_name}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"Response length: {len(text)} chars")
        print(f"Contains dice rolls: {has_dice}")
        print(f"Evidence saved to: {evidence_file}")
        return has_dice

    except Exception as e:
        print(f"ERROR: {e}")
        safe_name = model_name.replace("/", "_")
        error_file = EVIDENCE_DIR / "cerebras" / f"{safe_name}_error.txt"
        with open(error_file, "w") as f:
            f.write(str(e))
        return False


def test_openrouter_native_tools(model_name: str):
    """Test OpenRouter model with native_two_phase strategy."""
    print("\n" + "=" * 60)
    print(f"Testing OpenRouter {model_name} (native_two_phase strategy)")
    print("=" * 60)

    try:
        response = openrouter_provider.generate_content_with_native_tools(
            prompt_contents=[COMBAT_PROMPT],
            model_name=model_name,
            system_instruction_text=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=4000,
        )

        text = response.text if hasattr(response, "text") else str(response)

        has_dice = (
            "dice_rolls" in text.lower()
            or "rolled" in text.lower()
            or "d20" in text.lower()
        )

        evidence = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "strategy": "native_two_phase",
            "response_text": text,
            "has_dice_rolls": has_dice,
        }

        safe_name = model_name.replace("/", "_")
        evidence_file = EVIDENCE_DIR / "openrouter" / f"{safe_name}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"Response length: {len(text)} chars")
        print(f"Contains dice rolls: {has_dice}")
        print(f"Evidence saved to: {evidence_file}")
        return has_dice

    except Exception as e:
        print(f"ERROR: {e}")
        safe_name = model_name.replace("/", "_")
        error_file = EVIDENCE_DIR / "openrouter" / f"{safe_name}_error.txt"
        with open(error_file, "w") as f:
            f.write(str(e))
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("Native Two-Phase Tool Calling - Real API Smoke Tests")
    print("=" * 60)
    print(f"Evidence directory: {EVIDENCE_DIR}")
    print(f"Started: {datetime.now().isoformat()}")

    ensure_evidence_dirs()
    results = {}

    # Test Gemini models
    # Gemini 3 supports code_execution + JSON (verified Dec 2024)
    results["gemini-3-pro-preview"] = test_gemini_code_execution("gemini-3-pro-preview")

    # Gemini 2.x requires native_two_phase (code_execution + JSON broken)
    results["gemini-2.0-flash"] = test_gemini_native_tools("gemini-2.0-flash")

    # Test Cerebras models
    results["zai-glm-4.6"] = test_cerebras_native_tools("zai-glm-4.6")
    results["qwen-3-235b-a22b-instruct-2507"] = test_cerebras_native_tools(
        "qwen-3-235b-a22b-instruct-2507"
    )

    # Test OpenRouter models
    results["meta-llama/llama-3.1-70b-instruct"] = test_openrouter_native_tools(
        "meta-llama/llama-3.1-70b-instruct"
    )

    # Summary
    print("\n" + "=" * 60)
    print("SMOKE TEST SUMMARY")
    print("=" * 60)

    for model, success in results.items():
        status = "PASS" if success else "FAIL"
        icon = "\u2705" if success else "\u274C"
        print(f"  {icon} {status}: {model}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")

    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "passed": passed,
        "total": total,
    }
    summary_file = EVIDENCE_DIR / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nEvidence saved to: {EVIDENCE_DIR}/")
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
