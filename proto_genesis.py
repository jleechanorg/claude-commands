#!/usr/bin/env python3
"""
Proto Genesis - Interactive Goal Refinement System
Executes goal refinement using claude -p based on pre-defined goals from /goal command
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path


class SubagentPool:
    """Genesis-inspired subagent pool manager (configurable concurrent limit)"""
    def __init__(self, max_subagents=5):
        self.semaphore = threading.Semaphore(max_subagents)
        self.active_count = 0
        self.lock = threading.Lock()

    def execute_with_limit(self, prompt, timeout=300, use_codex=False):
        """Execute claude -p with subagent limit enforcement"""
        with self.semaphore:
            with self.lock:
                self.active_count += 1
                print(f"  🤖 Claude -p call {self.active_count} active")

            try:
                return execute_claude_command(prompt, timeout, use_codex)
            finally:
                with self.lock:
                    self.active_count -= 1

# Global subagent pool (Genesis pattern: configurable concurrent limit, default 5)
SUBAGENT_POOL = SubagentPool(max_subagents=5)  # Default 5, can be overridden

def execute_claude_command(prompt, timeout=30, use_codex=False, use_cerebras=False):
    """Execute claude, codex, or cerebras command with prompt and return output."""
    try:
        if use_codex:
            command = ["codex", "exec", "--yolo"]
            tool_name = "codex"
            input_method = "stdin"
        elif use_cerebras:
            # Use cerebras_direct.sh for fast generation
            script_path = os.path.join(os.path.dirname(__file__), ".claude", "commands", "cerebras", "cerebras_direct.sh")
            if os.path.exists(script_path):
                command = ["bash", script_path, prompt]
                tool_name = "cerebras"
                input_method = "arg"
            else:
                # Fallback to claude if cerebras script not found
                command = [
                    "claude",
                    "-p",
                    "--model",
                    "sonnet",
                    "--dangerously-skip-permissions",
                ]
                tool_name = "claude"
                input_method = "stdin"
        else:
            command = [
                "claude",
                "-p",
                "--model",
                "sonnet",
                "--dangerously-skip-permissions",
            ]
            tool_name = "claude"
            input_method = "stdin"

        result = subprocess.run(
            command,
            input=prompt if input_method == "stdin" else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"{tool_name.title()} error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print(f"{tool_name.title()} command timed out")
        return None
    except FileNotFoundError:
        print(
            f"Error: '{tool_name}' command not found. Please install {tool_name.title()} CLI."
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running {tool_name}: {e}")
        return None

# Remove duplicate - using original execute_claude_command

def set_subagent_pool_size(size):
    """Update global subagent pool size"""
    global SUBAGENT_POOL
    SUBAGENT_POOL = SubagentPool(max_subagents=size)


def load_goal_from_directory(goal_dir):
    """Load goal specification from goal directory structure."""
    goal_path = Path(goal_dir)

    if not goal_path.exists():
        print(f"Error: Goal directory not found: {goal_dir}")
        return None, None

    # Load goal definition
    goal_def_file = goal_path / "00-goal-definition.md"
    criteria_file = goal_path / "01-success-criteria.md"

    refined_goal = ""
    exit_criteria = ""

    try:
        if goal_def_file.exists():
            with open(goal_def_file) as f:
                content = f.read()
                # Extract refined goal from markdown
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if (
                        "refined goal" in line.lower()
                        or "specification" in line.lower()
                    ):
                        # Take next few lines as the goal
                        goal_lines = []
                        for j in range(i + 1, min(i + 10, len(lines))):
                            if lines[j].strip() and not lines[j].startswith("#"):
                                goal_lines.append(lines[j].strip())
                        refined_goal = " ".join(goal_lines)
                        break

                if not refined_goal:
                    # Fallback: take first meaningful paragraph
                    for line in lines:
                        if len(line.strip()) > 20 and not line.startswith("#"):
                            refined_goal = line.strip()
                            break

        if criteria_file.exists():
            with open(criteria_file) as f:
                exit_criteria = f.read()

        return refined_goal, exit_criteria

    except Exception as e:
        print(f"Error loading goal files: {e}")
        return None, None


def refine_goal_interactive(original_goal, use_codex=False):
    """Interactive goal refinement (only used with --refine flag)."""
    prompt = f"""Please refine this goal into a clear, specific technical specification for a coder to implement:

Original Goal: "{original_goal}"

Please provide:
1. Refined Goal: A specific, technical description of what needs to be built
2. Exit Criteria: Clear, measurable conditions that define when this goal is complete (at least 3 criteria)

Format your response as:
REFINED GOAL: [specific technical description]

EXIT CRITERIA:
- [criterion 1]
- [criterion 2]
- [criterion 3]
"""

    return execute_claude_command(prompt, use_codex=use_codex, use_cerebras=True)


def parse_refinement(response):
    """Parse the goal refinement response."""
    if not response:
        return None, None

    refined_goal = None
    exit_criteria = None

    # Use regex for more robust parsing
    goal_match = re.search(
        r"^\s*REFINED\s+GOAL\s*:\s*(.+)", response, re.IGNORECASE | re.MULTILINE
    )
    if goal_match:
        refined_goal = goal_match.group(1).strip()

    # Find exit criteria section
    criteria_match = re.search(
        r"^\s*EXIT\s+CRITERIA\s*:\s*(.+)",
        response,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if criteria_match:
        # Get everything from the match start to end of response
        start_pos = criteria_match.start()
        exit_criteria = response[start_pos:].strip()

    return refined_goal, exit_criteria


def summarize_for_next_stage(stage_name, stage_output, goal, iteration_num, use_codex=False):
    """Genesis pattern: Detailed summary with 2000 token max (enhanced context)"""
    prompt = f"""GENESIS CONTEXT ENHANCEMENT - 2000 TOKEN MAX SUMMARY

STAGE: {stage_name} | ITERATION: {iteration_num}
GOAL: {goal}

OUTPUT TO SUMMARIZE:
{stage_output}

CREATE MINIMAL SUMMARY (200 tokens max):
KEY DECISIONS: [critical decisions only]
ESSENTIAL FINDINGS: [key discoveries only]
NEXT FOCUS: [single priority item]
CONTEXT: [minimal essential only]

GENESIS RULE: Provide detailed context within 2000 tokens. Include essential details and context.
"""

    return execute_claude_command(prompt, timeout=60, use_codex=use_codex)


def update_plan_document(goal_dir, learnings, iteration_num, use_codex=False):
    """Genesis pattern: Maintain living @fix_plan.md with priority scoring"""
    from pathlib import Path

    plan_file = Path(goal_dir) / "fix_plan.md"
    existing_plan = ""

    if plan_file.exists():
        try:
            with open(plan_file) as f:
                existing_plan = f.read()
        except Exception:
            existing_plan = ""

    prompt = f"""GENESIS PLAN MAINTENANCE - PRIORITY SCORING

ITERATION: {iteration_num}
CURRENT PLAN:
{existing_plan}

NEW LEARNINGS:
{learnings}

GENESIS REQUIREMENTS:
1. Remove completed items (✅ status)
2. Add newly discovered tasks
3. PRIORITY SCORE each item (1-10, 10=critical)
4. Reorder by priority score (highest first)
5. Mark dependencies and blockers
6. Keep actionable (no vague items)

FORMAT:
## Priority 10 (Critical)
- [ ] Specific task description

## Priority 9 (High)
- [ ] Another task

Return updated fix_plan.md:
"""

    updated_plan = execute_claude_command(prompt, timeout=60, use_codex=use_codex)

    if updated_plan and plan_file.parent.exists():
        try:
            with open(plan_file, "w") as f:
                f.write(updated_plan)
        except Exception as e:
            print(f"Warning: Could not update fix_plan.md: {e}")

    return updated_plan


def validate_single_task_focus(strategy_text):
    """Genesis enforcement: Validate strategy focuses on ONE task only"""
    multi_task_indicators = [
        "and also", "additionally", "next we", "then do", "while doing",
        "simultaneously", "in parallel", "at the same time", "multiple"
    ]

    for indicator in multi_task_indicators:
        if indicator.lower() in strategy_text.lower():
            return False, f"REJECTED: Multi-task detected ({indicator}). Genesis requires ONE task per loop."

    # Check for numbered lists with multiple items
    lines = strategy_text.split('\n')
    task_lines = [line for line in lines if re.match(r'^\s*[0-9]+\.|^\s*[-*]', line)]
    if len(task_lines) > 1:
        return False, "REJECTED: Multiple numbered/bulleted tasks detected. Genesis requires ONE task per loop."

    return True, "APPROVED: Single task focus validated"

def generate_execution_strategy(
    refined_goal, iteration_num, previous_summary="", plan_context="", use_codex=False
):
    """Genesis pattern: Generate single-focus strategy with validation"""
    prompt = f"""GENESIS PRIMARY SCHEDULER - SINGLE TASK ENFORCEMENT

GENESIS PRINCIPLES:
- ONE ITEM PER LOOP: Choose exactly ONE specific task (validation enforced)
- DIRECT EXECUTION: Use claude -p directly for all work
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens
- NO PLACEHOLDERS: Full implementations only

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}
PREVIOUS SUMMARY: {previous_summary}

SCHEDULER REQUIREMENTS:
1. SELECT ONE SPECIFIC ITEM from plan context (if available)
2. REJECT multi-tasking (will be validated)
3. SPECIFY how to use claude -p subagents (max 5)
4. DEMAND full implementation (no TODOs)

SUBAGENT DELEGATION PATTERN:
- Code generation → claude -p subagent
- Testing/validation → claude -p subagent
- File operations → claude -p subagent
- Keep primary context as scheduler only

EXECUTION STRATEGY FORMAT:
SINGLE FOCUS: [ONE specific task only]
EXECUTION PLAN: [how to use claude -p directly]
SUCCESS CRITERIA: [clear completion criteria]
NO PLACEHOLDERS: [enforcement approach]

GENESIS VALIDATION: Strategy will be rejected if multiple tasks detected.
"""

    strategy = execute_claude_command(prompt, use_codex=use_codex)

    if strategy:
        is_valid, validation_msg = validate_single_task_focus(strategy)
        print(f"  🎯 Task Focus Validation: {validation_msg}")

        if not is_valid:
            print("  🔄 Regenerating strategy with stricter single-task enforcement...")
            # Retry with stricter prompt
            strict_prompt = f"""{prompt}

STRICT ENFORCEMENT: Previous strategy rejected for multi-tasking.
MUST focus on EXACTLY ONE TASK. No exceptions.
"""
            strategy = execute_claude_command(strict_prompt, use_codex=use_codex)

    return strategy


def validate_task_necessity(task_description, goal_dir):
    """Genesis pattern: Search-first approach - verify gap exists before building"""
    search_prompt = f"""GENESIS SEARCH-FIRST VALIDATION

TASK TO VALIDATE: {task_description}
GOAL DIRECTORY: {goal_dir}

SEARCH REQUIREMENTS:
1. Check for existing implementations
2. Look for TODO/placeholder patterns
3. Verify gap actually exists
4. Check for similar functionality

SEARCH PATTERN:
- Use find/grep to search codebase
- Check relevant files and directories
- Look for partial implementations

RETURN:
GAP EXISTS: [true/false]
EVIDENCE: [what was found/not found]
RECOMMENDATION: [proceed/skip/modify task]
"""

    return execute_claude_command(search_prompt, timeout=180)

def validate_implementation_quality(work_output):
    """Genesis pattern: Reject TODO/placeholder implementations"""
    placeholder_patterns = [
        r'TODO', r'FIXME', r'PLACEHOLDER', r'XXX', r'HACK',
        r'NotImplemented', r'pass\s*#', r'raise NotImplementedError',
        r'// TODO', r'// FIXME', r'/* TODO', r'<!-- TODO',
        r'def\s+\w+\([^)]*\):\s*pass\s*$',  # Empty function with just pass
        r'function\s+\w+\([^)]*\)\s*{\s*}',  # Empty JS function
    ]

    for pattern in placeholder_patterns:
        if re.search(pattern, work_output, re.IGNORECASE | re.MULTILINE):
            return False, f"REJECTED: Placeholder detected ({pattern}). Genesis demands full implementations."

    return True, "APPROVED: No placeholders detected"

def make_progress(
    refined_goal,
    iteration_num,
    execution_strategy,
    plan_context="",
    use_codex=False,
):
    """Genesis pattern: Execute with search-first validation and subagent delegation"""

    # Genesis principle: Search first before assuming implementation needed
    print("  🔍 Genesis Search-First Validation...")
    task_validation = validate_task_necessity(execution_strategy, plan_context)

    prompt = f"""GENESIS EXECUTION - SEARCH-FIRST WITH SUBAGENTS

CORE GENESIS PRINCIPLES:
- ONE ITEM PER LOOP: Execute exactly one task (enforced)
- SUBAGENT DELEGATION: Use claude -p for expensive work (max 5)
- SEARCH FIRST: Validate before building (see validation below)
- NO PLACEHOLDERS: Full implementations only
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}

SEARCH VALIDATION RESULT:
{task_validation}

EXECUTION STRATEGY:
{execution_strategy}

GENESIS EXECUTION REQUIREMENTS:
1. Honor search validation result above
2. Use claude -p subagents for expensive work:
   - Code generation → claude -p subagent
   - Testing/validation → claude -p subagent
   - File operations → claude -p subagent
3. Primary context = scheduler only
4. NO TODO/placeholder comments allowed
5. Full implementation or nothing

STRUCTURED OUTPUT:
SEARCH VALIDATION: [honored/ignored and why]
WORK COMPLETED: [specific accomplishments]
CLAUDE CALLS: [what was executed with claude -p]
FULL IMPLEMENTATION: [confirm no placeholders]
DISCOVERIES: [codebase learnings]
COMPLETION STATUS: [percentage for this iteration's focus]
NEXT PRIORITY: [single next focus item]

Execute using Genesis principles now.
"""

    result = execute_claude_command(prompt, timeout=600, use_codex=use_codex)

    # Validate result quality (Genesis no-placeholders policy)
    if result:
        is_quality, quality_msg = validate_implementation_quality(result)
        print(f"  🛡️ Implementation Quality: {quality_msg}")

        if not is_quality:
            print("  🔄 Requesting full implementation (Genesis policy)...")
            retry_prompt = f"""{prompt}

QUALITY REJECTION: Previous output contained placeholders.
GENESIS POLICY: Must provide full implementation or document why impossible.
"""
            result = execute_claude_command(retry_prompt, timeout=600, use_codex=use_codex)

    return result


def check_consensus(refined_goal, exit_criteria, iteration_summary, plan_context="", use_codex=False):
    """Genesis-inspired consensus validation using subagent for focused assessment."""
    prompt = f"""You are a validation subagent in a Genesis-inspired system.

GENESIS VALIDATION PRINCIPLES:
- FOCUSED ASSESSMENT: Evaluate only this iteration's progress
- NO ASSUMPTION: Search/verify before concluding anything is missing
- EVIDENCE-BASED: Base assessment on concrete evidence
- CONTEXT ENHANCEMENT: Provide detailed evaluation within limits

GOAL: {refined_goal}

EXIT CRITERIA:
{exit_criteria}

THIS ITERATION'S WORK:
{iteration_summary}

CURRENT PLAN CONTEXT:
{plan_context}

VALIDATION REQUIREMENTS:
1. Use /goal --validate command to check against criteria
2. Assess ONLY this iteration's contribution to the overall goal
3. Identify concrete evidence of progress made
4. Check if any exit criteria can now be marked as completed
5. Determine the single most important next step

CONSENSUS ASSESSMENT:
ITERATION COMPLETION: [X% for this iteration's specific task]
OVERALL PROGRESS: [X% toward complete goal]
CRITERIA VALIDATED: [which exit criteria are now satisfied]
EVIDENCE FOUND: [concrete proof of progress]
CRITICAL GAPS: [single most important remaining gap]
NEXT FOCUS: [one specific item for next iteration]

Use /goal --validate and provide evidence-based assessment.
"""

    return execute_claude_command(prompt, timeout=300, use_codex=use_codex)


def update_genesis_instructions(goal_dir, learnings, use_codex=False):
    """Genesis pattern: Update GENESIS.md with self-improvement learnings"""
    from pathlib import Path

    genesis_file = Path(goal_dir) / "GENESIS.md"
    existing_instructions = ""

    if genesis_file.exists():
        try:
            with open(genesis_file) as f:
                existing_instructions = f.read()
        except Exception:
            existing_instructions = ""

    prompt = f"""GENESIS SELF-IMPROVEMENT - UPDATE GENESIS.md

CURRENT GENESIS INSTRUCTIONS:
{existing_instructions}

NEW LEARNINGS FROM ITERATION:
{learnings}

UPDATE GENESIS.md WITH:
1. Successful claude -p command patterns that worked
2. Failure modes to avoid (what caused loops/blocks)
3. Better approaches discovered during execution
4. Specific subagent delegation patterns that were effective
5. Context optimization techniques learned
6. Genesis principle applications that succeeded/failed

FORMAT:
## Successful Patterns
- [specific commands/approaches that worked]

## Avoid These Patterns
- [what causes failures/loops]

## Genesis Optimizations
- [context conservation techniques]
- [subagent delegation improvements]

KEEP BRIEF and actionable. Focus on improving future iterations.

Return updated GENESIS.md content:
"""

    updated_instructions = execute_claude_command(prompt, timeout=60, use_codex=use_codex)

    if updated_instructions and genesis_file.parent.exists():
        try:
            with open(genesis_file, "w") as f:
                f.write(updated_instructions)
        except Exception as e:
            print(f"Warning: Could not update GENESIS.md: {e}")

    return updated_instructions

def detect_loop_back_opportunities(consensus_response, goal_dir):
    """Genesis pattern: Create loop-back when failures detected"""
    loop_back_triggers = [
        "build fail", "test fail", "error", "exception", "timeout",
        "not found", "missing", "incomplete", "broken", "stuck"
    ]

    needs_loop_back = any(trigger in consensus_response.lower() for trigger in loop_back_triggers)

    if needs_loop_back:
        loop_back_prompt = f"""GENESIS LOOP-BACK RECOVERY

FAILURE DETECTED IN: {consensus_response}
GOAL DIRECTORY: {goal_dir}

LOOP-BACK OPPORTUNITIES:
1. Add additional logging for debugging
2. Compile and examine build output
3. Run tests and analyze failure patterns
4. Check dependencies and environment
5. Examine error logs and stack traces

CREATE RECOVERY STRATEGY:
- What specific logging to add
- What compilation/build commands to run
- What tests to examine
- How to get more diagnostic information

Return concrete loop-back actions to take:
"""

        return execute_claude_command(loop_back_prompt, timeout=180)

    return None

def integrate_git_workflow(goal_dir, iteration_summary, use_codex=False):
    """Genesis pattern: Auto-commit when tests pass"""
    git_prompt = f"""GENESIS GIT WORKFLOW INTEGRATION

GOAL DIRECTORY: {goal_dir}
ITERATION SUMMARY: {iteration_summary}

GIT WORKFLOW REQUIREMENTS:
1. Check if tests are passing (look for test results in summary)
2. If tests pass, prepare for git operations:
   - git add -A
   - git commit with descriptive message
   - git push origin HEAD
   - create/increment git tag (0.0.1, 0.0.2, etc.)

DETECT TEST STATUS:
- Look for "tests pass", "all tests passed", "✅", "success" indicators
- Look for "test fail", "❌", "error", "failure" indicators

If tests are passing, return git commands to execute.
If tests failing or unclear, return "SKIP: Tests not confirmed passing"

Return git workflow actions:
"""

    return execute_claude_command(git_prompt, timeout=120, use_codex=use_codex)


def update_progress_file(goal_dir, iteration_data):
    """Update the progress tracking file in goal directory."""
    goal_path = Path(goal_dir)
    progress_file = goal_path / "02-progress-tracking.md"

    try:
        # Append iteration data to progress file
        with open(progress_file, "a") as f:
            f.write(f"\n## Iteration {iteration_data['iteration']}\n")
            f.write(
                f"**Work Completed**: {iteration_data.get('work_completed', 'N/A')}\n"
            )
            f.write(f"**Challenges**: {iteration_data.get('challenges', 'N/A')}\n")
            f.write(f"**Progress**: {iteration_data.get('progress', 'N/A')}\n")
            f.write(f"**Next Steps**: {iteration_data.get('next_steps', 'N/A')}\n")
            f.write(f"**Consensus**: {iteration_data.get('consensus', 'N/A')}\n\n")
    except Exception as e:
        print(f"Warning: Could not update progress file: {e}")


def generate_goal_files_fast(goal_description, goal_dir):
    """Use cerebras_direct.sh to generate all goal files at once (fast generation)"""
    prompt = f"""Generate complete goal directory structure for: {goal_description}

Create these files for proto_genesis workflow:

1. 00-goal-definition.md - Goal definition with refined goal analysis
2. 01-success-criteria.md - Clear success criteria and exit conditions
3. 02-implementation-notes.md - Technical approach and considerations
4. 03-testing-strategy.md - How to validate the implementation

Each file should be complete and detailed. Format as:

=== 00-goal-definition.md ===
[Complete markdown content]

=== 01-success-criteria.md ===
[Complete markdown content]

=== 02-implementation-notes.md ===
[Complete markdown content]

=== 03-testing-strategy.md ===
[Complete markdown content]

Generate all files now:"""

    try:
        # Use cerebras_direct.sh for fast generation
        output = execute_claude_command(prompt, timeout=60, use_cerebras=True)

        if output:
            # Parse and write files
            os.makedirs(goal_dir, exist_ok=True)

            # Split by file markers and write each file
            sections = output.split("=== ")
            for section in sections[1:]:  # Skip first empty section
                if " ===" in section:
                    filename, content = section.split(" ===", 1)
                    filepath = os.path.join(goal_dir, filename.strip())
                    with open(filepath, "w") as f:
                        f.write(content.strip())
                    print(f"✅ Generated: {filename.strip()}")

            return True
        else:
            print(f"❌ Fast generation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Fast generation error: {e}")
        return False

def main():
    """Main goal refinement execution with fast generation as default."""
    # Parse arguments
    if len(sys.argv) < 2:
        print(
            'Usage: python proto_genesis.py "<goal_description>" [goal_directory] [max_iterations] [--codex] [--pool-size N]'
        )
        print(
            '   or: python proto_genesis.py --execute <goal_directory> [max_iterations] [--codex] [--pool-size N]'
        )
        print(
            '   or: python proto_genesis.py --refine "<goal>" [max_iterations] [--codex] [--pool-size N]'
        )
        print("")
        print("Modes:")
        print("  DEFAULT       Fast generation + execution (recommended)")
        print("  --execute     Execute existing goal directory")
        print("  --refine      Interactive goal refinement")
        print("")
        print("Options:")
        print("  --codex       Use 'codex exec --yolo' instead of 'claude -p'")
        print("  --pool-size N Set subagent pool size (default: 5)")
        print("")
        print("Examples:")
        print('  python proto_genesis.py "code fibonacci function"  # Fast gen + execute')
        print('  python proto_genesis.py "build REST API" goals/api/ 5  # Custom dir')
        print("  python proto_genesis.py --execute goals/existing/ 10  # Execute existing")
        print('  python proto_genesis.py --refine "build a REST API" 5 --codex')
        sys.exit(1)

    # Check for flags
    use_codex = "--codex" in sys.argv
    if use_codex:
        sys.argv.remove("--codex")

    # Check for pool size
    pool_size = 5  # default
    if "--pool-size" in sys.argv:
        pool_idx = sys.argv.index("--pool-size")
        if pool_idx + 1 < len(sys.argv):
            try:
                pool_size = int(sys.argv[pool_idx + 1])
                sys.argv.remove("--pool-size")
                sys.argv.remove(str(pool_size))
                print(f"🤖 Setting subagent pool size to: {pool_size}")
                set_subagent_pool_size(pool_size)
            except ValueError:
                print("Error: --pool-size requires a number")
                sys.exit(1)
        else:
            print("Error: --pool-size requires a number")
            sys.exit(1)

    # Check for execution mode flags
    execute_mode = False
    if len(sys.argv) >= 2 and sys.argv[1] == "--execute":
        execute_mode = True
        sys.argv.remove("--execute")

    # Default mode: Fast generation + execution
    if not execute_mode and len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        goal_description = sys.argv[1]

        # Determine goal directory and max iterations
        if len(sys.argv) >= 3 and not sys.argv[2].isdigit() and not sys.argv[2].startswith("--"):
            goal_dir = sys.argv[2]
            max_iterations = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 5
        else:
            # Auto-generate directory name from goal
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
            goal_slug = goal_description.lower().replace(" ", "-").replace("'", "").replace('"', "")
            goal_dir = f"goals/{timestamp}-{goal_slug[:30]}/"
            max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5

        print("🚀 GENESIS FAST MODE: GENERATE + EXECUTE")
        print("=" * 50)
        print(f"Goal: {goal_description}")
        print(f"Directory: {goal_dir}")
        print(f"Max Iterations: {max_iterations}")
        print()

        # Step 1: Fast generation
        print("📋 STEP 1: Fast Goal Generation with /cereb")
        success = generate_goal_files_fast(goal_description, goal_dir)
        if not success:
            print("\n❌ Goal generation failed")
            return

        print("\n✅ Goal files generated successfully!")
        print()

        # Step 2: Execute immediately
        print("⚡ STEP 2: Executing Genesis workflow")
        print("-" * 30)

        # Continue to execution with the generated goal_dir
        sys.argv = [sys.argv[0], goal_dir, str(max_iterations)] + [arg for arg in sys.argv[2:] if not arg.isdigit() and not arg.startswith("--")]
        # Fall through to normal execution

    # Handle --refine mode (interactive goal refinement)
    if sys.argv[1] == "--refine":
        if len(sys.argv) < 3:
            print("Error: --refine requires a goal description")
            sys.exit(1)

        original_goal = sys.argv[2]
        max_iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 10

        print("=" * 60)
        print("PROTO GENESIS - Interactive Goal Refinement (--refine mode)")
        print("=" * 60)
        print(f"Original Goal: {original_goal}")
        print()

        # Interactive goal refinement
        print("STEP 1: Goal Refinement")
        print("-" * 30)

        refined_goal = None
        exit_criteria = None

        while True:
            print("Refining goal...")
            response = refine_goal_interactive(original_goal, use_codex)

            if response:
                refined_goal, exit_criteria = parse_refinement(response)

                print("\nProposed Refinement:")
                print(f"Refined Goal: {refined_goal}")
                print(f"Exit Criteria:\n{exit_criteria}")
                print()

                approval = (
                    input("Do you approve this refinement? (y/n): ").lower().strip()
                )
                if approval in ["y", "yes"]:
                    break
                elif approval in ["n", "no"]:
                    print("Let's refine again...\n")
                    continue
                else:
                    print("Please enter 'y' or 'n'")
            else:
                print("Error refining goal. Please try again.")
                return

        session_file = "proto_genesis_session.json"

    else:
        # Standard mode: use goal directory
        goal_dir = sys.argv[1]
        max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 10

        print("=" * 60)
        print("PROTO GENESIS - Goal Refinement Execution")
        print("=" * 60)
        print(f"Goal Directory: {goal_dir}")
        print(f"Max Iterations: {max_iterations}")
        print()

        # Load goal from directory
        refined_goal, exit_criteria = load_goal_from_directory(goal_dir)

        if not refined_goal:
            print("Error: Could not load goal from directory")
            return

        print("Loaded Goal:")
        print(f"Refined Goal: {refined_goal}")
        print(
            f"Exit Criteria: {exit_criteria[:200]}..."
            if len(exit_criteria) > 200
            else exit_criteria
        )
        print()

        session_file = os.path.join(goal_dir, "proto_genesis_session.json")

    # Genesis-inspired iteration loop with stage summarization
    print("STARTING GENESIS-INSPIRED ITERATIONS")
    print("=" * 30)
    print(f"Genesis Principles: One item per loop | Direct claude -p execution | Enhanced context: 2000 tokens | No placeholders")
    print()

    # Genesis-style context variables (minimal)
    previous_summary = ""
    plan_context = ""

    for i in range(max_iterations):
        print(f"🎯 GENESIS ITERATION {i + 1}/{max_iterations}")
        print("-" * 40)

        # Load current plan context if available
        if "goal_dir" in locals():
            plan_file = Path(goal_dir) / "fix_plan.md"
            if plan_file.exists():
                try:
                    with open(plan_file) as f:
                        plan_context = f.read()
                except Exception:
                    plan_context = ""

        # STAGE 1: Planning with Genesis principles
        print("📋 STAGE 1: Planning (Genesis Scheduler)")
        execution_strategy = generate_execution_strategy(
            refined_goal, i + 1, previous_summary, plan_context, use_codex
        )

        if execution_strategy:
            print("Execution Strategy Generated:")
            print(execution_strategy[:300] + "..." if len(execution_strategy) > 300 else execution_strategy)
            print()

            # Summarize planning stage for execution stage
            planning_summary = summarize_for_next_stage(
                "PLANNING", execution_strategy, refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Failed to generate execution strategy")
            continue

        # STAGE 2: Execution with subagent delegation
        print("⚡ STAGE 2: Execution (Genesis Direct)")
        progress_response = make_progress(
            refined_goal, i + 1, execution_strategy, plan_context, use_codex
        )

        if progress_response:
            print("Progress Made:")
            print(progress_response[:300] + "..." if len(progress_response) > 300 else progress_response)
            print()

            # Summarize execution stage for validation stage
            execution_summary = summarize_for_next_stage(
                "EXECUTION", progress_response, refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Failed to make progress")
            continue

        # STAGE 3: Validation with focused assessment
        print("✅ STAGE 3: Validation (Genesis Consensus)")
        consensus_response = check_consensus(
            refined_goal, exit_criteria, execution_summary, plan_context, use_codex
        )

        if consensus_response:
            print("Consensus Assessment:")
            print(consensus_response[:300] + "..." if len(consensus_response) > 300 else consensus_response)
            print()

            # Update plan document (Genesis living plan maintenance)
            if "goal_dir" in locals():
                updated_plan = update_plan_document(
                    goal_dir, f"{execution_summary}\n{consensus_response}", i + 1, use_codex
                )

                # Update genesis instructions (Genesis self-improvement)
                update_genesis_instructions(
                    goal_dir, f"Iteration {i+1} learnings:\n{progress_response}", use_codex
                )

            # Prepare summary for next iteration (context conservation)
            previous_summary = summarize_for_next_stage(
                "VALIDATION", consensus_response, refined_goal, i + 1, use_codex
            )

        # Save minimal session data (Genesis context conservation)
        session_data = {
            "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
            "refined_goal": refined_goal,
            "exit_criteria": exit_criteria,
            "max_iterations": max_iterations,
            "current_iteration": i + 1,
            "latest_summary": previous_summary,  # Only keep latest summary, not all work
            "latest_consensus": consensus_response,
            "genesis_principles": "One item per loop | Direct execution | Enhanced context"
        }

        # Update progress in goal directory if available
        if "goal_dir" in locals():
            iteration_data = {
                "iteration": i + 1,
                "work_completed": "See GENESIS.md and fix_plan.md for details",
                "genesis_approach": "Single focus with direct execution",
                "progress": "See consensus assessment",
                "next_steps": "See fix_plan.md priorities",
                "consensus": consensus_response.split("\n")[0] if consensus_response else "N/A",
            }
            update_progress_file(goal_dir, iteration_data)

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        # Check if goal achieved (enhanced Genesis completion detection)
        if consensus_response:
            # Look for OVERALL PROGRESS: XX% pattern (Genesis-specific)
            overall_match = re.search(
                r"OVERALL\s+PROGRESS\s*:\s*(\d+)%",
                consensus_response,
                re.IGNORECASE,
            )
            if overall_match:
                completion_percentage = int(overall_match.group(1))
                if completion_percentage >= 95:  # Genesis allows 95% as "close enough"
                    print("🎉 GENESIS GOAL ACHIEVED! 🎉")
                    print("Genesis principle: 95%+ completion with working implementation is success")
                    break

        # Genesis-style continuation (trust the process)
        if i < max_iterations - 1:
            print(f"📈 Progress made this iteration. Genesis continues...")
            print("Genesis principle: Trust the process, focus on next single task")
            print()

        print("=" * 60 + "\n")

    print("Goal refinement execution complete!")
    print(f"Session saved to: {session_file}")


if __name__ == "__main__":
    main()
