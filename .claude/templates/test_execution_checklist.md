# Test Execution Checklist Template

## 🚨 MANDATORY TEST EXECUTION CHECKLIST

**Task**: [TASK DESCRIPTION]
**Branch**: [BRANCH NAME]
**Date**: [DATE]

### Pre-Execution Status
- [ ] All tests passing before changes? YES/NO
- [ ] GitHub CI status before changes: _______

### Test Execution Progress

#### 1. Backend Unit Tests
```bash
./run_tests.sh
```
- [ ] Executed: YES/NO
- [ ] Result: ___/__ tests passing
- [ ] Status: ✅ ALL PASS / ❌ FAILURES
- [ ] If failures, all fixed: YES/NO/NA

**Output Evidence**:
```
[Paste actual test output here]
```

#### 2. Integration Tests
```bash
TESTING=true python mvp_site/test_integration/test_integration.py
```
- [ ] Required for this task: YES/NO
- [ ] Executed: YES/NO
- [ ] Result: ___/__ tests passing
- [ ] Status: ✅ ALL PASS / ❌ FAILURES / ⬜ NOT REQUIRED

**Output Evidence**:
```
[Paste actual test output here]
```

#### 3. Browser/UI Tests
```bash
./run_ui_tests.sh mock
```
- [ ] Required for this task: YES/NO
- [ ] Executed: YES/NO
- [ ] Result: ___/__ tests passing
- [ ] Status: ✅ ALL PASS / ❌ FAILURES / ⬜ NOT REQUIRED

**Output Evidence**:
```
[Paste actual test output here]
```

#### 4. GitHub CI Checks
```bash
gh pr view <PR#> --json statusCheckRollup
```
- [ ] PR Number: _____
- [ ] All checks executed: YES/NO
- [ ] All checks passing: YES/NO
- [ ] Status: ✅ ALL SUCCESS / ❌ FAILURES / ⏳ IN PROGRESS

**Check Status**:
- [ ] auto-resolve-conflicts: _______
- [ ] test-deployment-build: _______
- [ ] test: _______

#### 5. Screenshots/Visual Evidence
- [ ] Screenshots requested: YES/NO
- [ ] Screenshots captured: YES/NO/NA
- [ ] From actual running system: YES/NO/NA
- [ ] Location: _______

**Screenshot List**:
1. _______
2. _______
3. _______

### Final Verification

#### ALL Tests Summary
- [ ] Backend tests: 100% PASS
- [ ] Integration tests (if required): 100% PASS
- [ ] UI tests (if required): 100% PASS
- [ ] GitHub CI: ALL SUCCESS
- [ ] Screenshots (if requested): CAPTURED

### Task Completion Status

**CAN ONLY CHECK IF ALL ABOVE ARE ✅**
- [ ] All tests passing at 100%
- [ ] All requested evidence provided
- [ ] Task objectives completed
- [ ] Ready to mark as DONE

### Failure Log

If ANY test failed, document here:

**Test**: _______
**Error**: _______
**Fix Applied**: _______
**Retest Result**: _______

---

**Signed**: [Assistant Name]
**Time Completed**: [Timestamp]

## ENFORCEMENT NOTICE
⚠️ This checklist is MANDATORY. Marking a task complete without 100% test passage violates the Test Execution Protocol.
