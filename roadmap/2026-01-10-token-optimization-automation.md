# Token Optimization Automation Roadmap
**Created**: 2026-01-10
**Status**: Planning
**Priority**: High (impacts developer productivity and costs)

## Problem Statement

Multi-day coding sessions (4-6 days) with 8,000-9,000+ messages are consuming 50-60% of weekly token quota even with automatic summarization enabled.

**Evidence from analysis**:
- Largest session: 8,207 messages, 27.4 MB, 4.5 days duration
- Tool calls: 2,436 (mostly full file reads, git diffs)
- Context cost: 90% (processing prior messages)
- Response cost: 10%
- Single session consumed ~50% of weekly quota

**Root cause**: Token accumulation outpaces auto-summarization benefits due to:
1. Full file reads instead of targeted line ranges
2. Large git diff payloads (no `--minimal --unified=0` flags)
3. No tool call batching (each call has overhead)
4. System prompt re-sent every turn (CLAUDE.md is ~several KB)
5. No caching of repeated tool results

## Solution Overview

Move from **declarative rules** (CLAUDE.md that agents ignore) to **hard enforcement** via runtime hooks and MCP proxy layer.

**Expected impact**: 60-70% token reduction on intensive development sessions.

## Feasibility Verification

**Verified via web search (2026-01-10)**:
- ✅ **Hooks**: [Hooks reference documentation](https://code.claude.com/docs/en/hooks) confirms PreToolUse hooks (v2.0.10+) can modify tool inputs
- ✅ **Prompt caching**: [Claude prompt caching docs](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) confirms automatic caching with cryptographic hashes
- ✅ **Read tool parameters**: [Read tool accepts `offset` and `limit`](https://code.claude.com/docs/en/cli-reference) for partial file reads (max 2000 lines default)
- ⚠️ **MCP batching proxy**: Not verified - no official documentation found for CLAUDE_API_BASE_URL proxy interception
- ⚠️ **System prompt control**: Caching is automatic, developers cannot control hash generation directly

## Concrete Implementation Tasks (REVISED - Feasible Only)

### Phase 1: Foundation (Week 1) - Hooks & Workflow Optimization

#### Task 1.1: Create Targeted Read Hook (via offset/limit)
**Goal**: Use Read tool's `offset` and `limit` parameters to reduce payload (40-50% token reduction)

**Implementation**:
- Create `.claude/hooks/PreToolUse.sh` hook (v2.0.10+ feature)
- Intercept `Read` tool calls
- Modify JSON input to add `offset` and `limit` parameters
- Calculate optimal range based on file size:
  - Files <500 lines: Read full file
  - Files 500-2000 lines: Read relevant section only
  - Files >2000 lines: Read max 2000 lines around target
- Return modified JSON to CLI

**Acceptance criteria**:
- [x] Hook intercepts all Read tool calls
- [x] Modifies input to include offset/limit
- [x] Logs original vs reduced line count
- [x] Falls back to full read if range detection fails

**Reference**: [Hooks documentation](https://code.claude.com/docs/en/hooks)

#### Task 1.2: Create Bash Command Hook for Minimal Git Diffs
**Goal**: Force minimal git diff format (30-40% token reduction)

**Implementation**:
- Create `.claude/hooks/PreToolUse.sh` hook modification
- Intercept `Bash` tool calls that contain `git diff`
- Modify command to inject `--minimal --unified=0` flags
- Pattern matching: Look for `git diff` in command string
- Preserve other git diff arguments

**Acceptance criteria**:
- [x] Hook detects git diff commands in Bash tool
- [x] Automatically adds --minimal --unified=0 flags
- [x] Preserves other user arguments
- [x] Logs original vs modified command

**Reference**: [PreToolUse hook examples](https://code.claude.com/docs/en/hooks)

#### Task 1.3: Session Management Best Practices Guide
**Goal**: Document when to use `/clear` to prevent token accumulation

**Implementation**:
- Create `docs/token-optimization-guide.md`
- Document optimal session lengths (target: <1,000 messages)
- Workflow patterns:
  - Clear after PR merge
  - Clear at end of work day
  - Clear when switching major tasks
  - Clear after test suite passes
- Add session health check script to hooks
- Warning when session exceeds 500 messages

**Acceptance criteria**:
- [ ] Guide document created
- [x] Session health check in UserPromptSubmit hook
- [x] Warning displays at 500, 1000, 2000 message thresholds
- [x] Instructions for preserving context via git commits

### Phase 2: Integration (Week 2) - Monitoring & CLAUDE.md Optimization

#### Task 2.1: Optimize CLAUDE.md for Prompt Caching
**Goal**: Leverage automatic prompt caching to reduce redundant system prompt tokens

**Implementation**:
- Understand how Claude's [prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) works
- Structure CLAUDE.md to maximize cache hits:
  - Static rules at the beginning (high cache hit rate)
  - Dynamic/project-specific content at the end
- Avoid unnecessary edits to CLAUDE.md (breaks cache)
- Monitor cache hit rates via API response headers

**Acceptance criteria**:
- [ ] CLAUDE.md restructured with static content first
- [ ] Documentation on when CLAUDE.md edits break cache
- [ ] Cache hit rate >80% after initial request
- [ ] Team trained on caching behavior

**Note**: Caching is automatic - we cannot control hashing, but we can optimize content structure.

#### Task 2.2: Implement Hook Logging System
**Goal**: Track hook modifications and measure optimization impact

**Implementation**:
- Add logging to PreToolUse hooks:
  ```bash
  # Log to /tmp/worldarchitect.ai/[branch]/hook_modifications.log
  echo "{\"timestamp\":\"$(date -Iseconds)\",\"tool\":\"Read\",\"original_params\":{...},\"modified_params\":{...}}" >> $LOG_FILE
  ```
- PostToolUse hook to capture tool result sizes
- Track metrics:
  - Tool call count per session
  - File read sizes (lines/bytes)
  - Git diff sizes
  - Session message count
- Create report script: `scripts/hook_audit_report.sh`

**Acceptance criteria**:
- [x] Hooks log all modifications
- [x] Log includes original vs modified parameters
- [x] Report script shows optimization impact
- [x] Logs organized by branch/session

#### Task 2.3: Add Session Health Monitoring
**Goal**: Warn developers when sessions are getting large

**Implementation**:
- UserPromptSubmit hook checks session size
- Count messages in current conversation file:
  ```bash
  MSG_COUNT=$(wc -l < ~/.claude/projects/*/current-session.jsonl)
  ```
- Display warnings at thresholds:
  - 500 messages: ⚠️ "Session growing large - consider /clear soon"
  - 1,000 messages: 🟠 "Large session - recommend /clear"
  - 2,000 messages: 🔴 "Very large session - /clear strongly recommended"
- Log warning display to track adherence

**Acceptance criteria**:
- [x] Hook detects session size
- [x] Warnings display at correct thresholds
- [x] Non-intrusive (doesn't block workflow)
- [x] Logged for compliance tracking

### Phase 3: Validation (Week 3) - Real-World Testing

#### Task 3.1: 3-Day Production Test
**Goal**: Measure actual token savings on real development work

**Test plan**:
1. Enable all optimizations
2. Work on normal PR for 3 days
3. Compare token usage to baseline (without optimizations)
4. Collect metrics:
   - Total messages sent
   - Total tokens consumed
   - Breakdown by optimization type
   - Conversation file sizes
   - `/clear` frequency

**Success metrics**:
- [ ] 50%+ reduction in tokens vs baseline
- [ ] Conversation size <10MB after 3 days
- [ ] No workflow disruptions
- [ ] All optimizations working (per audit log)

#### Task 3.2: Edge Case Testing
**Goal**: Ensure optimizations work in all scenarios

**Test cases**:
1. PR with 100+ file changes (large diff)
2. PR with single file change (small diff)
3. Debugging session (many file reads)
4. Test execution (verbose output)
5. Binary file handling
6. Merge conflicts
7. Submodule changes

**Acceptance criteria**:
- [ ] All test cases pass
- [ ] No crashes or errors
- [ ] Graceful fallback when optimization fails
- [ ] Edge cases documented

#### Task 3.3: Performance Tuning
**Goal**: Optimize batch window and cache settings

**Tuning parameters**:
- Batch window: Test 100ms, 200ms, 500ms
- Cache size: Test 100, 500, 1000 entries
- Prompt cache TTL: Test 1hr, 4hr, 24hr
- Read hook range: Test 50, 100, 200 lines

**Acceptance criteria**:
- [ ] Optimal batch window identified
- [ ] Cache hit rate >70%
- [ ] No noticeable latency increase
- [ ] Settings documented

### Phase 4: Rollout (Week 4) - Documentation & Training

**Note**: MCP batching proxy (originally Task 4.1) has been removed from this phase as CLAUDE_API_BASE_URL proxy interception is unverified and not officially documented. Focus on validated optimizations only.

#### Task 4.1: Team Training & Documentation
**Goal**: Enable team to use optimized workflow

**Deliverables**:
1. User guide: How optimizations work
2. Troubleshooting guide: Common issues
3. Audit report guide: Reading token savings
4. Best practices: Session management
5. FAQ: When to use `/clear`

**Acceptance criteria**:
- [ ] Documentation complete
- [ ] Team training session conducted
- [ ] Support channel established
- [ ] Feedback mechanism in place

#### Task 4.2: Monitoring & Alerting
**Goal**: Detect regressions and track improvements

**Metrics to track**:
- Weekly token consumption per developer
- Average messages per session
- Average session duration
- Cache hit rates
- Optimization application rates (% of requests)
- Token savings trend over time

**Alerts**:
- MCP unreachable
- Token usage spike (>2x baseline)
- Cache hit rate <50%
- Audit log write failures

**Acceptance criteria**:
- [ ] Metrics dashboard created
- [ ] Alerts configured
- [ ] Weekly report automated
- [ ] Regression detection working

## Success Criteria (Overall)

### Quantitative Goals
- [ ] 60-70% token reduction on intensive sessions (vs baseline)
- [ ] Average session size <10MB after 3 days
- [ ] 90%+ optimization application rate
- [ ] Cache hit rate >70%
- [ ] Zero workflow disruptions

### Qualitative Goals
- [ ] Developers unaware of optimizations (transparent)
- [ ] No manual intervention required
- [ ] CLAUDE.md rules automatically enforced
- [ ] Audit trail proves compliance
- [ ] Extensible for future optimizations

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP proxy technology unverified | High | **REMOVED FROM PLAN** - Focus only on verified optimizations (hooks, CLAUDE.md) |
| Hooks break tool functionality | High | Comprehensive testing, graceful fallback, error handling wraps jq/grep |
| Session file naming convention changes | Medium | Hook uses most recent .jsonl file (robust to naming changes) |
| Cache poisoning (wrong CLAUDE.md) | Medium | Structure CLAUDE.md with static content first (minimize edits) |
| Team resistance to session breaks | Medium | Transparent warnings (non-blocking), clear benefits in guide |
| Hook performance overhead | Low | Minimal processing (jq/grep), exit 0 on errors, async logging |

## Dependencies

**Technical**:
- Python 3.11+ (for FastAPI proxy)
- Bash 4.0+ (for hook scripts)
- Claude Code CLI v1.x (hook support)
- MCP protocol v1.x (batching support)

**Infrastructure**:
- Localhost port 8000 available (or configurable)
- File system access for audit logs
- Git 2.30+ (for `--minimal --unified=0` flags)

**Team**:
- 1 week development time
- 1 week testing time
- 1 hour training session
- Ongoing monitoring (1 hr/week)

## Timeline

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|--------|
| Phase 1: Foundation | 1 week | 2026-01-10 | 2026-01-17 | ✅ **COMPLETE** (hooks implemented) |
| Phase 2: Integration | 1 week | 2026-01-13 | 2026-01-20 | ⬜ NOT STARTED |
| Phase 3: Validation | 1 week | 2026-01-20 | 2026-01-27 | ⬜ NOT STARTED |
| Phase 4: Rollout | 1 week | 2026-01-27 | 2026-02-03 | ⬜ NOT STARTED |
| **Total** | **3-4 weeks** | **2026-01-10** | **2026-02-03** |

**Note**: Phase 1 completed ahead of schedule (same day as planning). Timeline is aggressive but achievable given immediate relief priority. Phases may overlap as hooks are tested in production.

## Related Documents

- `/tmp/token_optimization_automation_blueprint.md` - Detailed technical implementation
- `~/Downloads/claude_token_usage_analysis.md` - Original problem analysis
- `.claude/hooks/` - Hook script implementations (to be created)
- `scripts/mcp_batch_proxy.py` - Proxy implementation (to be created)

## References

1. [Anthropic Token Management](https://docs.anthropic.com/claude/reference/token-management)
2. [Git diff manual](https://git-scm.com/docs/git-diff)
3. [OpenAI Batching Guide](https://platform.openai.com/docs/guides/batch)
4. [Claude Tool-Use](https://docs.anthropic.com/claude/reference/tool-use)

## Appendix: Expected Impact Analysis

### Baseline (Current State)
```
Session duration: 4.5 days
Messages: 8,207
Tool calls: 2,436
Size: 27.4 MB
Token quota consumed: 50%
```

### After Optimization (Projected)
```
Session duration: 4.5 days (same work)
Messages: ~2,500-3,000 (-60-70%)
Tool calls: ~800-1,000 (-60-70% payload)
Size: ~8-10 MB (-70%)
Token quota consumed: 15-20% (-60-70%)
```

### Breakdown by Optimization
```
Targeted reads:          40-50% reduction
Minimal git diffs:       30-40% reduction
Batched tool calls:      20-30% reduction
Prompt deduplication:    500-800 tokens/turn
Combined effect:         60-70% total reduction
```
