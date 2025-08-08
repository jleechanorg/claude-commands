# /testllm - LLM-Driven Test Execution Command

## Purpose
Execute test specifications directly as an LLM without generating intermediate scripts or files. Follow test instructions precisely with real authentication and browser automation.

## Usage Patterns
```bash
# Single-Agent Testing (Traditional)
/testllm path/to/test_file.md
/testllm path/to/test_file.md with custom user input
/testllm "natural language test description"

# Dual-Agent Verification (Enhanced Reliability)
/testllm verified path/to/test_file.md
/testllm verified path/to/test_file.md with custom input
/testllm verified "natural language test description"
```

## Core Principles
- **LLM-Native Execution**: Drive tests directly as Claude, no script generation
- **Real Mode Only**: NEVER use mock mode, test mode, or simulated authentication
- **Precise Following**: Execute test instructions exactly as written
- **Browser Automation**: Use Playwright MCP for real browser testing
- **Real Authentication**: Use actual Google OAuth with real credentials

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

### Pre-Execution Requirements
**CRITICAL**: Before starting ANY test specification, ALWAYS follow this systematic protocol:

1. **Read Specification Twice**: Complete understanding before execution
2. **Extract ALL Requirements**: Convert every requirement to TodoWrite checklist
3. **Identify Evidence Needs**: Document what proof is needed for each requirement
4. **Create Validation Plan**: Map each requirement to specific validation method
5. **Execute Systematically**: Complete each requirement with evidence collection
6. **Success Declaration**: Only declare success with complete evidence portfolio

### Anti-Pattern Prevention
- ❌ **NO Partial Success Declaration**: Cannot claim success based on partial validation
- ❌ **NO Assumption-Based Conclusions**: Every claim requires specific evidence
- ❌ **NO Skipping Failure Conditions**: Must test both positive and negative cases
- ✅ **ALWAYS Use TodoWrite**: Track validation state systematically
- ✅ **ALWAYS Collect Evidence**: Screenshots, logs, console output for each requirement

## Implementation Protocol

### Step 1: Systematic Requirement Analysis
- Read test specification completely (minimum twice)
- Extract ALL requirements into explicit TodoWrite checklist items
- Identify success criteria AND failure conditions for each requirement
- Document evidence collection plan for each requirement
- Create systematic validation approach before any execution

### Step 2: Test Environment Setup
- Verify real backend servers are running (Flask on :5005, React V2 on :3002)
- Ensure real authentication is configured (no test mode)
- Validate Playwright MCP availability for browser automation
- Confirm network connectivity for real API calls

### Step 3: Test Execution
- Follow test instructions step-by-step with LLM reasoning
- Use Playwright MCP for browser automation (headless mode)
- Make real API calls to actual backend
- Capture screenshots for evidence using proper file paths
- Monitor console errors and network requests
- Document findings with exact evidence references

### Step 4: Results Analysis
- Assess findings against test success criteria
- Classify issues as CRITICAL/HIGH/MEDIUM per test specification
- Provide actionable recommendations
- Generate evidence-backed conclusions

## Critical Rules

### Authentication Requirements
- ❌ NEVER use mock mode, test mode, or Dev Tools
- ❌ NEVER use test-user-basic or simulated users
- ✅ ALWAYS use real Google OAuth authentication
- ✅ ALWAYS require actual login credentials

### Browser Automation
- ✅ USE Playwright MCP as primary browser automation
- ✅ ALWAYS use headless mode for automation
- ✅ CAPTURE screenshots to docs/ directory with descriptive names
- ✅ MONITOR console errors and network requests

### API Integration
- ✅ MAKE real API calls to actual backend servers
- ✅ VERIFY network requests in browser developer tools
- ✅ VALIDATE response data and status codes
- ✅ TEST end-to-end data flow from frontend to backend

### Evidence Collection
- ✅ SAVE all screenshots to filesystem (not inline)
- ✅ REFERENCE screenshots by filename in results
- ✅ DOCUMENT exact error messages and console output
- ✅ PROVIDE specific line numbers and code references

## Execution Flow with Validation Gates

```
1. Systematic Requirement Analysis (MANDATORY GATE)
   ├── Read test specification twice completely
   ├── Extract ALL requirements to TodoWrite checklist
   ├── Identify success criteria AND failure conditions
   ├── Document evidence needs for each requirement
   ├── Create systematic validation plan
   └── ⚠️ GATE: Cannot proceed without complete requirements checklist

2. Environment Validation
   ├── Check server status (backend :5005, frontend :3002)
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
   ├── Generate evidence-backed report with file references
   ├── Apply priority classification with specific evidence
   └── ⚠️ FINAL GATE: Success only declared with complete evidence portfolio
```

## Error Handling
- **Authentication Failures**: Stop immediately, require real login
- **Server Connectivity**: Verify backend services are running
- **Browser Automation**: Ensure Playwright MCP is available
- **API Errors**: Document exact error messages and status codes
- **Screenshot Failures**: Save to filesystem, never rely on inline images

## Success Metrics
- All test steps executed without mock mode
- Real API calls made and documented
- Screenshots saved to filesystem with proper naming
- Console errors captured and analyzed
- Findings classified by priority (CRITICAL/HIGH/MEDIUM)
- Actionable recommendations provided

## Anti-Patterns to Avoid
- ❌ Generating Python or shell scripts unless explicitly requested
- ❌ Using mock mode or test mode for any reason
- ❌ Simulating authentication instead of using real OAuth
- ❌ Relying on inline screenshots instead of saved files
- ❌ Making assumptions about test results without evidence
- ❌ Skipping steps or taking shortcuts in test execution

## Command Execution Modes

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

### Execution Flow Selection Logic
```
if "verified" in command_args:
    execute_dual_agent_mode()
    spawn_testexecutor_agent()
    wait_for_evidence_package()
    spawn_testvalidator_agent()
    cross_validate_results()
else:
    execute_single_agent_mode()
    follow_systematic_validation_protocol()
```

### Evidence Package Handoff (Dual-Agent Only)
1. **TestExecutor Creates**: Structured JSON evidence package + artifact files
2. **File System Storage**: Evidence saved to `docs/test_evidence_TIMESTAMP/`
3. **Validator Receives**: Original test spec + evidence package only
4. **Independent Assessment**: Validator evaluates without execution context
5. **Cross-Validation**: Final report combines both agent perspectives

### Quality Assurance Benefits
- **Single-Agent**: Systematic validation protocol prevents shortcuts
- **Dual-Agent**: Independent verification eliminates execution bias
- **Evidence-Based**: Both modes require concrete proof for all claims
- **Comprehensive**: Both success AND failure scenarios validated
