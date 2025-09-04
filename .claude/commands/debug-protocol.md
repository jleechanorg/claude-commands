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

**[Critical] Technical State Extraction:**
- **DOM Inspector Output:** Extract CSS computed properties for visual elements
- **Network Request Analysis:** Document asset loading, API calls, response codes
- **Console Log Capture:** All errors, warnings, and relevant debug output
- **Browser State:** Screenshots with technical overlays showing element inspection

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

### Phase 0.5: Context-Aware Mandatory Code Walkthrough

🚨 **AUTOMATED CONTEXT DETECTION**: This phase automatically triggers for complex debugging scenarios requiring systematic code analysis.

**🎯 Walkthrough Triggers** (If ANY detected, Phase 0.5 is MANDATORY):
- **Version Comparison Issues**: Keywords like "V1 vs V2", "old vs new", "migration", "upgrade"
- **API Integration Problems**: Multiple system involvement, external service interactions
- **Architecture Debugging**: Component interaction issues, data flow problems
- **User Evidence Contradictions**: User screenshots/reports differ from automated observations
- **Complex System Issues**: Multiple files/modules involved, cross-component failures

**⚠️ MANDATORY USER EVIDENCE PRIMACY CHECK**:
- **Critical Rule**: If user provided screenshots, logs, or behavioral observations, treat as GROUND TRUTH
- **Required Action**: Compare user evidence with automated observations FIRST
- **Investigation**: If discrepancies exist, ask "Why am I seeing different results than the user?"
- **No Assumptions**: Never dismiss user evidence as environmental or user error

**📋 SYSTEMATIC CODE WALKTHROUGH PROTOCOL**:

**Step 1: Component Mapping (5 minutes)**
Using Serena MCP for semantic code analysis:
```
mcp__serena__find_symbol --name_path "[component_name]" --relative_path "[file_path]"
mcp__serena__get_symbols_overview --relative_path "[directory]"
```
- Identify equivalent functions/components between systems (e.g., V1 resumeCampaign vs V2 GamePlayView)
- Map corresponding API endpoints, data handlers, UI components
- Document component relationships and dependencies

**Step 2: Side-by-Side Code Analysis (10-15 minutes)**
Using systematic comparison methodology:
```
mcp__serena__find_symbol --name_path "[function1]" --include_body true
mcp__serena__find_symbol --name_path "[function2]" --include_body true
```
- Compare equivalent functions for missing logic, API calls, state management
- Identify architectural differences (server-side vs client-side patterns)
- Check for missing imports, configuration, or initialization code
- Verify error handling and edge case coverage

**Step 3: Execution Path Tracing**
Systematic flow analysis:
- **User Action → API Call**: Trace user interaction to backend request
- **API → Business Logic**: Follow request through service layer
- **Business Logic → Data Layer**: Track database/storage interactions
- **Data Layer → Response**: Verify response formation and return path
- **Response → UI Update**: Confirm UI state updates and rendering

**Step 4: Data Flow Verification**
Validate data transformations:
- **Input Format Verification**: Check data format expectations
- **Transformation Logic**: Verify data conversion between components
- **State Management**: Confirm state updates at each step
- **Output Format Validation**: Check final data format matches UI expectations

**Step 5: Gap Analysis & Evidence Synthesis (5 minutes)**
Systematic comparison results:
- **Missing Components**: Functions, API calls, or logic present in working version but absent in broken version
- **Different Implementations**: Variations in approach that could cause behavioral differences
- **Data Format Mismatches**: Input/output format incompatibilities
- **Architectural Differences**: Fundamental approach differences (e.g., server vs client rendering)

**🎯 WALKTHROUGH SUCCESS CRITERIA**:
- [ ] All equivalent components identified and compared
- [ ] Complete execution path traced in both systems (if comparative debugging)
- [ ] Data flow verified at each transformation point
- [ ] Specific gaps or differences documented with file:line references
- [ ] User evidence discrepancies explained or flagged for investigation

**⏱️ TIME-BOXED APPROACH**:
- **Quick Wins** (0-5 min): Check most obvious differences first
- **Systematic Deep Dive** (5-20 min): Complete component comparison and flow tracing
- **Escalation Criteria** (20+ min): If no clear gaps found, escalate complexity or broaden scope

**📚 Memory MCP Integration with Query Optimization**: Capture walkthrough patterns with enhanced search effectiveness:

**Query Optimization Enhancement**: Uses `scripts/memory_mcp_optimizer.py` for improved debug pattern discovery:
- **Smart Search Strategy**: Transform compound debug queries into optimized single-word searches
- **Enhanced Pattern Discovery**: Improve search success from ~30% to 70%+ for better debugging insights
- **Result Merging**: Combine multiple optimized searches for comprehensive debug analysis

**Enhanced Integration**: Capture walkthrough patterns for future reuse:
```
mcp__memory-server__create_entities([{
  "name": "debug_walkthrough_[system]_[timestamp]",
  "entityType": "debug_walkthrough_pattern",
  "observations": [
    "Context: [debugging situation requiring walkthrough]",
    "Components Compared: [specific functions/modules analyzed]",
    "Execution Path: [traced flow from user action to response]",
    "Gap Identified: [specific missing or different functionality]",
    "Evidence Reconciliation: [how user evidence guided analysis]",
    "Resolution Time: [total time from walkthrough to fix]"
  ]
}])
```

**Summary Checkpoint**: Document specific gaps, differences, or missing components found during walkthrough. These findings directly inform Phase 1 hypothesis formation.

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

**🧠 Root Cause Analysis (Enhanced by Walkthrough Evidence):**

Leverage sequential thinking capabilities enhanced by Phase 0.5 walkthrough findings to rank potential causes by:
(a) likelihood given the error message, research findings, AND walkthrough gap analysis
(b) evidence in the code snippets, walkthrough comparisons, and similar documented cases
(c) impact if true based on research patterns and systematic code analysis

**Evidence Integration**: Use walkthrough findings to inform hypothesis formation:
- **Component Analysis**: Incorporate missing functions/API calls identified in Step 2
- **Execution Path Gaps**: Consider flow interruptions found in Step 3 tracing
- **Data Flow Issues**: Include format mismatches discovered in Step 4 verification
- **User Evidence Reconciliation**: Integrate user observation explanations from walkthrough

**Investigation Focus:** Start by investigating the top 2 most likely causes enhanced by walkthrough evidence. If both are ruled out during validation, consider expanding to additional hypotheses informed by walkthrough patterns.

**Top Hypothesis (Walkthrough-Enhanced):** [e.g., "Data Flow Gap: V2 GamePlayView missing `apiService.getCampaign(campaignId)` call that V1 resumeCampaign() function makes, causing display of default content instead of loaded campaign data"]

**Reasoning (Evidence-Based):** [e.g., "Walkthrough comparison revealed V1 resumeCampaign() makes API call to load existing campaign data and populates UI, while V2 GamePlayView useEffect only creates new content. User screenshots showing minimal content vs rich content confirms this gap. Research shows this is common in server-side vs client-side migration patterns."]

**Secondary Hypothesis (Walkthrough-Informed):** [State your second most likely cause based on walkthrough evidence and research findings]

**Walkthrough Evidence Summary:** [Summarize specific gaps, missing components, or architectural differences found during systematic comparison that inform hypothesis ranking]

**Research-Enhanced Analysis:** [If research was conducted, summarize how findings combined with walkthrough evidence influenced hypothesis ranking and validation approach]

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

**Visual/UI Verification (if applicable):**
- [ ] **Screenshot comparison:** Before/after visual verification
- [ ] **DOM state verification:** CSS properties match expected values
- [ ] **Asset loading verification:** Network requests successful
- [ ] **Anti-bias check:** Test what should NOT be working

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

### Walkthrough-Triggering Issues (Phase 0.5 Automatically Activated)
```
/debug-protocol "V2 shows minimal content while V1 shows rich campaign data"
/debugp "API integration failing after migration from V1 to V2"  # Triggers systematic code comparison
/debug-protocol "User reports different behavior than what automated tests show"  # Triggers user evidence analysis
/debugp "Multi-component interaction causing data loss in new architecture"  # Triggers execution path tracing
```

### With Implementation
```
/debug-protocol /execute "Fix memory leak in background task processing"
/debugp /execute "Fix memory leak in background task processing"  # alias
```

### Research-Enhanced Debugging with Walkthrough
```
/debug-protocol /research "V1 vs V2 data loading pattern differences causing UI inconsistencies"
/debugp /research "Performance degradation after architectural migration"  # alias
```

### Learning-Integrated Debugging with Walkthrough Patterns
```
/debug-protocol /learn "Cross-version debugging methodology breakthrough"
/debugp /learn "Systematic code comparison preventing 3-4x debugging inefficiency"  # alias
```

### Complex Issue Analysis with Full Walkthrough
```
/debug-protocol "V2 GamePlayView showing default content while V1 displays rich campaign data despite same API"
/debugp "Cross-system integration failure with user evidence contradicting automated observations"  # alias
```

## Output Characteristics

**Enhanced phase-based structure** with explicit checkpoints and summaries:
- **Phase 0**: Context & Evidence Gathering
- **Phase 0.5**: Context-Aware Mandatory Code Walkthrough (auto-triggered for complex issues)
- **Phase 1**: Research & Root Cause Analysis (enhanced by walkthrough findings)
- **Phase 2**: Validation Before Fixing
- **Phase 3**: Surgical Fix
- **Phase 4**: Final Verification & Cleanup

**Evidence-based analysis** with redacted sensitive data and systematic code comparison
**Walkthrough-enhanced hypothesis ranking** focusing on top 2 most likely causes informed by code analysis
**User Evidence Primacy** ensuring user observations are treated as ground truth
**Validation requirements** before any code changes
**Behavioral constraints** preventing premature success declarations
**Memory MCP integration** for capturing successful debugging patterns

## Research Foundation

This protocol is based on systematic debugging research demonstrating significant improvements in debugging outcomes through structured, evidence-based approaches with validation steps before implementing fixes.
