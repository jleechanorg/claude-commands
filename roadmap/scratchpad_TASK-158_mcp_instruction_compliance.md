# Scratchpad: TASK-158 - MCP Instruction Compliance Tracking

**Branch**: roadmap23423g
**Priority**: Medium
**Estimated Time**: 3-4 hours
**Created**: 2025-01-10

## Goal
Implement automatic instruction compliance failure measurement for Claude using MCP (Model Context Protocol) servers, specifically by forking and customizing Invariant's MCP-scan for CLAUDE.md rule enforcement.

## Context - Conversation Summary

### The Problem
- Claude currently cannot measure its own instruction failure rate in real-time
- No persistent memory across sessions to track compliance patterns
- Existing self-monitoring in CLAUDE.md is reactive, not proactive
- Need for quantitative measurement of adherence to rules (especially meta-rules like "NO FALSE ✅", "NEVER SIMULATE", etc.)

### The Solution Discovery
Through research, we found that MCP servers can provide the missing capabilities:

1. **Persistent external memory** - Unlike Claude's session limitations
2. **Real-time monitoring** - Track all interactions through MCP protocol
3. **Security boundaries** - Protocol-layer enforcement points
4. **Existing infrastructure** - Several monitoring MCP servers already exist

### Key Research Findings

#### Existing MCP Servers for Monitoring
- **Invariant MCP-scan** - Real-time security auditing of MCP interactions (MOST RELEVANT)
- **Sentry MCP Server** - Error tracking and performance monitoring
- **Datadog MCP Server** - Comprehensive monitoring, dashboards, metrics
- **CloudWatch MCP Server** - AWS metrics, alarms, logs analysis
- **Honeybadger/Rollbar MCP** - Error tracking specialists

#### Invariant MCP-scan Details
- **Free & Open Source**: Available on GitHub
- **Real-time Proxy Mode**: Automatic continuous monitoring
- **Local Operation**: Can run with `--local-only` flag
- **Background Process**: No manual intervention required
- **Traffic Interception**: System-wide MCP monitoring
- **Policy Enforcement**: Currently security-focused, but customizable

## Implementation Plan

### Phase 1: Research & Setup (1 hour)
- [ ] Fork Invariant MCP-scan repository
- [ ] Analyze existing proxy architecture
- [ ] Understand current rule enforcement mechanisms
- [ ] Test basic installation and operation

### Phase 2: CLAUDE.md Rule Integration (2 hours)
- [ ] Parse CLAUDE.md rules into machine-readable format
- [ ] Identify key compliance patterns to track:
  - False ✅ detection (claiming completion without verification)
  - Simulation detection (fake file creation, pretending to run tests)
  - Meta-rule violations (positivity bias, excuse-making)
  - Evidence-based approach compliance
  - Test execution verification
- [ ] Replace security rules with instruction compliance rules
- [ ] Implement violation detection patterns

### Phase 3: Compliance Dashboard (1 hour)
- [ ] Create compliance metrics collection
- [ ] Build simple dashboard for viewing failure rates
- [ ] Add historical trend analysis
- [ ] Generate periodic compliance reports

## Technical Architecture

### Current MCP-scan Flow
```
Claude ↔ MCP Client ↔ [MCP-scan Proxy] ↔ MCP Server
                           ↓
                    Security Analysis
```

### Modified Flow for Compliance
```
Claude ↔ MCP Client ↔ [Custom Compliance Proxy] ↔ MCP Server
                           ↓
                    CLAUDE.md Rule Checking
                           ↓
                    Compliance Metrics DB
```

### Key Components to Modify
1. **Rule Engine**: Replace security checks with CLAUDE.md compliance
2. **Pattern Matching**: Detect false completions, simulations, meta-rule violations
3. **Metrics Collection**: Track failure rates, trends, patterns
4. **Alerting**: Real-time notifications for critical violations

## Expected Outcomes

### Quantitative Measurements
- **Instruction adherence rate** (% of responses following CLAUDE.md rules)
- **False completion rate** (% of ✅ claims without verification)
- **Simulation attempt rate** (% of responses creating fake outputs)
- **Evidence-based compliance** (% of responses with proper evidence extraction)

### Qualitative Improvements
- **Real-time feedback** for rule violations
- **Historical trend analysis** for improvement tracking
- **Pattern identification** for common failure modes
- **Proactive compliance** rather than reactive correction

## Technical Notes

### Installation Commands
```bash
# Fork and clone
git clone https://github.com/[username]/mcp-scan
cd mcp-scan
uv run pip install -e .

# Run in local-only mode
uv run -m src.mcp_scan.cli proxy --local-only
```

### Key Files to Modify
- `/src/mcp_scan/proxy.py` - Main proxy logic
- `/src/mcp_scan/rules/` - Rule definitions (replace security with compliance)
- `/src/mcp_scan/metrics/` - Metrics collection (new)

### CLAUDE.md Rules to Track
1. **Meta-Rules**:
   - "NO FALSE ✅" - Only use ✅ for 100% complete/working
   - "NEVER SIMULATE" - Ask if stuck, fake answer = 1000x worse
   - "NO POSITIVITY" - Be extremely self-critical

2. **Evidence-Based Approach**:
   - Extract exact error messages/code snippets before analyzing
   - Show actual output before suggesting fixes
   - Reference specific line numbers when debugging

3. **Test Execution**:
   - NEVER claim test completion without executing at least ONE test
   - Use ⚠️ "Created but unverified" instead of ✅ "Complete" for untested code

## Next Steps
1. Add TASK-158 to roadmap.md with medium priority
2. Add UUID mapping entry
3. Begin Phase 1 implementation when ready
4. Consider integration with existing WorldArchitect.AI monitoring infrastructure

## Context Preservation
This task emerged from a meta-discussion about Claude's ability to self-measure instruction compliance failures. The conversation revealed that while Claude has good self-monitoring protocols in CLAUDE.md, it lacks the persistent memory and real-time feedback mechanisms needed for quantitative compliance measurement. MCP servers provide the missing infrastructure for this capability.

The discovery of Invariant's MCP-scan was particularly significant because it already implements the exact architecture needed (real-time proxy monitoring with rule enforcement), just focused on security rather than instruction compliance. This makes it an ideal foundation for building instruction compliance tracking.
