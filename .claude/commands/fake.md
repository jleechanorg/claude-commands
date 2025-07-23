# Fake Code Detection Command - /fake

**Purpose**: Detect fake, demo, or simulated code that isn't truly working using Memory MCP-enhanced pattern recognition

**Usage**: `/fake` - Memory-enhanced comprehensive audit for non-functional code patterns

## 🚨 COMMAND COMPOSITION

This command combines: `/arch /thinku /devilsadvocate /diligent`

**Composition Logic**:
- **Architecture Analysis** (/arch): Understand system design and integration points
- **Deep Thinking** (/thinku): Thorough analysis of code functionality
- **Devil's Advocate** (/devilsadvocate): Challenge assumptions about what works
- **Diligent Review** (/diligent): Methodical examination of implementation details

## 🔍 DETECTION TARGETS

### Primary Patterns (from CLAUDE.md violations)
- **Placeholder Comments**: `# Note: In the real implementation`
- **Demo Files**: Non-functional demonstration code
- **Fake Intelligence**: Python files simulating .md logic
- **Duplicate Protocols**: Reimplemented existing functionality
- **Template Responses**: Generic replies without real analysis
- **Mock Implementations**: Functions that simulate rather than implement

### Code Quality Indicators
- **TODO/FIXME**: Unfinished implementation markers
- **Hardcoded Values**: Non-configurable demo data
- **Missing Error Handling**: Code that works only in perfect conditions
- **Incomplete Integration**: Functions that don't connect to real systems
- **Test-Only Logic**: Code that only works in test environments

## 🎯 ANALYSIS SCOPE

### Branch Comparison
- **Local vs Main**: Compare current branch against main branch
- **Local vs Remote PR**: Compare against remote PR if exists
- **Integration Points**: Check how changes affect existing systems
- **Dependency Analysis**: Verify all dependencies are real and functional

### File Type Focus
- **Python Files**: Check for actual functionality vs simulation
- **Configuration**: Verify settings connect to real services
- **Scripts**: Ensure automation actually works
- **Tests**: Distinguish real tests from fake validations
- **Documentation**: Flag docs describing non-existent features

## 🚨 EXECUTION PROTOCOL

### Phase 0: Memory Enhancement (Memory MCP Integration)
**Historical Pattern Learning**:
- Search Memory MCP for previously detected fake patterns: `mcp__memory-server__search_nodes("fake_patterns OR placeholder_code OR demo_files")`
- Query for codebase-specific fake pattern knowledge: `mcp__memory-server__search_nodes("fake code patterns [current_branch] [file_type]")`
  - **[current_branch]**: Replace with the name of the branch you are currently working on (e.g., `feature/new-feature` or `bugfix/issue-123`).
  - **[file_type]**: Replace with the type of file being analyzed (e.g., `python`, `config`, `script`, `test`, or `documentation`).
  - **Example**: `mcp__memory-server__search_nodes("fake code patterns feature/new-feature python")`
  - **[current_branch]**: Replace with the name of the branch you are currently working on (e.g., `feature/new-feature` or `bugfix/issue-123`)
  - **[file_type]**: Replace with the type of file being analyzed (e.g., `python`, `config`, `script`, `test`, or `documentation`)
  - **Example**: `mcp__memory-server__search_nodes("fake code patterns feature/new-feature python")`
- Retrieve context on areas prone to fake implementations
- Load learned detection strategies and their effectiveness
- **Log**: "🔍 Memory searched: X relevant fake patterns found"
- **Integration**: Use memory context to inform all subsequent analysis phases

### Phase 1: Architecture Analysis (/arch)
**System Understanding**:
- Map current system architecture
- Identify integration boundaries
- Understand data flow and dependencies
- Analyze how changes fit into existing system

### Phase 2: Deep Thinking (/thinku)
**Thorough Code Analysis**:
- Trace execution paths through new code
- Verify each function actually performs its stated purpose
- Check error handling and edge cases
- Analyze resource usage and performance implications

### Phase 3: Devil's Advocate (/devilsadvocate)
**Challenge Assumptions**:
- Question whether code actually works as claimed
- Look for scenarios where code would fail
- Challenge integration assumptions
- Verify all dependencies are available and functional

### Phase 4: Diligent Review (/diligent)
**Methodical Examination**:
- Line-by-line code review for fake patterns
- Verify all imports resolve to real modules
- Check configuration values point to real resources
- Validate test assertions match actual behavior

### Phase 5: Memory Persistence (Store Learnings)
**Knowledge Capture for Future Detection**:
- Create entities for new fake patterns discovered: `mcp__memory-server__create_entities([{name: "hardcoded_demo_data", entityType: "fake_code_pattern", observations: ["Hardcoded values found in demo.py", "demo.py, test_demo.py", "Identified by static analysis of hardcoded strings"]}])`
- Store relationships between fake patterns and file types/areas
- Record detection strategy effectiveness and user feedback
- Add observations to existing fake pattern entities if updating knowledge
- **Log**: "📚 Stored X new fake patterns in memory for future detection"
- **Benefits**: Builds persistent knowledge base for improved future detection

## 📋 DETECTION CHECKLIST

### Code Functionality
- [ ] All functions perform actual work (not just return mock data)
- [ ] Error handling exists and works with real failures
- [ ] External dependencies are real and accessible
- [ ] Configuration values connect to actual services
- [ ] Integration points function bidirectionally

### Implementation Quality
- [ ] No placeholder comments or TODOs in production code
- [ ] No hardcoded demo data masquerading as real functionality
- [ ] No duplicate implementations of existing systems
- [ ] No Python files simulating .md file logic
- [ ] No fake response generation using templates

### System Integration
- [ ] New code integrates with existing architecture
- [ ] Database connections use real schemas
- [ ] API calls reach actual endpoints
- [ ] File operations work with real file systems
- [ ] Authentication connects to real identity providers

## 🔍 REPORTING FORMAT

### Summary Report
```text
🚨 FAKE CODE AUDIT RESULTS (Memory-Enhanced)

📊 Files Analyzed: X
⚠️  Fake Patterns Found: Y  
✅ Verified Working Code: Z
🧠 Memory Patterns Used: A
📚 New Patterns Learned: B

🔍 MEMORY-ENHANCED DETECTION:
- [Patterns detected using historical knowledge]
- [Areas flagged based on past fake implementations]
- [Detection strategies informed by memory context]

🔴 CRITICAL ISSUES:
- [List fake implementations requiring immediate attention]

🟡 SUSPICIOUS PATTERNS:
- [List code that may be fake or incomplete]

✅ VERIFIED FUNCTIONAL:
- [List code confirmed to work correctly]

🧠 KNOWLEDGE CAPTURED:
- [New fake patterns stored for future detection]
- [Updated pattern entities with additional observations]
```

### Detailed Findings
For each fake pattern found:
- **File**: Exact location (file:line)
- **Pattern**: Type of fake implementation
- **Evidence**: Code snippet showing the issue
- **Impact**: How this affects system functionality  
- **Recommendation**: Specific action to resolve the issue

## 🧠 MEMORY-ENHANCED DETECTION BENEFITS

### Learning from History
**Pattern Recognition**: Memory MCP stores examples of fake patterns found in this codebase, enabling faster recognition of similar issues.

**Context Awareness**: The system learns which files, directories, or code areas tend to contain fake implementations.

**Strategy Evolution**: Detection approaches are refined based on what works well for this specific project.

### Continuous Improvement
**False Positive Reduction**: Memory helps distinguish between legitimate code and fake patterns by learning from corrections.

**Codebase-Specific Intelligence**: Understanding of project conventions helps identify what constitutes "fake" vs acceptable code.

**Cross-Session Knowledge**: Insights persist across different analysis sessions, building comprehensive detection capabilities.

### Memory Integration Flow
1. **Search**: Query memory for relevant fake patterns before analysis
2. **Analyze**: Use memory context to enhance detection accuracy  
3. **Learn**: Store new findings and update existing knowledge
4. **Evolve**: Each run improves future detection capabilities

## 🛠️ REMEDIATION GUIDANCE

### Immediate Actions
1. **Remove Fake Files**: Delete files that serve no functional purpose
2. **Fix Placeholder Code**: Replace comments with actual implementations
3. **Consolidate Duplicates**: Remove duplicate implementations, use existing systems
4. **Verify Integration**: Test that code actually works with real systems

### Long-term Prevention
1. **Code Review Standards**: Establish detection criteria for reviews
2. **Testing Requirements**: Mandate real functionality verification
3. **Integration Testing**: Ensure all code works with actual dependencies
4. **Documentation Accuracy**: Keep docs aligned with actual implementation

## 🎯 SUCCESS CRITERIA

**Command Succeeds When**:
- All fake/demo/simulated code is identified
- Each finding includes specific evidence and location
- Recommendations are actionable and specific
- Both local branch and PR context are analyzed
- Integration points are verified for real functionality
- **Memory MCP successfully queried** for historical fake patterns
- **New learnings stored** in Memory MCP for future detection improvement
- **Memory context integrated** naturally into analysis phases

**Red Flags Requiring Attention**:
- Files with placeholder comments in production areas
- Functions that only return mock data
- Duplicate implementations of existing functionality
- Code that works only in test environments
- Integration points that don't connect to real systems