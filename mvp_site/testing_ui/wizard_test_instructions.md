# Campaign Wizard Browser Testing Instructions

**Created**: 2025-07-15
**Purpose**: Manual testing guide for campaign wizard functionality using Puppeteer MCP

## Prerequisites

1. **Test Server Running**: Use `/testserver start` to start branch-specific server
2. **Test Mode URL**: `http://localhost:XXXX?test_mode=true&test_user_id=wizard-test-user`
3. **Puppeteer MCP**: Available in Claude Code CLI environment

## Test Scenarios

### 1. Wizard Initialization Test

**Objective**: Verify wizard loads and replaces original form in modern mode

**Steps**:
1. Navigate to test URL
2. Wait for test mode initialization (`window.testAuthBypass !== undefined`)
3. Click "Create New Campaign" button
4. Verify wizard appears (`#campaign-wizard` element)
5. Check that original form is hidden

**Expected Results**:
- Wizard container visible with 4-step progress bar
- Step 1 (Basics) active by default
- Dragon Knight campaign type pre-selected

### 2. Input Field Testing (Primary Focus)

**Objective**: Test `wizard-setting-input` field and auto-generation placeholders

**Key Test**: The `wizard-setting-input` field (textarea for world/setting)

**Steps**:
1. Locate `#wizard-setting-input` element
2. Verify placeholder text: "Random fantasy D&D world (auto-generate)"
3. Test input functionality:
   - Click in field
   - Type custom text
   - Clear field (should show placeholder again)
4. Test campaign type switching:
   - Click Custom campaign radio button
   - Verify placeholder changes
   - Click back to Dragon Knight
   - Verify placeholder reverts

**Expected Results**:
- Dragon Knight: Shows pre-filled World of Assiah description
- Custom: Shows "Random fantasy D&D world (auto-generate)" placeholder
- Field accepts input and updates preview

### 3. Form Validation Testing

**Objective**: Verify step navigation and validation

**Steps**:
1. Fill required fields in Step 1:
   - Campaign title: "Test Campaign"
   - Leave other fields with defaults
2. Click "Next" button
3. Verify advancement to Step 2
4. Test AI personality checkboxes:
   - Narrative (default: checked)
   - Mechanics (default: checked)
   - Companions (default: checked)
5. Continue to Step 3 and Step 4
6. Verify preview updates correctly

**Expected Results**:
- Navigation works without validation errors
- Preview reflects current selections
- Launch button appears in Step 4

### 4. Preview System Testing

**Objective**: Verify real-time preview updates

**Steps**:
1. Navigate to Step 4 (Launch)
2. Check preview elements:
   - `#preview-title`
   - `#preview-character`
   - `#preview-description`
   - `#preview-personalities`
   - `#preview-options`
3. Go back to earlier steps and modify values
4. Return to Step 4 and verify preview updates

## Puppeteer MCP Implementation

For Claude Code CLI with Puppeteer MCP access:

```javascript
// Navigate to test URL
await page.goto('http://localhost:8082?test_mode=true&test_user_id=wizard-test-user');

// Wait for test mode
await page.waitForFunction('window.testAuthBypass !== undefined');

// Click create campaign
await page.click('button:has-text("Create New Campaign")');

// Test wizard-setting-input field
const settingInput = await page.$('#wizard-setting-input');
const placeholder = await settingInput.getAttribute('placeholder');
console.log('Setting placeholder:', placeholder);

// Test input functionality
await settingInput.fill('Custom test world');
await settingInput.clear();

// Test campaign type switching
await page.click('#wizard-customCampaign');
await page.waitForTimeout(500);
const customPlaceholder = await settingInput.getAttribute('placeholder');
console.log('Custom placeholder:', customPlaceholder);

// Screenshots for verification
await page.screenshot({ path: 'wizard_test_step1.png' });
```

## Test Coverage Matrix

| Component | Test Type | Status |
|-----------|-----------|---------|
| Wizard initialization | Functional | ✓ Ready |
| wizard-setting-input field | Input validation | ✓ Ready |
| Auto-generation placeholders | UI behavior | ✓ Ready |
| Campaign type switching | Dynamic updates | ✓ Ready |
| Step navigation | Form flow | ✓ Ready |
| Preview system | Real-time updates | ✓ Ready |
| Form submission | Integration | ⏳ Manual test only |

## Manual Testing Checklist

- [ ] Server started with `/testserver start`
- [ ] Test mode URL accessible
- [ ] Wizard loads in place of original form
- [ ] wizard-setting-input placeholder correct for Dragon Knight
- [ ] wizard-setting-input placeholder changes for Custom
- [ ] Input field accepts text input
- [ ] Step navigation works (1→2→3→4)
- [ ] Preview updates reflect current selections
- [ ] Launch button visible in Step 4

## Integration with CI/CD

When Puppeteer MCP is available:
1. Add tests to `run_ui_tests.sh` workflow
2. Include wizard screenshots in test artifacts
3. Verify test mode URL parameters work consistently
4. Ensure mock APIs support wizard workflow

## Notes

- This test focuses on the `wizard-setting-input` field as highlighted in the scratchpad
- Tests use mock APIs to avoid costs during development
- Visual verification via screenshots is essential for UI components
- Test mode bypasses authentication for clean testing environment
