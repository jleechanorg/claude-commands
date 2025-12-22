# Evidence Standards for All Testing and Verification

## Core Principle

**Evidence must prove what you claim.** Mock data cannot prove production behavior.

## Three Evidence Rule (from CLAUDE.md)

**MANDATORY for ANY integration claim:**

1. **Configuration Evidence**: Show actual config file entries enabling the behavior
2. **Trigger Evidence**: Demonstrate automatic trigger mechanism (not manual execution)
3. **Log Evidence**: Timestamped logs from automatic behavior (not manual testing)

## Mock vs Real Mode Decision Tree

Before running ANY test, answer:

| Question | If YES → |
|----------|----------|
| Testing production/preview server behavior? | MUST use real mode |
| Validating actual API responses? | MUST use real mode |
| Checking data integrity (dice, state, persistence)? | MUST use real mode |
| Proving a bug is fixed in production? | MUST use real mode |
| Development workflow validation only? | Mock mode acceptable |
| Unit testing isolated functions? | Mock mode acceptable |

## Mock Mode Prohibition

**MOCK MODE = INVALID EVIDENCE** for:
- Production server validation
- API integration claims
- Data integrity verification (dice rolls, state changes)
- Bug fix confirmation
- Performance claims
- Security validation

**Mock mode tests ONLY prove:**
- Code syntax is correct
- Function signatures work
- Basic logic flow (in isolation)

**Mock mode tests NEVER prove:**
- Production behavior
- Real API responses
- Actual data execution
- Integration correctness

## Evidence Collection Requirements

### For Production Claims

Evidence MUST include:
- Real server URL (not localhost for production claims)
- Actual API responses with timestamps
- Real data from database/logs
- Specific values that prove execution (e.g., dice roll results)

### For Integration Claims

Evidence MUST show:
- Configuration enabling the integration
- Automatic triggering (not manual invocation)
- Logs proving automatic execution with timestamps

### For Bug Fix Claims

Evidence MUST include:
- Reproduction of original bug (before fix)
- Same scenario with fix applied
- Different outcome proving fix works

## Anti-Patterns

- **"Tests pass" without evidence type** - Mock tests passing ≠ production working
- **Health endpoint only** - Proves server is up, not that features work
- **Endpoint existence** - tools/list returning tools ≠ tools executing correctly
- **Assuming mock = real** - Mock data is fabricated; production data is evidence

## When to Stop and Ask

If you're about to:
- Run mock mode for production validation → STOP, use real mode
- Claim "tests pass" without specifying mode → STOP, clarify mode
- Skip actual execution evidence → STOP, collect real evidence
- Trust health checks as feature validation → STOP, test actual features

## Related Standards

- `CLAUDE.md` - Three Evidence Rule (lines 110-113)
- `generatetest.toml` - Mock mode prohibition (lines 433-441)
- `end2end-testing.md` - Test mode commands (/teste, /tester, /testerc)
- `browser-testing-ocr-validation.md` - OCR evidence for visual claims
