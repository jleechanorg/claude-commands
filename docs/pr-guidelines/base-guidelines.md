# AI Development Guidelines - Mistake Prevention System

**Version**: 1.0
**Created**: August 13, 2025
**Purpose**: Prevent recurring mistakes in AI-assisted development through systematic guidelines

## 🚨 MANDATORY: CLAUDE.MD SYNC PROTOCOL

**⚠️ CRITICAL FIRST STEP**: Before applying any guidelines from this document, you MUST read the latest CLAUDE.md to refresh instructions and ensure alignment with current project protocols.

**REQUIRED WORKFLOW**:
1. **ALWAYS READ CLAUDE.md FIRST** - Located at project root: `CLAUDE.md`
2. **SYNC INSTRUCTIONS** - Verify current protocols, file creation rules, and project-specific requirements
3. **APPLY BASE GUIDELINES** - Use this document's patterns in conjunction with CLAUDE.md mandates
4. **RESOLVE CONFLICTS** - CLAUDE.md rules take precedence over any conflicting guidance in this document

**Why This Matters**:
- CLAUDE.md contains live project rules that evolve rapidly
- File creation protocols and branch-specific requirements change frequently
- This document provides stable patterns; CLAUDE.md provides current enforcement rules
- Outdated instruction alignment causes protocol violations and workflow breaks

## Scope & De-duplication
- This document is the canonical reference for mistake-prevention protocols. Do not duplicate its systematic protocols elsewhere; instead, link to this document to prevent drift.
- Command/orchestrator docs (e.g., `/plan`, `/execute`) should reference these guidelines rather than restating them.
- Related: See the "MISTAKE PREVENTION SYSTEM" block in [CLAUDE.md](../../CLAUDE.md#mistake-prevention-system).

---

## 🎯 Sky's Architecture Principles

### PERSONA: ARCHITECT

**Key Principles:**
- Ship simple, working code
- Be direct and honest
- Challenge assumptions
- No guesswork or assumptions

**Critical Rules:**

#### 1. No Assumptions
- Must READ actual files
- ASK for clarification
- Request debug logs
- Never guess about code or business logic

#### 2. Underlying Issues
- Stop and explain root causes
- Offer quick patch vs. proper fix options
- Always ask before implementing patches

#### 3. Never Change UX
- Preserve user experience
- Find technical solutions that maintain intended design

#### 4. File Organization Standards
- **Do not add files to project root** - Use appropriate subdirectories
- **Do not make new test files unless none exist** - One test file per code file pattern
- **No inline imports** - All imports at module level
- **Look for existing functionality first** - Modify before adding new code paths

#### 5. Directory Context Awareness
- **Always specify directory when reporting git status across multiple repositories**
- **Never say "we are on branch X" when operating across different repositories**
- **Use clear language**: "In my working directory: /path/A (branch: X)" vs "In your directory: /path/B (branch: Y)"
- **Never mix up git status between different repositories** - causes confusion and wrong commands

**Code Priorities (in order):**
1. Pragmatic
2. Concise/DRY
3. Maintainable
4. Robust
5. Elegant
6. Performant

**Key Guidelines:**
- Prefer 3 lines over 30 lines
- Use boring tech over clever solutions
- Fix root causes, not symptoms
- Stop if implementation exceeds 50 lines

**Code Review Checklist:**
- Can this be simplified?
- Remove dead code
- Would this make sense at 3am?

**Fundamental Motto:** "Every line of code is a liability. Minimize liabilities while maximizing shipped value."

---

## 🎯 Core Principles

### 1. **Evidence-Based Development**
- ALWAYS verify current state before making changes
- Extract exact error messages and code snippets before analyzing
- Show actual output before suggesting fixes
- Reference specific line numbers in all analysis
- Never assume file contents from filenames or process names

### 2. **Systematic Change Management**
- ONE change per PR for clarity and easier review
- Create atomic, testable changes that can be validated independently
- Preserve backward compatibility unless explicitly breaking
- Test all changes before committing

### 3. **Resource-Efficient Operations**
- Use Serena MCP for semantic code analysis before reading entire files
- Apply targeted operations with filtering instead of bulk processing
- Monitor context consumption and checkpoint strategically
- Batch tool calls for parallel execution when appropriate

### 4. **Hybrid Code Generation with /qwen**
- **ARCHITECT-BUILDER Pattern**: Claude designs specifications, /qwen builds at 19.6x speed
- **Decision Documentation**: Log all /qwen vs Claude decisions in `docs/{branch}/qwen_decisions.md`
- **Smart Delegation**: Use /qwen for well-specified generation, Claude for understanding/integration
- **Learning Loop**: Review qwen_decisions.md regularly to optimize task delegation patterns

---

## 🏛️ Development Tenets

### 1. **Composition Over Duplication**
**Belief**: Reuse and orchestrate existing functionality rather than reimplementing

**Practice**:
- Use existing `/commentreply`, `/pushl`, `/fixpr` commands vs duplicating logic
- Enhance existing systems before building parallel new ones
- Trust LLM capabilities for natural language understanding vs building parsers

### 2. **Real Implementation Over Fake Placeholders**
**Belief**: Better to not implement than to create fake/placeholder code

**Practice**:
- Audit existing functionality before implementing new code
- Build functional code that integrates with existing systems
- If you can't implement properly, don't create the file at all

### 3. **Direct Solutions Over External Dependencies**
**Belief**: Prefer Claude's native capabilities over external API integrations

**Practice**:
- Ask "Can Claude solve this directly?" before adding external APIs
- Only use Gemini API when Claude lacks specific capabilities
- Implement direct solutions before justifying external integrations

### 4. **Evidence Over Speculation**
**Belief**: Primary evidence trumps agent findings and speculation

**Trust Hierarchy**:
1. Configuration files and system state
2. Logical analysis based on architecture
3. User direct evidence and observations
4. Agent/tool findings (require validation)

---

## 🎯 Quality Goals

### 1. **Zero False Implementations**
- No placeholder code in production
- No simulated intelligence using templates
- No hardcoded response patterns claiming to be "LLM-native"
- All code must provide real, functional value

### 2. **Context Optimization**
- Keep context usage under 60% for sustainable operations
- Use Serena MCP semantic tools before reading entire files
- Implement targeted operations with proper filtering
- Strategic checkpointing for large operations

### 3. **Testing Excellence**
- 100% test pass rate - no "pre-existing issues" excuses
- Fix ALL failing tests when asked
- Visual validation of end-to-end data flow
- Verify actual integration vs isolated component testing

---

## 🚫 Anti-Patterns & Common Mistakes

### **Slash Command Understanding Mistakes**

#### ❌ **Incorrect Assumptions About Command Execution**
```bash
# WRONG - Assuming all cross-command references are documentation
/plan "says it calls /guidelines but it's just documentation"

# WRONG - Assuming no commands actually call other commands
/copilot "only documents workflow, doesn't execute"
```

#### ✅ **Correct Understanding**
```bash
# CORRECT - Two distinct patterns exist:
1. Universal Composition: /copilot → /execute → orchestrates other commands
2. Embedded Implementation: /commentcheck embeds GitHub API calls directly

# CORRECT - Test actual execution to verify pattern
- /copilot DOES call other commands through /execute delegation
- /commentcheck embeds functionality instead of calling /commentfetch
- /plan was fixed to embed /guidelines functionality directly
```

#### 🔍 **Verification Method**
- **Always test**: Execute commands to observe actual behavior
- **Don't assume**: Cross-command references could be documentation OR execution
- **Pattern recognition**: Universal composition vs embedded implementation
- **Evidence-based**: Use actual execution results to determine pattern

### **Converge Autonomy Violations**

#### ❌ **CRITICAL: Progress Celebration Syndrome**
```bash
# WRONG - Stopping after partial progress for user acknowledgment
/converge "complete all tests" → T2.1 complete → STOP → wait for user praise

# WRONG - Treating individual milestones as stopping points
Goal: 20 tests → Complete 1 test → "Look what I did!" → PAUSE

# WRONG - Mixing progress reporting with approval requests
"T2.1 completed successfully! [IMPLIED: waiting for user to say continue]"
```

#### ✅ **Correct Autonomous Behavior**
```bash
# CORRECT - Continuous execution until goal fully achieved
/converge "complete all tests" → T2.1 complete → validate (30% done) → continue T2.2 immediately

# CORRECT - Progress reporting without stopping
"T2.1 completed (1/15 remaining). Continuing to T2.2..."

# CORRECT - Autonomy preservation
Report progress → Continue execution → No user intervention until 100% or max iterations
```

#### 🚨 **Critical Prevention Rules**
- **Never stop**: /converge continues until goal 100% achieved or max iterations
- **Progress ≠ Approval**: Report progress but never wait for permission
- **Autonomy boundary**: Zero user intervention after goal statement
- **Mental model**: "Set and forget" not "step-by-step approval system"

### **File Operation Mistakes**

#### ❌ **Creating Unnecessary Files**
```bash
# WRONG - Creating backup/version files
file_v2.sh, file_backup.sh, file_new.sh

# WRONG - Creating temp/duplicate files
temp_implementation.py, duplicate_logic.js
```

#### ✅ **Correct Approach**
```bash
# RIGHT - Edit existing files in place
Edit existing file using Edit/MultiEdit tools
Use git branches for experimental changes
Trust git for version control and rollback
```

### **File Justification Protocol**

**Authoritative Source**: See [CLAUDE.md File Justification Protocols](../../CLAUDE.md#-critical-file-justification--creation-protocol)

**Key Anti-Pattern**: Creating new files without proving integration into existing files is impossible.

**Essential Rule**: Follow CLAUDE.md's integration-first workflow and extreme anti-creation bias. Any Write tool usage must answer the 4 mandatory justification questions defined in CLAUDE.md before file creation.

### **Analysis Mistakes**

#### ❌ **Assuming File Contents**
```bash
# WRONG - Using bash commands for analysis
cat file.py | grep "pattern"
head -n 10 config.json

# WRONG - Assuming contents from context
# File named "test_X" must contain tests for X
# Process output shows "server.py" so it must be the main server
```

#### ✅ **Correct Approach**
```bash
# RIGHT - Always use Read tool for file analysis
Read tool to examine actual file contents
Verify actual file contents before drawing conclusions
Check configuration files for system behavior
```

### **Implementation Mistakes**

#### ❌ **Fake Intelligence Simulation**
```python
# WRONG - Simulating Claude responses with templates
def generate_response(prompt):
    templates = {
        "code_review": "Code looks good!",
        "bug_fix": "Fixed the issue!"
    }
    return templates.get(prompt_type, "Generic response")

# WRONG - Hardcoded keyword matching as "LLM-native"
if "test" in task:
    return "testing-agent"
```

#### ✅ **Correct Approach**
```python
# RIGHT - Invoke actual Claude for responses
def generate_response(prompt):
    result = claude_api.chat(prompt)
    return result.content

# RIGHT - Use actual LLM API calls for analysis
def classify_task(task):
    response = llm_api.analyze(task, context=capabilities)
    return response.classification
```

### **Import Mistakes**

#### ❌ **Inline and Try-Catch Imports**
```python
# WRONG - Inline imports inside functions
def process_data():
    import pandas as pd  # WRONG - Should be at module level
    return pd.DataFrame()

# WRONG - Try-catch imports for optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False  # WRONG - Hides dependency issues

# WRONG - Conditional imports in function scope
def analyze():
    if USE_ADVANCED:
        import scipy  # WRONG - Import at function level
        return scipy.optimize()
```

#### 🚨 **CRITICAL: Import Validation IMP002 Violations**

**Rule:** ALL imports must be at the absolute top of file with ZERO intervening code.

**Root Cause:** Import validator flags ANY non-import statement (including `sys.path.insert()`) as making subsequent imports "inline violations."

```python
# WRONG - Even sys.path setup breaks the rule
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))  # ← This triggers IMP002!
from local_modules import Class                 # ← Flagged as "inline import"
```

**SOLUTION:** Centralized path setup in package `__init__.py`:

```python
# In orchestration/__init__.py:
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

# In individual modules - NO path manipulation:
import standard_modules
from local_modules import LocalClass  # ← Clean imports only
```

#### ✅ **Correct Approach**
```python
# RIGHT - All imports at module level
import pandas as pd
import numpy as np  # Fail fast if missing
from typing import Optional

# RIGHT - Use proper dependency management
# If numpy is optional, handle in requirements.txt or setup.py
# Not with try-catch imports

# RIGHT - Imports always at top, use feature flags for logic
import scipy.optimize

def analyze():
    if USE_ADVANCED:
        return scipy.optimize.minimize(...)
    return basic_analysis()
```

**Key Learning (2025-09-08):** Import validators are EXTREMELY strict - even necessary path setup code triggers violations. Centralized path management in `__init__.py` is the only compliant solution.

### **Tool Usage Mistakes**

#### ❌ **Wrong Tool Selection**
```bash
# WRONG - Using bash for file content analysis
bash: cat large_file.py  # Should use Read tool
bash: grep pattern *.js  # Should use Grep tool

# WRONG - Duplicating functionality
# Creating new /myreview command instead of enhancing /review
```

#### ✅ **Correct Approach**
```bash
# RIGHT - Use appropriate tools for each task
Read tool for file content examination
Grep tool for pattern searching across files
Enhance existing commands vs creating duplicates
```

---

## 📋 Specific Patterns & Examples

### **Terminal Session Safety**

#### ❌ **Dangerous Exit Patterns**
```bash
#!/bin/bash
if [ ! -d "$REQUIRED_DIR" ]; then
    echo "Error: Directory not found"
    exit 1  # WRONG - Terminates user's terminal
fi
```

#### ✅ **Safe Error Handling**
```bash
#!/bin/bash
if [ ! -d "$REQUIRED_DIR" ]; then
    echo "Error: Directory not found"
    echo "Press Enter to continue in fallback mode..."
    read -r
    # Continue with graceful fallback
    # Note: use 'return 1' only inside a sourced script/function. In standalone scripts, prefer structured error handling without terminating the user's shell session unexpectedly. If termination is required, use 'exit 1' and document the behavior.
    return 1  # valid only when sourced / inside a function
fi
```

### **PR Comment Integration**

#### ❌ **Missing GitHub Integration**
```python
# WRONG - Generating review but not posting
def review_code(pr_files):
    analysis = analyze_files(pr_files)
    print(f"Found {len(analysis.issues)} issues")
    return analysis  # Never posted to GitHub
```

#### ✅ **Complete GitHub Integration**
```python
# RIGHT - Always post review comments
def review_code(pr_number):
    analysis = analyze_files(get_pr_files(pr_number))

    # Post inline comments
    for issue in analysis.issues:
        github_api.post_review_comment(
            pr_number, issue.file, issue.line,
            f"[AI reviewer] {issue.severity} {issue.message}"
        )

    # Post summary comment
    github_api.post_pr_comment(pr_number, analysis.summary)
    return analysis
```

### **Subprocess Safety**

#### ❌ **Security Vulnerabilities**
```python
# WRONG - Shell injection risk
subprocess.run(f"git {user_input}", shell=True)

# WRONG - Missing timeout
subprocess.run(["git", "fetch"], check=True)

# WRONG - Silent failures
result = subprocess.run(["git", "status"])
if result.returncode != 0:
    return "unknown"  # Silent failure - error information lost
```

#### ✅ **Secure Subprocess Usage**
```python
# RIGHT - Safe subprocess calls
subprocess.run(
    ["git", "fetch"],
    shell=False,
    timeout=30,
    check=True
)

# RIGHT - Explicit error handling
try:
    result = subprocess.run(
        ["git", "status"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True
    )
    return result.stdout
except subprocess.CalledProcessError as e:
    raise GitError(f"Git status failed: {e.stderr}")
# Note: subprocess.run with timeout can also raise subprocess.TimeoutExpired.
# Consider handling TimeoutExpired for completeness:
# except subprocess.TimeoutExpired as e:
#     raise GitError(f"Git status timed out: {e}")
```

---

## 📚 Historical Mistake Analysis

### **PR #1285 - Terminal Exit Issue**
**Problem**: create_worktree.sh used `exit 1` which terminated user's terminal session
**Solution**: Changed to graceful navigation with return codes
**Learning**: Scripts must preserve user's terminal session control
**Pattern**: Use graceful error handling vs terminal exit

### **PR #1283 - Payload Size Limits**
**Problem**: Hardcoded 100KB limit caused failures with complex game states (105KB)
**Solution**: Increased to 10MB with proper headroom analysis
**Learning**: Size limits should account for real-world data growth
**Pattern**: Set limits with generous headroom based on actual usage

### **PR #1282 - Documentation Compression**
**Problem**: CLAUDE.md became too large (64K chars) affecting readability
**Solution**: Systematic compression to 40K chars while preserving functionality
**Learning**: Documentation size impacts usability and must be managed
**Pattern**: Compress without losing critical information

### **PR #1277 - Command Documentation Clarity**
**Problem**: /reviewdeep documentation unclear about actual execution vs conceptual composition
**Solution**: Explicit execution flow documentation with step-by-step protocols
**Learning**: Command documentation must clearly state what gets executed
**Pattern**: Document actual behavior, not conceptual models

### **PR #1275 - Inconsistent Comment Attribution**
**Problem**: Review commands used different comment author tags ([Code Reviewer] vs [AI reviewer])
**Solution**: Standardized all commands to use [AI reviewer] tag
**Learning**: Consistent attribution across related commands improves user experience
**Pattern**: Standardize related functionality for consistency

---

## ⚡ Common Performance Mistakes

### **Context Consumption**
- Reading entire large files instead of using Serena MCP semantic tools
- Not using targeted operations with proper filtering
- Missing strategic checkpoints in large operations
- Failing to batch parallel tool calls

### **Resource Management**
- Creating unnecessary backup files instead of trusting git
- Not cleaning up temporary resources in error paths
- Missing timeout enforcement in subprocess calls
- Inefficient sequential operations that could be parallelized

### **Tool Selection**
- Using Bash commands for file analysis instead of Read tool
- Using individual commands instead of appropriate composition commands
- Not leveraging existing specialized commands before building new ones

### **Helper Function Extraction for Code >100 Delta Lines** {#helper-functions}

**Core Principle**: When adding new code >100 delta lines, extract into helper functions to maintain readability and reusability.

**Extraction Rules**:
- **Threshold**: Code blocks >100 delta lines MUST be extracted into helper functions/scripts
- **Location**: Place helper functions in `scripts/` directory for shell scripts, or appropriate module directory for Python
- **Naming**: Use descriptive names that clearly indicate the function's purpose
- **Documentation**: Include header comments with purpose, usage, and parameters

**Examples**:
```bash
# WRONG - 100+ lines inline in workflow file
"import-validation-delta")
  echo "Running validation..."
  # 30+ lines of bash code here...
  ;;

# RIGHT - Extract to helper script
"import-validation-delta")
  ./scripts/validate_imports_delta.sh
  ;;
```

**Benefits**:
- Improved workflow file readability
- Reusable logic across multiple contexts
- Easier testing and maintenance of complex logic
- Better separation of concerns

### **Tool Selection Criteria & Validation** {#tool-selection}

**Selection Hierarchy** (apply top-down):
1. **Serena MCP** - Semantic/code-aware analysis before full-file reads
2. **Read tool** - File contents; **Grep tool** - Pattern search; avoid Bash for content inspection
3. **Edit/MultiEdit** - In-place changes; avoid creating backup/duplicate files
4. **Task orchestration** - Parallelizable sub-work, otherwise sequential
5. **Bash** - OS-level operations only (not content analysis)

**Validation Workflow**:
- **Planning (/plan)**: Display chosen tools with justification against the hierarchy
- **Execution (/execute)**: Confirm adherence; flag deviations with rationale
- **Review**: Check plan/execution displays for compliance; deviations require explicit approval

**Enforcement**:
- TodoWrite must include "Guidelines validation" (tools chosen per hierarchy)
- CI/docs checks may grep for the validation line in plan/execute outputs

---

## 🔧 Implementation Guidelines

### **Before Making Changes**
1. **Verify Current State**: Read actual files, check configuration, examine system state
2. **Check Existing Solutions**: Search for existing implementations before creating new ones
3. **Plan Systematically**: Use TodoWrite for complex tasks, break into atomic steps
4. **Consider Context**: Monitor context usage, optimize for resource efficiency

### **During Implementation**
1. **Use Appropriate Tools**: Read tool for files, Grep for patterns, Serena MCP for semantic analysis
2. **Implement Incrementally**: Make atomic changes that can be tested independently
3. **Handle Errors Explicitly**: No silent failures, specific error messages with context
4. **Preserve Safety**: No terminal exits, proper resource cleanup, timeout enforcement

### **After Implementation**
1. **Test Thoroughly**: 100% test pass rate, visual validation of end-to-end flows
2. **Verify Integration**: Check actual system behavior, not just component testing
3. **Document Evidence**: Reference specific line numbers, include exact error messages
4. **Update Guidelines**: Add new patterns to this document when discovered

---

## 📊 Success Metrics

### **Code Quality Indicators**
- Zero test failures after changes
- No silent fallback patterns in error handling
- All subprocess calls include timeouts and proper error handling
- No file operations assume contents without verification

### **Integration Quality Indicators**
- All review commands post actual GitHub comments
- Configuration files accurately reflect system behavior
- End-to-end workflows complete successfully
- No placeholder or fake implementations in production

### **Efficiency Indicators**
- Context usage stays under 60% for sustainable operations
- Operations use appropriate tool selection (Serena MCP vs Read tool)
- Parallel operations used where beneficial
- No unnecessary file creation (use editing instead)

---

## 🔄 Continuous Improvement

### **Learning Process**
1. **Document Mistakes**: Add new patterns to this document immediately when discovered
2. **Update Anti-Patterns**: Include specific examples from actual incidents
3. **Enhance Guidelines**: Refine principles based on recurring issue patterns
4. **Share Knowledge**: Use Memory MCP to persist learnings across sessions

### **Review Integration**
- All `/plan` and `/execute` commands should reference these guidelines
- Code review agents should check for these anti-patterns
- CLAUDE.md should link to this document for comprehensive guidance
- New patterns should be captured and added systematically

---

**Usage**: This document should be consulted by all AI agents before implementing changes, referenced in planning phases, and updated when new mistake patterns are identified.
