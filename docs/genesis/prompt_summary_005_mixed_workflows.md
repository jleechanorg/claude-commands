# Mixed Workflow Patterns (Prompts 4001-5000)

## Overview
Analysis of complex multi-command workflows from authentic conversation data, showing how different commands combine in real development scenarios.

## Mixed Command Usage Probability
Analysis shows sophisticated users frequently combine multiple commands in single sessions, with common patterns emerging around complementary command sequences.

## Primary Mixed Workflow Triggers

### 1. Multi-Phase Development Context
**Pattern**: Complex features requiring multiple development approaches
**Trigger Context**: When single command insufficient for complete task
**Example Pattern**:
```
> I need to add user notifications - analyze the current system, design the architecture, implement with TDD, and deploy
```
**Command Sequence**: `/copilot` → `/arch` → `/tdd` → `/execute` → `/pr`

### 2. Problem-Solution-Validation Context
**Pattern**: Systematic approach to complex problem resolution
**Trigger Context**: When problems require investigation, solution, and verification
**Example Pattern**:
```
> The authentication system is failing randomly - investigate thoroughly, fix with proper testing, then optimize
```
**Command Sequence**: `/copilot` → `/tdd` → `/redgreen` → `/execute`

### 3. Research-Design-Implementation Context
**Pattern**: New feature development from concept to deployment
**Trigger Context**: When building something new requiring research and planning
**Example Pattern**:
```
> Research best practices for user onboarding, design our implementation, build with tests, and deploy
```
**Command Sequence**: `/research` → `/arch` → `/tdd` → `/execute` → `/pr`

## Mixed Workflow Communication Patterns

### Comprehensive Task Style
**Characteristics**:
- Recognition of task complexity
- Expectation of systematic approach
- Willingness to invest time in proper process
- Focus on complete solution rather than quick fix

**Example Phrases**:
```
> Do this properly - research, design, implement, test, deploy
> Handle this comprehensively from analysis through deployment
> Take the full systematic approach to this feature
> Complete end-to-end solution needed
```

### Expert Orchestration Style
**Characteristics**:
- Understanding of when different approaches needed
- Sophisticated command composition knowledge
- Expectation of intelligent command selection
- Trust in automated workflow coordination

## Mixed Workflow Trajectories

### Research → Design → Implement Trajectory
**Common Sequence**: `/research` → `/arch` → `/tdd` → `/execute`
1. **Research Phase**: Understanding requirements and best practices
2. **Design Phase**: Architectural planning and specification
3. **Implementation Phase**: Test-driven development
4. **Execution Phase**: Integration and deployment

### Investigation → Fix → Optimization Trajectory
**Common Sequence**: `/copilot` → `/debug` → `/tdd` → `/redgreen`
1. **Investigation Phase**: Comprehensive problem analysis
2. **Debug Phase**: Issue identification and isolation
3. **Fix Phase**: Test-driven problem resolution
4. **Optimization Phase**: Performance and quality improvement

### Analysis → Planning → Execution → Validation Trajectory
**Common Sequence**: `/copilot` → `/arch` → `/execute` → `/review`
1. **Analysis Phase**: System understanding and assessment
2. **Planning Phase**: Solution design and architecture
3. **Execution Phase**: Implementation and integration
4. **Validation Phase**: Quality assurance and review

## Complexity Indicators for Mixed Workflows

### High Complexity Mixed Workflows (70-80%)
- Multiple system interactions required
- Cross-cutting concerns (security, performance, scalability)
- Integration with existing complex systems
- Regulatory or compliance requirements
- Multiple stakeholder coordination

### Moderate Complexity Mixed Workflows (15-20%)
- Standard feature development with testing
- Typical refactoring and improvement tasks
- Normal integration and deployment workflows
- Standard quality assurance processes

### Low Complexity Mixed Workflows (5-10%)
- Simple enhancements with basic testing
- Straightforward configuration changes
- Minor bug fixes with validation

## Intent Classification for Mixed Workflows

### 1. Complete Feature Development (40-45%)
**Context**: Building comprehensive new functionality
**Mixed Approach**: Research → Design → Implement → Deploy
**Example**: `> Add complete user notification system with email, SMS, and push notifications`

### 2. System Improvement Project (25-30%)
**Context**: Enhancing existing systems comprehensively
**Mixed Approach**: Analysis → Planning → Implementation → Optimization
**Example**: `> Improve the authentication system for better security and performance`

### 3. Problem Resolution Project (15-20%)
**Context**: Solving complex issues requiring multiple approaches
**Mixed Approach**: Investigation → Debug → Fix → Validate
**Example**: `> Resolve the intermittent payment processing failures completely`

### 4. Integration Project (10-15%)
**Context**: Connecting systems or adding complex integrations
**Mixed Approach**: Research → Architecture → Implementation → Testing
**Example**: `> Integrate with third-party CRM system properly`

## Environmental Context for Mixed Workflows

### Project Maturity Context
- **Established Codebases**: Complex systems requiring careful modification
- **Quality Standards**: High expectations for proper process
- **Technical Debt**: Accumulated complexity requiring systematic approaches
- **Stakeholder Expectations**: Professional development practices expected

### Team Dynamics Context
- **Solo Development**: Need for systematic personal process
- **Code Review**: Preparation for thorough review process
- **Handoff Requirements**: Documentation and testing for team transitions
- **Compliance**: Regulatory or audit requirements

## Mixed Workflow Behavioral Patterns

### Core Tenets Driving Mixed Workflows

#### Professional Development Standards
- Commitment to complete solutions
- Understanding of proper development process
- Quality-first mentality
- Long-term maintainability focus

#### Systematic Problem Solving
- Recognition of complexity requiring multiple approaches
- Patience for thorough process
- Understanding of interdependencies
- Strategic thinking about solutions

#### Risk Management
- Preference for validated approaches
- Testing and verification expectations
- Incremental progress with safety nets
- Reversible decision making

## Mixed Command Sequence Patterns

### Common Multi-Command Patterns

#### Discovery → Implementation Pattern
**Sequence**: `/research` or `/copilot` → `/arch` → `/tdd` → `/execute`
**Usage**: When building something new or unfamiliar
**Success Rate**: High due to thorough preparation

#### Problem → Solution Pattern
**Sequence**: `/debug` or `/copilot` → `/tdd` → `/redgreen` → `/execute`
**Usage**: When solving complex bugs or issues
**Success Rate**: High due to systematic approach

#### Quality → Improvement Pattern
**Sequence**: `/review` or `/copilot` → `/arch` → `/redgreen` → `/execute`
**Usage**: When improving existing functionality
**Success Rate**: High due to careful planning

## Predictive Patterns for Mixed Workflows

### High Mixed Workflow Probability (0.4+ probability)
- Complex feature requests spanning multiple systems
- Major refactoring or improvement projects
- Integration with external systems
- Performance optimization projects
- Security enhancement initiatives

### Medium Mixed Workflow Probability (0.2-0.4 probability)
- Standard feature development
- Moderate system improvements
- Bug fixes in complex systems
- Code quality improvement projects

### Low Mixed Workflow Probability (<0.2 probability)
- Simple configuration changes
- Minor bug fixes
- Documentation updates
- Straightforward maintenance tasks

## Success Indicators for Mixed Workflows

### Process Completion Metrics
- **All Phases Completed**: Every command in sequence executed successfully
- **Quality Gates Passed**: Tests, reviews, and validations successful
- **Integration Success**: All components working together properly
- **Stakeholder Acceptance**: Requirements fully satisfied

### Quality Outcomes
- **Comprehensive Testing**: Full test coverage across all components
- **Documentation Complete**: Proper documentation for maintenance
- **Performance Verified**: Performance requirements met
- **Security Validated**: Security requirements satisfied

## Real Prompt Examples for Mixed Workflows

### Feature Development Mixed Workflows
```
> Add comprehensive user analytics - research best practices, design the architecture, implement with full testing, and deploy with monitoring
> Build complete payment processing system - analyze requirements, design for security, implement with TDD, integrate with existing systems
> Create user notification system - research options, design for scalability, implement with proper testing, deploy with rollback capability
```

### System Improvement Mixed Workflows
```
> Improve the authentication system completely - analyze current issues, design better architecture, implement with comprehensive testing, optimize for performance
> Modernize the user management system - assess current state, design modern approach, implement systematically, validate thoroughly
> Enhance the API layer - review current implementation, design improvements, implement with testing, optimize for scale
```

### Problem Resolution Mixed Workflows
```
> Fix the intermittent database connection issues - investigate thoroughly, design proper solution, implement with testing, validate under load
> Resolve the email delivery problems - analyze the entire flow, design robust solution, implement with proper error handling, test comprehensively
> Address the performance degradation - investigate all causes, design optimization strategy, implement improvements, validate results
```

### Integration Mixed Workflows
```
> Integrate with Salesforce properly - research their API, design our integration architecture, implement with comprehensive testing, deploy with monitoring
> Connect to payment gateway securely - analyze requirements, design secure implementation, build with full testing, deploy with fraud protection
> Add third-party authentication - research providers, design integration strategy, implement with fallback options, test all scenarios
```

This analysis provides practical guidance for recognizing when users need sophisticated multi-command workflows based on task complexity, quality requirements, and professional development practices.
