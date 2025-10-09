description: /consensus Command - Multi-Agent Consensus Review
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Mode Selection & Parallel Agent Execution (2025 Optimization)

**Action Steps:**
1. Determine the correct execution mode using the "Modes & Scopes" guidance below. If the scope is ambiguous, pause and ask the user to choose a mode via TodoWrite before continuing.
2. Once the mode is confirmed, load the corresponding 5-agent roster.
3. Run those 5 agents simultaneously using Task tool parallel execution with the mode-appropriate context and role definitions.

## 📋 REFERENCE DOCUMENTATION

# /consensus Command - Multi-Agent Consensus Review

**Purpose**: Fast consensus-building analysis for solo MVP projects using 2025 multi-agent protocols. Supports code reviews, product spec validation, launch-readiness assessments, and other decision-heavy tasks. Uses a simple 3-round maximum with early termination when agents agree. Focus on pragmatic outcomes over enterprise-grade security theater.

**⚡ Performance**: 2-5 minutes total with parallel agent execution and smart early termination.

**🚀 Solo Unlaunched MVP Context**: Optimized for pre-launch projects with ZERO external users. Only serious external attacker security vulnerabilities matter (SQL injection, RCE, auth bypass). Enterprise security theater is counterproductive. GitHub rollbacks provide safety net.

## Modes & Scopes

`/consensus` adapts to the given scope. Claude must select an execution mode before delegating:

- **Code Review Mode** (default when scope includes code changes or active PR): Uses software-focused agents and expects diff context.
- **Documentation & Spec Mode** (when reviewing docs, research, requirements, or validation evidence): Prioritizes accuracy checks, traceability to evidence, and clarity of product decisions.
- **Operational Decision Mode** (release go/no-go, launch readiness, roadmap decisions): Emphasizes risk analysis, stakeholder impacts, and mitigation steps.

When scope is ambiguous, ask the user which mode they want via TodoWrite before executing.

## Usage

```

> ℹ️ macOS users: install GNU coreutils (`brew install coreutils`) so `gtimeout` is available for enforced timeouts.
/consensus [<scope>]
/cons [<scope>]          # Alias
```
- **Default scope**: Current PR (if tracking a GitHub pull request) plus any local unmerged files.
- **Optional scope**: Specific file(s), folder(s), or PR number to narrow the review focus.

## Context Acquisition (Always Performed First)

1. **Detect active PR** using `gh pr status` or `git config branch.<name>.merge` to extract the PR number and remote.
2. **Record latest commit** with `git log -1 --stat`.
3. **Capture local changes**:
   - `git status --short` for staged/unstaged files.
   - `git diff --stat` and targeted `git diff` snippets for modified files.
4. **Verify synchronization with GitHub**:
   - Fetch PR files: `gh pr view <pr> --json files,headRefName,baseRefName`.
   - Confirm branch alignment (`git rev-parse HEAD` vs PR head SHA).
5. **Basic credential filtering**: Remove obvious API keys/passwords from context (unlaunched MVP with zero external users - basic filtering sufficient)
6. **Assemble review bundle** containing: PR description, latest commit message, diff summaries, and local-only edits.

### Simplified Consensus Rules

**Fast Multi-Agent Consensus**: Run 5 agents in parallel and calculate simple majority agreement. Pick the correct agent set for the selected mode:
- **Code Review Mode (default)**: `code-review`, `codex-consultant`, `gemini-consultant`, `cursor-consultant`, `code-centralization-consultant`
- **Documentation & Spec Mode**: `accuracy-reviewer`, `evidence-verifier`, `product-strategist`, `delivery-ops`, `clarity-editor`
- **Operational Decision Mode**: `risk-analyst`, `product-strategist`, `delivery-ops`, `customer-advocate`, `exec-synthesizer`

**Success threshold**: 3+ of 5 agents PASS with average confidence ≥6

**Failure threshold**: 3+ agents REWORK OR average confidence <5

**Mixed signals**: Document disagreements, proceed with majority decision, and flag open questions.

**Simple Consensus Calculation**:
1. Run all 5 agents for the selected mode in parallel using Task tool
2. Collect PASS/REWORK + confidence (1-10) from each agent
3. Calculate results:
   - **CONSENSUS_PASS**: 3+ agents PASS AND average confidence ≥6
   - **CONSENSUS_REWORK**: 3+ agents REWORK OR average confidence <5
   - **MIXED_SIGNALS**: Document conflicts, use majority decision

**Agent Specialization**:
- **Code Review Mode**:
  - **`code-review`**: Architecture validation, correctness, maintainability
  - **`codex-consultant`**: System design patterns, scalability foundations
  - **`gemini-consultant`**: 2025 best practices, performance optimization
  - **`cursor-consultant`**: Practical concerns, deployment readiness
  - **`code-centralization-consultant`**: Duplication detection, shared utility recommendations
- **Documentation & Spec Mode**:
  - **`accuracy-reviewer`**: Verifies factual correctness and catches contradictions
  - **`evidence-verifier`**: Cross-checks claims against attached logs, tests, or references
  - **`product-strategist`**: Evaluates alignment with product goals and user outcomes
  - **`delivery-ops`**: Checks operational feasibility, rollout risks, and support readiness
  - **`clarity-editor`**: Improves narrative flow, highlights ambiguous sections, ensures stakeholder readability
- **Operational Decision Mode**:
  - **`risk-analyst`**: Identifies blockers, severity, and mitigation paths
  - **`product-strategist`**: Confirms alignment with roadmap and KPIs
  - **`delivery-ops`**: Evaluates team capacity, timeline, and implementation complexity
  - **`customer-advocate`**: Represents user experience and support impact
  - **`exec-synthesizer`**: Creates concise go/no-go recommendations with rationale

### Enhanced Agent Context & Execution Framework

**Agent Infrastructure**: Uses existing `Task` tool with `subagent_type` parameter for parallel multi-agent coordination. Follows proven patterns from `/reviewdeep` and `/arch` commands with optimized execution orchestration. Claude must supply mode-specific prompts and evaluation criteria when launching each agent.

**Execution Guards**: Per-agent timeout (180 seconds), token caps (5000 tokens max), and maximum 10 findings per round to prevent runaway executions. Enhanced with context-aware resource allocation.

**Command Orchestration**: Delegates to `/execute` for intelligent coordination following `/reviewdeep` optimization patterns:

**Agent Execution**: Launch 5 agents in parallel using Task tool with 180-second timeout. Provide custom prompts per mode:

- **Code Review Mode**: Focus prompts on diff analysis, architecture correctness, high-impact bugs, and MVP launch risk.
- **Documentation & Spec Mode**: Direct agents to cross-reference claims with evidence, note missing validation, and highlight unclear reasoning or terminology.
- **Operational Decision Mode**: Ask agents to surface blockers, quantify risk, evaluate resource alignment, and recommend next steps.

**Solo MVP Context Applied to All Agents**:
- Pre-launch product with ZERO external users
- GitHub rollback safety available
- Focus on real bugs, architecture, factual accuracy, and serious security vulnerabilities only
- Skip enterprise security theater and theoretical concerns

**Implementation Details**:
- **`code-review`**: `Task(subagent_type="code-review", description="Architecture validation", prompt="...")`
- **`codex-consultant`**: `Task(subagent_type="codex-consultant", description="System design analysis", prompt="...")`
- **`gemini-consultant`**: `Task(subagent_type="gemini-consultant", description="Best practices review", prompt="...")`
- **`cursor-consultant`**: `Task(subagent_type="cursor-consultant", description="Practical reality check", prompt="...")`
- **`code-centralization-consultant`**: `Task(subagent_type="code-centralization-consultant", description="Duplication analysis", prompt="...")`

**Speed Optimizations**:
- **Parallel execution**: All agents run simultaneously (not sequential)
- **Early termination**: Stop on architectural blockers or critical bugs
- **Simple consensus**: Agents provide PASS/REWORK verdict with confidence (1-10)
- **Evidence required**: Findings must include file:line references
- **MVP Context**: GitHub rollbacks available, focus on architecture over security paranoia

## Fast Consensus Loop (3 Rounds Max)

Streamlined workflow optimized for speed and simplicity:

1. **Parallel Agent Consultation** (2-3 minutes)
   - Launch all 5 agents simultaneously using Task tool with full context
   - **Context Provided to Each Agent**:
     - Solo MVP project status (pre-launch, rollback safety available)
     - Current PR/branch context and file changes
     - Architecture focus over enterprise security concerns
     - GitHub rollback strategy as primary safety mechanism
     - 2025 best practices adapted for solo developer workflow
   - Each agent provides: PASS/REWORK + confidence (1-10) + specific issues
   - Early termination if any agent finds architectural blockers or critical bugs
   - Collect findings in structured format with file:line evidence
   - **Agent Context Awareness**: Each agent understands the working multi-agent system and MVP context

2. **Simple Consensus Calculation** (30 seconds)
   - **CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6
   - **CONSENSUS_REWORK**: 3+ agents REWORK OR average confidence <5
   - **MIXED_SIGNALS**: Document conflicts, proceed with majority decision

3. **Quick Fix Application** (If REWORK, 1-2 minutes)
   - Apply highest-confidence architectural fixes with clear file:line references
   - Skip complex remediation planning - fix obvious issues immediately
   - Document all changes made during this round

4. **Automated Test Validation** (1-3 minutes)
   - **Syntax Validation**: Quick linting/parsing checks
     ```bash
     # Auto-detect and run project-specific linters
     if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent 2>/dev/null | grep -q "lint"; then
       npm run lint
     elif command -v eslint >/dev/null 2>&1; then
       eslint .
     elif command -v flake8 >/dev/null 2>&1; then
       flake8 .
     elif command -v ruff >/dev/null 2>&1; then
       ruff check .
     else
       echo "No supported linter found - manual validation required"
     fi
     ```
   - **Unit Tests**: Focused tests for modified components
     ```bash
     # Auto-detect test framework and run relevant tests
     if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent 2>/dev/null | grep -q "test"; then
       npm test
     elif command -v vpython >/dev/null 2>&1; then
       env TESTING=true python -m pytest
     elif command -v python3 >/dev/null 2>&1; then
       env TESTING=true python3 -m pytest
     elif command -v python >/dev/null 2>&1; then
       env TESTING=true python -m pytest
     else
       echo "No recognized test runner found - manual validation required"
     fi
     ```
   - **Integration Tests**: If APIs/interfaces changed
     ```bash
     # Run integration test suite if available
     npm run test:integration \
       || ( [ -x ./run_tests.sh ] && ./run_tests.sh ) \
       || ( [ -x ./run_ui_tests.sh ] && ./run_ui_tests.sh mock )
     ```
   - **Manual Validation**: User-guided spot checks if automated tests insufficient

**Context-Aware Validation**:
- **Code Review Mode**:
  - **High Context**: Full test suite validation
  - **Medium Context**: Targeted test execution based on changed files
  - **Low Context**: Essential syntax and unit tests only
- **Documentation & Spec Mode**:
  - Corroborate claims against linked evidence, logs, and test artifacts
  - Highlight unsupported statements and request clarification or new experiments
  - Ensure timelines, metrics, and MCP/tool names match underlying data sources
- **Operational Decision Mode**:
  - Validate assumptions with available telemetry, user data, or roadmap docs
  - Stress-test mitigation plans and identify missing owners or follow-up actions
  - Confirm launch checklists or go/no-go criteria are satisfied

**Simplified Test/Validation Detection (Code Review Mode)**:
```bash

# Safe test command detection with proper validation
TIMEOUT_CMD=$(command -v timeout || command -v gtimeout)

run_with_timeout() {
  if [ -n "$TIMEOUT_CMD" ]; then
    "$TIMEOUT_CMD" "$@"
  else
    "$@"
  fi
}

if command -v npm >/dev/null 2>&1 && [ -f "package.json" ] && npm run --silent 2>/dev/null | grep -q "test"; then
    run_with_timeout 300 npm test
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    run_with_timeout 300 env TESTING=true python -m pytest 2>/dev/null || run_with_timeout 300 env TESTING=true python3 -m pytest
elif [ -f "run_tests.sh" ] && [ -x "run_tests.sh" ]; then
    run_with_timeout 300 ./run_tests.sh
else
    echo "No automated tests detected - skipping test validation"
fi

if [ -z "$TIMEOUT_CMD" ]; then
    echo "⚠️ Install GNU timeout (coreutils) for enforced timeouts (macOS: brew install coreutils)" >&2
fi
```

For documentation and decision scopes, replace automated tests with evidence checklists and explicit sign-off from responsible agents.

5. **Round Completion Decision**
   - **CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6 + validation complete for the selected mode
   - **CONSENSUS_REWORK**: 3+ agents REWORK OR validation gaps OR average confidence <5
   - **TEST_FAILURE_ABORT / VALIDATION_ABORT**: Critical test or evidence failures abort the round
   - **ROUND_LIMIT_REACHED**: Maximum 3 rounds completed

#### Consensus Calculation Rules:

- **✅ SUCCESS**: CONSENSUS_PASS achieved (workflow complete)
- **🔄 CONTINUE**: REWORK status + round < 3 + tests pass (next round)
- **❌ ABORT**: TEST_FAILURE_ABORT or critical agent blockers (stop immediately)
- **⚠️ LIMIT**: ROUND_LIMIT_REACHED (document remaining issues)

The loop stops immediately when a round achieves PASS status or after three rounds (whichever occurs first).

#### Early Termination Triggers:

- **✅ CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6 + validation complete
- **❌ CRITICAL_BUG**: Any agent reports severity 9-10 issue
- **❌ TEST_FAILURE / EVIDENCE_FAILURE**: Automated tests or evidence cross-checks fail
- **❌ COMPILATION_ERROR / EXECUTION_BLOCKER**: Code doesn't compile/parse or operational criteria can't be executed

## General Consensus Principles (2025 MVP Optimization)

- **Speed First**: Parallel execution, early termination, 3-round limit
- **Evidence Based**: All findings require references (file:line, document section, metric source) + confidence scores
- **Clear Thresholds**: PASS ≥6 confidence, REWORK <5 confidence, mixed signals documented
- **Mode-Aware Focus**: Tailor evaluation criteria to code quality, factual accuracy, or decision readiness
- **Practical Focus**: Fix or flag the highest-impact issues now, document lower-priority work for later
- **Basic Safety**: Filter obvious credentials, but don't over-engineer for solo MVP
- **GitHub Safety Net**: Easy rollbacks available for any problematic changes

## Output Format

```

# Consensus Review Report

## Summary

- Round count: <1-3>
- Final status: PASS | REWORK_LIMIT_REACHED | VALIDATION_ABORT
- Mode: Code Review | Documentation & Spec | Operational Decision
- Key validated areas

## Major Findings

| Round | Source Agent | File/Section/Artifact | Severity | Resolution |
|-------|--------------|------------------------|----------|------------|

## Implemented Fixes / Actions

- <bullet list of code updates, document edits, or operational decisions per round>

## Evidence & Validation Log

- Tests run / evidence cross-checked / stakeholders consulted

## Round-by-Round Summaries

- Round <n>: <main conversation highlights>
  - <agent name>: <key takeaways>

## Remaining Follow-Ups

- <nitpicks, deferred improvements, outstanding risks>
```
Include references to executed test commands, reviewed evidence files, and any required stakeholder approvals.

## 🛡️ Solo MVP Developer Focus

The solo MVP assumptions remain, but the emphasis shifts with each mode.

### **Code Review Mode Focus Areas**

- Architecture quality, real bugs, maintainability, integration issues
- Skip enterprise theater, complex compliance, and premature optimization

### **Documentation & Spec Mode Focus Areas**

- Factual accuracy, evidence traceability, clarity for stakeholders
- Flag unsupported claims, contradictory metrics, or missing validation
- Skip exhaustive copy edits unless they block comprehension

### **Operational Decision Mode Focus Areas**

- Launch risk, mitigation planning, stakeholder readiness
- Confirm owners, timelines, and fallback options
- Skip deep program-management artifacts unless the decision depends on them

## 🔧 Agent Prompt Structure (Implementation Details)

Following `/reviewdeep` and `/arch` patterns for proper agent context. Claude must adapt the templates per mode.

### **Enhanced Agent Prompt Template** (Mode-Aware Multi-Agent Analysis)

```markdown
[Agent Role] consensus analysis of [target] for solo MVP project context.

**ENHANCED CONTEXT FRAMEWORK**:
- **Project Type**: Solo MVP (pre-launch, GitHub rollbacks available for safety)
- **Current Scope**: [scope definition, e.g., PR details, document path, decision statement]
- **Infrastructure**: Working multi-agent consensus system using Task tool parallel execution
- **Agent Network**: Part of 5-agent consensus ([list selected agents])
- **Goal**: Fast consensus-building with 3-round maximum, early termination on agreement
- **Mode**: Code Review | Documentation & Spec | Operational Decision (pick one)

**ROLE-SPECIFIC CONTEXT SPECIALIZATION**:
- Outline what this agent must evaluate based on the chosen mode

**COMPREHENSIVE ANALYSIS FRAMEWORK**:
1. **Strategic Layer**: Architecture/design/product implications
2. **Tactical Layer**: Implementation details, factual accuracy, or operational feasibility
3. **Consensus Layer**: Inter-agent agreement consideration, conflict resolution
4. **Solo MVP Reality**: No team constraints, practical deployment focus, rollback safety net
5. **Speed Optimization**: Fast analysis with early termination on critical issues

**MODE-FOCUSED CHECKLIST**:
- Provide targeted bullet list (bugs/security for code, evidence/log links for docs, risks/mitigations for decisions)

**OUTPUT REQUIREMENTS FOR CONSENSUS**:
- Verdict: PASS/REWORK with confidence score (1-10)
- Evidence: Mode-appropriate references (file:line, section heading, metric source, stakeholder signal)
- Summary: 2-3 bullet highlights tailored to the mode
- Recommended next actions if verdict is REWORK
```

#### **`code-review` Agent Context**:

```markdown
**Summary**: Architecture correctness and maintainability gatekeeper for consensus rounds.

**Responsibilities**
- Audit diffs for structural regressions, SOLID violations, and high-severity bugs.
- Verify patterns, interfaces, and dependency boundaries support the MVP roadmap.
- Identify critical refactors that unblock safe shipping.

**Output Format**: PASS or REWORK with confidence (1-10) plus bullet evidence citing file:line.

**Example Prompt**:
Task(
  subagent_type="code-review",
  description="Architecture validation for PR #{PR_NUMBER}",
  prompt="""Focus on architecture flaws, SOLID violations, and correctness blockers. Cite file:line evidence for every finding."""
)
```

#### **`codex-consultant` Agent Context**:

```markdown
**Summary**: Scaling strategist ensuring the design supports future load without derailing MVP velocity.

**Responsibilities**
- Stress-test architecture for throughput, latency, and data integrity risks.
- Recommend pragmatic scalability upgrades (caching, queues, sharding) tied to roadmap milestones.
- Highlight distributed system anti-patterns introduced by the change.

**Output Format**: PASS or REWORK with confidence (1-10) plus quantified impact notes.

**Example Prompt**:
Task(
  subagent_type="codex-consultant",
  description="Scalability sweep for PR #{PR_NUMBER}",
  prompt="""Identify performance or scaling risks in this diff. Suggest lightweight fixes that keep the MVP shippable."""
)
```

#### **`gemini-consultant` Agent Context**:

```markdown
**Summary**: Modern frameworks and optimization advisor keeping the MVP aligned with 2025 standards.

**Responsibilities**
- Compare implementation against current best practices for the language/framework.
- Spot practical security, accessibility, and performance upgrades with high ROI.
- Recommend lightweight tooling or linting that prevents regressions.

**Output Format**: PASS or REWORK with confidence (1-10) plus concise best-practice gaps.

**Example Prompt**:
Task(
  subagent_type="gemini-consultant",
  description="Best-practice sweep for PR #{PR_NUMBER}",
  prompt="""List modern standards this change violates and actionable patches to align quickly."""
)
```

#### **`cursor-consultant` Agent Context**:

```markdown
**Summary**: Pragmatic deployment reviewer who ensures recommendations survive real-world constraints.

**Responsibilities**
- Challenge assumptions with rollout, monitoring, and incident response realities.
- Call out hidden toil, manual steps, or tooling gaps that block a solo ship.
- Verify the plan covers rollback, feature flags, and observability basics.

**Output Format**: PASS or REWORK with confidence (1-10) plus concrete deployment readiness notes.

**Example Prompt**:
Task(
  subagent_type="cursor-consultant",
  description="Deployment readiness scan for PR #{PR_NUMBER}",
  prompt="""List practical launch blockers (ops, tooling, failure modes). Recommend quick mitigations."""
)
```

#### **`code-centralization-consultant` Agent Context**:

```markdown
**Summary**: Duplication hunter driving shared utilities that cut future maintenance cost.

**Responsibilities**
- Detect overlapping logic, config, or tooling that should be centralized.
- Propose lightweight refactors that reduce drift without blocking delivery.
- Flag risks where divergence could introduce bugs or inconsistent behavior.

**Output Format**: PASS or REWORK with confidence (1-10) plus consolidation recommendations.

**Example Prompt**:
Task(
  subagent_type="code-centralization-consultant",
  description="Consolidation scan for PR #{PR_NUMBER}",
  prompt="""List duplication hotspots and suggest minimal shared abstractions to implement now."""
)
```

#### **`accuracy-reviewer` Agent Context**:

```markdown
**Summary**: Factual accuracy reviewer safeguarding trust in documentation and specs.

**Responsibilities**
- Cross-check every claim against attached evidence, logs, or test results.
- Flag contradictions, outdated metrics, and ambiguous terminology.
- Request missing citations or new validation work when proof is absent.

**Output Format**: PASS or REWORK with confidence (1-10) plus citation-ready evidence notes.

**Example Prompt**:
Task(
  subagent_type="accuracy-reviewer",
  description="Factual review for spec #{PR_NUMBER}",
  prompt="""List inaccurate or unproven statements and reference the evidence required to fix them."""
)
```

#### **`evidence-verifier` Agent Context**:

```markdown
**Summary**: Evidence auditor ensuring every assertion maps to verifiable artifacts.

**Responsibilities**
- Validate referenced logs, payloads, screenshots, and test results actually exist.
- Confirm data values in the doc match underlying sources and timestamps.
- Identify missing validation and recommend follow-up experiments.

**Output Format**: PASS or REWORK with confidence (1-10) plus evidence checklist updates.

**Example Prompt**:
Task(
  subagent_type="evidence-verifier",
  description="Evidence traceability review",
  prompt="""Confirm each claim cites a real artifact. List missing or outdated evidence with remediation steps."""
)
```

#### **`clarity-editor` Agent Context**:

```markdown
**Summary**: Clarity editor ensuring docs are immediately actionable for stakeholders.

**Responsibilities**
- Highlight ambiguous language, missing context, or unclear ownership.
- Suggest concise rewrites that improve readability without bloating the doc.
- Verify next steps, metrics, and timelines are obvious to the reader.

**Output Format**: PASS or REWORK with confidence (1-10) plus recommended rewrites.

**Example Prompt**:
Task(
  subagent_type="clarity-editor",
  description="Clarity pass for spec #{PR_NUMBER}",
  prompt="""Call out any sections that confuse stakeholders and propose sharper wording or structure."""
)
```

#### **`product-strategist` Agent Context** (shared across documentation/operational modes):

```markdown
**Summary**: Product strategist aligning decisions with roadmap impact and user value.

**Responsibilities**
- Evaluate how the proposal advances KPIs, user outcomes, and launch milestones.
- Surface trade-offs, opportunity costs, and sequencing implications.
- Recommend scope adjustments that maximize learning velocity.

**Output Format**: PASS or REWORK with confidence (1-10) plus KPI / roadmap rationale.

**Example Prompt**:
Task(
  subagent_type="product-strategist",
  description="Product alignment review",
  prompt="""Assess whether this work advances the current goal. Flag scope creep or missing success metrics."""
)
```

#### **`delivery-ops` Agent Context** (shared across documentation/operational modes):

```markdown
**Summary**: Delivery operator validating feasibility, owners, and rollout steps.

**Responsibilities**
- Check that owners, timelines, and dependencies are explicit and realistic.
- Verify tooling, environments, and runbooks exist for execution and support.
- Flag process or capacity gaps that would delay shipping.

**Output Format**: PASS or REWORK with confidence (1-10) plus readiness checklist results.

**Example Prompt**:
Task(
  subagent_type="delivery-ops",
  description="Delivery readiness review",
  prompt="""List missing owners, tooling gaps, or sequencing risks. Recommend fixes before launch."""
)
```

#### **`risk-analyst` Agent Context**:

```markdown
**Summary**: Risk analyst quantifying severity, likelihood, and mitigation coverage.

**Responsibilities**
- Enumerate credible failure modes, severity, and detection coverage.
- Confirm mitigations, owners, and rollback paths exist for each major risk.
- Recommend go/no-go posture based on residual risk tolerance.

**Output Format**: PASS or REWORK with confidence (1-10) plus risk table updates.

**Example Prompt**:
Task(
  subagent_type="risk-analyst",
  description="Risk register review",
  prompt="""List top risks with severity/likelihood, mitigation status, and whether launch is acceptable."""
)
```

#### **`customer-advocate` Agent Context**:

```markdown
**Summary**: Customer advocate translating technical changes into user and support impact.

**Responsibilities**
- Evaluate onboarding flow, messaging, and UX changes for confusion risks.
- Forecast support volume and tooling needs triggered by the release.
- Recommend mitigations (docs, in-app cues, FAQ updates) that preserve trust.

**Output Format**: PASS or REWORK with confidence (1-10) plus user-impact notes.

**Example Prompt**:
Task(
  subagent_type="customer-advocate",
  description="Customer impact review",
  prompt="""Explain how this change affects first-use experience and support. Suggest mitigations for any friction."""
)
```

#### **`exec-synthesizer` Agent Context**:

```markdown
**Summary**: Executive synthesizer producing crisp go/no-go decisions with rationale.

**Responsibilities**
- Summarize agent findings into a balanced recommendation and success criteria.
- Highlight unresolved risks, required follow-ups, and decision owners.
- Provide next-step checklist that keeps the solo developer unblocked.

**Output Format**: PASS or REWORK with confidence (1-10) plus executive summary bullets.

**Example Prompt**:
Task(
  subagent_type="exec-synthesizer",
  description="Decision synthesis",
  prompt="""Combine agent findings into a clear go/no-go call. List decisive evidence and required follow-ups."""
)
```

### **Dynamic Context Variables**

- `{PR_NUMBER}`: Auto-detected from current branch context (when applicable)
- `{FILE_LIST}`: From git diff and PR analysis (code mode)
- `{TARGET_SCOPE}`: User-specified scope or default context (files, docs, decisions)
- `{MVP_STAGE}`: Pre-launch, rollback-safe development phase
- `{AGENT_NETWORK}`: Selected 5-agent consensus roster for the chosen mode
- `{CONSENSUS_ROUND}`: Current round (1-3) in consensus-building process

## Post-Run Clean Up

1. Ensure working tree cleanliness (`git status --short`).
2. If changes were made, restate next steps (commit, push, or request manual review).
3. Update Memory MCP with consensus patterns and successful issue resolutions.
4. Note: GitHub rollbacks available if any issues discovered post-merge.
