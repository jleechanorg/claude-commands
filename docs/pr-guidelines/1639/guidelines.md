# PR #1639 Guidelines - copilot-expanded Command Specification

## 🎯 PR-Specific Principles

- **Specification Completeness**: Command specifications must include implementation algorithms, not just high-level descriptions
- **Self-Containment Claims**: Either embed all dependencies or avoid "self-contained" terminology
- **Realistic Performance Targets**: Base execution time estimates on actual tool capabilities and workflow complexity
- **Measurable Success Criteria**: Define quantifiable metrics for validation and testing

## 🚫 PR-Specific Anti-Patterns

### ❌ **Vague Implementation Specifications**
```markdown
# WRONG: Leaves implementation undefined
"Parse and categorize feedback by priority: Security, Runtime errors, Test failures"

# Problem: No algorithm specified for categorization
```

### ✅ **Concrete Implementation Details**
```markdown
# CORRECT: Provides specific implementation guidance
"Parse comments using regex patterns for categorization:
- Security: Keywords 'vulnerability', 'injection', 'auth', 'XSS', 'SQL'
- Runtime: Keywords 'error', 'exception', 'crash', 'timeout'
- Tests: Keywords 'test', 'failing', 'assertion', 'coverage'"
```

### ❌ **Contradictory Self-Containment Claims**
```markdown
# WRONG: Claims self-contained but lists external dependencies
"A complete standalone workflow... without external dependencies"
"Apply File Justification Protocol... using Edit/MultiEdit tools"

# Problem: External protocol and tool dependencies contradict claim
```

### ✅ **Accurate Dependency Documentation**
```markdown
# CORRECT: Honest about dependencies
"Comprehensive workflow that integrates with existing project protocols"
"Requires: File Justification Protocol, Edit/MultiEdit tools, git/gh CLI"
```

### ❌ **Unrealistic Performance Claims**
```markdown
# WRONG: Performance target conflicts with scope
"Target execution time: 3 minutes with comprehensive validation"
"Run comprehensive test suite, verify all concerns addressed"

# Problem: Comprehensive analysis cannot be completed in 3 minutes
```

### ✅ **Evidence-Based Performance Estimates**
```markdown
# CORRECT: Realistic timeline based on actual tool capabilities
"Estimated execution time: 5-10 minutes for comprehensive analysis"
"Performance optimized through parallel execution and targeted processing"
```

### ❌ **Unmeasurable Success Criteria**
```markdown
# WRONG: Subjective and unmeasurable criteria
"Generate detailed technical responses"
"Ensure comprehensive change summary"

# Problem: "Detailed" and "comprehensive" are subjective
```

### ✅ **Quantifiable Success Metrics**
```markdown
# CORRECT: Objective and measurable criteria
"Generate responses with minimum 50 words explaining fix rationale"
"Achieve 100% comment response rate with specific implementation details"
```

## 📋 Implementation Patterns for This PR

### **Command Specification Structure**
- **Purpose**: Clear, single-sentence functionality description
- **Workflow**: Numbered phases with specific inputs/outputs
- **Tools**: Explicit tool dependencies and integration points
- **Success Criteria**: Measurable outcomes with validation methods
- **Performance**: Evidence-based time estimates with optimization details

### **Technical Implementation Requirements**
- **Algorithm Specification**: Define categorization, parsing, and filtering logic
- **GitHub Integration**: Specify API endpoints, authentication, and error handling
- **Tool Dependencies**: Document required tools and their specific usage patterns
- **Error Handling**: Define failure scenarios and recovery mechanisms

### **Quality Validation Approaches**
- **Phase Dependencies**: Ensure each phase has defined inputs from previous phases
- **Tool Availability**: Verify all referenced tools exist and are accessible
- **Protocol Compliance**: Embed or reference external protocols explicitly
- **Performance Validation**: Base estimates on similar command benchmarks

## 🔧 Specific Implementation Guidelines

### **For Slash Command Development**
1. **Start with concrete implementation**: Define algorithms before high-level descriptions
2. **Validate tool dependencies**: Ensure all referenced tools exist and are available
3. **Test performance claims**: Benchmark similar workflows before setting time targets
4. **Define measurable outcomes**: Use quantifiable success criteria for validation

### **For Specification Writing**
1. **Avoid "self-contained" unless truly isolated**: Embed dependencies or remove claim
2. **Provide implementation examples**: Show concrete code or logic patterns
3. **Include error handling**: Document failure scenarios and recovery mechanisms
4. **Base performance on evidence**: Use actual tool benchmarks for time estimates

### **For Quality Assurance**
1. **Implementation feasibility check**: Verify every described action is implementable
2. **Dependency audit**: Ensure all tools and protocols are available and documented
3. **Performance reality check**: Compare time estimates with similar command execution
4. **Success criteria validation**: Confirm all criteria are objectively measurable

## 🏗️ Architecture Insights

### **Command System Integration**
- New commands must fit existing command architecture patterns
- Integration with File Justification Protocol requires explicit embedding or clear referencing
- Performance claims should align with existing command benchmarks (5-10 minutes for comprehensive analysis)

### **Specification Best Practices**
- Implementation details are more valuable than high-level descriptions
- Tool dependencies should be explicitly documented and validated
- Success criteria must be testable and measurable
- Error handling should be specified for each major operation

### **Quality Gates for Future Command Specifications**
1. **Implementation Completeness**: Every described action has implementation guidance
2. **Dependency Accuracy**: All tool and protocol dependencies are valid and accessible
3. **Performance Realism**: Time estimates based on actual benchmarks
4. **Measurable Outcomes**: Success criteria can be objectively validated

This PR demonstrates the importance of balancing ambitious functionality with realistic implementation details and honest dependency documentation.
