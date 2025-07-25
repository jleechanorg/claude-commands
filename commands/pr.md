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
- Use realistic execution protocol
- Consider subagents for parallel work
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
- Analyze code quality
- Check for potential issues
- Verify test coverage
- Document any concerns

## Command Combination

**The `/pr` command is a MANDATORY PROTOCOL**:
- **MUST** execute all 5 phases: Think→Execute→Push→Copilot→Review
- **CANNOT** be treated as content suggestion - it's an execution mandate
- **REQUIRES** complete workflow before declaring task complete
- **ENFORCES** comprehensive development experience through protocol

## Example Flow

**`/pr` Flow**:
```
User: /pr implement user login validation
Assistant: I detected these commands: /think /execute /push /copilot /review and will combine them intelligently.

Phase 1 - Think:
[Deep analysis of login validation requirements]

Phase 2 - Execute:
[Implementation with optional subagents]

Phase 3 - Push:
[Create PR with comprehensive description]

Phase 4 - Copilot (Auto):
[Address automated feedback and make PR mergeable]

Phase 5 - Review:
[Comprehensive code review]
```

## Key Benefits

- ✅ **Complete lifecycle** - from concept to mergeable PR
- ✅ **Integrated workflow** - all phases work together
- ✅ **Auto-fix issues** - /copilot runs automatically after push
- ✅ **Combo command support** - uses universal composition system
- ✅ **Realistic execution** - based on actual capabilities
- ✅ **Comprehensive coverage** - thinking, implementation, auto-fix, review

## When to Use

**Perfect for**:
- Feature development requiring full lifecycle
- Complex implementations needing thorough review
- PR preparation for important changes
- Complete development workflow automation
- Tasks requiring strategic thinking and comprehensive execution

**Alternative commands**:
- `/execute` - Just implementation
- `/plan` - Implementation with approval
- `/push` - Just create PR
- `/review` - Just code review
- `/copilot` - Just handle feedback