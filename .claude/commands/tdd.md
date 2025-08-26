# Matrix-Enhanced Test-Driven Development Command

**Purpose**: Test-driven development workflow with comprehensive matrix testing integration

**Action**: Red → Green → Refactor workflow enhanced with systematic path coverage

**Usage**: `/tdd` or `/rg`

## 🧪 Enhanced TDD Workflow with Matrix Testing

### Phase 0: Matrix Planning (⚠️ MANDATORY FIRST STEP)
**BEFORE writing any tests, create comprehensive test matrix:**

#### **Complete Field Matrix Creation**
```markdown
## Campaign Creation Test Matrix - All Field Combinations

### **Matrix 1: Core Field Interactions (Campaign Type × Character × Setting)**
| | **Empty Character** | **Custom Character** | **Special Chars** | **Unicode** | **Long Name** |
|---|---|---|---|---|---|
| **Dragon Knight + Empty** | [1,1,1] | [1,2,1] | [1,3,1] | [1,4,1] | [1,5,1] |
| **Dragon Knight + Short** | [1,1,2] | [1,2,2] | [1,3,2] | [1,4,2] | [1,5,2] |
| **Custom + Empty** | [2,1,1] | [2,2,1] | [2,3,1] | [2,4,1] | [2,5,1] |
| **Custom + Short** | [2,1,2] | [2,2,2] | [2,3,2] | [2,4,2] | [2,5,2] |

### **Matrix 2: AI Personality Testing (All Checkbox Combinations)**
| Campaign Type | Default World | Mechanical | Companions | Expected Behavior |
|---------------|---------------|------------|-------------|-------------------|
| Dragon Knight | ✅ | ✅ | ✅ | All personalities active |
| Dragon Knight | ✅ | ✅ | ❌ | Default + Mechanical only |
| Dragon Knight | ❌ | ❌ | ❌ | No AI personalities |
| Custom | ✅ | ✅ | ✅ | All personalities with custom |
| Custom | ❌ | ❌ | ❌ | Minimal custom setup |

### **Matrix 3: State Transition Testing**
| From State | To State | Expected Behavior |
|------------|----------|-------------------|
| Dragon Knight → Custom | Placeholder changes, data preserved |
| Custom → Dragon Knight | Auto-fills setting, maintains character |
| Collapsed → Expanded | Shows textarea, preserves state |
| Expanded → Collapsed | Hides textarea, preserves text |

**Total Matrix Tests**: 86 systematic test cases covering all field interactions
```

#### **Combinatorial Coverage Analysis**
1. **Identify Variables**: List all user interaction variables (buttons, inputs, selections)
2. **Generate Combinations**: Create matrix of all meaningful variable combinations
3. **Prioritize Paths**: High-risk, high-usage, edge-case prioritization
4. **Boundary Conditions**: Include edge cases and error conditions

### Phase 1: RED - Matrix-Driven Failing Tests
**Implementation**:
1. **Write Failing Tests for ENTIRE Matrix**: Each matrix cell becomes a test case
2. **Systematic Test Generation**: Convert each matrix row to specific test
3. **Path Coverage Verification**: Ensure every user path has corresponding test
4. **Edge Case Integration**: Include boundary conditions from matrix analysis
5. **Confirm ALL Tests Fail**: Verify comprehensive test failure before implementation

**Matrix Test Structure**:
```javascript
// Complete Matrix-Driven Test Structure
describe('Campaign Creation - Full Field Matrix', () => {
  // Matrix 1: Core Field Interactions (50 test combinations)
  test.each([
    // Dragon Knight combinations
    ['dragon-knight', '', '', 'Knight of Assiah', 'pre-filled setting'],
    ['dragon-knight', 'Custom Name', '', 'Knight of Assiah', 'pre-filled setting'],
    ['dragon-knight', '!@#$%', '', 'Knight of Assiah', 'pre-filled setting'],
    ['dragon-knight', '龍騎士', '', 'Knight of Assiah', 'pre-filled setting'],
    ['dragon-knight', 'Very Long Character Name That Tests UI Boundaries', '', 'Knight of Assiah', 'pre-filled setting'],

    // Custom Campaign combinations
    ['custom', '', '', 'Your character name', 'empty setting'],
    ['custom', 'Custom Name', '', 'Your character name', 'empty setting'],
    ['custom', '!@#$%', '', 'Your character name', 'empty setting'],
    ['custom', '龍騎士', 'Custom setting', 'Your character name', 'custom setting'],
    ['custom', 'Long Name', 'Very long custom setting text...', 'Your character name', 'custom setting'],
  ])('Matrix [%s,%s,%s] → expects %s placeholder and %s',
    (campaignType, character, setting, expectedPlaceholder, expectedSetting) => {
    // RED: Test fails initially
    render(<CampaignCreation />);

    // Select campaign type
    fireEvent.click(screen.getByText(campaignType === 'dragon-knight' ? 'Dragon Knight' : 'Custom'));

    // Verify dynamic placeholder
    const characterInput = screen.getByLabelText(/character/i);
    expect(characterInput).toHaveAttribute('placeholder', expectedPlaceholder);

    // Test character input
    fireEvent.change(characterInput, { target: { value: character } });
    expect(characterInput.value).toBe(character);

    // Verify setting behavior
    const settingInput = screen.getByLabelText(/setting/i);
    if (expectedSetting === 'pre-filled setting') {
      expect(settingInput.value).toContain('World of Assiah');
    } else {
      expect(settingInput.value).toBe('');
    }
  });

  // Matrix 2: AI Personality Combinations (16 test combinations)
  test.each([
    ['dragon-knight', true, true, true, 'all personalities enabled'],
    ['dragon-knight', true, true, false, 'default + mechanical only'],
    ['dragon-knight', false, false, false, 'no AI personalities'],
    ['custom', true, true, true, 'all personalities with custom'],
    ['custom', false, false, false, 'minimal custom setup'],
  ])('AI Matrix [%s] with [%s,%s,%s] → %s',
    (campaignType, defaultWorld, mechanical, companions, expectedBehavior) => {
    // RED: Test AI personality matrix combinations
    render(<CampaignCreation />);

    // Navigate to AI step
    fireEvent.click(screen.getByText('Next'));

    // Set AI personality checkboxes
    const defaultCheckbox = screen.getByLabelText(/default world/i);
    const mechanicalCheckbox = screen.getByLabelText(/mechanical/i);
    const companionsCheckbox = screen.getByLabelText(/companions/i);

    fireEvent.click(defaultCheckbox);
    fireEvent.click(mechanicalCheckbox);
    fireEvent.click(companionsCheckbox);

    // Verify checkbox states match matrix cell
    expect(defaultCheckbox.checked).toBe(defaultWorld);
    expect(mechanicalCheckbox.checked).toBe(mechanical);
    expect(companionsCheckbox.checked).toBe(companions);
  });

  // Matrix 3: State Transition Testing (8 test combinations)
  test.each([
    ['dragon-knight', 'custom', 'Knight of Assiah', 'Your character name'],
    ['custom', 'dragon-knight', 'Your character name', 'Knight of Assiah'],
  ])('State Transition [%s → %s] changes placeholder [%s → %s]',
    (fromType, toType, fromPlaceholder, toPlaceholder) => {
    // RED: Test dynamic placeholder switching
    render(<CampaignCreation />);

    // Start with fromType
    fireEvent.click(screen.getByText(fromType === 'dragon-knight' ? 'Dragon Knight' : 'Custom'));
    let characterInput = screen.getByLabelText(/character/i);
    expect(characterInput).toHaveAttribute('placeholder', fromPlaceholder);

    // Switch to toType
    fireEvent.click(screen.getByText(toType === 'dragon-knight' ? 'Dragon Knight' : 'Custom'));
    characterInput = screen.getByLabelText(/character/i);
    expect(characterInput).toHaveAttribute('placeholder', toPlaceholder);
  });
});
```

### Phase 2: GREEN - Minimal Implementation for Matrix Coverage
**Implementation**:
1. **Matrix-Guided Development**: Use matrix to drive implementation priorities
2. **Incremental Path Implementation**: Implement one matrix path at a time
3. **Minimal Sufficient Code**: Write only enough code to pass current matrix tests
4. **Path Verification**: Verify each matrix cell passes before moving to next
5. **Systematic Coverage**: Ensure all matrix paths have implementation

### Phase 3: REFACTOR - Matrix-Validated Improvements
**Implementation**:
1. **Matrix-Preserved Refactoring**: Ensure all matrix tests remain passing
2. **Pattern Recognition**: Use matrix results to identify code patterns
3. **Edge Case Handling**: Refactor based on matrix edge case findings
4. **Path Optimization**: Optimize code paths identified through matrix testing
5. **Coverage Validation**: Confirm matrix coverage maintained after refactoring

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
