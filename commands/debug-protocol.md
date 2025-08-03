# Debug Protocol Command

**Usage**: `/debug-protocol [issue description]` or `/debugp [issue description]` (alias)

**Purpose**: Apply comprehensive forensic debugging methodology for complex issues requiring systematic evidence gathering, hypothesis validation, and documented root cause analysis.

## 🔬 Research-Backed Methodology

Based on software engineering research showing:
- **30% faster troubleshooting** with structured approaches vs ad-hoc debugging
- **80% bug detection** with validation-before-fixing methodologies
- **60% defect reduction** with systematic validation processes
- **Evidence-driven debugging** shows measurable improvement over intuition-based approaches

## 🛠️ DEBUGGING PROTOCOL ACTIVATED 🛠️

### Phase 0: Context & Evidence Gathering
**[Critical] Reproduction Steps:** Describe the exact, minimal steps required to reliably trigger the bug.
- **Example Format:**
  1. Login as admin user
  2. Navigate to `/dashboard`
  3. Click the "Export" button
  4. Observe the error message displayed

**[High] Observed vs. Expected Behavior:**
- **Observed:** [e.g., "API returns 500 when user is admin"]
- **Expected:** [e.g., "API should return 200 with user data"]

**[Medium] Impact:** Describe the user/system impact [e.g., "Critical data loss," "UI crashes for all users," "Performance degradation on admin dashboard"]

**[Low] Last Known Working State:** [e.g., "Commit hash `a1b2c3d`," "Worked before the 2.4.1 deployment"]

**⚠️ Relevant Code Snippets (REDACTED):**
```language
// ⚠️ REDACT sensitive data (API keys, passwords, PII, database connection strings, internal URLs, user IDs, session tokens, and other sensitive identifiers) from code. Use [REDACTED] as a placeholder.
[Paste code here]
```

**⚠️ Error Message / Stack Trace (REDACTED):**
```
// ⚠️ REDACT all sensitive data from logs.
[Paste logs here]
```

**Summary Checkpoint:** Before proceeding, clearly restate the problem using the evidence above.

### Phase 1: Research & Root Cause Analysis

**🔬 Research Phase (for complex/novel issues):**
For complex issues, unknown technologies, or patterns requiring broader investigation, leverage `/research` for systematic analysis:

**When to Use Research:**
- Novel error patterns not seen before
- Technology stack unfamiliar to debugging context
- Issues requiring architectural understanding
- Pattern analysis across multiple systems
- Security vulnerability assessment
- Performance debugging requiring domain knowledge

**Research Integration** (`/research`):
- **Research Planning**: Define specific questions about the debugging context
- **Multi-source Information Gathering**: Search across multiple engines for similar issues
- **Analysis Integration**: Synthesize findings to inform hypothesis generation
- **Pattern Recognition**: Identify common patterns in similar debugging scenarios

**Research Query Examples:**
```
/research "TypeError undefined property authentication middleware Express.js"
/research "Memory leak debugging Node.js background tasks patterns"
/research "Race condition data corruption multi-user database transactions"
```

**🧠 Root Cause Analysis:**

Leverage sequential thinking capabilities to rank potential causes by:
(a) likelihood given the error message and research findings
(b) evidence in the code snippets and similar documented cases
(c) impact if true based on research patterns

**Investigation Focus:** Start by investigating the top 2 most likely causes to maintain focus. If both are ruled out during validation, consider expanding to additional hypotheses as needed. Use research findings to inform additional hypothesis generation.

**Top Hypothesis:** [e.g., "Data Flow: The `user` object is undefined when the `isAdmin` check runs in the `/auth` endpoint"]

**Reasoning:** [e.g., "The `TypeError` references a property of `undefined`, and the code shows `user.id` is used without a null check right after the admin check. Research shows this is a common Express.js middleware timing issue."]

**Secondary Hypothesis:** [State your second most likely cause and reasoning, enhanced by research findings]

**Research-Enhanced Analysis:** [If research was conducted, summarize how findings influenced hypothesis ranking and validation approach]

**Summary Checkpoint:** Summarize the primary and secondary hypotheses, including any research insights, before proposing a validation plan.

### Phase 2: Validation Before Fixing (Critical!)

Create a precise, testable plan to validate the top hypothesis without changing any logic.

**Logging & Validation Plan:**
- **Action:** [e.g., "Add `console.log('User object before admin check:', JSON.stringify(user));` at Line 42 of `auth-service.js`"]
- **Rationale:** [e.g., "This will prove whether the `user` object is `null` or `undefined` immediately before the point of failure"]

**Expected vs. Actual Results:**

| Checkpoint | Expected (If Hypothesis is True) | Actual Result |
|------------|----------------------------------|--------------|
| [Test condition] | [Expected outcome] | [Fill after testing] |
| [Log output] | [Expected log content] | [Fill after testing] |

**Summary Checkpoint:** Confirm the validation plan is sound and the hypothesis is clearly testable.

### Phase 3: Surgical Fix

**⚠️ Only proceed if Phase 2 successfully validates the hypothesis.**

**Proposed Fix:**
```diff
// Provide the code change in a diff format for clarity
- [problematic code]
+ [corrected code]
```

**Justification:** Explain why this specific change solves the root cause identified and validated earlier.

**Impact Assessment:** Document what this change affects and potential side effects.

### Phase 4: Final Verification & Cleanup

**Testing Protocol:**
- [ ] Run all original failing tests - confirm they now pass
- [ ] Run related passing tests - confirm no regressions
- [ ] Test edge cases related to the fix
- [ ] Remove any temporary debugging logs added in Phase 2

**Documentation Updates:**
- [ ] Update relevant documentation if fix changes behavior
- [ ] Add test cases to prevent regression
- [ ] Document lessons learned for future debugging

## 🚨 STRICT PROTOCOLS & BEHAVIORAL CONSTRAINTS 🚨

### ⚡ ZERO TOLERANCE FOR PREMATURE SUCCESS
**ABSOLUTE RULE: NO CELEBRATIONS UNTIL ORIGINAL PROBLEM IS 100% SOLVED**
- ❌ NO "partial success" acknowledgments
- ❌ NO "framework is working" statements until the SPECIFIC bug is detected
- ❌ NO "debugging protocol worked" claims until the ORIGINAL ISSUE is resolved
- ❌ NO stopping early with "this tells us valuable information" - THAT IS FAILURE
- ❌ NO claiming progress until the exact issue is resolved

### 🎯 BRUTAL SUCCESS CRITERIA
**ONLY SUCCESS:** The exact production issue reported is completely resolved
- **ANYTHING LESS IS FAILURE:** No exceptions, no excuses, no partial credit
- **BE RUTHLESSLY HONEST:** If the original problem isn't solved, the debugging failed
- **BUILD MUST WORK:** If code doesn't compile or tests fail, it's complete failure

### ⚡ RELENTLESS DEBUGGING RULES
- **Failed Validation:** If validation disproves the hypothesis, return to Phase 1 with new findings
- **Alternative Reasoning:** After failed validation, consider less obvious causes (race conditions, memory leaks, upstream corruption)
- **Test Integrity:** Never modify existing tests to make them pass
- **Root Cause Focus:** Focus strictly on the validated root cause, not symptoms
- **One Change at a Time:** Implement one precise change at a time
- **NO STOPPING:** Continue debugging until the ORIGINAL problem is completely solved

## When to Use `/debugp` vs `/debug`

**Use `/debugp` for:**
- Complex production issues requiring forensic analysis
- Critical bugs where thoroughness is essential
- Issues requiring evidence documentation
- Team debugging scenarios needing clear methodology
- High-stakes debugging where validation is critical

**Use `/debug` for:**
- Routine debugging and quick issues
- General debugging with other commands (`/debug /test`)
- Lightweight debugging scenarios

## Integration with Other Commands

**Enhanced Command Composition**:
- `/debug-protocol /execute` - Apply protocol during implementation with comprehensive logging
- `/debug-protocol /test` - Use protocol for test debugging with systematic validation
- `/debug-protocol /arch` - Apply forensic methodology to architectural debugging
- `/debug-protocol /think` - Enhanced analytical depth with protocol structure
- `/debug-protocol /research` - Comprehensive debugging with research-backed analysis
- `/debug-protocol /learn` - Capture debugging insights with Memory MCP integration

**Research-Enhanced Debugging** (`/debug-protocol /research`):
Automatically integrates research methodology for complex debugging scenarios:
1. **Research Planning**: Systematic approach to information gathering about the issue
2. **Multi-source Investigation**: Search across Claude, DuckDuckGo, Perplexity, and Gemini for similar issues
3. **Pattern Recognition**: Identify debugging patterns from multiple information sources
4. **Evidence Synthesis**: Combine research findings with local debugging evidence

**Learning Integration** (`/debug-protocol /learn`):
Automatically captures debugging insights using Memory MCP:
- Debug session entities with complete resolution paths
- Pattern recognition for similar future issues
- Technical implementation details with file:line references
- Reusable debugging methodologies and validation techniques

**With Other Debug Commands:**
- Can be combined with `/debug` for maximum debugging coverage
- Complements `/debug`'s lightweight approach with comprehensive methodology
- Integrates with `/research` for research-backed debugging analysis
- Works with `/learn` for persistent debugging knowledge capture

**Enhanced Memory MCP Integration:**
🔍 **Automatic Memory Search**: This command uses the full Memory Enhancement Protocol for:
- Past debugging patterns and successful methodologies
- Similar issue resolutions and root cause analysis
- Evidence-based debugging strategies
- Hypothesis validation techniques
- Common failure patterns and solutions
- Technical debugging implementations with file:line references
- Root cause analysis journeys with measurable outcomes

**Enhanced Memory MCP Implementation Steps:**

1. **Enhanced Search & Context**:
   - Extract specific technical terms (error messages, file names, stack traces)
   - Search: `mcp__memory-server__search_nodes("technical_terms")`
   - Log: "🔍 Searching memory..." → Report "📚 Found X relevant memories"
   - Integrate found context naturally into debugging analysis

2. **Quality-Enhanced Entity Creation**:
   - Use high-quality entity patterns with specific technical details
   - Include canonical naming: `{system}_{issue_type}_{timestamp}` format
   - Ensure actionable observations with file:line references
   - Add measurable outcomes and verification steps

3. **Structured Debug Session Capture**:
   ```json
   {
     "name": "{system}_{debug_type}_{timestamp}",
     "entityType": "debug_session",
     "observations": [
       "Context: {specific debugging situation with timestamp}",
       "Technical Detail: {exact error message/stack trace with file:line}",
       "Root Cause: {identified cause with validation evidence}",
       "Solution Applied: {specific fix implementation steps}",
       "Code Changes: {file paths and line numbers modified}",
       "Verification: {test results, metrics, confirmation method}",
       "References: {PR URLs, commit hashes, related documentation}",
       "Debugging Pattern: {methodology applied and effectiveness}",
       "Lessons Learned: {insights for future similar issues}"
     ]
   }
   ```

4. **Enhanced Relation Building**:
   - Link fixes to original problems: `{fix} fixes {original_issue}`
   - Connect debugging patterns: `{session} used_methodology {debug_pattern}`
   - Associate solutions with locations: `{solution} implemented_in {file_path}`
   - Build debugging genealogies: `{advanced_fix} supersedes {basic_fix}`

**Memory Query Terms**: debugging methodology, systematic debugging, evidence-based debugging, hypothesis validation, root cause analysis, debug session, technical debugging, error resolution patterns

**Enhanced Memory MCP Entity Types**:
- `debug_session` - Complete debugging journeys with evidence and resolution
- `technical_learning` - Specific debugging solutions with code/errors
- `implementation_pattern` - Successful debugging patterns with reusable details
- `root_cause_analysis` - Systematic analysis methodologies with outcomes
- `validation_technique` - Hypothesis validation methods with effectiveness data
- `debugging_methodology` - Protocol applications with success metrics

**Quality Requirements for Debug Sessions**:
- ✅ Specific file paths with line numbers (auth.py:42)
- ✅ Exact error messages and stack traces
- ✅ Complete hypothesis-validation-fix cycle
- ✅ Measurable outcomes (test results, performance metrics)
- ✅ References to PRs, commits, or documentation
- ✅ Reusable debugging patterns for similar issues

**Enhanced Function Call Integration**:
```
# Enhanced debugging session search
# This error handling pattern demonstrates graceful degradation when Memory MCP is unavailable.
try:
    memory_results = mcp__memory-server__search_nodes(
        # Example: query="TypeError Express.js middleware debugging"
        query="[error_type] [technology_stack] [debugging_pattern]"
    )
    if memory_results:
        # Using language-agnostic string concatenation for clarity
        log("📚 Found " + str(len(memory_results)) + " relevant debugging memories")
        # Integrate memory context into debugging analysis
except Exception as e:
    log("Memory MCP search failed: " + str(e))

# Create comprehensive debug session entity
try:
    mcp__memory-server__create_entities([{
        "name": "{system}_{error_type}_{timestamp}",  # Example: 'express_auth_error_2024-08-15T10:30:00Z'
        "entityType": "debug_session",
        "observations": [
            "Context: {debugging situation with reproduction steps}",
            "Technical Detail: {exact error/stack trace with file:line}",
            "Research Findings: {/research results if applicable}",
            "Hypothesis Formation: {ranked hypotheses with reasoning}",
            "Validation Method: {specific validation approach used}",
            "Validation Results: {evidence confirming/refuting hypothesis}",
            "Root Cause: {validated root cause with technical explanation}",
            "Solution Applied: {specific fix implementation with file:line}",
            "Code Changes: {diff or specific modifications made}",
            "Verification: {test results, metrics, validation evidence}",
            "References: {PR URLs, commits, documentation links}",
            "Debugging Pattern: {methodology effectiveness and insights}",
            "Lessons Learned: {transferable knowledge for similar issues}",
            "Research Integration: {how /research informed the process}"
        ]
    }])

    # Build debugging relations
    mcp__memory-server__create_relations([{
        "from": "{session_name}",
        "to": "{related_technique}",
        "relationType": "used_methodology"
    }, {
        "from": "{session_name}",
        "to": "{fixed_issue}",
        "relationType": "resolved"
    }])

except Exception as e:
    log("Memory MCP entity creation failed: " + str(e))
    # Continue with local debugging documentation
```

**Error Handling Strategy**:
- **Graceful Degradation**: Continue debugging even if Memory MCP fails
- **User Notification**: Inform user when Memory MCP unavailable but debugging proceeds
- **Fallback Mode**: Local-only debugging documentation when Memory MCP unavailable
- **Robust Operation**: Never let Memory MCP failures prevent debugging progress

## Examples

### Basic Protocol Usage
```
/debug-protocol "Authentication API returns 500 for admin users"
/debugp "Authentication API returns 500 for admin users"  # alias
```

### With Implementation
```
/debug-protocol /execute "Fix memory leak in background task processing"
/debugp /execute "Fix memory leak in background task processing"  # alias
```

### Research-Enhanced Debugging
```
/debug-protocol /research "Intermittent race condition causing data corruption in multi-user scenarios"
/debugp /research "Performance degradation in Redis cluster during high load"  # alias
```

### Learning-Integrated Debugging
```
/debug-protocol /learn "Memory optimization in Node.js streaming API"
/debugp /learn "Database connection pool exhaustion debugging"  # alias
```

### Complex Issue Analysis
```
/debug-protocol "Intermittent race condition causing data corruption in multi-user scenarios"
/debugp "Intermittent race condition causing data corruption in multi-user scenarios"  # alias
```

## Output Characteristics

**Phase-based structure** with explicit checkpoints and summaries
**Evidence-based analysis** with redacted sensitive data
**Hypothesis ranking** focusing on top 2 most likely causes
**Validation requirements** before any code changes
**Behavioral constraints** preventing premature success declarations

## Research Foundation

This protocol is based on systematic debugging research demonstrating significant improvements in debugging outcomes through structured, evidence-based approaches with validation steps before implementing fixes.
