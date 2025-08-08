# V1 vs V2 Campaign Creation Comparison Test Guide

## Overview

This comprehensive test suite systematically compares V1 (Flask) and V2 (React) campaign creation workflows using TDD methodology and mandatory QA protocol requirements.

## 🔬 Test Architecture

### Test Matrix Coverage
The test systematically covers all combinations of:
- **Campaign Types**: Dragon Knight (default), Custom with "Lady Elara", Full Customization
- **System Versions**: V1 (http://localhost:5005) vs V2 (http://localhost:3000)  
- **Test Scenarios**: Navigation, Form Interaction, API Integration, Planning Block (V2), Character Selection, Gameplay Transition, Error Handling

### TDD Methodology
- **RED PHASE**: Tests failure scenarios and validates test methodology can detect differences
- **GREEN PHASE**: Tests success scenarios after fixes are applied
- **EVIDENCE COLLECTION**: Screenshots, API timing, console logs, error documentation at each step

## 🚀 Execution Instructions

### Prerequisites
1. **Start both servers**:
   ```bash
   # Terminal 1: Start V1 Flask server
   TESTING=true PORT=5005 python main.py serve
   
   # Terminal 2: Start V2 React server  
   cd mvp_site/frontend_v2
   PORT=3000 npm start
   ```

2. **Verify server health**:
   ```bash
   curl http://localhost:5005/health
   curl http://localhost:3000/health
   ```

### Run Complete Test Suite
```bash
# From project root
TESTING=true vpython mvp_site/tests/test_v1_vs_v2_campaign_comparison.py
```

### Run Specific Test Phases
```bash
# RED Phase only
TESTING=true vpython mvp_site/tests/test_v1_vs_v2_campaign_comparison.py V1VsV2CampaignComparisonTest.test_red_phase_dragon_knight_comparison

# GREEN Phase only  
TESTING=true vpython mvp_site/tests/test_v1_vs_v2_campaign_comparison.py V1VsV2CampaignComparisonTest.test_green_phase_dragon_knight_comparison
```

## 📊 Evidence Collection

### Systematic Screenshot Capture
All screenshots follow the mandatory format:
- **Path Label Format**: "Screenshot: Custom Campaign → Step 1 → Character Field"
- **File Naming**: `{test_id}_{step}_{timestamp}.png`
- **Storage**: `docs/v1_vs_v2_comparison/screenshots/`

### API Performance Measurement
- Response time tracking for critical endpoints
- Success/failure rate monitoring
- Performance comparison between V1 and V2
- Storage: `docs/v1_vs_v2_comparison/performance/`

### Error State Documentation
- Systematic capture of error conditions
- Graceful degradation testing
- Edge case validation
- Storage: `docs/v1_vs_v2_comparison/error_states/`

## 🔍 Test Scenarios Explained

### 1. Dragon Knight Default Campaign
- Tests the simplest path through both systems
- Validates basic functionality works end-to-end
- Compares default template handling

### 2. Custom Lady Elara Campaign
- **CRITICAL**: Tests end-to-end data flow validation
- Input "Lady Elara" → API → Database → UI Display
- Verifies custom character names appear in final game content
- Tests form handling differences between V1 and V2

### 3. Full Customization Campaign
- Tests complex form interactions
- Validates all customization options work
- Compares advanced feature handling

### 4. V2 Planning Block Functionality (V2 Only)
- Tests V2's unique planning block features
- Validates React-specific functionality
- Documents features not available in V1

## 📋 Mandatory QA Protocol Compliance

### Pre-Testing Checklist
- ✅ Test Matrix Created - All combinations documented
- ✅ Evidence Directories - Screenshot/log storage ready
- ✅ Server Verification - Both V1 and V2 systems running

### Testing Evidence Requirements  
- ✅ Screenshots for each test matrix cell with exact path labels
- ✅ Evidence documented for each ✅ claim with specific file references
- ✅ Path Coverage Report showing tested vs untested combinations

### Completion Validation Gates
- ✅ Adversarial Testing Completed - Actively tried to break the systems
- ✅ Testing Debt Documented - Related patterns verified
- ✅ All Evidence Screenshots - Properly labeled and linked

## 🚨 Critical Validation Points

### End-to-End Data Flow Testing
The test specifically validates that user input data flows correctly through the entire system:
1. **User Input**: "Lady Elara" character name
2. **Form Submission**: Data sent to backend API
3. **Database Storage**: Character data persisted
4. **Game Loading**: Data retrieved and displayed
5. **UI Verification**: "Lady Elara" appears in game content (not hardcoded "Shadowheart")

### API Integration Success vs Content Rendering Success
The test distinguishes between:
- **API Integration Success**: HTTP 200 responses, successful campaign creation
- **Content Rendering Success**: Actual user data displayed in UI

This prevents false positives where API calls succeed but UI shows hardcoded/placeholder content.

## 📄 Report Generation

### Comprehensive Test Report
The test generates a detailed JSON report including:
- Test matrix coverage percentage
- Individual test results for each scenario
- API performance comparisons
- Error handling effectiveness
- Evidence file locations
- QA protocol compliance verification

### Report Location
`docs/v1_vs_v2_comparison/comprehensive_test_report_{timestamp}.json`

## 🔧 Troubleshooting

### Common Issues

1. **Playwright MCP Not Available**
   ```bash
   # Install Playwright if needed
   pip install playwright
   playwright install chromium
   ```

2. **Server Not Responding**
   ```bash
   # Check server processes
   ps aux | grep python
   ps aux | grep node
   
   # Verify ports are open
   netstat -tlnp | grep :5005
   netstat -tlnp | grep :3000
   ```

3. **Permission Denied on Evidence Directory**
   ```bash
   # Fix permissions
   chmod -R 755 docs/v1_vs_v2_comparison/
   ```

### Debug Mode Execution
For detailed debugging with verbose output:
```bash
TESTING=true DEBUG=true vpython mvp_site/tests/test_v1_vs_v2_campaign_comparison.py -v
```

## 📚 Integration with Testing Commands

### Use with /testllm Command
This test file is designed to work with the `/testllm` command:
```bash
/testllm test_v1_vs_v2_campaign_comparison.py
```

### Integration with CI/CD
The test includes CI environment detection and can be integrated into automated testing pipelines with proper server setup.

## 🎯 Success Criteria

A successful test run should show:
1. ✅ All test matrix combinations executed
2. ✅ Screenshots captured for each critical step  
3. ✅ API performance measured and documented
4. ✅ Error handling verified for both systems
5. ✅ End-to-end data flow validated (especially "Lady Elara" test)
6. ✅ V2 planning block functionality confirmed
7. ✅ Comprehensive report generated with all evidence

The test is considered COMPLETE only when all mandatory QA protocol requirements are satisfied and comprehensive evidence is collected for systematic V1 vs V2 comparison.