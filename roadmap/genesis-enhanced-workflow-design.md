# Genesis Enhanced Workflow Design

**Version**: v4.0 Minimal Orchestration
**Date**: 2025-09-25
**Status**: Prompt-Based Pipeline

## 🎯 Overview

Minimal Genesis workflow enhancement using simple Python orchestration to pipe output from one stage as input to the next stage via prompts. All intelligence and execution handled by Claude and Cerebras - Python only manages the prompt pipeline flow.

## 🏗️ Architecture

### Current Genesis Structure (Reused)
```
Main Loop:
├── generate_execution_strategy() → Planning
├── generate_tdd_implementation() → TDD Generation
├── make_progress() → Execution
└── check_consensus() → Validation
```

### Minimal Orchestration Structure
```
Prompt-Based Pipeline:
├── STAGE A: Bulk Generation (iterations 1-2)
│   ├── A1: Cerebras Enhanced Goal Prompt
│   └── A2: Cerebras Comprehensive TDD Prompt
└── STAGE B: Iterative Refinement (iterations 3+)
    ├── B1: Smart Model Integration & Testing
    ├── B2: Smart Model Goal Validation (/cons for Claude)
    ├── B3: Smart Model Milestone Planning
    ├── B4: Two-Phase Code Generation (B4.1→B4.2→B4.3)
    └── B5: Smart Model Code Review → loop back to B1
```

**Key Principle**: Python orchestration only manages prompt construction and output parsing. All intelligence from Claude/Cerebras via prompts.

## 📋 Minimal Orchestration Design

### **STAGE A: Bulk Generation Prompts**

#### A1: Enhanced Goal Prompt (Cerebras)
- **Input**: Original goal string
- **Prompt**: "Enhanced Goal Generation: Take this goal and expand it into a comprehensive specification with clear milestones: {goal}"
- **Output**: Enhanced goal specification with milestones
- **Orchestration**: `cerebras_call(a1_prompt.format(goal=goal))`

#### A2: Comprehensive TDD Prompt (Cerebras)
- **Input**: Enhanced goal from A1
- **Prompt**: "Comprehensive TDD Implementation: Create complete test suite and initial implementation for: {enhanced_goal}"
- **Output**: Complete test framework + implementation code
- **Orchestration**: `cerebras_call(a2_prompt.format(enhanced_goal=a1_output))`

### **STAGE B: Iterative Refinement Prompts**

#### B1: Integration & Testing (Smart Model)
- **Input**: Current comprehensive suite + original goal
- **Prompt**: "Integration & Testing: Run all relevant tests and integrate changes for goal '{original_goal}': {comprehensive_suite}"
- **Process**:
  - Run ALL relevant tests (existing project tests + new tests from A2)
  - Apply integration changes to working directory
  - **Autonomous Testing**: Automatically validate integration without user prompts
  - Only proceed if all tests pass AND integration validation complete
- **Output**: Updated comprehensive suite with passing tests and integration status written to `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_integration_status.txt`
- **Orchestration**: `smart_model_call(b1_prompt.format(comprehensive_suite=current_suite, original_goal=goal))`
- **Quality Gate**: Only proceed if all tests pass AND integration validation complete (autonomous)

#### B2: Goal Validation & Verification (Smart Model)
- **Input**: Updated suite from B1 + original goal + enhanced goal spec (read from `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_integration_status.txt`)
- **Process**: Validate if original spec and goal are implemented correctly
- **Review Logic**:
  - If Claude: Use `/cons` command to review implementation against goal
  - If Codex/other: Standard goal validation review without slash commands
- **Prompt**: "Goal Validation: Verify that the implementation satisfies the original goal '{original_goal}' and enhanced spec: {enhanced_goal_spec}"
- **Output**: Goal compliance validation + implementation gaps written to `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_goal_validation.txt`
- **Orchestration**:
  - Claude: Include `/cons` review in prompt execution
  - Codex: `smart_model_call(b2_prompt.format(original_goal=goal, enhanced_goal_spec=enhanced_goal))`
- **Dual Exit Condition**: Workflow complete ONLY when BOTH:
  1. Goal fully implemented (B2 validation complete)
  2. All tests passing (from B1 and later B4.3 validation)

#### B3: Milestone Planning (Smart Model)
- **Input**: Goal validation results from B2 + Original Goal (read from `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_goal_validation.txt`)
- **Prompt Logic**:
  - If implementation gaps: "Milestone Planning: Based on implementation gaps and overall goal '{original_goal}', create prioritized milestones: {validation_results}"
  - If goal complete: Workflow terminates successfully
- **Output**: Prioritized list of milestones for remaining implementation written to `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_milestones.txt`
- **Orchestration**:
  ```python
  with open(f"/tmp/{os.path.basename(os.getcwd())}/{subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()}/genesis_goal_validation.txt", "r") as f:
      validation_results = f.read()
  return smart_model_call(b3_prompt.format(validation_results=validation_results, original_goal=goal))
  ```

#### B4: Two-Phase Code Generation

##### B4.1: Execution Planning (Smart Model)
- **Input**: Milestones from B3 + Original Goal (read from `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_milestones.txt`)
- **Prompt**:
  - If Claude: Uses `jleechan_simulation_prompt.md` + "Generate execution plan for goal '{original_goal}' milestones: {milestones}"
  - If Codex: "Generate execution plan for goal '{original_goal}' milestones: {milestones}"
- **Output**: Detailed execution strategy written to `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_execution_plan.txt`
- **Orchestration**:
  ```python
  with open(f"/tmp/{os.path.basename(os.getcwd())}/{subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()}/genesis_milestones.txt", "r") as f:
      milestones = f.read()
  return smart_model_call(b41_prompt.format(milestones=milestones, original_goal=goal))
  ```

##### B4.2: TDD Code Generation (Cerebras)
- **Input**: B4.1 execution plan + B3 milestones + Original Goal (read from `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_execution_plan.txt` and `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_milestones.txt`)
- **Prompt**: "TDD Code Generation: Using execution plan and milestones for goal '{original_goal}': Plan: {execution_plan} Milestones: {milestones}"
- **Process**: Generate code and write it to appropriate files in working directory
- **Output**: Generated code implementing milestones (written to filesystem)
- **Orchestration**:
  ```python
  repo_name = os.path.basename(os.getcwd())
  branch_name = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
  tmp_path = f"/tmp/{repo_name}/{branch_name}"

  with open(f"{tmp_path}/genesis_execution_plan.txt", "r") as f:
      execution_plan = f.read()
  with open(f"{tmp_path}/genesis_milestones.txt", "r") as f:
      milestones = f.read()
  return cerebras_call(b42_prompt.format(execution_plan=execution_plan, milestones=milestones, original_goal=goal))
  ```

##### B4.3: Test Validation (Smart Model)
- **Input**: Generated code from B4.2 (written to working directory)
- **Process**: Run all relevant tests (existing project tests + new tests from A2)
- **Success Path**: All tests pass → Continue to B5
- **Failure Path**: Any tests fail → Loop back to B4.1 with failure details
- **Prompt**: "Test Validation: Run all relevant tests and analyze results for goal '{original_goal}'"
- **Output**: Test results + validation status written to `/tmp/$(basename $PWD)/$(git branch --show-current)/genesis_test_results.txt`
- **Orchestration**: `smart_model_call(b43_prompt.format(original_goal=goal))`
- **Loop Logic Implementation**:
  ```python
  test_results = smart_model_call(b43_prompt.format(original_goal=goal))
  if "tests failed" in test_results.lower() or "failure" in test_results.lower():
      # Write failure details to temp file for B4.1
      repo_name = os.path.basename(os.getcwd())
      branch_name = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
      tmp_path = f"/tmp/{repo_name}/{branch_name}"

      with open(f"{tmp_path}/genesis_failure_details.txt", "w") as f:
          f.write(f"Test Failures: {test_results}")
      # Loop back to B4.1 execution planning with failure context
      return "LOOP_BACK_TO_B4_1_WITH_FAILURES"
  else:
      # Tests passed, continue to B5
      return test_results
  ```

#### B5: Code Review (Model-Specific)
- **Input**: Generated code from B4.2 that passed B4.3 validation (already written to working directory)
- **Process**: Review analyzes current working directory state
- **Review Logic**:
  - If Claude: Use `/cons` slash command to review working directory
  - If Codex: Standard code review without slash commands
- **Output**: Code review feedback and validation
- **Orchestration**:
  - Claude: `SlashCommand("/cons")` (reviews current working directory)
  - Codex: `smart_model_call("Code Review: Review current implementation")`
- **Integration**: Apply review feedback and loop back to B1 for next iteration

## 🔄 Minimal Python Orchestration

### Simple Orchestration Code
```python
def enhanced_genesis_workflow(goal, iteration_num, previous_output=None):
    """Minimal orchestration using /tmp file-based data flow"""
    import os
    import subprocess

    # Setup /tmp paths
    repo_name = os.path.basename(os.getcwd())
    branch_name = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
    tmp_path = f"/tmp/{repo_name}/{branch_name}"
    os.makedirs(tmp_path, exist_ok=True)

    if iteration_num == 1:
        # A1: Enhanced Goal (Cerebras)
        prompt = f"Enhanced Goal Generation: Take this goal and expand it into a comprehensive specification with clear milestones: {goal}"
        return cerebras_call(prompt)

    elif iteration_num == 2:
        # A2: Comprehensive TDD (Cerebras)
        prompt = f"Comprehensive TDD Implementation: Create complete test suite and initial implementation for: {previous_output}"
        return cerebras_call(prompt)

    else:
        # Stage B: Use detailed design workflow (B1-B5) with /tmp file data flow
        current_suite = previous_output

        # Detailed workflow implementation follows B1-B5 design specification
        # (Implementation details in sections above using /tmp file-based data passing)
        return execute_detailed_b1_to_b5_workflow(current_suite, goal, tmp_path)

# Helper functions (minimal)
def cerebras_call(prompt):
    """Simple wrapper for Cerebras API call"""
    return execute_claude_command(prompt, use_cerebras=True)

def execute_codex_command(prompt):
    """Execute command using Codex API"""
    # Implementation: Call Codex API with prompt
    # Returns: Codex response string
    return codex_api_call(prompt)

def smart_model_call(prompt):
    """Smart model wrapper - Claude by default, Codex if --codex flag"""
    import sys  # Import sys for argv access
    use_codex = "--codex" in sys.argv  # Global flag affects all calls within single Genesis instance
    if use_codex:
        return execute_codex_command(prompt)
    else:
        return execute_claude_command(prompt, use_cerebras=False)
```

### Enhanced Orchestration Flow
```
Iteration 1: goal → [Cerebras A1 Prompt] → enhanced_goal
Iteration 2: enhanced_goal → [Cerebras A2 Prompt] → comprehensive_suite + tests
Iteration 3+: suite → [Smart Model B1] → integration + tests + manual verification
              → [Smart Model/cons B2] → goal validation
                  ↓ (if goal complete - WORKFLOW COMPLETE)
              → [Smart Model B3] → milestones (based on implementation gaps)
              → [Smart Model B4.1] → execution_plan (with user mimic if Claude)
              → [Cerebras B4.2] → generated_code (written to files)
              → [Smart Model B4.3] → test_validation
                  ↓ (if tests pass)     ↑ (if tests fail - loop back to B4.1)
              → [/cons or Smart Model B5] → code_review
              → (loop back to B1 for next iteration)
              (repeat until B2 goal validation complete)
```

**Key Enhancements**:
- **B1 Integration**: Combined testing + integration with manual verification gate
- **B2 Goal Validation**: Uses `/cons` for Claude to validate goal implementation
- **B4.3 Test Validation**: Explicit test validation with loop-back to B4.1 on failure
- **Goal-Driven Workflow**: B2 determines workflow completion vs continuing
- **Model Flexibility**: --codex flag switches Claude→Codex globally
- **Working Directory**: /cons reviews actual files, not parameters

## 🧩 Minimal Integration Points

### Existing Genesis Functions (Reused As-Is)
- **`execute_claude_command()`** → Core function for both Claude and Cerebras calls
- **Main Genesis loop** → Enhanced with iteration-based stage detection
- **Session management** → Unchanged, uses existing patterns
- **Consensus validation** → Leveraged via prompt-based "all tests pass" detection

### New Orchestration Functions (Minimal)
- **`enhanced_genesis_workflow()`** → 30-line orchestration function
- **`cerebras_call()`** → 2-line wrapper for Cerebras API
- **`claude_call()`** → 2-line wrapper for Claude API

### Integration Pattern
```python
# Minimal orchestration - just prompt construction
prompt = f"Task: {instruction} Context: {previous_output}"
result = api_call(prompt)
return result  # Pass to next stage
```

**Key Simplification**: No complex functions, no state management, no external integrations - just prompt-based pipeline orchestration.

## 📊 Prompt-Based Data Flow

### Pure String Pipeline
```python
# All data passed as strings through prompts
iteration_1_output = "Enhanced goal: Build authentication system with milestones..."
iteration_2_output = "Test suite + implementation: class AuthTest... class AuthService..."
iteration_3_output = "Updated suite with fixes: class AuthTest... (fixed issues)"
```

### Data Flow Pattern
```python
# Simple string-to-string pipeline
goal_string = "Build user authentication"
enhanced_goal_string = cerebras_call(f"Enhance this goal: {goal_string}")
comprehensive_suite_string = cerebras_call(f"Create TDD for: {enhanced_goal_string}")
updated_suite_string = claude_b1_to_b5_pipeline(comprehensive_suite_string)
```

**Ultra Simplification**: No data structures, no parsing, no objects - pure string-based prompts and outputs.

## 🎯 Simplified Success Criteria

### Stage A Success
- **A1 Complete**: Enhanced goal specification generated by Cerebras
- **A2 Complete**: Comprehensive TDD suite + implementation generated by Cerebras
- **Pipeline Clean**: Each output properly formatted for next stage input

### Stage B Success
- **Test Analysis Working**: `analyze_test_results()` identifies failures correctly
- **Milestone Planning Working**: `define_milestones_from_failures()` creates actionable fix list
- **Code Generation Working**: Cerebras generates fixes for identified milestones
- **Integration Working**: `integrate_fixes()` properly merges fixes into suite
- **Exit Condition Working**: Workflow terminates when all tests pass

### Overall Success
- **Simple Pipeline**: Each step takes previous output as input, no external state
- **Backward Compatible**: Existing Genesis usage unchanged
- **Autonomous Parallel**: Multiple instances can run independently
- **Clean Implementation**: 6 simple functions, no complex orchestration

## 🔧 Minimal Implementation Strategy

### Phase 1: Core Orchestration (30 min)
- Add `enhanced_genesis_workflow()` function (30 lines)
- Add simple helper functions `cerebras_call()` and `claude_call()` (4 lines total)
- Integrate into existing Genesis main loop with iteration-based detection

### Phase 2: Prompt Engineering (45 min)
- Define 6 prompt templates (A1, A2, B1-B5) for each stage
- Test prompt effectiveness with sample goals
- Refine prompts based on Claude/Cerebras output quality

### Phase 3: Integration Testing (30 min)
- Test complete prompt pipeline with real goals
- Verify string-to-string data flow works correctly
- Test "all tests pass" exit condition detection

### Phase 4: Parallel Validation (15 min)
- Test multiple Genesis instances running simultaneously
- Verify no state sharing or conflicts
- Validate autonomous operation

**Total Implementation Time**: 2 hours → Minimal code, maximum leverage of existing Claude/Cerebras intelligence.

## ⚡ Minimal Orchestration Benefits

1. **Ultra-Simple Code**: Only ~35 lines of new Python code total
2. **Pure Prompt Pipeline**: All intelligence from Claude/Cerebras via prompts
3. **Zero State Management**: No persistent objects, files, or databases
4. **Autonomous Parallel**: Multiple instances with zero coordination needed
5. **Existing Genesis Unchanged**: Complete backward compatibility
6. **Easy Implementation**: 2 hours total implementation time

---

**Ready for implementation with minimal Python orchestration approach.**
