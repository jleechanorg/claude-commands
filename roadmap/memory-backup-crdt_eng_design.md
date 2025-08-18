# Memory Backup CRDT Engineering Design

## Table of Contents
1. [Engineering Goals](#engineering-goals)
2. [Engineering Tenets](#engineering-tenets)
3. [Technical Overview](#technical-overview)
4. [System Design](#system-design)
5. [Implementation Plan](#implementation-plan)
6. [Quality Assurance](#quality-assurance)
7. [Testing Strategy](#testing-strategy)
8. [Risk Assessment](#risk-assessment)
9. [Decision Records](#decision-records)
10. [Rollout Plan](#rollout-plan)
11. [Monitoring & Success Metrics](#monitoring--success-metrics)

## Engineering Goals

### Primary Engineering Goals
- **Goal 1**: Achieve 100% data preservation in parallel backup scenarios [Baseline: 85% with race conditions]
- **Goal 2**: Sub-second merge performance for 10,000 entries [Target: <500ms]
- **Goal 3**: Zero coordination overhead - no distributed locks [Current: Git lock attempts cause 30s delays]

### Secondary Engineering Goals
- Simplify codebase by removing complex locking logic
- Improve developer productivity with reliable backups
- Reduce operational overhead - no lock cleanup needed

## Engineering Tenets

### Core Principles
1. **Eventually Consistent**: Accept temporary divergence, guarantee convergence
2. **Lock-Free Design**: No distributed coordination required
3. **Deterministic Merging**: Same inputs always produce same output
4. **Fail-Safe Operations**: Local backup preservation on any failure
5. **Idempotent Actions**: Operations can be safely retried

### Quality Standards
- All operations must be atomic at file level
- No data loss under any failure scenario
- Comprehensive logging for debugging
- Exponential backoff for network operations

## Technical Overview

### Architecture Approach
The CRDT-based memory backup system uses a **state-based CRDT (CvRDT)** approach where each environment maintains its own state and periodically synchronizes with the central repository. The merge operation uses a **grow-only set (G-Set)** semantic with last-write-wins conflict resolution for identical IDs.

### Technology Choices
- **Python 3.11+**: Primary implementation language for clean CRDT algorithms
- **Native JSON**: Built-in `json` module for data processing
- **Git**: Distributed version control for state synchronization (via subprocess)
- **CRDT Type**: State-based G-Set with LWW (Last-Write-Wins)
- **Testing**: pytest with property-based testing (hypothesis)

### Integration Points
- `memory.json`: Source memory file from each environment
- `memory-${HOSTNAME}.json`: Environment-specific backup files
- `unified-memory.json`: Merged CRDT result
- Git repository: Synchronization medium

## System Design

### Component Architecture

```
┌─────────────────────────────────────────────────┐
│                 Environment A                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ memory.  │→ │ CRDT Prepare │→ │ memory-  │  │
│  │ json     │  │ (metadata)   │  │ hostA.   │  │
│  └──────────┘  └──────────────┘  │ json     │  │
│                                   └──────────┘  │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│                Git Repository                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ memory-  │  │ memory-  │  │ unified-     │  │
│  │ hostA.   │  │ hostB.   │  │ memory.json  │  │
│  │ json     │  │ json     │  │ (CRDT merge) │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────┐
│                 Environment B                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ memory.  │→ │ CRDT Prepare │→ │ memory-  │  │
│  │ json     │  │ (metadata)   │  │ hostB.   │  │
│  └──────────┘  └──────────────┘  │ json     │  │
│                                   └──────────┘  │
└─────────────────────────────────────────────────┘
```

### CRDT Data Structure

```json
{
  "id": "original_id",
  "content": "...",
  "_crdt_metadata": {
    "host": "hostname",
    "timestamp": "2025-01-01T00:00:00Z",
    "version": 1,
    "unique_id": "hostname_originalid_timestamp"
  }
}
```

### Merge Algorithm

```python
def crdt_merge(memory_files: List[str]) -> List[dict]:
    """
    Merge multiple memory files using CRDT semantics.
    
    1. Collect all entries from all memory-*.json files
    2. Group by unique_id
    3. For duplicates, keep entry with latest timestamp (LWW)
    4. Sort by original timestamp for readability
    5. Return unified result
    """
    merged = {}
    for file_path in memory_files:
        with open(file_path) as f:
            entries = json.load(f)
            for entry in entries:
                uid = entry['_crdt_metadata']['unique_id']
                if uid not in merged or entry['_crdt_metadata']['timestamp'] > merged[uid]['_crdt_metadata']['timestamp']:
                    merged[uid] = entry
    return sorted(merged.values(), key=lambda x: x['_crdt_metadata']['timestamp'])
```

### State Synchronization Flow

1. **Local Backup**: Save memory.json with CRDT metadata
2. **Git Pull**: Fetch latest state from repository
3. **Merge**: Apply CRDT merge algorithm
4. **Commit**: Atomic commit of changes
5. **Push**: Upload with exponential backoff on conflicts

## Implementation Plan

### AI-Assisted Timeline (Claude Code CLI)

#### Phase 1: Core CRDT Implementation (15 min - 2 agents parallel)
- **Agent 1**: CRDT metadata injection and unique ID generation (~150 lines)
- **Agent 2**: Merge algorithm implementation (~200 lines)

#### Phase 2: Git Integration (15 min - 2 agents parallel)
- **Agent 3**: Atomic Git operations with retry logic (~150 lines)
- **Agent 4**: Conflict detection and resolution (~100 lines)

#### Phase 3: Testing & Validation (15 min - 2 agents parallel)
- **Agent 5**: Parallel backup test suite (~200 lines)
- **Agent 6**: Stress testing and edge cases (~150 lines)

#### Phase 4: Integration & Documentation (15 min - 1 agent)
- **Agent 7**: Integration with existing backup script (~100 lines)
- Documentation and rollout preparation

**Total: 60 minutes** (vs 3-5 days traditional development)

## Quality Assurance

### Mandatory Practices
- **Test-Driven Development**: Write parallel backup tests first
- **Property-Based Testing**: Verify CRDT properties (commutativity, associativity, idempotence)
- **Stress Testing**: 10+ parallel environments, 100K+ entries
- **Failure Injection**: Network failures, Git conflicts, disk full

### Development Standards
- All CRDT operations must be deterministic
- Comprehensive logging at each step
- Atomic file operations only
- No external service dependencies

## Testing Strategy

### Unit Tests
- CRDT metadata generation correctness
- Unique ID collision impossibility
- Merge algorithm determinism
- Timestamp parsing accuracy

### Integration Tests
- Parallel backup from 10 environments
- Git push/pull race conditions
- Network failure recovery
- Large file handling (>10MB)

### Property Tests
```python
# Using hypothesis for property-based testing
@given(memories_a=memory_strategy(), memories_b=memory_strategy())
def test_commutative_merge(memories_a, memories_b):
    """Commutativity: merge(A,B) = merge(B,A)"""
    assert crdt_merge([memories_a, memories_b]) == crdt_merge([memories_b, memories_a])

@given(memories_a=memory_strategy(), memories_b=memory_strategy(), memories_c=memory_strategy())
def test_associative_merge(memories_a, memories_b, memories_c):
    """Associativity: merge(merge(A,B),C) = merge(A,merge(B,C))"""
    left = crdt_merge([crdt_merge([memories_a, memories_b]), memories_c])
    right = crdt_merge([memories_a, crdt_merge([memories_b, memories_c])])
    assert left == right

@given(memories=memory_strategy())
def test_idempotent_merge(memories):
    """Idempotence: merge(A,A) = A"""
    assert crdt_merge([memories, memories]) == memories
```

### Acceptance Tests
- Zero data loss across 1000 parallel operations
- Performance within targets
- Automatic conflict resolution
- Backwards compatibility

## Risk Assessment

### Technical Risks
- **High Risk**: Clock skew between machines → **Mitigation**: Use monotonic clocks + sequence numbers
- **Medium Risk**: Git repository corruption → **Mitigation**: Local backup retention, validation checks
- **Low Risk**: JSON parsing failures → **Mitigation**: Schema validation, error recovery

### Dependencies & Blockers
- Python 3.11+ for modern type hints and performance
- Git 2.0+ for atomic operations
- pytest 7.0+ for testing framework
- hypothesis for property-based testing (optional but recommended)
- No external service dependencies

## Decision Records

### Decision: CRDT vs Distributed Locking
**Date**: 2025-08-18  
**Context**: Need parallel backup without coordination  
**Options**: 
1. Distributed locks (Redis, etcd)
2. Git-based locking
3. CRDT approach

**Rationale**: CRDT chosen for zero-coordination requirement and simplicity  
**Consequences**: Eventually consistent, requires merge logic  
**Review Date**: 2025-09-18

### Decision: State-based vs Operation-based CRDT
**Date**: 2025-08-18  
**Context**: Choosing CRDT implementation style  
**Options**:
1. State-based (CvRDT) - share full state
2. Operation-based (CmRDT) - share operations

**Rationale**: State-based simpler with Git, no operation log needed  
**Consequences**: Higher bandwidth but simpler implementation  
**Review Date**: 2025-09-18

## Rollout Plan

### Phase 1: Canary Deployment (Day 1-3)
- Deploy to 2-3 volunteer developers
- Monitor for data loss or errors
- Collect performance metrics

### Phase 2: Gradual Rollout (Day 4-7)
- Expand to 25% of team
- A/B test against old system
- Measure success metrics

### Phase 3: Full Deployment (Day 8-10)
- Roll out to all developers
- Deprecate old locking system
- Documentation and training

### Rollback Strategy
- Git revert to previous version
- Local backups preserved
- No data loss on rollback

## Monitoring & Success Metrics

### Logging Strategy
```bash
# Log levels and destinations
INFO:  /tmp/memory-backup.log     # Normal operations
WARN:  /tmp/memory-backup.log     # Retries, conflicts
ERROR: /tmp/memory-backup-error.log # Failures
DEBUG: /tmp/memory-backup-debug.log # Detailed trace
```

### Performance Monitoring
- Merge operation duration
- Git operation latency
- Memory file size growth
- CPU/memory usage during merge

### Success Metrics
- **Reliability**: >99.99% backup success rate
- **Performance**: <1s for typical merge
- **Correctness**: 100% data preservation
- **Adoption**: 90% usage within 2 weeks

### Alerting Thresholds
- Merge time >5 seconds
- Backup failure rate >0.1%
- Memory file >50MB
- Git push failures >3 retries