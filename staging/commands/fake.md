# Fake Code Detection Command

**Purpose**: Detect fake, demo, or simulated code that isn't truly working using Memory MCP-enhanced pattern recognition

**Usage**: `/fake` - Memory-enhanced comprehensive audit for non-functional code patterns

## 🔄 RELATED COMMANDS

**Light Alternative**: For quick screening, use `/fakel` command which provides the same detection patterns with faster analysis (4 thoughts vs 10+ thoughts).

## 🚨 COMMAND COMPOSITION

This command combines: `/arch /thinku /devilsadvocate /diligent`

**⚠️ CRITICAL**: This composition MUST be executed with Memory MCP integration as described in the Execution Protocol below. The Memory MCP operations are MANDATORY, not optional.

**Composition Logic**:
- **Architecture Analysis** (/arch): Understand system design and integration points
- **Deep Thinking** (/thinku): Thorough analysis of code functionality (10+ thoughts)
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

**⚠️ MANDATORY**: When executing /fake, you MUST perform the Memory MCP operations described below. These are NOT optional documentation - they are required execution steps.

### Phase 0: Memory Enhancement (Memory MCP Integration)
**ACTUAL IMPLEMENTATION STEPS**:

1. **Search for existing fake patterns**:
   ```python
   🔍 Searching memory for fake patterns...
   result1 = mcp__memory-server__search_nodes("fake_patterns OR placeholder_code OR demo_files OR fake_implementation")
   ```

2. **Get branch-specific patterns**:
   ```python
   import subprocess
   current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
   result2 = mcp__memory-server__search_nodes(f"fake patterns {current_branch}")
   ```

3. **Log results**:
   - Show: "🔍 Memory searched: {len(result1.entities + result2.entities)} relevant fake patterns found"
   - If patterns found, list them briefly
   - Use these patterns to inform subsequent analysis

**Integration**: The memory context MUST inform all subsequent analysis phases

### Enhanced Composition Execution

Execute the composed commands WITH memory context awareness:

### Phase 1: Architecture Analysis (/arch)
**System Understanding** (enhanced with memory):
- Map current system architecture
- Pay special attention to areas where fake patterns were previously found
- Identify integration boundaries
- Understand data flow and dependencies
- Analyze how changes fit into existing system

### Phase 2: Deep Thinking (/thinku)
**Thorough Code Analysis** (10+ thoughts, informed by memory):
- Trace execution paths through new code
- Verify each function actually performs its stated purpose
- Check for patterns similar to remembered fake implementations
- Check error handling and edge cases
- Analyze resource usage and performance implications

### Phase 3: Devil's Advocate (/devilsadvocate)
**Challenge Assumptions** (using historical knowledge):
- Question whether code actually works as claimed
- Look for scenarios where code would fail
- Use past fake patterns to challenge current implementations
- Challenge integration assumptions
- Verify all dependencies are available and functional

### Phase 4: Diligent Review (/diligent)
**Methodical Examination** (with specific attention to problem areas):
- Line-by-line code review for fake patterns
- Focus on file types/areas that historically had fake implementations
- Verify all imports resolve to real modules
- Check configuration values point to real resources
- Validate test assertions match actual behavior

### Phase 5: Memory Persistence (Store Learnings)
**ACTUAL IMPLEMENTATION STEPS**:

After analysis completes, store new findings:

1. **For each fake pattern found**:
   ```python
   pattern_name = f"{pattern_type}_{timestamp}"
   mcp__memory-server__create_entities([{
     "name": pattern_name,
     "entityType": "fake_code_pattern",
     "observations": [
       "Description of pattern",
       f"Location: {file}:{line}",
       f"Detection method: {method}",
       f"Found on branch: {current_branch}",
       f"Detected by: /fake command"
     ]
   }])
   ```

2. **Create relationships** (if applicable):
   ```python
   mcp__memory-server__create_relations([{
     "from": pattern_name,
     "to": component_name,
     "relationType": "found_in"
   }])
   ```

3. **Log storage**:
   - Show: "📚 Stored {count} new fake patterns in memory for future detection"
   - List what was stored for transparency

**Benefits**: Builds persistent knowledge base for improved future detection

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
