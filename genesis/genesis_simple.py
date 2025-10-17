#!/usr/bin/env python3
"""Simplified Genesis runner that reuses shared CLI parsing."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .common_cli import (
    GenesisArguments,
    GenesisHelpRequested,
    GenesisUsageError,
    parse_genesis_cli,
    print_usage as print_cli_usage,
)
from . import genesis as genesis_full

COMPLETION_KEYWORDS = [
    "CONVERGED",
    "OBJECTIVE ACHIEVED",
    "GENESIS COMPLETION",
    "FINAL ASSESSMENT",
]
SESSION_FILENAME = "proto_genesis_session.json"
MAX_SUMMARY_LINES = 40


def detect_completion(text: str) -> bool:
    upper_text = text.upper()
    return any(keyword in upper_text for keyword in COMPLETION_KEYWORDS)


def build_prompt(
    refined_goal: str,
    exit_criteria: str,
    iteration: int,
    max_iterations: int,
    previous_summary: str,
    skip_initial_generation: bool,
) -> str:
    previous_text = previous_summary.strip() or "No previous work recorded yet."
    exit_text = exit_criteria.strip() or "(no explicit exit criteria provided)"
    progress_text = (
        "Initial planning is skipped; focus on incremental execution."
        if skip_initial_generation
        else "Start with a concise plan then execute the next concrete actions."
    )
    return (
        "### PROTO GENESIS SIMPLE LOOP\n"
        "You are operating headless without UI feedback.\n"
        "Maintain momentum, avoid placeholders, and finish the task.\n\n"
        f"Iteration: {iteration}/{max_iterations}\n"
        f"Mode: {'Iterative refinement' if skip_initial_generation else 'Plan + execute'}\n"
        "\n"
        f"Refined Goal:\n{refined_goal}\n\n"
        f"Exit Criteria:\n{exit_text}\n\n"
        f"Previous Summary:\n{previous_text}\n\n"
        "Instructions:\n"
        "1. Outline the concrete actions you will perform this iteration.\n"
        "2. Execute those actions step-by-step, reasoning explicitly.\n"
        "3. Summarize the new state of the world.\n"
        "4. If work is fully complete, explicitly write 'GENESIS COMPLETION' and describe final validation.\n"
        "5. If more work remains, provide the most important next focus area.\n"
        f"\nContextual Guidance: {progress_text}\n"
    )


def load_session(session_path: Path) -> Dict[str, object]:
    if not session_path.exists():
        return {}
    try:
        return json.loads(session_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(
            f"⚠️ Existing session file at {session_path} is not valid JSON; starting fresh.",
            file=sys.stderr,
        )
        return {}


def save_session(session_path: Path, session: Dict[str, object]) -> None:
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")


def ensure_goal_context(goal_dir: Optional[str], session: Dict[str, object]) -> None:
    if not goal_dir:
        return
    session.setdefault("goal_directory", goal_dir)


def summarize_output(output: str) -> str:
    lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    return "\n".join(lines[-MAX_SUMMARY_LINES:]) if lines else ""


def handle_refine_mode(cli_args: GenesisArguments) -> Dict[str, Optional[str]]:
    original_goal = cli_args.refine_goal or ""
    use_codex = cli_args.use_codex

    print("🔄 REFINE MODE DETECTED (genesis_simple)")
    print(f"📝 Goal: {original_goal[:100]}...")
    print(f"🔢 Max Iterations: {cli_args.max_iterations}")

    refined_goal: Optional[str] = None
    exit_criteria: Optional[str] = None

    while True:
        response = genesis_full.refine_goal_interactive(original_goal, use_codex)
        if not response:
            raise RuntimeError("Goal refinement failed to produce a response.")

        refined_goal, exit_criteria = genesis_full.parse_refinement(response)
        if not refined_goal:
            raise RuntimeError("Unable to parse refined goal from response.")

        print("\nProposed Refinement:")
        print(f"Refined Goal: {refined_goal}")
        if exit_criteria:
            print(f"Exit Criteria:\n{exit_criteria}")

        if not cli_args.interactive:
            break

        if not sys.stdin.isatty():
            print("stdin is not interactive; auto-approving refinement.")
            break

        approval = input("Do you approve this refinement? (y/n): ").strip().lower()
        if approval in {"y", "yes"}:
            break
        print("Re-attempting refinement...\n")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    goal_slug = "-".join(original_goal.lower().split()[:4]) or "goal"
    goal_dir = f"goals/{timestamp}-{goal_slug}"
    description = f"REFINED GOAL: {refined_goal}\n\nEXIT CRITERIA:\n{exit_criteria or 'Not specified.'}"

    print(f"\n🎯 Creating goal directory: {goal_dir}")
    success = genesis_full.generate_goal_files_fast(description, goal_dir)
    if not success:
        print("❌ Goal directory generation failed; using repository root session file.")
        return {
            "goal_dir": None,
            "session_file": SESSION_FILENAME,
            "refined_goal": refined_goal,
            "exit_criteria": exit_criteria,
        }

    session_file = str(Path(goal_dir) / SESSION_FILENAME)
    print(f"✅ Goal directory created: {goal_dir}")
    print(f"📁 Session file: {session_file}")

    return {
        "goal_dir": goal_dir,
        "session_file": session_file,
        "refined_goal": refined_goal,
        "exit_criteria": exit_criteria,
    }


def main() -> None:
    original_args = list(sys.argv)

    try:
        cli_args: GenesisArguments = parse_genesis_cli(sys.argv)
    except GenesisHelpRequested:
        print_cli_usage()
        sys.exit(0)
    except GenesisUsageError as exc:
        print_cli_usage(str(exc))
        sys.exit(1)

    genesis_full.GENESIS_USE_CODEX = cli_args.use_codex

    genesis_full.set_subagent_pool_size(cli_args.pool_size)
    if any(arg.startswith("--pool-size") for arg in original_args):
        print(f"🤖 Setting subagent pool size to: {cli_args.pool_size}")

    skip_initial_generation = cli_args.skip_initial_generation
    if skip_initial_generation:
        print("🔄 --iterate active: skipping initial bulk generation phase.")
    else:
        print("🚀 Standard mode: initial iteration may include planning.")

    if cli_args.mode == "refine":
        refine_context = handle_refine_mode(cli_args)
        goal_dir = refine_context["goal_dir"]
        session_file = refine_context["session_file"] or SESSION_FILENAME
        refined_goal = refine_context["refined_goal"] or cli_args.refine_goal or ""
        exit_criteria = refine_context["exit_criteria"] or ""
    else:
        goal_dir = cli_args.goal_directory
        if not goal_dir:
            raise SystemExit("Goal directory must be provided in goal mode.")
        refined_goal, exit_criteria = genesis_full.load_goal_from_directory(goal_dir)
        session_file = str(Path(goal_dir) / SESSION_FILENAME)

    session_path = Path(session_file)
    session_data = load_session(session_path)

    session_data.setdefault("refined_goal", refined_goal)
    session_data.setdefault("exit_criteria", exit_criteria)
    session_data.setdefault("max_iterations", cli_args.max_iterations)
    session_data.setdefault("history", [])
    ensure_goal_context(goal_dir, session_data)

    previous_summary = session_data.get("latest_summary", "") or ""
    start_iteration = int(session_data.get("current_iteration", 0))

    print("\nSTARTING SIMPLE GENESIS LOOP")
    print("=" * 40)
    print(f"Goal Context: {session_data.get('refined_goal', '')[:120]}...")
    print(f"Exit Criteria Preview: {session_data.get('exit_criteria', '')[:120]}...")
    print(f"Session file: {session_path}")
    print()

    if start_iteration >= cli_args.max_iterations:
        print("No iterations to run; already at or beyond max_iterations.")
        return

    for iteration in range(start_iteration, cli_args.max_iterations):
        iteration_number = iteration + 1
        print(f"🎯 Iteration {iteration_number}/{cli_args.max_iterations}")

        if cli_args.interactive and sys.stdin.isatty():
            answer = input("Proceed with this iteration? (y/n): ").strip().lower()
            if answer not in {"y", "yes", ""}:
                print("Stopping at user request.")
                break

        prompt = build_prompt(
            refined_goal=session_data.get("refined_goal", ""),
            exit_criteria=session_data.get("exit_criteria", ""),
            iteration=iteration_number,
            max_iterations=cli_args.max_iterations,
            previous_summary=previous_summary,
            skip_initial_generation=skip_initial_generation and iteration_number == 1,
        )

        print("🧠 Dispatching prompt to model...")
        try:
            if cli_args.use_codex:
                response = genesis_full.execute_codex_command(prompt)
            else:
                response = genesis_full.execute_claude_command(prompt)
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Model invocation failed: {exc}")
            save_session(session_path, session_data)
            break

        if not response:
            print("❌ Model did not return a response; aborting loop.")
            break

        print("📥 Model response received (truncated preview):")
        print("-" * 60)
        preview = "\n".join(response.splitlines()[:30])
        print(preview)
        print("-" * 60)

        history: List[Dict[str, object]] = session_data.setdefault("history", [])  # type: ignore[assignment]
        history.append(
            {
                "iteration": iteration_number,
                "timestamp": time.time(),
                "output": response,
            }
        )

        previous_summary = summarize_output(response)
        session_data["latest_summary"] = previous_summary
        session_data["current_iteration"] = iteration_number

        save_session(session_path, session_data)
        print(f"💾 Session updated at {session_path}")

        if detect_completion(response):
            print("✅ Completion marker detected. Stopping iterations.")
            break

        print("➡️  Continuing to next iteration...\n")
    else:
        print("Max iterations reached without explicit completion signal.")

    print("\nSession Summary:")
    print(f"  Iterations executed: {session_data.get('current_iteration', 0)}")
    print(f"  Session file: {session_path}")


if __name__ == "__main__":
    main()
