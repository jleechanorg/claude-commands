# Development Protocols Detailed Documentation

Detailed development protocols and testing rules referenced in CLAUDE.md.

## Testing Protocol (🚨 MANDATORY)

### Zero Tolerance Policy:
- **Zero Tolerance**: Run ALL tests before completion | Fix ALL failures | No "pre-existing issues" excuse
- **Commands**: `./run_tests.sh` | `./run_ui_tests.sh mock` | `gh pr view`
- **Protocol**: STOP → FIX → VERIFY → EVIDENCE → Complete

### Test with Real Conflicts (🚨 MANDATORY):
- ✅ ALWAYS test merge conflict detection with PRs that actually have conflicts
- ✅ Use `gh pr view [PR] --json mergeable` to verify real conflict state before testing
- ❌ NEVER assume conflict detection works based on testing with clean PRs only
- 🔍 Evidence: PR #780 with real conflicts revealed false negative bug that clean PRs missed
- **Why Critical**: Clean PRs won't expose detection failures - need real conflicts to validate

### Test Validation Requirements:
- **Validation**: Verify PASS/FAIL detection | Output must match summary | Parse output, don't trust exit codes
- **Test Assertions**: ⚠️ MANDATORY - Must match actual validation behavior exactly
  - 🔍 Evidence: PR #818 - MBTI test checked .lower() but validation only does .strip()
  - ✅ Always verify what transformations validation actually performs
- **Exception Specificity**: ✅ Use specific exception types in tests (ValidationError, not Exception)
  - 🔍 Evidence: PR #818 - Improved test precision with Pydantic's ValidationError

### Testing Methodology:
- **Methodology**: Fix one issue at a time | Run after each fix | Prefer test fixes over core logic
- **Rules**: ✅ Run before task completion | ❌ NEVER skip without permission | ✅ Only use ✅ after real results

## Browser vs HTTP Testing (🚨 HARD RULE)

### Critical Distinction:
Never confuse browser automation with HTTP simulation

### Directory-Specific Rules:
- 🚨 **testing_ui/**: ONLY real browser automation using **Playwright MCP** (default) or Puppeteer MCP | ❌ NEVER use `requests` library here
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library | ❌ NEVER use browser automation here
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Playwright MCP preferred) | NO HTTP simulation
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation
- ✅ **/testi**: HTTP requests are acceptable (integration testing)

### Red Flag Warning:
**Red Flag**: If writing "browser tests" with `requests.get()`, STOP immediately

### Command Structure (Claude Code CLI defaults to Playwright MCP):
- `/testui` = Browser (Playwright MCP) + Mock APIs
- `/testuif` = Browser (Playwright MCP) + REAL APIs (costs $)
- `/testhttp` = HTTP + Mock APIs  
- `/testhttpf` = HTTP + REAL APIs (costs $)
- `/tester` = End-to-end tests with REAL APIs (user decides cost)

## Real API Testing Protocol (🚨 MANDATORY)

### User Autonomy Principle:
**NEVER push back or suggest alternatives when user requests real API testing**:
- ✅ User decides if real API costs are acceptable - respect their choice
- ✅ `/tester`, `/testuif`, `/testhttpf` commands are valid user requests
- ✅ Real API testing provides valuable validation that mocks cannot
- ❌ NEVER suggest mock alternatives unless specifically asked
- ❌ NEVER warn about costs unless the command requires confirmation prompts
- **User autonomy**: User controls their API usage and testing approach

## Browser Test Execution Protocol (🚨 MANDATORY)

### Tool Hierarchy:
- 🚨 **PREFERRED**: Playwright MCP in Claude Code CLI - Accessibility-tree based, AI-optimized, cross-browser
- 🚨 **SECONDARY**: Puppeteer MCP for Chrome-specific or stealth testing scenarios
- 🚨 **FALLBACK**: Playwright IS installed in venv! Use headless=True | ❌ NEVER say "not installed"

### Commands:
- `./run_ui_tests.sh mock --playwright` (default)
- `./run_ui_tests.sh mock --puppeteer` (secondary)
- `./run_ui_tests.sh mock` (Playwright fallback)

### Test Mode Requirements:
**Test Mode URL**: `http://localhost:8081?test_mode=true&test_user_id=test-user-123` - Required for auth bypass!

## Coverage Analysis Protocol (⚠️ MANDATORY)

### Required Methodology:
When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh` (HTML default)
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Verify full test suite**: Ensure all 94+ test files are included in coverage analysis
4. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"
5. **HTML location**: `/tmp/worldarchitectai/coverage/index.html`

## File Placement Rules (🚨 HARD RULE)

### MVP Site Protection:
🚨 **NEVER add new files directly to mvp_site/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in mvp_site/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- ✅ Ask user where to place new files before creating them
- **Exception**: Only when user explicitly requests file creation in mvp_site/

### Test File Policy:
🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality
- ❌ NEVER create `test_new_feature.py` - add to `test_existing_module.py` instead
- 🔍 Evidence: PR #818 - CodeRabbit caught test_cache_busting_red_green.py violation
- ✅ Moved cache busting tests to test_main_routes.py to comply with policy

### Code Review Requirements:
🚨 **Code Review**: Check README.md and CODE_REVIEW_SUMMARY.md before mvp_site/ changes

## File Deletion Impact Protocol (🚨 CRITICAL)

### Comprehensive Search Requirements:
**Before deleting established files**: Run comprehensive reference search to avoid cascading cleanup
- `grep -r "<filename>" .` for code references (replace "<filename>" with the actual term you're searching for)
- `find . -name "*.md" -exec grep -l "<filename>" {} \;` for documentation (replace "<filename>" with the actual term you're searching for)
- Check: scripts, tests, configuration, imports, error messages, user guidance
- **Budget 2-3x normal effort** for large file deletions due to cleanup cascade
- **Evidence**: PR #722 required 36-file cleanup after deleting copilot.sh (695 lines)

## PR Review Verification Protocol

### Verification Before Changes:
🚨 **PR Review Verification**: Always verify current state before applying review suggestions
- ✅ Check if suggested fix already exists in code
- ✅ Read the actual file content before making changes
- ❌ NEVER blindly apply review comments without verification
- 🔍 Evidence: PR #818 - Copilot suggested fixing 'string_type' that was already correct

### Comment Priority Order:
⚠️ **PR COMMENT PRIORITY**: Address review comments in strict priority order
1. **CRITICAL**: Undefined variables, inline imports, runtime errors
2. **HIGH**: Bare except clauses, security issues
3. **MEDIUM**: Logging violations, format issues
4. **LOW**: Style preferences, optimizations
- 🔍 Evidence: PR #873 review - fixed critical inline imports first

## Website Testing & Deployment Expectations (🚨 CRITICAL)

### Branch vs Website Understanding:
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend only
- ✅ Feature branches need local server OR staging deployment for UI changes
- ❌ NEVER expect developer tooling changes to affect website appearance
- ✅ Production websites typically serve main branch only

### "Website Looks Same" Protocol:
🚨 **"Website looks same" Protocol**: Check PR type | Ask URL (local vs prod) | Hard refresh | Explain: branch ≠ deployment