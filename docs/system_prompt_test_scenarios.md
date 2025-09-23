# System Prompt Test Scenarios

## Test Scenario 1: PR Review Task
**Goal**: Process PR #1641 for authentication issues
**Summary**: PR has security vulnerabilities and test failures
**Last 5k tokens**: Discussion about authentication module bugs
**Expected User Prompt**: `/copilot 1641`

## Test Scenario 2: Implementation Task
**Goal**: Add user session management to WorldArchitect.AI
**Summary**: Need to implement session persistence and logout functionality
**Last 5k tokens**: Auth system discussion, Firebase integration patterns
**Expected User Prompt**: `/execute implement session management with Firebase persistence and logout functionality`

## Test Scenario 3: Complex Workflow
**Goal**: Set up automated deployment pipeline with testing
**Summary**: Manual deployment is causing issues, need CI/CD automation
**Last 5k tokens**: Discussion of deployment failures and testing requirements
**Expected User Prompt**: `/orch create automated deployment pipeline with testing gates and rollback capabilities`

## Test Scenario 4: Bug Fix
**Goal**: Fix failing tests in mvp_site/tests/
**Summary**: Authentication tests are failing after recent changes
**Last 5k tokens**: Test output showing specific failure points
**Expected User Prompt**: `fix test failures in mvp_site/tests/test_auth.py - session validation errors`

## Test Scenario 5: Code Generation
**Goal**: Create new API endpoint for campaign management
**Summary**: Need REST endpoint for CRUD operations on D&D campaigns
**Last 5k tokens**: Discussion of API structure and database schema
**Expected User Prompt**: `/cerebras create REST API endpoint for campaign CRUD operations with Firebase backend`

## Validation Criteria

The system prompt should generate prompts that:
1. **Start with action** (command or direct instruction)
2. **Are concise** (typically 10-50 words)
3. **Include specific technical details** when needed
4. **Prefer automation/orchestration** over manual steps
5. **Assume Claude competence** (no hand-holding)
6. **Follow CLAUDE.md protocols** implicitly

## Quality Indicators

✅ **Good Prompt Examples**:
- `/execute implement user authentication with Firebase`
- `/copilot 1641`
- `fix database connection timeout in mvp_site/core/db.py`
- `/orch setup automated testing pipeline with coverage reports`

❌ **Poor Prompt Examples**:
- "Hi Claude, could you please help me with implementing authentication?"
- "I'm having trouble with the database, what do you think I should do?"
- "Can you walk me through the steps to fix this issue?"
- "Please explain how authentication works and then implement it"
