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

### Phase 1: Root Cause Analysis

Leverage sequential thinking capabilities to rank potential causes by:
(a) likelihood given the error message
(b) evidence in the code snippets
(c) impact if true

**Investigation Focus:** Start by investigating the top 2 most likely causes to maintain focus. If both are ruled out during validation, consider expanding to additional hypotheses as needed.

**Top Hypothesis:** [e.g., "Data Flow: The `user` object is undefined when the `isAdmin` check runs in the `/auth` endpoint"]

**Reasoning:** [e.g., "The `TypeError` references a property of `undefined`, and the code shows `user.id` is used without a null check right after the admin check"]

**Secondary Hypothesis:** [State your second most likely cause and reasoning]

**Summary Checkpoint:** Summarize the primary and secondary hypotheses before proposing a validation plan.

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

**Command Composition** (similar to `/debug` modifier capabilities):
- `/debug-protocol /execute` - Apply protocol during implementation with comprehensive logging
- `/debug-protocol /test` - Use protocol for test debugging with systematic validation
- `/debug-protocol /arch` - Apply forensic methodology to architectural debugging
- `/debug-protocol /think` - Enhanced analytical depth with protocol structure

**With Other Debug Commands:**
- Can be combined with `/debug` for maximum debugging coverage
- Complements `/debug`'s lightweight approach with comprehensive methodology

**Memory Integration:**
🔍 **Automatic Memory Search**: This command searches Memory MCP for:
- Past debugging patterns and successful methodologies
- Similar issue resolutions and root cause analysis
- Evidence-based debugging strategies
- Hypothesis validation techniques
- Common failure patterns and solutions

**Memory Query Terms**: debugging methodology, systematic debugging, evidence-based debugging, hypothesis validation, root cause analysis

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
