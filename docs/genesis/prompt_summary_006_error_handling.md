# Error Handling Patterns (Prompts 5001-6000)

## Overview
Analysis of error resolution and debugging patterns from authentic conversation data, focusing on systematic approaches to problem identification and resolution.

## Error Handling Context Probability
Error handling scenarios show high correlation with systematic debugging approaches and test-driven problem resolution.

## Primary Error Handling Triggers

### 1. Immediate Error Response Context
**Pattern**: Active errors requiring immediate attention
**Trigger Phrases**:
- "getting an error"
- "this is failing"
- "not working"
- "exception thrown"
**Example Pattern**:
```
> Getting a 500 error when users try to login
> The payment processing is throwing database connection errors
> User registration is failing with validation errors
> Email sending is not working - no error messages shown
```
**Response Approach**: Immediate diagnosis followed by systematic resolution

### 2. Intermittent Problem Context
**Pattern**: Unpredictable failures requiring investigation
**Trigger Context**: When errors occur sporadically without clear patterns
**Example Pattern**:
```
> Users report random logout issues
> Payment processing works sometimes but fails other times
> Email notifications are delivered inconsistently
> Database connections timeout occasionally
```
**Response Approach**: Systematic investigation using `/copilot` or `/debug`

### 3. Performance Degradation Context
**Pattern**: System working but performing poorly
**Trigger Context**: When functionality exists but user experience degraded
**Example Pattern**:
```
> Login is working but takes 30 seconds
> Database queries are correct but too slow
> API responses are accurate but timeout frequently
> File uploads work but consume too much memory
```

## Error Communication Patterns

### Urgent Problem Style
**Characteristics**:
- Immediate problem description
- Focus on user impact
- Expectation of quick resolution
- Stress indicators in language

**Example Phrases**:
```
> This is broken and users are complaining
> Critical error - payment processing down
> Urgent: email system not sending notifications
> Production issue: authentication failing randomly
```

### Diagnostic Information Style
**Characteristics**:
- Technical error details provided
- Stack traces or log excerpts included
- Context about when/how error occurs
- Previous troubleshooting attempts mentioned

**Example Phrases**:
```
> Getting SQLException: timeout after 30 seconds
> HTTP 500 error in authentication endpoint, stack trace shows...
> ValueError in user validation: email format invalid
> Database connection pool exhausted during peak hours
```

### Investigation Request Style
**Characteristics**:
- Acknowledgment of complexity
- Request for systematic investigation
- Willingness to invest time in proper diagnosis
- Focus on root cause identification

## Error Handling Workflow Trajectories

### Immediate → Diagnose → Fix → Validate Trajectory
**Common Sequence**: Problem Report → `/debug` → `/tdd` → `/execute`
1. **Problem Report**: User identifies immediate issue
2. **Diagnosis**: Systematic investigation of root cause
3. **Fix Implementation**: Test-driven resolution
4. **Validation**: Verification that fix works and doesn't break other functionality

### Investigate → Understand → Resolve → Prevent Trajectory
**Common Sequence**: `/copilot` → `/debug` → `/tdd` → `/redgreen`
1. **Investigation**: Comprehensive analysis of problem domain
2. **Understanding**: Root cause identification and impact assessment
3. **Resolution**: Proper fix with comprehensive testing
4. **Prevention**: Refactoring to prevent similar issues

### Monitor → Isolate → Fix → Optimize Trajectory
**Common Sequence**: Problem Monitoring → `/debug` → `/tdd` → `/redgreen`
1. **Monitoring**: Tracking intermittent problems
2. **Isolation**: Reproducing and isolating the issue
3. **Fix**: Targeted solution with tests
4. **Optimization**: Performance improvements to prevent recurrence

## Complexity Indicators for Error Handling

### High Complexity Error Scenarios (50-60%)
- Intermittent or race condition errors
- Multi-system integration failures
- Performance degradation under load
- Data consistency issues
- Security-related failures
- Legacy system integration problems

### Moderate Complexity Error Scenarios (30-35%)
- Standard application errors with clear stack traces
- Configuration-related issues
- Database query optimization needs
- API integration problems
- User input validation failures

### Low Complexity Error Scenarios (10-15%)
- Simple syntax or configuration errors
- Clear error messages with obvious solutions
- Single-component failures
- Typos or formatting issues

## Intent Classification for Error Handling

### 1. Immediate Problem Resolution (45-50%)
**Context**: Active errors affecting users or system functionality
**Approach**: Quick diagnosis followed by targeted fix
**Example**: `> Users can't login - getting 500 errors on authentication endpoint`

### 2. Systematic Investigation (25-30%)
**Context**: Complex or intermittent issues requiring thorough analysis
**Approach**: Comprehensive analysis using systematic debugging
**Example**: `> Payment processing fails randomly - need to investigate the entire flow`

### 3. Performance Problem Resolution (15-20%)
**Context**: Functional but slow or resource-intensive operations
**Approach**: Performance analysis and optimization
**Example**: `> Database queries work but take too long during peak hours`

### 4. Preventive Problem Solving (5-10%)
**Context**: Addressing potential issues before they become critical
**Approach**: Proactive analysis and improvement
**Example**: `> Error handling in payment system needs improvement before holiday traffic`

## Environmental Context for Error Handling

### Production vs Development Context
- **Production Errors**: Immediate priority, minimal risk solutions
- **Development Errors**: Opportunity for comprehensive fixes and improvements
- **Testing Errors**: Learning opportunities and test coverage gaps
- **Integration Errors**: Often require cross-system coordination

### User Impact Context
- **User-Facing Errors**: High priority, communication requirements
- **Internal System Errors**: Technical debt and maintenance focus
- **Performance Errors**: User experience and scalability concerns
- **Data Errors**: Integrity and consistency priorities

## Error Handling Behavioral Patterns

### Core Tenets Driving Error Handling

#### Immediate Response Priority
- User impact drives urgency
- Quick stabilization before comprehensive fixes
- Communication about status and timeline
- Minimal disruption to working functionality

#### Systematic Problem Solving
- Root cause identification over symptom fixing
- Test-driven problem resolution
- Prevention of similar future issues
- Documentation of solutions for team knowledge

#### Quality and Reliability Focus
- Comprehensive testing of fixes
- Consideration of edge cases and regression risks
- Performance impact assessment
- Long-term system health improvements

## Error Handling Command Sequence Patterns

### Common Error Response Patterns

#### Quick Fix Pattern
**Sequence**: Problem Report → `/debug` → `/execute`
**Usage**: When clear solution exists and time is critical
**Risk**: May not address root cause

#### Thorough Investigation Pattern
**Sequence**: Problem Report → `/copilot` → `/debug` → `/tdd` → `/execute`
**Usage**: When problem is complex or has broad impact
**Success Rate**: Higher long-term success, prevents recurrence

#### Performance Fix Pattern
**Sequence**: Performance Issue → `/copilot` → `/redgreen` → `/execute`
**Usage**: When functionality correct but performance inadequate
**Focus**: Optimization while maintaining correctness

## Predictive Patterns for Error Handling

### High Error Handling Probability (0.6+ probability)
- Active production errors affecting users
- System failures or downtime
- Performance degradation reports
- Security incident reports
- Data corruption or consistency issues

### Medium Error Handling Probability (0.3-0.6 probability)
- Development environment errors
- Test failures requiring investigation
- Integration issues during development
- Code quality issues identified in review

### Low Error Handling Probability (<0.3 probability)
- Feature development tasks
- Documentation updates
- Configuration changes
- Routine maintenance activities

## Success Indicators for Error Handling

### Immediate Success Metrics
- **Error Resolved**: Primary error no longer occurring
- **System Stability**: No new errors introduced
- **User Impact Minimized**: Quick restoration of functionality
- **Clear Communication**: Status updates provided to stakeholders

### Long-term Success Metrics
- **Root Cause Addressed**: Underlying issue fixed, not just symptoms
- **Prevention Implemented**: Measures to prevent similar issues
- **Test Coverage Added**: Tests to catch similar problems in future
- **Documentation Updated**: Knowledge captured for team

## Real Prompt Examples for Error Handling

### Immediate Error Response
```
> Users getting 500 errors when trying to upload files
> Payment processing is down - customers can't complete purchases
> Database connection errors causing login failures
> Email system not sending password reset emails
> API returning 404 for valid user requests
```

### Intermittent Problem Investigation
```
> Users report random logout issues - happens occasionally but not consistently
> Payment processing works most of the time but fails randomly for some transactions
> Database queries timeout occasionally during peak hours
> Email notifications delivered to some users but not others
> File uploads work locally but fail in production sometimes
```

### Performance Problem Resolution
```
> Login authentication takes 15-30 seconds instead of instant
> Database queries for user dashboard timeout during business hours
> File upload processing uses excessive memory and crashes server
> API responses are correct but take 10+ seconds to return
> Search functionality works but is too slow with large datasets
```

### Complex System Errors
```
> Integration with payment gateway failing with cryptic error messages
> User session management behaving inconsistently across load balancers
> Database replication causing data inconsistency between regions
> Third-party API integration working in test but failing in production
> Microservices communication breaking under high load
```

### Error Pattern Investigation
```
> Getting the same database deadlock error repeatedly - need systematic investigation
> Authentication failures spike every day at the same time - investigate pattern
> Memory usage grows continuously until restart required - find root cause
> Specific user actions trigger cascade failures - analyze the pattern
> Error rates increase with certain data patterns - comprehensive analysis needed
```

This analysis provides practical guidance for recognizing different types of error handling scenarios and selecting appropriate systematic approaches based on urgency, complexity, and user impact.
