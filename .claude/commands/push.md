# Push Command

**Purpose**: Pre-push review, validation, PR update, and test server startup

**Action**: Virtual agent review → push if clean → update PR desc → start test server

**Usage**: `/push`

**Implementation**: 
- Perform virtual agent review of changes
- Check for code quality issues
- Verify tests pass
- Validate commit messages
- Push to remote only if all checks pass
- Create PR if needed
- **Update PR description if significant changes detected**
- Start test server on available port for this branch
- Display server URL for immediate testing

**PR Description Auto-Update**:
- Analyzes commit messages since PR creation
- Detects significant scope changes:
  - Architecture migrations (e.g., string → JSON)
  - New test protocols or policies
  - Breaking changes
  - Major feature additions
- Updates PR description to reflect current state
- Preserves test results and adds new ones
- Includes breaking change warnings if applicable

**Test Server Integration**:
- Automatically starts test server after successful push
- Uses branch-specific port allocation (6006+)
- Server accessible at http://localhost:[port]
- Logs stored in /tmp/worldarchitectai_logs/[branch].log
- Server can be stopped with `/integrate` or manually