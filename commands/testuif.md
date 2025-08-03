# Intelligent Regression Testing with Playwright MCP

**Purpose**: Perform comprehensive regression testing using `/think` and `/execute`, comparing old Flask site to new React V2 site with full functionality validation

**Action**: Always use `/think` to analyze context, then `/execute` for systematic testing. Adapts plan based on user input after command.

**Usage**:
- `/testuif` (automatic analysis and testing)
- `/testuif [specific instructions]` (adapts plan to user requirements)

## Execution Protocol

### Phase 1: Automatic Thinking & Planning

**🧠 ALWAYS START WITH `/think`:**
Execute `/think` to analyze:
- Current PR context and changed files
- Git diff analysis against main branch
- Frontend vs backend changes identification
- Risk assessment for functionality impacts
- Test strategy prioritization

### Phase 2: Plan Adaptation

**🎯 IF USER PROVIDED INSTRUCTIONS:**
Adapt the plan based on user input after `/testuif`:
- Parse user requirements and constraints
- Modify testing scope and priorities accordingly
- Integrate user-specific test scenarios
- Adjust comparison strategy as requested

**📋 DEFAULT COMPARISON STRATEGY:**
When no specific instructions given:
- Test ALL functionality from Flask frontend in React V2
- Ensure feature parity between old and new sites
- Validate critical user journeys work identically
- Document any missing or broken functionality

### Phase 3: Systematic Execution

**⚡ ALWAYS USE `/execute`:**
Use `/execute` with comprehensive testing plan:

```
/execute
1. Set up browser automation environment (Playwright MCP with headless=true)
2. Test Flask frontend functionality (baseline)
3. Test React V2 equivalent functionality
4. Compare feature parity and user experience
5. Document findings with screenshots
6. Post results to PR documentation
```

**🚨 MANDATORY HEADLESS CONFIGURATION:**
```bash
# Environment variables for headless enforcement
export PLAYWRIGHT_HEADLESS=1
export BROWSER_HEADLESS=true

# Playwright MCP configuration with explicit headless flag
mcp__playwright-mcp__browser_navigate --headless=true --url="http://localhost:8081"
mcp__playwright-mcp__browser_take_screenshot --headless=true --filename="baseline.png"
```

**🚨 FAILURE-EXIT SEMANTICS:**
```bash
# Exit codes for parity check failures
PARITY_CHECK_PASSED=0    # All functionality matches
PARITY_CHECK_FAILED=1    # Feature parity failures detected
CRITICAL_ERROR=2         # Browser automation or system errors

# Bail-on-failure implementation
set -e  # Exit immediately on any command failure
set -o pipefail  # Fail on any pipe command failure

# Example parity validation with non-zero exit
validate_feature_parity() {
    local flask_result="$1"
    local react_result="$2"

    if [ "$flask_result" != "$react_result" ]; then
        echo "❌ PARITY FAILURE: Feature mismatch detected"
        echo "Flask: $flask_result"
        echo "React: $react_result"
        exit $PARITY_CHECK_FAILED
    fi

    echo "✅ PARITY VERIFIED: Feature behavior matches"
    return 0
}
```

**🔄 FULL FUNCTIONALITY COMPARISON TESTING:**

**Flask Frontend (Baseline) - Test ALL of:**
- Landing page and authentication flows
- Campaign list, creation, and management
- Campaign gameplay and story continuation
- Settings, profile, and user preferences
- Navigation, routing, and deep linking
- Asset loading, performance, and errors

**React V2 Frontend (New) - Validate SAME functionality:**
- Identical user journeys and workflows
- Feature-complete comparison to Flask
- Performance and user experience validation
- Integration with Flask backend APIs
- Authentication and session management
- Error handling and edge cases

### Phase 4: PR Documentation

**📸 SCREENSHOT POSTING PROTOCOL:**
Always post screenshots to PR using structured directory:

```
docs/pr[NUMBER]/
├── flask_baseline/
│   ├── 01_landing_page.png
│   ├── 02_campaign_list.png
│   ├── 03_campaign_creation.png
│   └── ...
├── react_v2_comparison/
│   ├── 01_landing_page.png
│   ├── 02_campaign_list.png
│   ├── 03_campaign_creation.png
│   └── ...
├── technical_verification/
│   ├── dom_inspector_output.txt
│   ├── css_properties_extracted.json
│   ├── network_requests_log.json
│   ├── console_errors_warnings.txt
│   └── verification_evidence.md
├── issues_found/
│   ├── broken_functionality.png
│   ├── missing_features.png
│   └── ...
└── testing_report.md
```

**📊 AUTO-GENERATE PR COMMENT:**
Create structured comment on PR with:
- Executive summary of testing results
- **Technical Verification Summary:** DOM state, CSS properties, network requests, console logs
- Feature parity analysis (✅ Working, ❌ Broken, ⚠️ Different)
- **Evidence-Based Confidence Score:** Percentage based on technical verification completeness
- Performance comparison between frontends
- Critical issues requiring attention
- Links to all screenshot AND technical evidence
- **Anti-bias verification:** What was tested that should NOT work
- Recommendations for deployment readiness

## Example Execution Flows

### Basic Usage
```
User: /testuif
Claude: /think [analyzes PR context and creates testing strategy]
Claude: /execute [comprehensive Flask vs React V2 comparison testing]
Claude: [Posts results to docs/pr1118/ with full screenshot documentation]
```

### Adapted Usage
```
User: /testuif and make sure you compare old site to the new site and all functionality in the old site fully tested in new site
Claude: /think [incorporates specific comparison requirements into strategy]
Claude: /execute [focused on complete feature parity validation between sites]
Claude: [Detailed functionality mapping and gap analysis with visual evidence]
```

### Custom Focus
```
User: /testuif focus on campaign creation workflow and authentication only
Claude: /think [narrows scope to campaign creation and auth testing]
Claude: /execute [deep dive testing of specified functionality areas]
Claude: [Targeted testing report with focused recommendations]
```

## Critical Requirements

**🧠 MANDATORY SLASH COMMAND USAGE:**
- ALWAYS start with `/think` for analysis and planning
- ALWAYS use `/execute` for actual test implementation
- NEVER execute testing directly without proper slash command orchestration

**🔄 COMPLETE FUNCTIONALITY VALIDATION:**
- Test EVERY feature available in Flask frontend
- Ensure React V2 has equivalent functionality
- Document any gaps, differences, or improvements
- Validate identical user workflows and outcomes

**📸 COMPREHENSIVE VISUAL DOCUMENTATION:**
- Screenshot every major functionality in both frontends
- Organize by PR number in structured directories
- Generate comparative analysis with visual evidence
- Post complete testing report as PR comment

**🚨 REAL BROWSER AUTOMATION:**
- Use Playwright MCP (preferred) or Puppeteer MCP
- Real API calls with Firebase and Gemini (costs money!)
- **MANDATORY HEADLESS**: `PLAYWRIGHT_HEADLESS=1` environment variable enforced
- **FAILURE SEMANTICS**: Non-zero exit codes bubble up parity failures (`exit 1`)
- Actual browser interactions, never HTTP simulation
- **CLI Contract**: `--headless=true --bail` flags prevent silent partial passes

**✅ DEPLOYMENT READINESS ASSESSMENT:**
Final output always includes:
- Go/No-Go recommendation for React V2 deployment
- Critical issues list with severity levels
- Feature parity score (% complete)
- Performance impact analysis
- Risk assessment and mitigation steps

## Intelligence Features

**🎯 CONTEXTUAL ADAPTATION:**
- Automatically adjusts testing scope based on PR changes
- Recognizes frontend vs backend modifications
- Prioritizes testing based on risk and impact
- Incorporates user feedback into execution plan

**🔍 ISSUE DETECTION:**
- MIME type errors and asset loading failures
- Authentication and session management problems
- API integration and data persistence issues
- UI/UX differences and regression bugs
- Performance degradation and user experience impacts

**📋 ACTIONABLE REPORTING:**
- Specific steps to fix identified issues
- Priority ranking of problems found
- Feature gap analysis with implementation suggestions
- Performance optimization recommendations
- User experience improvement opportunities

This command provides intelligent, comprehensive regression testing that ensures your React V2 frontend is deployment-ready with full feature parity to the existing Flask frontend.
