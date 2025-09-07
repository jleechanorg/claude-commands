# PR #1559 Guidelines - feat: Add Gemini CLI and Codex CLI subagents for enhanced code review

**PR**: #1559 - [feat: Add Gemini CLI and Codex CLI subagents for enhanced code review](https://github.com/jleechanorg/worldarchitect.ai/pull/1559)
**Created**: September 7, 2025
**Purpose**: Guidelines for external AI consultation agent integration patterns

## Scope
- This document contains PR-specific patterns, evidence, and decisions for PR #1559.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### 1. **Plugin Architecture for AI Integration**
External AI tools should be integrated using a plugin/agent architecture that maintains system stability even when external dependencies fail.

### 2. **Security-First External Tool Integration**
All external CLI tools must use sandboxing, timeout controls, and graceful error handling to prevent system compromise or resource exhaustion.

### 3. **Solo Developer Extensibility**
AI consultation patterns should be easily extensible by solo developers without complex infrastructure requirements.

### 4. **Parallel Execution with Fallback**
External consultations should run in parallel for efficiency while maintaining system functionality when individual consultants fail.

## 🚫 PR-Specific Anti-Patterns

### ❌ **Unsafe External CLI Integration**
```bash
# WRONG - No sandboxing, no timeout, poor error handling
gemini "analyze this code: $USER_INPUT"
result=$(codex analyze)
if [ $? -ne 0 ]; then
    exit 1  # Breaks entire workflow
fi
```

**Problems:**
- No sandbox isolation for external tools
- No timeout controls for external API calls
- User input directly interpolated into commands
- Hard failure breaks entire review workflow
- No consideration for missing external tools

### ✅ **Secure External CLI Integration Pattern**
```bash
# RIGHT - Proper sandboxing, timeout, graceful error handling
if timeout 300s gemini -p "You are a senior software engineer conducting analysis.
Do not write code - provide analysis only.
[structured prompt with redacted context]"; then
    echo "✅ Gemini consultation completed successfully"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⏰ GEMINI CONSULTATION TIMEOUT: External consultation exceeded 5-minute limit"
    elif [ $exit_code -eq 127 ]; then
        echo "🚫 GEMINI CLI NOT FOUND: gemini command not available on system"
    else
        echo "💥 GEMINI CONSULTATION ERROR: Command failed with exit code $exit_code"
    fi
    echo "⚠️ Proceeding without external Gemini analysis"
fi
```

**Correct Patterns:**
- Explicit timeout controls (300s) prevent indefinite hangs
- Detailed error code handling with user-friendly messages  
- Graceful degradation - workflow continues despite external failures
- Structured prompts with clear instructions and context boundaries
- Sandbox enforcement for tools that support it

### ❌ **Hardcoded Configuration in Agent Logic**
```markdown
# WRONG - Hardcoded timeouts and command flags in agent definitions
timeout 300s gemini -p "analysis prompt"
timeout 300s codex exec --sandbox read-only "analysis prompt"
```

**Problems:**
- Timeout values not configurable per environment
- Command flags scattered across multiple agent definitions
- No way to adjust resource limits without editing agent files
- Difficult to tune performance based on actual usage patterns

### ✅ **Externalized Configuration Pattern**
```markdown
# RIGHT - Configuration externalization for maintenance
timeout ${GEMINI_TIMEOUT:-300}s gemini -p "analysis prompt"
timeout ${CODEX_TIMEOUT:-300}s codex exec --sandbox read-only "analysis prompt"
```

**Benefits:**
- Environment-specific timeout configuration
- Easy performance tuning without code changes
- Consistent configuration management across agents
- Solo developer can optimize based on their infrastructure

### ❌ **Duplicated Error Handling Logic**
```bash
# WRONG - Identical error handling in multiple agents
# gemini-consultant.md
if timeout 300s gemini -p "$prompt"; then
    echo "✅ Gemini consultation completed"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⏰ TIMEOUT"
    elif [ $exit_code -eq 127 ]; then
        echo "🚫 NOT FOUND"
    fi
fi

# codex-consultant.md  
if timeout 300s codex exec --sandbox read-only "$prompt"; then
    echo "✅ Codex consultation completed"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⏰ TIMEOUT"
    elif [ $exit_code -eq 127 ]; then
        echo "🚫 NOT FOUND"
    fi
fi
```

### ✅ **Centralized Error Handling Pattern**
```bash
# RIGHT - Shared error handling function
handle_external_tool_error() {
    local tool_name="$1"
    local exit_code="$2"
    
    if [ $exit_code -eq 124 ]; then
        echo "⏰ ${tool_name^^} CONSULTATION TIMEOUT: External consultation exceeded limit"
    elif [ $exit_code -eq 127 ]; then
        echo "🚫 ${tool_name^^} CLI NOT FOUND: ${tool_name} command not available"
    else
        echo "💥 ${tool_name^^} CONSULTATION ERROR: Command failed with exit code $exit_code"
    fi
    echo "⚠️ Proceeding without external ${tool_name} analysis"
}

# Usage in agents
if timeout 300s gemini -p "$prompt"; then
    echo "✅ Gemini consultation completed successfully"
else
    handle_external_tool_error "gemini" $?
fi
```

## 📋 Implementation Patterns for This PR

### 1. **Agent-Based Consultation Architecture**
- Create self-contained agent definitions in `.claude/agents/`
- Each agent has single responsibility (Gemini: multi-dimensional, Codex: deep analysis)
- Agents integrate into existing command workflows without breaking changes
- Plugin pattern enables future AI consultant additions

### 2. **Comprehensive Context Gathering Protocol**
```markdown
### 1. Gather Complete Context
**MANDATORY Context Collection**:
- **Read PR Description**: Use GitHub MCP to get full PR details
- **Read Changed Files**: Examine all modified, added, deleted files  
- **Read Related Files**: Identify and read dependent/imported files
- **Read Configuration**: Check relevant configs, requirements, etc.
- **Read Tests**: Review existing and new test files
- **Read Documentation**: Check README, API docs, inline documentation
```

**Benefits:**
- Consistent context gathering across all AI consultants
- Comprehensive understanding enables better analysis
- Structured approach prevents missing critical context
- Template ensures all consultants have necessary information

### 3. **Multi-Stage Analysis Framework**
```markdown
## Multi-Stage Analysis Framework:

### Stage 1 - Deep Logic Analysis:
- Control flow validation and edge case identification
- Data flow tracking and state management verification
- Boundary condition analysis and error handling assessment

### Stage 2 - Security Vulnerability Analysis:  
- OWASP Top 10 vulnerability patterns
- Input validation and sanitization gaps
- Authentication and authorization flow verification

### Stage 3 - Performance and Resource Analysis:
- Algorithmic complexity assessment (time/space)
- Memory leak and resource cleanup validation
- Database query efficiency and N+1 problem detection

### Stage 4 - Architectural Quality Review:
- SOLID principles adherence verification
- Design pattern implementation assessment
- Module coupling and cohesion analysis
```

**Benefits:**
- Systematic analysis approach ensures comprehensive coverage
- Structured stages prevent missing critical analysis dimensions
- Consistent methodology across different AI consultants
- Professional-grade review depth matching industry standards

## 🔧 Specific Implementation Guidelines

### 1. **External Tool Security Checklist**
✅ **MANDATORY Before Integration:**
- [ ] Sandbox enforcement for all CLI tools (prefer read-only)
- [ ] Timeout controls to prevent resource exhaustion  
- [ ] Graceful error handling that doesn't break parent workflow
- [ ] Input sanitization and secret redaction in prompts
- [ ] Static command construction (no dynamic interpolation)
- [ ] Clear, actionable error messages without information leakage

### 2. **Agent Definition Standards**
✅ **Required Sections:**
- [ ] Clear agent description with usage examples
- [ ] CRITICAL REQUIREMENT section mandating CLI tool usage
- [ ] Comprehensive context gathering protocol
- [ ] Multi-stage analysis framework
- [ ] Proper error handling template with timeout
- [ ] Integration notes for workflow composition

### 3. **Performance Optimization Guidelines**
✅ **Resource Management:**
- [ ] Parallel execution where appropriate (Track B integration)
- [ ] Configurable timeout values with reasonable defaults
- [ ] Context gathering efficiency (avoid redundant reads)
- [ ] Resource cleanup in error scenarios
- [ ] Benchmarking considerations for timeout tuning

### 4. **Solo Developer Maintenance Requirements**
✅ **Maintainability Standards:**
- [ ] Self-contained agent definitions in markdown
- [ ] Clear troubleshooting guidance in error messages
- [ ] No complex code dependencies requiring specialized knowledge
- [ ] Comprehensive documentation with usage examples
- [ ] Extensible patterns for future AI consultant additions

## 📚 Key Lessons Learned

### 1. **External Dependencies Need Graceful Degradation**
**Evidence**: Codex consultation failed with 404 errors during review, but system continued successfully.
**Learning**: Always design external integrations to fail gracefully without compromising core functionality.
**Pattern**: `⚠️ Proceeding without external [tool] analysis` messaging pattern works well.

### 2. **Security Through Sandboxing is Essential**
**Evidence**: `codex exec --sandbox read-only` prevents file system modifications.
**Learning**: External AI tools must be constrained to analysis-only operations for security.
**Pattern**: Always investigate and use sandbox options for external CLI tools.

### 3. **Plugin Architecture Scales Well**
**Evidence**: Two different AI consultants integrated cleanly into existing workflow.
**Learning**: Agent-based patterns make it easy to add new AI consultants without system changes.
**Pattern**: `.claude/agents/[tool]-consultant.md` convention works well for organization.

### 4. **Comprehensive Context Gathering Improves Quality**
**Evidence**: Both agents use detailed context collection protocols for better analysis.
**Learning**: AI consultants need complete context to provide valuable insights.
**Pattern**: Mandatory context collection with structured prompts ensures consistency.

### 5. **Error Handling Code Should Be Centralized**
**Evidence**: Nearly identical error handling logic in both agent definitions.
**Learning**: DRY principle applies to error handling patterns across agents.  
**Pattern**: Extract common error handling into shared functions/templates.

---
**Status**: Active guidelines based on PR #1559 implementation
**Last Updated**: September 7, 2025
**Next Review**: After production usage feedback