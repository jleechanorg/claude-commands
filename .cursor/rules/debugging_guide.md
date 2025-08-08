# Systematic Debugging Guide

**Purpose**: Comprehensive debugging methodologies to prevent inefficient debugging sessions and ensure systematic problem resolution.

## 🚨 Critical Debugging Protocols

### User Evidence Primacy Protocol

**When to Apply**: Any time user provides screenshots, observations, or evidence that contradicts Claude's automated observations

**Steps**:
1. **Treat User Evidence as Ground Truth**: Never dismiss or assume Claude's view is more accurate
2. **Immediate Investigation**: Ask "Why am I seeing different results than the user?"
3. **Discrepancy Analysis**: Focus on understanding the difference, not defending automated results
4. **Root Cause First**: Investigate the discrepancy before attempting fixes

**Common Anti-Patterns**:
- ❌ Assuming automated tests/screenshots are more reliable than user evidence
- ❌ Working around user observations instead of investigating them
- ❌ Dismissing user evidence as "user error" or environmental issues

### Cross-Version Systematic Debugging

**When to Apply**: Debugging issues between V1/V2 or any version comparison scenarios

**Systematic Order**:
1. **Side-by-Side Code Comparison**: Compare equivalent components immediately
2. **Data Flow Tracing**: API → Database → UI in both versions systematically  
3. **Architectural Gap Identification**: Focus on missing functionality, not symptoms
4. **Implementation with Conversion**: Add missing functionality with proper data format conversion

**Time Target**: 15-20 minutes for architectural gap identification

**Example Applications**:
- V1 server-side vs V2 client-side data loading patterns
- Legacy API vs modernized API integration differences
- Authentication flow differences between implementations

### Evidence-Based Debugging Workflow

**Phase 1: Evidence Gathering**
1. **Collect All Evidence**: Screenshots, error messages, logs, user observations
2. **Verify Environment**: Confirm testing conditions and setup
3. **Document Contradictions**: Note any discrepancies between expected and actual results

**Phase 2: Systematic Analysis**
1. **Code Comparison**: Compare relevant implementations side-by-side
2. **Data Flow Analysis**: Trace data from source to display in all versions
3. **Architecture Review**: Identify fundamental differences in approach

**Phase 3: Targeted Implementation**
1. **Gap Identification**: Pinpoint specific missing functionality
2. **Format Conversion Planning**: Plan data format conversions if needed
3. **Implementation with Validation**: Implement fixes with immediate verification

## 🎯 Debugging Methodologies by Context

### API Integration Issues

**Systematic Approach**:
1. **Compare API Calls**: Check if both versions make the same API calls
2. **Response Format Analysis**: Verify response format handling
3. **Error Handling Comparison**: Compare error handling between versions
4. **Authentication Flow**: Verify token handling and authentication

**Common Patterns**:
- Missing API calls in newer implementations
- Different response format expectations
- Authentication token timing or format differences

### UI Content Display Issues

**Systematic Approach**:
1. **Data Source Verification**: Confirm data is loaded correctly
2. **Component Comparison**: Compare rendering components between versions  
3. **State Management**: Verify state initialization and updates
4. **Format Conversion**: Check if data format conversion is needed

**V1/V2 Specific Patterns**:
- V1 server-side rendering vs V2 client-side data fetching
- Different component initialization patterns
- State management differences (server state vs React state)

### Authentication and Session Issues

**Systematic Approach**:
1. **Token Flow Comparison**: Compare token generation and validation
2. **Clock Skew Analysis**: Check for timing-related authentication failures
3. **Session Persistence**: Verify session management differences
4. **Error Recovery**: Compare authentication error handling

## 📊 Success Metrics and Validation

### Debugging Session Assessment

**Efficient Session Indicators**:
- Root cause identified within 15-20 minutes
- Clear evidence trail from symptom to cause
- Systematic approach applied consistently
- User evidence treated as ground truth

**Inefficient Session Warning Signs**:
- Extended symptom investigation without architectural analysis
- User evidence dismissed or worked around
- Multiple attempts without systematic comparison
- Focus on routing/display issues before data flow analysis

### Post-Resolution Validation

**Required Validation Steps**:
1. **Comparative Testing**: Verify fix works in both versions
2. **Screenshot Evidence**: Document working state with visual proof
3. **Data Flow Verification**: Confirm complete data pipeline works
4. **Edge Case Testing**: Test error conditions and edge cases

## 🔄 Continuous Improvement

### Learning Integration

**After Each Debugging Session**:
1. **Time Analysis**: Compare actual time to 15-20 minute target
2. **Methodology Review**: Identify which protocols were/weren't followed
3. **Pattern Recognition**: Document reusable patterns discovered
4. **Anti-Pattern Documentation**: Record inefficient approaches to avoid

### Knowledge Capture

**Documentation Requirements**:
- **CLAUDE.md**: Critical protocols affecting all future work
- **lessons.mdc**: Technical details and specific code patterns
- **debugging_guide.md**: Systematic methodologies and processes
- **Memory MCP**: Persistent cross-conversation learning

## 📚 Related Documentation

- **CLAUDE.md**: User Evidence Primacy Protocol, Cross-Version Systematic Debugging
- **lessons.mdc**: V1/V2 Debugging Methodology Breakthrough, Technical Implementation Details
- **Memory MCP**: Persistent debugging session entities and workflow insights

---

**Purpose**: This guide provides systematic debugging methodologies to ensure efficient problem resolution and prevent extended debugging sessions through evidence-based, systematic approaches.