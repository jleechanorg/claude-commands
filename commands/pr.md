# PR Command - Complete Development Lifecycle

**Purpose**: Complete development lifecycle from thinking through to PR review

**Usage**: `/pr` - Think, execute, push, review, and handle feedback

## 🚨 MANDATORY COMPLETE PR WORKFLOW

**⚠️ CRITICAL**: This command MUST execute ALL 5 phases in sequence. No partial execution allowed.

This command **MANDATORILY** combines the functionality of: `/think /execute /push /copilot /review`

**❌ NEVER STOP MIDWAY** - Each phase must complete before task is considered done.

### Phase 1: Think (/think)

**Strategic thinking about the task**:
- Analyze the problem deeply
- Consider multiple approaches
- Identify potential challenges
- Plan implementation strategy

### Phase 2: Execute (/execute)

**Implement the solution**:
- Use realistic execution protocol with optimal strategy
- Work through implementation systematically
- Test and validate as we go

### Phase 3: Push (/push)

**Create PR with comprehensive details**:
- Commit all changes
- Push to remote branch
- Create detailed PR description
- Include test results and screenshots
- **Auto-run /copilot** - Immediately analyze and fix any issues

### Phase 4: Copilot (/copilot) - AUTO-EXECUTED

**Address automated feedback** (runs automatically after push):
- Handle GitHub bot comments
- Fix failing tests
- Address security/performance suggestions
- Make PR mergeable
- Post replies to all review comments

### Phase 5: Review (/review)

**Comprehensive code review**:
- Self-review implementation
- Check for potential issues
- Validate test coverage
- Document any additional considerations