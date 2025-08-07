**🛠️ DEBUGGING PROTOCOL ACTIVATED 🛠️**

### Phase 0: Context & Evidence Gathering
* **[Critical] Reproduction Steps:** [Describe the exact, minimal steps required to reliably trigger the bug.]
* **[High] Observed vs. Expected Behavior:** [Observed: e.g., "API returns 500 when user is admin." Expected: e.g., "API should return 200 with user data."]
* **[Medium] Impact:** [Describe the user/system impact, e.g., "Critical data loss," "UI crashes for all users," "Performance degradation on admin dashboard."]
* **[Low] Last Known Working State:** [e.g., "Commit hash `a1b2c3d`," "Worked before the 2.4.1 deployment."]
* **⚠️ Relevant Code Snippets (REDACTED):**
    ```language
    // ⚠️ REDACT sensitive data (API keys, passwords, PII) from code. Use [REDACTED] as a placeholder.
    [Paste code here]
    ```
* **⚠️ Error Message / Stack Trace (REDACTED):**
    ```
    // ⚠️ REDACT all sensitive data from logs.
    [Paste logs here]
    ```
**Summary Checkpoint:** Before proceeding, clearly restate the problem using the evidence above.

### Phase 1: Root Cause Analysis
thought
Leverage your extended reasoning capabilities. I will rank potential causes by (a) likelihood given the error message, (b) evidence in the code snippets, and (c) impact if true. I will only investigate the top 2 most likely causes to maintain focus.
end_thought

* **Top Hypothesis:** [e.g., "Data Flow: The `user` object is undefined when the `isAdmin` check runs in the `/auth` endpoint."]
* **Reasoning:** [e.g., "The `TypeError` references a property of `undefined`, and the code shows `user.id` is used without a null check right after the admin check."]
* **Secondary Hypothesis:** [State your second most likely cause and reasoning.]

**Summary Checkpoint:** Summarize the primary and secondary hypotheses before proposing a validation plan.

### Phase 2: Validation Before Fixing (Critical!)
thought
I will now create a precise, testable plan to validate the top hypothesis without changing any logic.
end_thought

1.  **Logging & Validation Plan:**
    * **Action:** Add `console.log('User object before admin check:', JSON.stringify(user));` at Line 42 of `auth-service.js`.
    * **Rationale:** This will prove whether the `user` object is `null` or `undefined` immediately before the point of failure.
2.  **Expected vs. Actual Table:**

| Checkpoint                 | Expected (If Hypothesis is True)        |
| -------------------------- | --------------------------------------- |
| Log output of `user` object | `undefined` or `null`                   |
| API Response Code          | `500` (since the error will still occur) |

**Summary Checkpoint:** Confirm the validation plan is sound and the hypothesis is clearly testable.

### Phase 3: Surgical Fix
*Instruction:* Only proceed if Phase 2 successfully validates the hypothesis.

thought
The hypothesis was validated. I will now implement the minimal, targeted fix that directly addresses the confirmed root cause.
end_thought

* **Proposed Fix:**
    ```diff
    // Provide the code change in a diff format for clarity
    ```
* **Justification:** [Explain why this specific change solves the root cause identified and validated earlier.]

### Phase 4: Final Verification & Cleanup
* Run all original failing and related passing tests to verify the fix and check for regressions.
* Remove any temporary debugging logs added in Phase 2.

### 🚨 STRICT CONSTRAINTS & PROTOCOLS 🚨
* **Failed Validation:** If validation disproves the hypothesis, return to Phase 1 with the new findings as evidence.
* **Alternative Reasoning:** After a failed validation, explicitly consider less obvious causes (e.g., race conditions, memory leaks, upstream data corruption).
* **Test Integrity:** Never simplify or modify existing tests to make them pass.
* **Root Cause Focus:** Focus strictly on the validated root cause. Do not patch symptoms.
* **One Change at a Time:** Implement one precise change at a time.v
