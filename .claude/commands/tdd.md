---
description: Matrix-Enhanced Test-Driven Development Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 0: Plan Matrix Coverage (⚠️ RUN FIRST)

**Action Steps:**
1. Open TodoWrite and create a checklist titled `TDD Matrix Plan`.
2. Identify the primary dimensions that influence behavior (e.g., user role, feature flag, input format).
3. Populate the checklist with every matrix cell you will cover (one TodoWrite item per combination).
4. Save the matrix definition to `tests/matrix_plan.md` for reference alongside the suite.

### Phase 1: RED - Author Matrix-Driven Failing Tests

**Action Steps:**
**Implementation**:
1. Generate a parametrized test module (e.g., `tests/test_matrix_workflow.py`) that iterates every TodoWrite matrix entry.
2. For each matrix cell, assert preconditions, trigger the behavior under test, and validate the expected outcome.
3. Ensure boundary values and failure modes from the matrix are explicitly represented.
4. Run the suite (`pytest tests/test_matrix_workflow.py`) and confirm every test fails to prove the matrix is complete.

**Matrix Test Structure (language-agnostic example using pytest):**
```python
import pytest

from myapp.domain import process_order

MATRIX = [
    pytest.param("admin", "csv", True, 200, id="admin-csv-happy-path"),
    pytest.param("admin", "json", False, 200, id="admin-json-disabled-feature"),
    pytest.param("staff", "csv", True, 403, id="staff-forbidden"),
    pytest.param("guest", "json", True, 422, id="guest-invalid-input"),
]


@pytest.mark.parametrize("role, input_format, feature_enabled, expected_status", MATRIX)
def test_matrix_paths(role, input_format, feature_enabled, expected_status, settings, factory):
    """RED: Each matrix cell should currently fail until implementation catches up."""
    payload = factory.build_payload(format=input_format, feature_flag=feature_enabled)
    response = process_order(role=role, payload=payload, settings=settings)

    assert response.status_code == expected_status
```

### Phase 2: GREEN - Minimal Implementation for Matrix Coverage

**Action Steps:**
**Implementation**:
1. **Matrix-Guided Development**: Use matrix to drive implementation priorities
2. **Incremental Path Implementation**: Implement one matrix path at a time
3. **Minimal Sufficient Code**: Write only enough code to pass current matrix tests
4. **Path Verification**: Verify each matrix cell passes before moving to next
5. **Systematic Coverage**: Ensure all matrix paths have implementation

### Phase 3: REFACTOR - Matrix-Validated Improvements

**Action Steps:**
**Implementation**:
1. **Matrix-Preserved Refactoring**: Ensure all matrix tests remain passing
2. **Pattern Recognition**: Use matrix results to identify code patterns
3. **Edge Case Handling**: Refactor based on matrix edge case findings
4. **Path Optimization**: Optimize code paths identified through matrix testing
5. **Coverage Validation**: Confirm matrix coverage maintained after refactoring

## 📋 REFERENCE DOCUMENTATION

# Matrix-Enhanced Test-Driven Development Command

**Purpose**: Test-driven development workflow with comprehensive matrix testing integration

**Action**: Red → Green → Refactor workflow enhanced with systematic path coverage

**Usage**: `/tdd` or `/rg`

#### **Matrix Design Template**

```markdown
## Example Matrix Definition

| Scenario ID | User Role | Input Format | Feature Flag | Expected Status | Notes |
|-------------|-----------|--------------|--------------|-----------------|-------|
| M-001       | admin     | csv          | enabled      | 200             | Happy path |
| M-002       | admin     | json         | disabled     | 200             | Feature toggle off |
| M-003       | staff     | csv          | enabled      | 403             | Authorization enforced |
| M-004       | guest     | json         | enabled      | 422             | Validation error |

### State Transition Coverage

| Transition ID | From State      | To State        | Expected Outcome |
|---------------|-----------------|-----------------|------------------|
| T-001         | draft           | submitted       | Status changes, timestamp set |
| T-002         | submitted       | approved        | Approver recorded |
| T-003         | approved        | archived        | Archival metadata persisted |

**Matrix Checklist**: Track each Scenario ID in TodoWrite and ensure the associated test is written, fails (RED), passes (GREEN), and remains passing after refactors.
```

#### **Combinatorial Coverage Analysis**

1. **Identify Variables**: List all user interaction variables (buttons, inputs, selections)
2. **Generate Combinations**: Create matrix of all meaningful variable combinations
3. **Prioritize Paths**: High-risk, high-usage, edge-case prioritization
4. **Boundary Conditions**: Include edge cases and error conditions

## 🔍 Matrix Testing Integration Points

### **Automated Matrix Generation**

```bash

# Component analysis for matrix generation

rg "useState|props|interface" --type tsx -A 3 -B 1
rg "onClick|onChange|onSubmit" --type tsx -A 2

# Generate test matrix from component analysis

```

### **Matrix-Driven Test Organization**

```
tests/
├── matrix_tests/
│   ├── [component]_matrix.test.tsx    # Full matrix test suite
│   ├── [component]_paths.md           # Matrix documentation
│   └── [component]_coverage.json      # Coverage tracking
├── unit_tests/                        # Traditional unit tests
└── integration_tests/                 # Cross-component tests
```

### **Matrix Coverage Tracking**

```markdown

## Complete Matrix Coverage Report

✅ **Core Field Matrix**: 50/50 tests
  - Campaign Type × Character × Setting: All combinations covered
  - Dynamic placeholder switching: Verified
  - State preservation during transitions: Tested

✅ **AI Personality Matrix**: 16/16 tests
  - All checkbox combinations: Covered
  - Visual highlighting verification: Tested
  - Campaign type compatibility: Verified

✅ **Title Variations Matrix**: 12/12 tests
  - Empty, short, long, special chars, Unicode: Covered
  - UI layout handling: Verified
  - Text truncation behavior: Tested

✅ **State Transition Matrix**: 8/8 tests
  - Type switching with data: Covered
  - Description expand/collapse: Tested
  - Form state persistence: Verified

**Total Matrix Coverage**: 86/86 tests

❌ **Previously Failing Patterns**:
- ✅ FIXED: Custom Campaign + Empty Character (Cell [2,1,1])
- ✅ FIXED: Hardcoded "Ser Arion" removed
- ✅ FIXED: Dynamic placeholder based on campaign type

⚠️ **Edge Cases Identified**:
- Unicode character display in all browsers
- Very long text input handling and truncation
- Special character sanitization and XSS prevention
- Rapid state switching and race conditions
```

## 🚨 Matrix TDD Enforcement Rules

**RULE 1**: Cannot proceed to GREEN phase without complete matrix in RED
**RULE 2**: Each matrix cell must have corresponding test case
**RULE 3**: All matrix tests must FAIL before implementation begins
**RULE 4**: REFACTOR phase must maintain 100% matrix test coverage
**RULE 5**: Matrix coverage report required before completion

## Advanced Matrix Techniques

### **Pairwise Testing Integration**

- Generate minimal test sets covering all parameter pairs
- Reduce matrix size while maintaining comprehensive coverage
- Focus on high-impact parameter combinations

### **State Transition Matrices**

- Model component state changes as matrix transitions
- Test all valid state transitions systematically
- Identify invalid transitions and error handling

### **User Journey Matrices**

- Map complete user workflows as matrix sequences
- Test end-to-end paths through matrix combinations
- Validate user story completion through matrix verification
