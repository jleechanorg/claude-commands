# Scratchpad: JavaScript Tests & Test Server Followups

**Branch**: longer_dk1  
**Goal**: JavaScript testing improvements and test server architecture cleanup  
**Started**: 2025-07-15

## Current State

### JavaScript Test Context
- User selected campaign-wizard.js input field: `wizard-setting-input`
- Placeholder text: "Random fantasy D&D world (auto-generate)"
- Investigating test server architecture revealed multiple systems

### Test Server Architecture Issues
- Multiple conflicting server management systems
- `/testserver` command documentation without implementation
- Need to consolidate and improve testing workflows

## JavaScript Testing Priorities

### 1. Campaign Wizard Testing
- **Target**: `mvp_site/static/js/campaign-wizard.js`
- **Focus**: Input validation, auto-generation features
- **Current Issue**: User highlighted wizard-setting-input field
- **Testing Needs**:
  - [ ] Test input field validation
  - [ ] Test auto-generation functionality
  - [ ] Test placeholder behavior
  - [ ] Test form submission

### 2. UI Test Infrastructure
- **Browser Testing**: Use Puppeteer MCP (preferred) or Playwright
- **Test Mode**: `?test_mode=true&test_user_id=test-user-123`
- **Commands**: `/testui` (mock) or `/testuif` (real APIs)

### 3. Test Server Requirements
- **Multi-branch support**: Different servers for different branches
- **Port management**: Avoid conflicts
- **Log separation**: Branch-specific logs
- **Easy startup/shutdown**: Simple commands

## Test Server Architecture Cleanup

### Current Systems (Needs Consolidation)
1. **`test_server_manager.sh`** - Multi-branch (8081-8090)
2. **`run_test_server.sh`** - Single server 
3. **`run_local_server.sh`** - Development (5005)
4. **`push.py`** - Python implementation
5. **`/testserver`** - Documentation only ❌

### Recommended Approach
- **Foundation**: Use shell scripts (deterministic, visible)
- **Interface**: Create working `/testserver` command
- **Integration**: Ensure `/push`, `/integrate` use same system
- **Consolidation**: Remove conflicting implementations

## JavaScript Test Followups

### Immediate Tasks
- [ ] Test campaign wizard input functionality
- [ ] Verify auto-generation placeholder behavior
- [ ] Set up browser testing for wizard workflow
- [ ] Create test cases for form validation

### Infrastructure Tasks
- [ ] Implement actual `/testserver` command
- [ ] Standardize on `test_server_manager.sh` foundation
- [ ] Create unified server management wrapper
- [ ] Document actual vs. expected behavior

### Testing Workflow
- [ ] Use `/testui` for JavaScript testing
- [ ] Start test server for current branch
- [ ] Navigate to wizard with test mode params
- [ ] Test input field behavior
- [ ] Verify auto-generation functionality

## Context & Notes

- User is focused on JavaScript testing improvements
- Campaign wizard appears to be a key component
- Test server architecture needs cleanup before effective testing
- Should prioritize working solutions over theoretical improvements
- Selected input field suggests focus on form validation/UX

## Branch Context

**Current Branch**: longer_dk1  
**Previous Work**: God mode planning blocks feature completed  
**Current Focus**: JavaScript testing and test server architecture  
**Related PR**: #605 (context unclear)