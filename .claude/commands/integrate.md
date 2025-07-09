# Integration Command

**Purpose**: Create fresh branch from main and cleanup test servers

**Action**: Stop test server → Run `./integrate.sh` script → Clean environment

**Usage**: `/integrate`

**Implementation**: 
- Stop test server for current branch (if running)
- Execute `./integrate.sh` script
- Creates new branch from latest main
- Ensures clean starting point for new features
- Pulls latest changes from main
- Sets up proper branch naming
- Cleans up branch-specific test server resources

**Test Server Integration**:
- Automatically stops test server for current branch before integration
- Removes branch-specific PID and log files
- Ensures no orphaned server processes
- New branch starts with clean server state
- Use `/push` to start server for new branch