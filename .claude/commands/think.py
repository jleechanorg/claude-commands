#!/usr/bin/env python3
"""
Enhanced Think Command with Fake Detection

Performs systematic problem-solving using sequential thinking with automatic
detection of fake/demo/simulation patterns in code and implementations.
"""

import os
import sys
from typing import List

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from fake_detector import FakeDetector, FakePattern


def parse_think_level(args: List[str]) -> tuple[str, str]:
    """Parse thinking level and problem from arguments"""
    if not args:
        return "light", ""

    # Check if first argument is a level
    level_map = {
        "light": "light",
        "l": "light",
        "medium": "medium",
        "m": "medium",
        "deep": "deep",
        "d": "deep",
        "ultra": "ultra",
        "u": "ultra",
    }

    first_arg = args[0].lower()
    if first_arg in level_map:
        level = level_map[first_arg]
        problem = " ".join(args[1:]) if len(args) > 1 else ""
    else:
        level = "light"  # Default
        problem = " ".join(args)

    return level, problem


def detect_fake_in_problem(problem: str) -> List[FakePattern]:
    """Detect if the problem mentions fake implementations"""
    detector = FakeDetector()

    # Check for mentions of fake/demo patterns in the problem description
    fake_keywords = [
        "fake",
        "demo",
        "simulation",
        "mock",
        "placeholder",
        "hardcoded",
        "todo",
        "unfinished",
        "not implemented",
    ]

    patterns = []
    problem_lower = problem.lower()

    for keyword in fake_keywords:
        if keyword in problem_lower:
            patterns.append(
                FakePattern(
                    type="problem_mentions_fake",
                    severity="medium",
                    location="user_input",
                    description=f"Problem description mentions '{keyword}' - suggests fake implementation concern",
                    evidence=problem,
                    suggestion="Consider analyzing specific files or code for fake patterns",
                )
            )
            break  # Only report once per problem

    return patterns


def analyze_current_directory_for_fakes() -> List[FakePattern]:
    """Analyze current directory for fake patterns"""
    detector = FakeDetector()
    patterns = []

    # Look for Python files in current directory and common subdirectories
    search_paths = [".", "mvp_site", ".claude/commands", "tests"]

    for search_path in search_paths:
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories and __pycache__
                dirs[:] = [
                    d for d in dirs if not d.startswith(".") and d != "__pycache__"
                ]

                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        file_patterns = detector.analyze_file(filepath)
                        patterns.extend(file_patterns)

                        # Limit to prevent overwhelming output
                        if len(patterns) > 20:
                            break
                if len(patterns) > 20:
                    break
            if len(patterns) > 20:
                break

    return patterns


def format_thinking_prompt(
    level: str, problem: str, fake_patterns: List[FakePattern]
) -> str:
    """Format the prompt for sequential thinking with fake detection context"""

    base_prompt = (
        f"Problem: {problem}\n" if problem else "General analysis requested.\n"
    )

    if fake_patterns:
        base_prompt += f"\n🚨 FAKE PATTERNS DETECTED ({len(fake_patterns)}):\n"
        for pattern in fake_patterns[:5]:  # Show top 5
            base_prompt += (
                f"- {pattern.type}: {pattern.description} ({pattern.location})\n"
            )
        if len(fake_patterns) > 5:
            base_prompt += f"- ... and {len(fake_patterns) - 5} more patterns\n"

        base_prompt += "\nConsider these fake patterns in your analysis. Focus on identifying root causes and permanent solutions.\n"

    # Add level-specific guidance
    level_guidance = {
        "light": "Provide a quick analysis focusing on the most critical aspects.",
        "medium": "Provide a thorough analysis considering multiple perspectives.",
        "deep": "Provide a comprehensive analysis with detailed reasoning and alternatives.",
        "ultra": "Provide maximum depth analysis with extensive exploration of causes, solutions, and implications.",
    }

    base_prompt += f"\nThinking Level: {level.title()} - {level_guidance[level]}"

    return base_prompt


def main():
    """Main think command with fake detection"""
    args = sys.argv[1:]

    # Parse arguments
    level, problem = parse_think_level(args)

    print(f"🧠 Think Command (Level: {level.title()})")

    # Detect fake patterns in the problem statement
    problem_patterns = detect_fake_in_problem(problem) if problem else []

    # Auto-detect fake patterns in current environment
    print("🔍 Scanning for fake/demo patterns...")
    env_patterns = analyze_current_directory_for_fakes()

    all_patterns = problem_patterns + env_patterns

    if all_patterns:
        print(f"\n⚠️  Found {len(all_patterns)} potential fake patterns")
        detector = FakeDetector()
        fake_report = detector.generate_report(all_patterns[:10])  # Show top 10
        print(fake_report)
        print()
    else:
        print("✅ No obvious fake patterns detected in current environment")
        print()

    # Format the thinking prompt
    thinking_prompt = format_thinking_prompt(level, problem, all_patterns)

    print("🤔 Initiating sequential thinking analysis...")
    print(f"📝 Problem: {problem}" if problem else "📝 General analysis mode")
    print(f"🎯 Level: {level.title()}")
    print()

    # Here we would normally call the sequential thinking tool
    # Since this is a command-line script, we'll output what would be done
    print("=" * 60)
    print("THINKING PROMPT:")
    print("=" * 60)
    print(thinking_prompt)
    print("=" * 60)
    print()
    print(
        "💡 In Claude Code, this would trigger the mcp__sequential-thinking__sequentialthinking tool"
    )
    print(f"   with totalThoughts: {get_thought_count(level)} and the above prompt.")
    print()

    # Show actionable recommendations based on fake patterns
    if all_patterns:
        print("🛠️  RECOMMENDED ACTIONS:")
        critical_patterns = [p for p in all_patterns if p.severity == "critical"]
        if critical_patterns:
            print("🚨 CRITICAL (Fix Immediately):")
            for pattern in critical_patterns[:3]:
                print(f"   - {pattern.suggestion} ({pattern.location})")

        high_patterns = [p for p in all_patterns if p.severity == "high"]
        if high_patterns:
            print("⚠️  HIGH PRIORITY:")
            for pattern in high_patterns[:3]:
                print(f"   - {pattern.suggestion} ({pattern.location})")

        print()
        print("💡 Run '/arch <file>' or '/reviewdeep <target>' for detailed analysis")


def get_thought_count(level: str) -> int:
    """Get thought count for thinking level"""
    counts = {"light": 4, "medium": 6, "deep": 8, "ultra": 12}
    return counts.get(level, 4)


if __name__ == "__main__":
    main()
