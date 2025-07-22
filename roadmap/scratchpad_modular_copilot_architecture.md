# Modular Copilot Architecture - Scratchpad

## Table of Contents
1. [Goal](#goal)
2. [Proposed Commands](#proposed-commands)
3. [Architecture Principles](#architecture-principles)
4. [Implementation Plan](#implementation-plan)
5. [Benefits](#benefits)
6. [Example Workflows](#example-workflows)
7. [Next Steps](#next-steps)
8. [PR #796 File Analysis](#pr-796-file-analysis-for-replication)
9. [Detailed Implementation Plan](#detailed-implementation-plan)

## Goal
Refactor the monolithic /copilot command into composable, single-purpose commands with strong I/O protocols.

## Proposed Commands

### Core Commands
1. **`/commentfetch`** - Fetch PR comments from all sources
   - Input: `--pr NUMBER [--output FILE]`
   - Output: `tmp/copilot/comments.json`
   - Purpose: Data collection only

2. **`/fixpr`** - Fix CI failures and merge conflicts
   - Input: `--pr NUMBER [--comments FILE]`
   - Output: `tmp/copilot/fixes.json`
   - Purpose: Automated fixing

3. **`/pushl`** - Push local changes to remote
   - Input: `[--fixes FILE] [--message STRING]`
   - Output: `tmp/copilot/push.json`
   - Purpose: Git operations

4. **`/commentreply`** - Generate and post comment responses
   - Input: `--comments FILE [--template STRING]`
   - Output: `tmp/copilot/replies.json`
   - Purpose: Response generation (via Claude)

### Master Command
5. **`/copilot`** - Orchestrate all commands
   - Remains as high-level driver
   - Calls individual commands in sequence
   - Provides integrated experience

## Architecture Principles

### 1. Unix Philosophy
- Do one thing well
- Composable like pipes
- Text (JSON) interfaces
- No hidden state

### 2. Strong I/O Contracts
```json
// comments.json schema
{
  "pr": 796,
  "fetched_at": "2025-01-21T10:00:00Z",
  "comments": [
    {
      "id": 123,
      "type": "inline|general|review",
      "author": "username",
      "body": "comment text",
      "file": "path/to/file.py",
      "line": 42,
      "requires_response": true
    }
  ],
  "metadata": {
    "total": 15,
    "sources": ["github_api", "copilot_suppressed"]
  }
}
```

### 3. Failure Isolation
- Each command can fail independently
- Clear error messages with recovery hints
- No cascading failures

### 4. Progressive Enhancement
- Start with basic functionality
- Add sophistication incrementally
- Maintain backward compatibility

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] Create base command class with I/O validation
- [ ] Implement JSON schema validation
- [ ] Set up tmp/copilot/ directory structure
- [ ] Create command registry system

### Phase 2: Individual Commands
- [ ] Implement /commentfetch
- [ ] Implement /fixpr
- [ ] Implement /pushl
- [ ] Implement /commentreply

### Phase 3: Integration
- [ ] Update /copilot to orchestrate
- [ ] Add pipeline support
- [ ] Create example workflows
- [ ] Write comprehensive tests

### Phase 4: Advanced Features
- [ ] Add --dry-run flag
- [ ] Implement command chaining
- [ ] Add progress indicators
- [ ] Create workflow templates

## Key Learnings from PR #796

### What Went Wrong
1. **Monolithic Design**: Everything bundled together made debugging hard
2. **Unnecessary Gemini API**: Added complexity without value
3. **No Separation of Concerns**: Data collection mixed with intelligence
4. **All-or-Nothing Execution**: No way to run parts independently

### What We're Fixing
1. **Modular Design**: Each piece testable and debuggable
2. **Claude-First Intelligence**: No external APIs unless justified
3. **Clear Layer Separation**: Collection → Intelligence → Execution
4. **Flexible Workflows**: Run any subset of commands

## Benefits

### For Power Users
- Fine-grained control
- Custom workflows
- Easy debugging
- Scriptable automation

### For Regular Users
- /copilot still works as before
- Better error messages
- Faster execution (parallelizable)
- More reliable

### For Maintainers
- Easier to test
- Clear boundaries
- Single responsibility
- Reusable components

## Example Workflows

### Standard Flow
```bash
/copilot --pr 796
# Internally runs:
# /commentfetch --pr 796
# /fixpr --pr 796
# /pushl
# /commentreply --comments tmp/copilot/comments.json
```

### Review First Flow
```bash
/commentfetch --pr 796
/think "Let me review these comments"
# ... user reviews ...
/commentreply --comments tmp/copilot/comments.json --template thoughtful
```

### Fix-Only Flow
```bash
/fixpr --pr 796
/pushl --message "Fix CI failures"
```

### Debug Flow
```bash
/commentfetch --pr 796 --output debug.json
cat debug.json | jq '.comments[] | select(.author == "copilot")'
```

## Next Steps
1. Create PR with this scratchpad
2. Use /replicate to identify useful parts from PR #796
3. Plan implementation with /plan
4. Build modular commands incrementally
5. Maintain backward compatibility

## PR #796 File Analysis for Replication

### Files to Replicate (with modifications)

1. **CLAUDE.md** (100 lines changed)
   - Added "NO UNNECESSARY EXTERNAL APIS" rule - critical learning to keep
   - Added "GEMINI API JUSTIFICATION REQUIRED" rule - essential for preventing anti-pattern
   - Added "AUTONOMOUS VERIFICATION GATES" - good for quality control
   - Added "THREE-LAYER CI VERIFICATION" - valuable CI knowledge
   - **Replicate**: All new rules, they're broadly applicable beyond copilot

2. **.claude/commands/copilot.py** (240 lines added)
   - Core GitHubCopilotProcessor class with comment fetching logic
   - Methods for parsing different comment sources (inline, general, reviews)
   - Comment posting and verification logic
   - **Replicate**: Comment fetching/parsing logic, but split into /commentfetch command
   - **Discard**: Gemini integration attempts, template generation code

3. **.claude/commands/copilot_verification.py** (432 lines new)
   - Comprehensive test suite for copilot functionality
   - Tests for comment fetching, parsing, and posting
   - **Replicate**: Test patterns and verification approaches for our modular commands

4. **.claude/commands/copilot.md** (103 lines changed)
   - Documentation explaining the copilot system
   - **Replicate**: Adapt for new modular architecture documentation

5. **roadmap/scratchpad_comment_responder_learning.md** (119 lines new)
   - Detailed learning journey from anti-pattern to correct architecture
   - Three-layer architecture diagram (Collection → Intelligence → Execution)
   - **Replicate**: Entire file as historical context and architecture guide

### Files to Skip

6. **.claude/commands/arch.md** / **archreview.md** (minor updates)
   - Just formatting and minor improvements, not copilot-specific

7. **export/cursor_commands_export/header.sh** (8 lines)
   - Minor fix for default branch detection, useful but not copilot-related

8. **simple_test.py** / **test_copilot_processing.py** (63 lines)
   - Quick test files for Gemini integration
   - **Skip**: These test the wrong approach (Gemini API)

9. **.claude/commands/README.md** (15 lines)
   - Just added copilot to command list
   - **Skip**: Will update when we add modular commands

### Key Code to Extract

From `copilot.py`, the valuable comment fetching logic:
```python
def get_pr_comments(pr_number: str) -> dict
def get_pr_inline_comments(pr_number: str) -> list  
def get_copilot_comments(pr_number: str) -> list
def parse_comment_for_response(comment: dict) -> dict
```

The verification patterns:
```python
def verify_comment_posted(initial_count: int, expected_increase: int) -> bool
```

### Replication Strategy

1. **Phase 1**: Create base infrastructure
   - Command base class with I/O contracts
   - JSON schema definitions
   - Shared utilities

2. **Phase 2**: Extract and adapt code
   - Move comment fetching to /commentfetch
   - Move fix logic to /fixpr
   - Move posting to /commentreply
   - Keep verification patterns

3. **Phase 3**: New /copilot orchestrator
   - Simple command chaining
   - Progress reporting
   - Error aggregation

---
Branch: modular-copilot-architecture
Created: 2025-01-21

## Detailed Implementation Plan

### Overview
Complete implementation of modular copilot architecture with 4 core commands + 1 orchestrator using a **hybrid Python + Markdown approach**.

### Architecture Decision: Hybrid Approach
**Core Principle**: Python handles mechanics, Markdown guides intelligence

#### Command Architecture Summary
- **`/commentfetch`**: Pure Python (100% mechanical)
- **`/fixpr`**: Hybrid - fixpr.py collects data, fixpr.md analyzes  
- **`/commentreply`**: Hybrid - guided by copilot.md
- **`/pushl`**: Pure Python (already exists)
- **`/copilot`**: Pure Markdown (orchestration needs intelligence)

### Timeline Estimate  
- **With subagents**: ~3 hours (parallel execution)
- **Without subagents**: ~5-6 hours (sequential)
- **Chunked approach**: 8-10 small milestones to avoid timeouts

### Phase 1: Core Command Implementation (2 hours)

#### 1.1 `/fixpr` Command Implementation
**File**: `.claude/commands/copilot_modules/fixpr.py`

**Responsibilities**:
- Three-layer CI verification (local, GitHub, merge-tree)
- Merge conflict detection and analysis
- Auto-fix hooks for resolvable issues
- CI status aggregation

**Key Methods to Extract from PR #796**:
```python
- check_github_ci_status() → Adapt for modular use
- check_merge_conflicts() → Full implementation
- _find_conflict_markers() → File scanning logic
- attempt_auto_resolution() → Hook for Claude fixes
```

**I/O Contract**:
```json
// Input: PR number + optional comments
{
  "pr": "820",
  "comments_file": "comments.json"  // optional
}

// Output: fixes.json
{
  "pr": "820",
  "analyzed_at": "2025-01-21T10:00:00Z",
  "ci_status": {
    "layer1_local": "passing",
    "layer2_github": "failing",
    "layer3_merge": "conflicts"
  },
  "conflicts": {
    "detected": true,
    "files": ["CLAUDE.md", "README.md"],
    "auto_resolvable": ["README.md"]
  },
  "fixes_applied": [],
  "needs_manual": ["CLAUDE.md"],
  "metadata": {
    "total_issues": 3,
    "auto_fixed": 0,
    "manual_required": 1
  }
}
```

#### 1.2 `/pushl` Command Implementation
**File**: `.claude/commands/copilot_modules/pushl.py`

**Responsibilities**:
- Stage changes (if any)
- Create commit with message
- Push to remote with verification
- Handle push conflicts gracefully

**Key Features**:
- Auto-detect branch and remote
- Verify push success via API
- Support commit message templates
- Handle force-push scenarios safely

**I/O Contract**:
```json
// Input: Optional fixes + message
{
  "fixes_file": "fixes.json",  // optional
  "message": "fix: Resolve CI failures and conflicts",
  "force": false
}

// Output: push.json
{
  "pushed_at": "2025-01-21T10:30:00Z",
  "branch": "modular-copilot-architecture",
  "remote": "origin",
  "commit_sha": "abc123def",
  "files_changed": 5,
  "message": "fix: Resolve CI failures and conflicts",
  "success": true,
  "push_url": "https://github.com/user/repo/commit/abc123def"
}
```

#### 1.3 `/copilot` Orchestrator Update
**File**: `.claude/commands/copilot_modules/copilot_orchestrator.py`

**Responsibilities**:
- Chain commands in correct sequence
- Handle errors between stages
- Aggregate results for final report
- Maintain backward compatibility

**Execution Flow**:
```python
1. Parse arguments (PR number required)
2. Execute /commentfetch → comments.json
3. Execute /fixpr → fixes.json
4. If fixes needed: Execute /pushl → push.json
5. If comments need replies: Get Claude responses
6. Execute /commentreply → replies.json
7. Generate summary report
```

**Progress Reporting**:
```
🔍 Fetching comments... ✓ (42 found)
🔧 Analyzing CI & conflicts... ✓ (3 issues)
🚀 Pushing fixes... ✓ (commit: abc123)
💬 Posting replies... ✓ (15 posted)
✅ Copilot analysis complete!
```

### Phase 2: Integration & Infrastructure (1 hour)

#### 2.1 Command Registration System
**File**: `.claude/commands/copilot_modules/__init__.py`

```python
from .base import CopilotCommandBase
from .commentfetch import CommentFetch
from .commentreply import CommentReply
from .fixpr import FixPR
from .pushl import PushLocal
from .copilot_orchestrator import CopilotOrchestrator

# Command registry for dynamic loading
COMMAND_REGISTRY = {
    'commentfetch': CommentFetch,
    'commentreply': CommentReply,
    'fixpr': FixPR,
    'pushl': PushLocal,
    'copilot': CopilotOrchestrator
}

def get_command(name: str):
    """Get command class by name."""
    return COMMAND_REGISTRY.get(name)
```

#### 2.2 CLI Entry Points
**Files**: Create wrapper scripts in `.claude/commands/`

- `commentfetch` → `python3 copilot_modules/commentfetch.py "$@"`
- `commentreply` → `python3 copilot_modules/commentreply.py "$@"`
- `fixpr` → `python3 copilot_modules/fixpr.py "$@"`
- `pushl` → `python3 copilot_modules/pushl.py "$@"`

#### 2.3 Shared Utilities
**File**: `.claude/commands/copilot_modules/utils.py`

- GitHub API helpers
- Git command wrappers
- JSON schema validators
- Common error messages

### Phase 3: Testing & Documentation (30 mins)

#### 3.1 Test Suite Structure
```
.claude/commands/tests/
├── test_commentfetch.py
├── test_commentreply.py
├── test_fixpr.py
├── test_pushl.py
├── test_orchestrator.py
└── test_integration.py
```

#### 3.2 Documentation Updates
1. Update `.claude/commands/README.md` with new commands
2. Create individual `.md` files for each command
3. Add examples to main copilot.md
4. Update this scratchpad with results

### Phase 4: Verification & Deployment (30 mins)

#### 4.1 Manual Testing Checklist
- [ ] Test each command individually
- [ ] Test full orchestration flow
- [ ] Test error scenarios
- [ ] Test backward compatibility
- [ ] Verify JSON schemas
- [ ] Check command help texts

#### 4.2 Integration Verification
```bash
# Individual command tests
./commentfetch 820 --output test_comments.json
./fixpr 820 --comments test_comments.json
./pushl --message "test: Manual test of pushl"
./commentreply 820 --comments test_comments.json

# Full orchestration test
./copilot 820
```

### Implementation Order

1. **Start with `/fixpr`** (most complex, reuses most from PR #796)
2. **Then `/pushl`** (simpler, Git operations)
3. **Update `/copilot` orchestrator** (ties everything together)
4. **Finally testing and documentation** (verify everything works)

### Success Metrics

✅ **Functional Requirements**
- All commands work independently
- Orchestrator chains commands correctly
- I/O contracts validated
- Error handling robust

✅ **Quality Requirements**
- Tests pass (unit + integration)
- Documentation complete
- Code follows patterns from base.py
- Backward compatibility maintained

✅ **Performance Requirements**
- Commands complete in reasonable time
- Parallel execution where beneficial
- Efficient GitHub API usage
- Minimal redundant operations

### Risk Mitigation

**Risk**: Breaking existing /copilot users
**Mitigation**: Keep old copilot.py, make orchestrator call it for backward compatibility

**Risk**: Complex state management between commands
**Mitigation**: Use JSON files as explicit state, no hidden dependencies

**Risk**: GitHub API rate limits
**Mitigation**: Implement caching, batch operations where possible

### Notes for Implementation

1. **Reuse from PR #796**: Don't reinvent - adapt existing code
2. **Keep it simple**: Each command does ONE thing
3. **Explicit > Implicit**: Clear I/O contracts, no magic
4. **Test as you go**: Verify each command before moving on
5. **Document everything**: Future you will thank present you

## Chunked Implementation Milestones

To avoid timeouts, work is broken into small, focused chunks. Each chunk should take 15-30 minutes.

### Chunk 1: Base Infrastructure Enhancement ✅
- [x] Add CI replica comparison to base.py
- [x] Create utils.py with shared GitHub/Git helpers
- [x] Test base functionality with existing commands
- **Deliverable**: Enhanced base.py, new utils.py

### Chunk 2: fixpr.py Data Collection ✅
- [x] Extract CI check methods from PR #796
- [x] Implement three-layer CI verification
- [x] Add run_ci_replica.sh execution
- [x] Output comparison.json with discrepancies
- **Deliverable**: Working fixpr.py that collects data

### Chunk 3: fixpr.md Intelligence Layer ✅
- [x] Create fixpr.md command documentation
- [x] Define analysis workflow for CI failures
- [x] Add discrepancy handling logic
- [x] Integration with fixpr.py for fixes
- **Deliverable**: Complete /fixpr hybrid command

### Chunk 4: Test /fixpr End-to-End ✅
- [x] Test with clean PR (no issues)
- [x] Test with CI failures
- [x] Test with merge conflicts
- [x] Test CI replica discrepancies
- **Deliverable**: Verified /fixpr command

### Chunk 5: copilot.md Orchestrator ✅
- [x] Create copilot.md with workflow logic
- [x] Define adaptive decision points
- [x] Add error handling strategies
- [x] Integration with all commands
- **Deliverable**: Intelligent orchestrator

### Chunk 6: Command Registration & CLI ✅
- [x] Create __init__.py with registry
- [x] Add CLI wrapper scripts
- [x] Update existing copilot.py for compatibility
- [x] Test command discovery
- **Deliverable**: Working command system

### Chunk 7: Integration Testing ✅
- [x] Test full workflow with real PR
- [x] Test error scenarios
- [x] Test partial workflows
- [x] Verify backward compatibility
- **Deliverable**: Validated system

### Chunk 8: Documentation Package ✅
- [x] Update README.md with new commands
- [x] Create individual command .md files
- [x] Add example workflows
- [x] Update this scratchpad with results
- **Deliverable**: Complete documentation

### Chunk 9: Performance & Polish
- [ ] Optimize API calls
- [ ] Add progress indicators
- [ ] Improve error messages
- [ ] Cache where beneficial
- **Deliverable**: Production-ready commands

### Chunk 10: Final Verification
- [ ] Run through all test scenarios
- [ ] Get user feedback on workflow
- [ ] Address any issues found
- [ ] Create summary report
- **Deliverable**: Completed modular copilot

### Chunk Execution Strategy
1. **Complete one chunk at a time**
2. **Test after each chunk**
3. **Commit working code frequently**
4. **Don't move forward if chunk fails**
5. **Each chunk is independently valuable**

This approach ensures:
- No timeout issues
- Incremental progress
- Easy rollback if needed
- Clear milestones
- Testable deliverables