# /commentreply Command

🎯 **Purpose**: Systematically process ALL PR comments with real technical responses and GitHub threading

## 🚨 MODERN WORKFLOW (3-Step Process)

### Step 1: Load Fetched Comments (MANDATORY)
```bash
# MUST run /commentfetch first in session to populate comment data
# Load comments from: /tmp/{branch_name}/comments.json
```

### Step 2: Claude Analysis & Fixes (CORE RESPONSIBILITY)
**Claude MUST**:
1. **Read each comment content** from the JSON data
2. **Analyze technical issues** raised in each comment
3. **Implement actual fixes** using Edit/MultiEdit tools when code changes needed
4. **Generate technical responses** addressing specific points raised
5. **Verify changes** with git diff and commit with descriptive messages

### Step 3: Automated Posting (Python Execution)
```bash
# Get repo info and pass to Python script
OWNER=$(gh repo view --json owner --jq .owner.login)
REPO=$(gh repo view --json name --jq .name)
PR_NUMBER=$(gh pr view --json number --jq .number)

# Python handles secure API posting with threading
python3 .claude/commands/commentreply.py "$OWNER" "$REPO" "$PR_NUMBER"
```

## 🔧 CLAUDE'S TECHNICAL RESPONSIBILITIES

### Issue Analysis
For each comment, Claude must:
- **Extract specific issues**: What exactly is the comment asking for?
- **Identify file/line context**: Where does this need to be fixed?
- **Determine fix approach**: What technical changes are required?

### Implementation Requirements
- **✅ MANDATORY**: Use Edit/MultiEdit tools for actual file changes
- **✅ MANDATORY**: Run `git diff` to verify changes were made
- **✅ MANDATORY**: Commit changes with comment reference
- **❌ FORBIDDEN**: Generic acknowledgments without technical substance
- **❌ FORBIDDEN**: Claiming fixes without actual file modifications

## 🚨 CRITICAL: PATTERN-BASED FIX PROTOCOL

**⚠️ MANDATORY**: When fixing patterns/variables mentioned in comments, apply systematic verification to prevent incomplete implementations.

### Discovery Phase (MANDATORY)
```bash
# Find ALL instances of flawed pattern BEFORE claiming fix
grep -n "problematic_pattern" target_file.py
rg "problematic_pattern" . --type py -A 2 -B 2
```

### Implementation Phase (MANDATORY)
- **✅ Map ALL instances**: Document each occurrence and required fix
- **✅ Fix ALL instances**: Not just obvious ones - systematic coverage required
- **❌ FORBIDDEN**: Partial pattern fixes that miss related usage

### Verification Phase (MANDATORY)
```bash
# Prove ALL instances addressed before declaring complete
git add -A && git diff --cached | grep -E "(\+|\-)" | grep "problematic_pattern"
git show HEAD | grep -A 3 -B 3 "problematic_pattern"
```

### Examples of Pattern-Based Fixes
- **Variable Usage**: `all_comments` vs `processed_comments` - must fix ALL usage (success criteria AND error reporting)
- **Function Calls**: Signature changes require ALL call sites updated
- **Import Changes**: Must verify ALL dependent code updated

**🚨 LESSON**: Incomplete pattern fixes create false confidence - always verify completeness with evidence

### Response Generation
**🚨 MANDATORY: [AI responder] TAG REQUIREMENT**
ALL responses MUST begin with the tag **[AI responder]** to distinguish AI-generated responses from manual human responses.

Create technical responses that:
- **Start with [AI responder] tag** (MANDATORY for identification)
- **Quote original comment** for context
- **Explain specific changes made** with technical detail
- **Include commit hash** for verification
- **Reference file/line numbers** where applicable
- **Provide verification commands** (git show, git diff)

## 📋 COMMENT PROCESSING PROTOCOL

### Performance Issues (Example: Copilot efficiency comments)
```
[AI responder] ✅ **Performance Fix Applied** (Commit: abc1234)

> The get_git_commit_hash() function is called multiple times...

**Analysis**: You're absolutely right about the inefficiency.

**Fix Implemented**:
- ✅ Moved get_git_commit_hash() call to start of processing
- ✅ Pass commit hash as parameter to avoid repeated git commands
- ✅ Reduced from 3+ git calls to 1 git call per run

**Performance Impact**: ~67% reduction in git command execution

**Verification**: `git show abc1234 -- path/to/file.py`
```

### Security Issues (Example: Shell injection vulnerabilities)
```
[AI responder] ✅ **Security Issue Fixed** (Commit: def5678)

> Using f-string with json.dumps() output in shell command is unsafe...

**Analysis**: Valid security concern about shell injection vulnerability.

**Security Fix Applied**:
- ✅ Replaced dangerous echo 'json' | bash -c approach
- ✅ Implemented secure tempfile + gh --input mechanism
- ✅ Eliminated JSON embedding in shell command strings

**Verification**: `git show def5678 -- .claude/commands/commentreply.py`
```

### Code Structure Issues (Example: CodeRabbit suggestions)
```
[AI responder] ✅ **Code Structure Improved** (Commit: ghi9012)

> Add strict mode and tool checks to fail fast...

**Implementation**:
- ✅ Added set -Eeuo pipefail for fail-fast error handling
- ✅ Added python3/gh CLI availability checks
- ✅ Proper exit codes when required tools missing

**Verification**: `git show ghi9012 -- .claude/commands/commentreply`
```

## ⚠️ QUALITY GATES

Before processing any comments:
1. **✅ Content Reading**: Read actual comment.body text from JSON data
2. **✅ Technical Analysis**: Address specific technical points raised
3. **✅ File Editing**: Make actual file changes when issues require fixes
4. **✅ Verification**: Run git diff to confirm changes were made
5. **✅ Commit Reference**: Include commit hash in all responses

## 🚀 EXECUTION FLOW

```mermaid
graph TD
    A[/commentfetch loads JSON] --> B[Claude reads comments]
    B --> C[Claude analyzes technical issues]
    C --> D[Claude implements fixes]
    D --> E[Claude generates responses]
    E --> F[Python posts with threading]
    F --> G[Verify coverage]
```

## 📊 SUCCESS CRITERIA

- **✅ 100% Comment Coverage**: Every comment gets a technical response
- **✅ Real Fixes Implemented**: Actual file changes for code issues
- **✅ Technical Quality**: Specific analysis, not generic templates
- **✅ GitHub Threading**: Proper in_reply_to_id threading via Python
- **✅ Verification**: All responses include commit hash references

## 🛠️ INTEGRATION

- **Depends on**: `/commentfetch` must run first to populate JSON data
- **Uses**: Edit/MultiEdit tools for implementing fixes
- **Calls**: Python script for secure API posting and threading
- **Outputs**: Real technical responses with proper GitHub threading

This streamlined workflow ensures Claude focuses on technical analysis and implementation while Python handles the complex GitHub API security and threading requirements.
