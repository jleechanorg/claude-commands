# Dice Roll Authenticity - Evidence Package

## Overview

This directory contains evidence for PR #2551 which fixes dice roll fabrication in WorldArchitect.AI's Gemini code_execution path.

## The Bug

LLMs can "fabricate" dice rolls by executing code that prints dice values without using actual random number generation:

```python
# FABRICATION - No RNG call!
print('{"rolls": [16], "total": 21}')  # Hardcoded value
```

**Statistical Detection**: Chi-squared test showed 411.81 (vs expected 19-30), proving dice distribution was "statistically impossible" from true RNG.

## Evidence Standards

### Three Types of Evidence Required

| Type | Description | Purpose |
|------|-------------|---------|
| **Statistical** | Chi-squared analysis | Proves anomaly exists |
| **Causal** | Real LLM reproduction | Explains HOW bug occurs |
| **Regression** | TDD tests (RED→GREEN) | Prevents recurrence |

### Chi-Squared Thresholds

| Value | Interpretation |
|-------|----------------|
| < 30 | PASS - Normal random |
| 30-50 | WARNING - Investigate |
| 50-100 | FAIL - Significant deviation |
| > 100 | FAIL - Likely fabrication |
| **411.81** | Reference case (this bug) |

## Evidence Files

### 1. Real Gemini API Reproduction
**File**: `pr2551-real-gemini-repro.md`

- **Method**: Local MCP server with real Gemini 3 Flash API calls
- **Commit tested**: `0c2873533` (pre-fix)
- **Result**: LLM printed `"random.randint"` as string (not function call), old code accepted fabricated dice

**Key log entry**:
```
GEMINI_CODE_EXECUTION_PARTS: evidence={
  'stdout': 'random.randint\n{"rolls": [16], ...}',
  'code_contains_rng': True,   # WRONG - should be False
  'rng_verified': True         # WRONG - fabrication accepted!
}
```

### 2. TDD Evidence
**File**: `pr2551-tdd-evidence.md`

- **RED state**: Tests fail on old commit `0c2873533`
- **GREEN state**: Tests pass on fixed commit
- **Tests**: `TestSystemPromptEnforcementWarning` class

### 3. Chi-Squared Reference
**Source**: Original bug report

- Chi-squared: 411.81 (vs expected 19-30)
- Sample size: Campaign dice audit
- Conclusion: Distribution statistically impossible from true RNG

## Evidence Gathering Methods

### Method 1: Statistical Analysis (Chi-Squared)

```bash
# Audit campaign dice distribution
WORLDAI_DEV_MODE=true python scripts/audit_dice_rolls.py <campaign_id>
```

**What to look for**:
- Chi-squared > 50 = suspicious
- Chi-squared > 100 = likely fabrication
- Impossible values (0, 21+ on d20)

### Method 2: Real LLM Reproduction

```bash
# Start local MCP server on old commit
git checkout <old_commit>
python -m mvp_site.mcp_server --port 5000

# Send prompts that instruct LLM to fabricate
# Check logs for rng_verified=True with no actual RNG
```

**Evidence requirements**:
- Real API calls (not mocked)
- `MOCK_SERVICES_MODE=false`
- Server logs showing `google_genai` remote calls
- Evidence dict showing `code_contains_rng` and `rng_verified` values

### Method 3: TDD Validation (RED→GREEN)

```bash
# RED: Run tests on old commit - should FAIL
git checkout <old_commit>
pytest mvp_site/tests/test_code_execution_dice_rolls.py -k TestName

# GREEN: Run tests on fixed commit - should PASS
git checkout <fixed_commit>
pytest mvp_site/tests/test_code_execution_dice_rolls.py -k TestName
```

**Evidence requirements**:
- Actual pytest output showing failures on old code
- Actual pytest output showing passes on new code
- Same test file used for both

## The Fix

### Before (Vulnerable)
```python
# Substring matching - fooled by string literals
def _code_contains_rng(code_text: str) -> bool:
    return "random.randint" in code_text.lower()
```

### After (Secure)
```python
# AST parsing - detects actual function calls
def _code_contains_rng(code_text: str) -> bool:
    tree = ast.parse(code_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for actual RNG function calls
            ...
```

## Related Documentation

- `.claude/skills/dice-authenticity-standards.md` - Full standards document
- `.claude/skills/dice-roll-audit.md` - Campaign audit workflow
- `.claude/skills/dice-real-mode-tests.md` - MCP testing procedures

## PR Reference

**PR #2551**: Fix dice roll uniformity by enforcing true RNG in code_execution
- Branch: `claude/fix-dice-roll-uniformity-ePxxE`
- Commits: See PR for full history
