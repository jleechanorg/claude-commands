# Push Command

**Purpose**: Pre-push review, validation, and test server startup

**Action**: Virtual agent review → push if clean → start test server

**Usage**: `/push`

**Implementation**: 
- Perform virtual agent review of changes
- Check for code quality issues
- Verify tests pass
- Validate commit messages
- Push to remote only if all checks pass
- Create PR if needed
- Start test server on available port for this branch
- Display server URL for immediate testing

**Test Server Integration**:
- Automatically starts test server after successful push
- Uses branch-specific port allocation (6006+)
- Server accessible at http://localhost:[port]
- Logs stored in /tmp/worldarchitectai_logs/[branch].log
- Server can be stopped with `/integrate` or manually