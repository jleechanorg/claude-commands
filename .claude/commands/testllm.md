---
description: /testllm - LLM-Driven Test Execution Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Mandatory First Step

**Action Steps:**
1. **Read the Entire Suite First**: Before planning, checklist creation, or any execution, explicitly read every test specification in the `${CLAUDE_TESTLLM_DIR:-testing_llm/}` directory to internalize scope, dependencies, and evidence requirements.

### Phase 2: Report Integrity Checklist (MANDATORY)

**Action Steps:**
Before submitting final report, verify:

1. [ ] Every claimed evidence file verified with `ls -la` command
2. [ ] No references to non-existent files or screenshots
3. [ ] Exit status tracked for all commands
4. [ ] Final SUCCESS/FAILURE aligned with actual exit codes
5. [ ] No contradictions between claims and evidence
6. [ ] All TodoWrite items have corresponding verified evidence

### Phase 3: Pre-Execution Requirements

**Action Steps:**
**CRITICAL**: Before starting ANY test specification, ALWAYS follow this systematic protocol:

1. **Read Specification Twice**: Complete understanding before execution
2. **Extract ALL Requirements**: Convert every requirement to TodoWrite checklist
3. **Identify Evidence Needs**: Document what proof is needed for each requirement
4. **Create Validation Plan**: Map each requirement to specific validation method
5. **Execute Systematically**: Complete each requirement with evidence collection
6. **Success Declaration**: Only declare success with complete evidence portfolio

### Phase 4: Step 1: Complete Directory Analysis (MANDATORY GATE)

**Action Steps:**
1. **Read ALL test files** in the specified directory before any execution
2. **Catalog ALL test cases** across all files in TodoWrite checklist
3. **Identify test dependencies** and execution order requirements
4. **Verify test coverage** spans all requested functionality
5. **Document test matrix** showing all scenarios to be validated
6. **⚠️ GATE: Cannot proceed without complete test inventory from ALL files**

### Phase 5: Step 2: Comprehensive Test Planning

**Action Steps:**
1. **Extract requirements from EACH test file** into unified checklist
2. **Map test interdependencies** (authentication → campaign creation, etc.)
3. **Plan execution sequence** respecting prerequisites
4. **Estimate total test duration** for all cases combined
5. **Document evidence collection** needs for complete matrix
6. **⚠️ GATE: Cannot start testing without unified execution plan**

### Phase 6: Step 3: Sequential Test Execution

**Action Steps:**
1. **Execute ALL test files** in logical dependency order
2. **Complete each test matrix** before moving to next file
3. **Collect evidence for EVERY test case** across all files
4. **Track completion status** for entire directory scope
5. **Validate success criteria** for combined test suite
6. **⚠️ GATE: Cannot declare success without ALL files tested**

### Phase 7: Step 1: Systematic Requirement Analysis

**Action Steps:**
1. Read test specification completely (minimum twice)
2. Extract ALL requirements into explicit TodoWrite checklist items
3. Identify success criteria AND failure conditions for each requirement
4. Document evidence collection plan for each requirement
5. Create systematic validation approach before any execution

### Phase 8: Step 2: Test Environment Setup

**Action Steps:**
1. Review `run_local_server.sh` to understand how the local environment should be launched
2. Detect whether the local server stack started by `run_local_server.sh` is already running
3. If servers are not running, execute `run_local_server.sh` and wait for successful startup
4. Ensure real authentication is configured (no test mode)
5. Validate Playwright MCP availability for browser automation
6. Confirm network connectivity for real API calls
7. Determine the current repository name (`git rev-parse --show-toplevel | xargs basename`) and active branch (`git rev-parse --abbrev-ref HEAD`) to construct result paths under `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}`

### Phase 9: Step 2.5: Result Output Directory Standard

**Action Steps:**
1. Create (if necessary) the directory `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}`
2. Store **all** test outputs, logs, screenshots, and evidence artifacts inside this directory or its subdirectories
3. After execution, enumerate every created file and subdirectory so the user receives a complete inventory
4. Explicitly communicate the absolute path to the `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` directory and its contents in the final summary

### Phase 10: Step 3: Test Execution

**Action Steps:**
1. Follow test instructions step-by-step with LLM reasoning
2. Use Playwright MCP for browser automation (headless mode)
3. Make real API calls to actual backend
4. Capture screenshots for evidence using proper file paths
5. Monitor console errors and network requests
6. Document findings with exact evidence references

### Phase 11: Step 4: Results Analysis

**Action Steps:**
1. Assess findings against test success criteria
2. Classify issues as CRITICAL/HIGH/MEDIUM per test specification
3. Provide actionable recommendations
4. Generate evidence-backed conclusions

### Phase 12: Execution Flow with Validation Gates

**Action Steps:**
```
1. Systematic Requirement Analysis (MANDATORY GATE)
   ├── Read test specification twice completely
   ├── Extract ALL requirements to TodoWrite checklist
   ├── Identify success criteria AND failure conditions
   ├── Document evidence needs for each requirement
   ├── Create systematic validation plan
   └── ⚠️ GATE: Cannot proceed without complete requirements checklist

2. Environment Validation
   ├── Inspect `run_local_server.sh` for the expected services and health checks
   ├── Determine if the local server stack is already running; start it with `run_local_server.sh` if needed
   ├── Verify authentication configuration
   ├── Confirm Playwright MCP availability
   ├── Validate network connectivity
   └── ⚠️ GATE: Cannot proceed without environment validation

3. Systematic Test Execution
   ├── Execute EACH TodoWrite requirement individually
   ├── Capture evidence for EACH requirement (screenshots, logs)
   ├── Test positive cases AND negative/failure cases
   ├── Update TodoWrite status: pending → in_progress → completed
   ├── Validate evidence quality before marking complete
   └── ⚠️ GATE: Cannot proceed to next requirement without evidence

4. Comprehensive Results Validation
   ├── Verify ALL TodoWrite items marked completed with evidence
   ├── Cross-check findings against original specification
   ├── Validate that failure conditions were tested (not just success)
   ├── 🚨 MANDATORY: Run `ls -la ${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` to verify all claimed evidence files
   ├── 🚨 MANDATORY: Compare claimed evidence files against actual directory listing
   ├── 🚨 MANDATORY: Remove any phantom file references from report
   ├── Generate evidence-backed report with ONLY verified file references
   ├── Apply priority classification with specific evidence
   ├── 🚨 MANDATORY: Check exit status of all executed commands
   ├── 🚨 MANDATORY: Align final SUCCESS/FAILURE with actual exit codes
   └── ⚠️ FINAL GATE: Success only declared with exit code 0 AND complete verified evidence portfolio
```

### Phase 13: Command Execution Modes

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### Phase 14: Execution Flow Selection Logic

**Action Steps:**
```
if not command_args:
    execute_directory_suite("testing_llm", mode="single_agent")
elif command_args == ["verified"]:
    execute_directory_suite("testing_llm", mode="dual_agent")
elif "verified" in command_args:
    execute_dual_agent_mode()
    spawn_testexecutor_agent()
    wait_for_evidence_package()
    spawn_testvalidator_agent()
    cross_validate_results()
else:
    execute_single_agent_mode()
    follow_systematic_validation_protocol()
```

## 📋 REFERENCE DOCUMENTATION

# /testllm - LLM-Driven Test Execution Command

## Purpose

Execute test specifications directly as an LLM without generating intermediate scripts or files. Follow test instructions precisely with real authentication and browser automation.

## Usage Patterns

```bash

# Default Directory Suite (No Arguments)

/testllm
/testllm verified

# Single-Agent Testing (Traditional)

/testllm path/to/test_file.md
/testllm path/to/test_file.md with custom user input
/testllm "natural language test description"

# Dual-Agent Verification (Enhanced Reliability)

/testllm verified path/to/test_file.md
/testllm verified path/to/test_file.md with custom input
/testllm verified "natural language test description"
```

### Default Behavior (No Arguments Provided)

- **Automatic Directory Coverage**: When invoked without a specific test file or natural language specification, `/testllm` automatically executes the full `${CLAUDE_TESTLLM_DIR:-testing_llm/}` directory test suite using the [🚨 DIRECTORY TESTING PROTOCOL](#-directory-testing-protocol---mandatory-for-all-directory-based-tests).
- **Verified Mode Support**: `/testllm verified` with no additional arguments runs the same `${CLAUDE_TESTLLM_DIR:-testing_llm/}` directory workflow, but with the dual-agent verification architecture for independent validation.
- **Extensible Overrides**: Providing any explicit file path, directory, or natural language description overrides the default and targets the requested scope.
- **Configurable Directory**: Set `CLAUDE_TESTLLM_DIR` to override the default `${CLAUDE_TESTLLM_DIR:-testing_llm/}` path for directory-wide executions.

## Core Principles

- **LLM-Native Execution**: Drive tests directly as Claude, no script generation
- **Real Mode Only**: NEVER use mock mode, test mode, or simulated authentication
- **Precise Following**: Execute test instructions exactly as written
- **Browser Automation**: Use Playwright MCP for real browser testing
- **Real Authentication**: Use actual Google OAuth with real credentials
- **🚨 TOTAL FAILURE PROTOCOL**: Apply [Total Failure Protocol](total_failure.md) - 100% working or TOTAL FAILURE

## 🚨 ANTI-FALSE-POSITIVE PROTOCOL (MANDATORY)

### Evidence File Verification (CRITICAL)

Before generating ANY test report, you MUST:

1. **Run File System Check**: Execute `ls -laR ${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}`
2. **Compare Claims vs Reality**: Cross-reference every file mentioned in report against actual directory listing
3. **Remove Phantom Files**: Delete ANY file references that don't appear in the `ls` output
4. **Zero Tolerance**: If you claim a file exists, it MUST be verified by command output

### Exit Status Validation (CRITICAL)

Before declaring test SUCCESS, you MUST:

1. **Track All Exit Codes**: Monitor exit status of every command executed
2. **Aggregate Status**: If ANY command exits with code 1, overall result is FAILURE
3. **Align Report with Reality**: FORBIDDEN to report "SUCCESS" with exit code 1
4. **Evidence of Success**: Success requires BOTH exit code 0 AND complete verified evidence

## Dual-Agent Architecture (Enhanced Reliability)

### Independent Verification System

When `verified` keyword is used, `/testllm` employs a dual-agent architecture to eliminate execution bias:

**TestExecutor Agent**:
- **Role**: Pure execution and evidence collection
- **Focus**: Follow specifications methodically, capture all evidence
- **Constraint**: Cannot declare success/failure, only "evidence collected"
- **Output**: Structured evidence package with neutral documentation

**TestValidator Agent**:
- **Role**: Independent validation with fresh context
- **Focus**: Critical evaluation of evidence against original requirements
- **Constraint**: Zero execution context, no bias toward success
- **Input**: Original test spec + evidence package only

### Bias Elimination Benefits

- **Execution Bias Removed**: Separate agent validates without execution investment
- **Fresh Perspective**: Validator sees only evidence, not execution challenges
- **Cross-Verification**: Both agents must agree for final success declaration
- **Systematic Quality**: Evidence-based validation prevents premature success claims

## Systematic Validation Protocol (MANDATORY)

### Anti-Pattern Prevention

- 🚨 **TOTAL FAILURE PROTOCOL ENFORCEMENT**: Apply [Total Failure Protocol](total_failure.md) before declaring any results
- ❌ **NO Partial Success Declaration**: Cannot claim success based on partial validation
- ❌ **NO Assumption-Based Conclusions**: Every claim requires specific evidence
- ❌ **NO Skipping Failure Conditions**: Must test both positive and negative cases
- ✅ **ALWAYS Use TodoWrite**: Track validation state systematically
- ✅ **ALWAYS Collect Evidence**: Screenshots, logs, console output for each requirement

## 🚨 DIRECTORY TESTING PROTOCOL - MANDATORY FOR ALL DIRECTORY-BASED TESTS

### When User Requests "${CLAUDE_TESTLLM_DIR:-testing_llm/} test cases" or Similar Directory-Based Testing:

**Default Invocation Note**: Running `/testllm` with no additional arguments automatically triggers this full protocol for the `${CLAUDE_TESTLLM_DIR:-testing_llm/}` directory.

**🚨 CRITICAL RULE: NEVER TEST JUST ONE FILE WHEN DIRECTORY REQUESTED**

### Anti-Pattern Prevention (MANDATORY ENFORCEMENT)

- ❌ **FORBIDDEN**: Reading only one test file when directory/multiple tests requested
- ❌ **FORBIDDEN**: Declaring success after partial file execution
- ❌ **FORBIDDEN**: Assuming "working authentication" means "testing complete"
- ✅ **REQUIRED**: Complete directory inventory before any test execution
- ✅ **REQUIRED**: TodoWrite checklist encompassing ALL files in scope
- ✅ **REQUIRED**: Evidence collection from ALL test cases across ALL files

### Directory Testing Success Criteria

**PASS requires:**
- ✅ ALL test files in requested directory executed
- ✅ ALL test cases within each file completed with evidence
- ✅ Combined test matrix shows comprehensive coverage
- ✅ Evidence portfolio contains screenshots/logs from every test scenario
- ✅ No skipped files or partial execution within scope

**FAIL indicators:**
- ❌ Only executed subset of available test files
- ❌ Declared success based on single file completion
- ❌ Missing evidence from test cases in unexecuted files
- ❌ Partial coverage of requested directory scope

## Implementation Protocol

## Critical Rules

### Authentication Requirements

- ❌ AVOID mock mode, test mode for production testing (dev tools allowed for debugging with caution)
- ❌ NEVER use test-user-basic or simulated users for real workflow validation
- ✅ ALWAYS use real Google OAuth authentication for production testing
- ✅ ALWAYS require actual login credentials for authentic user experience testing
- ⚠️ **Dev Tools Exception**: Browser dev tools may be used for debugging issues, but with clear documentation of when/why used

### Browser Automation

- ✅ USE Playwright MCP as primary browser automation
- ✅ ALWAYS use headless mode for automation
- ✅ CAPTURE screenshots to the `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` results directory with descriptive names
- ✅ MONITOR console errors and network requests

### API Integration

- ✅ MAKE real API calls to actual backend servers
- ✅ VERIFY network requests in browser developer tools
- ✅ VALIDATE response data and status codes
- ✅ TEST end-to-end data flow from frontend to backend

### Evidence Collection

- ✅ SAVE all screenshots and artifacts to `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` (never inline)
- ✅ REFERENCE screenshots by filename in results and include the absolute path within `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}`
- ✅ DOCUMENT exact error messages and console output
- ✅ PROVIDE specific line numbers and code references
- ✅ ALWAYS inform the user of the `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` directory location and list every file created within it
- 🚨 **MANDATORY FILE VERIFICATION**: Before mentioning ANY evidence file in reports, VERIFY it exists using `ls -la`
- 🚨 **NO PHANTOM FILES**: NEVER claim evidence files exist without explicit verification command output
- 🚨 **VERIFY BEFORE REPORTING**: After test completion, run `ls -la ${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` and ONLY list files that actually appear in output

## Error Handling

- **Authentication Failures**: Stop immediately, require real login
- **Server Connectivity**: Verify backend services are running
- **Browser Automation**: Ensure Playwright MCP is available
- **API Errors**: Document exact error messages and status codes
- **Screenshot Failures**: Save to filesystem, never rely on inline images

## Success Metrics

- All test steps executed without mock mode
- Real API calls made and documented
- Screenshots saved under `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` with proper naming
- Console errors captured and analyzed
- Findings classified by priority (CRITICAL/HIGH/MEDIUM)
- Actionable recommendations provided
- Final report clearly states the `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}` directory path and inventories all artifacts within it

### 🚨 EXIT STATUS VALIDATION (MANDATORY)

- **CRITICAL**: Test execution MUST track and report actual exit status
- **Status Code 0**: Success - all tests passed, all evidence collected
- **Status Code 1**: Failure - tests failed OR incomplete evidence
- **FORBIDDEN**: Reporting "TOTAL SUCCESS" with exit code 1
- **REQUIRED**: Final report MUST align with actual exit status
- **VALIDATION**: If ANY command fails, overall status MUST be FAILURE
- **EVIDENCE ALIGNMENT**: Success claims require both exit code 0 AND complete evidence

## Anti-Patterns to Avoid

- ❌ Generating Python or shell scripts unless explicitly requested
- ❌ Using mock mode or test mode for any reason
- ❌ Simulating authentication instead of using real OAuth
- ❌ Relying on inline screenshots instead of saved files
- ❌ Making assumptions about test results without evidence
- ❌ Skipping steps or taking shortcuts in test execution

### Single-Agent Mode (Traditional)

When `/testllm` is invoked WITHOUT `verified` keyword:

**Single Agent Process:**
1. **Systematic Requirements Analysis** - Read spec, create TodoWrite checklist
2. **Environment Validation** - Verify servers, authentication, tools
3. **Test Execution** - Execute requirements with evidence collection
4. **Results Compilation** - Generate final report with findings

### Dual-Agent Mode (Enhanced Verification)

When `/testllm verified` is invoked:

**Phase 1: TestExecutor Agent Execution**
```
Task(
  subagent_type="testexecutor",
  description="Execute test specification with evidence collection",
  prompt="Follow test specification methodically. Create evidence package with screenshots, logs, console output. NO success/failure judgments - only neutral documentation."
)
```

**Phase 2: Independent Validation**
```
Task(
  subagent_type="testvalidator",
  description="Independent validation of test results",
  prompt="Evaluate evidence package against original test specification. Fresh context assessment - no execution bias. Provide systematic requirement-by-requirement validation."
)
```

**Phase 3: Cross-Verification**
1. **Compare Results** - TestExecutor evidence vs TestValidator assessment
2. **Resolve Disagreements** - Validator decision takes precedence in conflicts
3. **Final Report** - Combined analysis with both perspectives
4. **Quality Assurance** - Dual-agent verification eliminates execution bias

### Evidence Package Handoff (Dual-Agent Only)

1. **TestExecutor Creates**: Structured JSON evidence package + artifact files
2. **File System Storage**: Evidence saved to `${CLAUDE_TESTLLM_RESULTS_DIR:-/tmp/<repo_name>/<branch_name>/}test_evidence_TIMESTAMP/`
3. **Validator Receives**: Original test spec + evidence package only
4. **Independent Assessment**: Validator evaluates without execution context
5. **Cross-Validation**: Final report combines both agent perspectives

### Quality Assurance Benefits

- **Single-Agent**: Systematic validation protocol prevents shortcuts
- **Dual-Agent**: Independent verification eliminates execution bias
- **Evidence-Based**: Both modes require concrete proof for all claims
- **Comprehensive**: Both success AND failure scenarios validated
- **🚨 TOTAL FAILURE PROTOCOL**: Apply [Total Failure Protocol](total_failure.md) for all result declarations
