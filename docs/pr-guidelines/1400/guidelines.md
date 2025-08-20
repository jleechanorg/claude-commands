# PR #1400 Guidelines - Memory MCP Dropbox-like Synchronization System

**PR**: #1400 - Memory MCP Dropbox-like Synchronization System
**Created**: 2025-08-20
**Purpose**: Security and architecture guidelines for CRDT-based memory synchronization systems

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1400.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### CRDT Memory Synchronization Patterns
- **Last-Write-Wins Strategy**: Appropriate for Memory MCP where latest version typically wins
- **Git as Transport Layer**: Leverage proven distributed version control for conflict-free distributed sync
- **Dual Format Architecture**: Clean separation between Git storage (JSONL) and MCP usage (JSON array)
- **Eventual Consistency**: Design for network partition tolerance with graceful offline fallback

### Multi-Machine Security Requirements
- **Repository URL Validation**: Always validate Git repository ownership before clone operations
- **Atomic Format Conversion**: Implement temporary files with atomic `mv` for JSONL ↔ JSON conversion
- **Path Sanitization**: Comprehensive validation of all file paths to prevent directory traversal
- **Shell Injection Prevention**: Never use variable substitution in inline Python scripts

## 🚫 PR-Specific Anti-Patterns

### Critical Security Anti-Patterns
- ❌ **Shell Variable Substitution in Python**: `python3 -c "repo_file = '$REPO_FILE'"` (shell injection risk)
- ❌ **Unvalidated Git Clones**: Direct cloning without repository URL verification
- ❌ **Non-Atomic Dual Format Updates**: Format conversion outside Git transactions
- ❌ **Hardcoded Repository Paths**: Different defaults causing configuration drift

### Performance Anti-Patterns
- ❌ **O(n) Processing on Every Sync**: Processing entire memory set instead of deltas
- ❌ **No Clock Skew Handling**: Simple timestamp comparison without timezone/drift consideration
- ❌ **Missing Incremental Sync**: No Git diff utilization for changed-only processing
- ❌ **Synchronous Format Conversion**: Blocking operations for large memory sets

### Architecture Anti-Patterns
- ❌ **Race Conditions in CRDT Merge**: Concurrent access during format conversion windows
- ❌ **Missing Error Recovery**: No rollback mechanisms for partial operations
- ❌ **Configuration Fragmentation**: Multiple hardcoded paths instead of centralized configuration
- ❌ **Missing Resource Cleanup**: No cleanup for temporary files on error paths

## 📋 Implementation Patterns for This PR

### Security Implementation Patterns
```bash
# ✅ GOOD: Safe JSON processing with jq
jq -s 'map(select(. != null))' "$REPO_FILE" > "$CACHE_FILE"

# ✅ GOOD: Repository URL validation
if [[ ! "$REPO_URL" =~ ^https://github\.com/jleechanorg/ ]]; then
    echo "❌ Invalid repository URL: $REPO_URL"
    exit 1
fi

# ✅ GOOD: Atomic format conversion
temp_file=$(mktemp)
convert_format "$input" > "$temp_file" && mv "$temp_file" "$output"
```

### CRDT Implementation Patterns
```python
# ✅ GOOD: Logical clock for conflict resolution
def get_memory_timestamp(memory):
    """Extract timestamp with logical clock fallback"""
    timestamp = memory.get('timestamp', '1970-01-01T00:00:00Z')
    logical_clock = memory.get('logical_clock', 0)
    return (timestamp, logical_clock)

# ✅ GOOD: Content-based ID generation for missing IDs
def get_stable_id(memory):
    """Generate stable ID based on content hash"""
    if 'id' in memory:
        return memory['id']
    content_hash = hashlib.sha256(json.dumps(memory, sort_keys=True).encode()).hexdigest()[:8]
    return f"memory_{content_hash}"
```

### Performance Optimization Patterns
```bash
# ✅ GOOD: Incremental sync using Git diff
git diff --name-only HEAD~1 HEAD | grep "memory\.json" && needs_merge=true

# ✅ GOOD: Centralized configuration
REPO_DIR="${WORLDARCHITECT_MEMORY_REPO_DIR:-$HOME/projects/worldarchitect-memory-backups}"
```

## 🔧 Specific Implementation Guidelines

### Security Requirements (MANDATORY)
1. **Shell Script Safety**:
   - Use `jq` for JSON processing instead of Python inline scripts
   - Add `set -euo pipefail` to all shell scripts
   - Implement comprehensive path validation with whitelist patterns
   - Add timeout protection to all network operations

2. **Git Operations Security**:
   - Validate repository URLs before any clone/pull operations
   - Implement signed commit verification for production deployments
   - Use `git pull --rebase` with autostash for conflict avoidance
   - Add proper error recovery for failed Git operations

3. **Format Conversion Safety**:
   - Implement atomic conversion using temporary files + `mv`
   - Add JSON validation before writing to cache
   - Include data integrity checks (SHA256) for large transfers
   - Ensure proper cleanup on conversion failures

### Performance Requirements
1. **Incremental Processing**:
   - Use Git diff to identify changed memories only
   - Implement delta-based sync for large memory sets
   - Add adaptive scheduling based on activity levels
   - Consider binary format for very large datasets

2. **CRDT Optimization**:
   - Add logical clocks for true conflict-free resolution
   - Implement content-based IDs for stable identity
   - Handle timezone differences and clock skew
   - Add vector timestamps for concurrent modification detection

### Architecture Requirements
1. **Configuration Management**:
   - Centralize all paths in environment variables
   - Create shared configuration module for Python scripts
   - Implement unified error handling across all scripts
   - Add proper logging using `logging_util` instead of `print`

2. **Error Recovery**:
   - Implement rollback mechanisms for partial operations
   - Add backup creation before destructive operations
   - Ensure graceful degradation on network failures
   - Implement proper resource cleanup in finally blocks

## 🎯 MVP Shipping Criteria

### Ship Blockers (Must Fix)
- [ ] Shell injection vulnerability in `fetch_memory.sh`
- [ ] Git repository URL validation
- [ ] Atomic format conversion implementation
- [ ] Comprehensive path sanitization

### Quality Gates (Should Fix)
- [ ] Logical clocks for CRDT conflict resolution
- [ ] Incremental sync using Git diffs
- [ ] Centralized repository path configuration
- [ ] Error recovery and rollback mechanisms

### Future Enhancements (Post-MVP)
- [ ] Event sourcing pattern for memory operations
- [ ] Real-time sync using file watchers
- [ ] Monitoring and alerting dashboard
- [ ] Schema versioning for memory format evolution

## 📊 Success Metrics

### Security Metrics
- Zero shell injection vulnerabilities in static analysis
- 100% repository URL validation coverage
- All format conversions atomic and validated
- No hardcoded paths in production deployments

### Performance Metrics
- Sync latency under 5 seconds for normal loads (< 100 memories)
- Memory growth handling up to 10,000 entries
- Network partition recovery within 2 sync cycles
- CPU usage under 10% during background sync

### Reliability Metrics
- 99.9% sync success rate in normal conditions
- Zero data loss during conflict resolution
- Graceful degradation with network issues
- Complete recovery from partial failures

## 📝 Decision Log

### Architecture Decisions
1. **CRDT Strategy**: Chose Last-Write-Wins over vector clocks for simplicity
2. **Transport Layer**: Git selected over direct database sync for proven reliability
3. **Format Design**: Dual format (JSONL/JSON) for Git compatibility vs MCP requirements
4. **Conflict Resolution**: Timestamp-based with logical clock fallback

### Security Decisions
1. **Repository Validation**: Whitelist approach for trusted repository URLs
2. **Shell Script Safety**: jq replacement for Python inline scripts
3. **Atomic Operations**: Temporary file pattern for all format conversions
4. **Error Handling**: Graceful degradation over hard failures

### Performance Decisions
1. **Sync Frequency**: 15-minute intervals as compromise between freshness and overhead
2. **Processing Strategy**: Full merge initially, incremental as optimization
3. **Scaling Approach**: Git compression and deduplication for storage efficiency
4. **Format Optimization**: JSON/JSONL balance for human readability vs performance

---

**Status**: Complete - Comprehensive guidelines for Memory MCP sync system
**Last Updated**: 2025-08-20