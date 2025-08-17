# AI Development Guidelines - Mistake Prevention System

**Version**: 1.0  
**Created**: August 13, 2025  
**Purpose**: Prevent recurring mistakes in AI-assisted development through systematic guidelines  

## Scope & De-duplication
- This document is the canonical reference for mistake-prevention protocols. Do not duplicate its systematic protocols elsewhere; instead, link to this document to prevent drift.
- Command/orchestrator docs (e.g., `/plan`, `/execute`) should reference these guidelines rather than restating them.
- Related: See the "MISTAKE PREVENTION SYSTEM" block in [CLAUDE.md](../../CLAUDE.md#mistake-prevention-system).

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