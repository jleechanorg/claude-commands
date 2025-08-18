# PR #1368 Guidelines - Git Worktree Isolation for Copilotsuper Command

**PR**: #1368 - feat: Add git worktree isolation to copilotsuper command  
**Created**: August 18, 2025  
**Purpose**: Specific guidelines for orchestration system security and architecture improvements

## Scope
- This document contains PR #1368-specific deltas, evidence, and decisions.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### 1. **Security-First Orchestration**
- **Principle**: All orchestration operations must operate within explicit security boundaries
- **Application**: Remove `--dangerously-skip-permissions` flag before merge
- **Evidence**: Security assessment identified critical vulnerabilities requiring immediate attention

### 2. **Unified Naming System Excellence**
- **Principle**: Agent and workspace names must align perfectly for operational clarity
- **Application**: Maintain the elegant naming abstraction established in this PR
- **Evidence**: TDD tests in `test_unified_naming.py` demonstrate comprehensive coverage

### 3. **Architectural Maturity Over Quick Fixes**
- **Principle**: Prefer well-architected solutions that enable future extensibility
- **Application**: The modular design patterns in this PR should be template for future work
- **Evidence**: Code review identified 9/10 architectural quality score

## 🚫 PR-Specific Anti-Patterns

### **Security Anti-Patterns**
- ❌ **NEVER use `--dangerously-skip-permissions`** in production code paths
- ❌ **NEVER accept unsanitized user input** for subprocess operations
- ❌ **NEVER run subprocess calls** without explicit timeouts and resource limits
- ❌ **NEVER inherit excessive permissions** in spawned processes

### **Implementation Anti-Patterns**
- ❌ **NEVER create backup files** when git provides version control (`file_v2.py`, `backup_implementation.py`)
- ❌ **NEVER skip comprehensive input validation** for orchestration commands
- ❌ **NEVER assume subprocess success** without explicit error handling
- ❌ **NEVER hardcode resource limits** without configuration flexibility

## 📋 Implementation Patterns for This PR

### **Successful Architecture Patterns**
1. **TDD-First Development**: Comprehensive test coverage before implementation
2. **Modular Component Design**: Clean separation between dispatching and execution
3. **Configuration Extraction**: Elegant parsing of workspace config from descriptions
4. **Graceful Degradation**: Appropriate fallback mechanisms for edge cases

### **Working Security Patterns** (To Be Implemented)
1. **Capability-Based Permissions**: Explicit resource boundaries for orchestration
2. **Input Sanitization Pipeline**: Multi-layer validation for user-provided data
3. **Subprocess Sandboxing**: Container or cgroup-based isolation
4. **Resource Monitoring**: Real-time tracking of CPU, memory, and disk usage

### **Effective Testing Patterns**
1. **Collision Handling Tests**: Verify meaningful names preserved during conflicts
2. **Configuration Parsing Tests**: Validate workspace config extraction accuracy
3. **Integration Testing**: End-to-end agent-workspace coordination verification
4. **Failure Mode Testing**: Error conditions and recovery mechanisms

## 🔧 Specific Implementation Guidelines

### **Security Implementation Requirements**
- **Input Validation**: All user inputs must pass through sanitization pipeline
- **Resource Limits**: Explicit CPU, memory, and disk quotas for all spawned processes
- **Permission Model**: Capability-based system with minimal required privileges
- **Audit Logging**: Comprehensive logging of all security-relevant operations

### **Performance Implementation Standards**
- **Agent Pooling**: Reuse idle agents instead of creating new instances
- **Async Processing**: Non-blocking task submission and status monitoring
- **Caching Strategy**: Cache system state to reduce redundant subprocess calls
- **Resource Optimization**: Monitor and optimize tmux integration overhead

### **Code Quality Requirements**
- **TDD Methodology**: Tests written before implementation for all new features
- **Error Handling**: Explicit error cases with specific error messages and context
- **Documentation**: Inline documentation for complex orchestration logic
- **Monitoring Integration**: Structured logging with correlation IDs for debugging

### **Integration Testing Standards**
- **End-to-End Scenarios**: Complete workflow testing from task submission to completion
- **Failure Recovery**: Test automated recovery from common failure modes
- **Security Boundary Testing**: Verify enforcement of permission and resource limits
- **Performance Benchmarking**: Baseline metrics for agent creation and coordination

---

## 🚨 **CRITICAL DECISION LOG**

### **Security Decision: Remove Dangerous Permissions Flag**
- **Decision**: `--dangerously-skip-permissions` flag must be removed before merge
- **Rationale**: Creates unacceptable security exposure for arbitrary code execution
- **Alternative**: Implement capability-based permissions with explicit resource grants
- **Timeline**: Must be completed before PR approval

### **Architecture Decision: Maintain Unified Naming System**
- **Decision**: Keep the elegant agent-workspace naming abstraction
- **Rationale**: Provides clear operational benefits and clean abstraction layer
- **Evidence**: Comprehensive test coverage demonstrates robustness
- **Timeline**: Ready for merge once security issues resolved

### **Performance Decision: Defer Agent Pooling**
- **Decision**: Implement agent pooling in subsequent PR
- **Rationale**: Current performance adequate for development workloads
- **Evidence**: Performance assessment showed 7/10 score with clear optimization path
- **Timeline**: Target for next performance-focused iteration

---

**Status**: Active development - Security hardening in progress  
**Last Updated**: August 18, 2025  
**Next Review**: After security implementation completion