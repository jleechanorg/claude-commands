#!/usr/bin/env python3
"""Long-Running Harness — CLI orchestrator for multi-agent coding tasks.

Usage:
  harness.py research   --task "..." --repo /path/to/repo [--project-id ID]
  harness.py plan       --task "..." --repo /path/to/repo
  harness.py implement --repo /path/to/repo --todo-file .hermes/plans/todo.md
  harness.py evaluate   --repo /path/to/repo --plan-file .hermes/plans/plan.md
  harness.py run        --task "..." --repo /path/to/repo --project-id ID

Phases:
  research  — Haiku agent deep-reads codebase → research.md
  plan      — Sonnet agent writes plan.md + todo.md
  implement — Sonnet+Opus agent implements one todo at a time
  evaluate  — Opus agent grades output against plan spec
  run       — Full pipeline: research → plan → implement → evaluate
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def run_cmd(cmd: str, cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=check
    )


def ensure_plans_dir(repo: str) -> Path:
    """Create .hermes/plans/ in the repo if it doesn't exist."""
    plans = Path(repo) / ".hermes" / "plans"
    plans.mkdir(parents=True, exist_ok=True)
    return plans


def load_template(name: str) -> str:
    """Load a prompt template from the templates directory."""
    path = TEMPLATES_DIR / name
    if not path.exists():
        print(f"ERROR: template {name} not found at {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text()


def write_artifact(plans_dir: Path, filename: str, content: str) -> Path:
    """Write an artifact to the plans directory."""
    path = plans_dir / filename
    path.write_text(content)
    return path


def spawn_ao_agent(
    task_prompt: str,
    project_id: str,
    model: str = "sonnet",
    bead_id: str | None = None,
) -> str:
    """Spawn an AO agent and return the session name."""
    # Create task file
    task_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    task_file.write(task_prompt)
    task_file.close()

    try:
        # Spawn session
        spawn_cmd = f"ao spawn {bead_id or 'harness-task'} -p {project_id}"
        result = run_cmd(spawn_cmd)
        if result.returncode != 0:
            print(f"ERROR: ao spawn failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Extract session name from output
        session_name = result.stdout.strip().split("\n")[-1].strip()
        if not session_name:
            print("ERROR: could not determine session name from ao spawn output", file=sys.stderr)
            sys.exit(1)

        # Send task
        send_cmd = f"ao send {session_name} --file {task_file.name}"
        run_cmd(send_cmd)

        return session_name
    finally:
        os.unlink(task_file.name)


def phase_research(task: str, repo: str, project_id: str | None = None) -> Path:
    """Phase 1: Research agent deep-reads codebase."""
    plans_dir = ensure_plans_dir(repo)
    template = load_template("researcher-prompt.md")

    prompt = f"""{template}

## Task
{task}

## Repository
{repo}

## Instructions
Read the relevant parts of this codebase deeply. Write your findings to `.hermes/plans/research.md`.
"""

    print(f"[harness] Phase 1: RESEARCH — deep-reading codebase")

    # For research, we use a simpler approach — write the prompt and let the
    # human spawn the agent (or use ao if project_id provided)
    task_file = write_artifact(plans_dir, "research-task.md", prompt)
    print(f"[harness] Research prompt written to: {task_file}")
    print(f"[harness] Next: review the prompt, then run:")
    print(f"  ao spawn harness-research -p {project_id or '<project-id>'}")
    print(f"  ao send <session> --file {task_file}")
    print(f"[harness] After agent completes, review .hermes/plans/research.md")
    print(f"[harness] Add inline notes (prefixed with '> NOTE:') to research.md, then re-run this cycle if needed.")

    return plans_dir / "research.md"


def phase_plan(task: str, repo: str) -> Path:
    """Phase 2: Planner agent writes plan.md + todo.md."""
    plans_dir = ensure_plans_dir(repo)
    research_path = plans_dir / "research.md"

    if not research_path.exists():
        print("ERROR: research.md not found. Run 'research' phase first.", file=sys.stderr)
        sys.exit(1)

    research = research_path.read_text()
    template = load_template("planner-prompt.md")

    prompt = f"""{template}

## Task
{task}

## Repository
{repo}

## Research Findings
{research}

## Instructions
Write a detailed implementation plan to `.hermes/plans/plan.md` and a granular todo list to `.hermes/plans/todo.md`.
"""

    print(f"[harness] Phase 2: PLAN — writing implementation plan")

    task_file = write_artifact(plans_dir, "plan-task.md", prompt)
    print(f"[harness] Plan prompt written to: {task_file}")
    print(f"[harness] After agent completes, review .hermes/plans/plan.md")
    print(f"[harness] Add inline notes to plan.md, then re-run this cycle until satisfied.")
    print(f"[harness] When satisfied, proceed to 'implement' phase.")

    return plans_dir / "plan.md"


def phase_implement(repo: str, todo_file: str, project_id: str | None = None) -> None:
    """Phase 3: Executor agent implements one todo at a time."""
    plans_dir = ensure_plans_dir(repo)
    todo_path = Path(repo) / todo_file

    if not todo_path.exists():
        # Try relative to plans dir
        alt = plans_dir / "todo.md"
        if alt.exists():
            todo_path = alt
        else:
            print(f"ERROR: todo file not found: {todo_file}", file=sys.stderr)
            sys.exit(1)

    plan_path = plans_dir / "plan.md"
    research_path = plans_dir / "research.md"
    handoff_path = plans_dir / "handoff.md"

    template = load_template("executor-prompt.md")

    # Read existing artifacts
    plan_content = plan_path.read_text() if plan_path.exists() else "No plan found."
    research_content = research_path.read_text() if research_path.exists() else "No research found."
    handoff_content = handoff_path.read_text() if handoff_path.exists() else ""

    # Parse todos — find first unchecked item
    todos = []
    for line in todo_path.read_text().splitlines():
        if line.strip().startswith("- [ ]"):
            todos.append(line)
        elif line.strip().startswith("- [x]"):
            continue  # already done

    if not todos:
        print("[harness] All todos complete!")
        return

    current_todo = todos[0]
    print(f"[harness] Phase 3: IMPLEMENT — working on: {current_todo.strip()}")

    prompt = f"""{template}

## Current Todo
{current_todo}

## Plan
{plan_content}

## Research
{research_content}
"""

    if handoff_content:
        prompt += f"""
## Previous Session Handoff
{handoff_content}
"""

    prompt += """
## Instructions
Implement the current todo item. Follow the plan exactly. Write handoff.md when done or if you hit context limits.
"""

    task_file = write_artifact(plans_dir, "implement-task.md", prompt)
    print(f"[harness] Implementation prompt written to: {task_file}")
    print(f"[harness] Spawn executor with:")
    print(f"  ao spawn harness-exec -p {project_id or '<project-id>'}")
    print(f"  ao send <session> --file {task_file}")
    print(f"[harness] Use ao-babysit to monitor for context resets.")


def phase_evaluate(repo: str, plan_file: str) -> None:
    """Phase 4: Evaluator agent grades output against plan spec."""
    plans_dir = ensure_plans_dir(repo)
    plan_path = Path(repo) / plan_file

    if not plan_path.exists():
        alt = plans_dir / "plan.md"
        if alt.exists():
            plan_path = alt
        else:
            print(f"ERROR: plan file not found: {plan_file}", file=sys.stderr)
            sys.exit(1)

    plan_content = plan_path.read_text()
    template = load_template("evaluator-prompt.md")

    # Get git diff: working-tree changes first, then committed diff as fallback
    result = run_cmd("git diff", cwd=repo, check=False)
    if not result.stdout.strip():
        result = run_cmd("git diff HEAD~1", cwd=repo, check=False)
    diff = result.stdout if result.returncode == 0 and result.stdout.strip() else "No changes detected."

    prompt = f"""{template}

## Plan Specification
{plan_content}

## Code Changes (git diff)
```
{diff}
```

## Instructions
Evaluate the code changes against the plan specification. Write your evaluation to `.hermes/plans/eval_report.md`.
"""

    print(f"[harness] Phase 4: EVALUATE — grading output against plan")

    task_file = write_artifact(plans_dir, "eval-task.md", prompt)
    print(f"[harness] Evaluation prompt written to: {task_file}")
    print(f"[harness] Spawn evaluator with Opus:")
    print(f"  ao spawn harness-eval -p <project-id> --model opus")
    print(f"  ao send <session> --file {task_file}")


def phase_run(task: str, repo: str, project_id: str) -> None:
    """Full pipeline: research → plan → implement → evaluate."""
    print(f"[harness] ═══════════════════════════════════════")
    print(f"[harness] LONG-RUNNING HARNESS — Full Pipeline")
    print(f"[harness] Task: {task}")
    print(f"[harness] Repo: {repo}")
    print(f"[harness] Project: {project_id}")
    print(f"[harness] ═══════════════════════════════════════")
    print()

    # Phase 1: Research
    print(f"[harness] ─── Phase 1: RESEARCH ───")
    phase_research(task, repo, project_id)
    print()

    # Remaining phases require human approval (annotation cycle)
    print(f"[harness] ─── Awaiting Human Review ───")
    print(f"[harness] Review .hermes/plans/research.md")
    print(f"[harness] Add notes, then run:")
    print(f"  harness.py plan --task '{task}' --repo {repo}")
    print()
    print(f"[harness] After plan is approved:")
    print(f"  harness.py implement --repo {repo} --todo-file .hermes/plans/todo.md")
    print(f"  harness.py evaluate --repo {repo} --plan-file .hermes/plans/plan.md")


def main():
    parser = argparse.ArgumentParser(description="Long-Running Harness")
    subparsers = parser.add_subparsers(dest="phase", required=True)

    # research
    p_research = subparsers.add_parser("research", help="Research phase")
    p_research.add_argument("--task", required=True, help="Task description")
    p_research.add_argument("--repo", required=True, help="Path to repo")
    p_research.add_argument("--project-id", help="AO project ID")

    # plan
    p_plan = subparsers.add_parser("plan", help="Planning phase")
    p_plan.add_argument("--task", required=True, help="Task description")
    p_plan.add_argument("--repo", required=True, help="Path to repo")

    # implement
    p_impl = subparsers.add_parser("implement", help="Implementation phase")
    p_impl.add_argument("--repo", required=True, help="Path to repo")
    p_impl.add_argument("--todo-file", default=".hermes/plans/todo.md")
    p_impl.add_argument("--project-id", help="AO project ID")

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluation phase")
    p_eval.add_argument("--repo", required=True, help="Path to repo")
    p_eval.add_argument("--plan-file", default=".hermes/plans/plan.md")

    # run (full pipeline)
    p_run = subparsers.add_parser("run", help="Full pipeline")
    p_run.add_argument("--task", required=True, help="Task description")
    p_run.add_argument("--repo", required=True, help="Path to repo")
    p_run.add_argument("--project-id", required=True, help="AO project ID")

    args = parser.parse_args()

    if args.phase == "research":
        phase_research(args.task, args.repo, args.project_id)
    elif args.phase == "plan":
        phase_plan(args.task, args.repo)
    elif args.phase == "implement":
        phase_implement(args.repo, args.todo_file, getattr(args, "project_id", None))
    elif args.phase == "evaluate":
        phase_evaluate(args.repo, args.plan_file)
    elif args.phase == "run":
        phase_run(args.task, args.repo, args.project_id)


if __name__ == "__main__":
    main()
