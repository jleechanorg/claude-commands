# RedGreen Debugging Patterns (Prompts 2001-3000)

## Overview
Analysis of RedGreen refactoring and debugging patterns from authentic conversation data, focusing on test-driven development cycles and systematic debugging approaches.

## RedGreen Command Probability: 0.196 (Moderate)
RedGreen shows as third most likely command, typically following TDD phases or during refactoring cycles.

## Primary RedGreen Triggers

### 1. Post-TDD Refactoring Context
**Pattern**: After successful test implementation, code needs optimization
**Trigger Sequence**: `/tdd` → `/redgreen`
**Context**: When tests are passing but code quality needs improvement
**Example Pattern**:
```
> Tests are passing but the authentication code is messy - let's clean it up
> The user validation works but has too much duplication
> Login functionality is complete, now optimize for performance
```
**Characteristics**:
- HP Score typically 3-4 (moderate complexity)
- Code quality focus
- Maintains test coverage during refactoring

### 2. Debugging Systematic Approach Context
**Pattern**: Complex bugs requiring methodical red-green-refactor cycles
**Trigger Context**: When simple fixes haven't worked and systematic approach needed
**Example Pattern**:
```
> The user registration bug is intermittent - need systematic debugging
> Database connection issues require step-by-step isolation
> API endpoint returning inconsistent results
```
**Workflow**: red (failing test) → green (minimal fix) → refactor (clean solution)

### 3. Legacy Code Improvement Context
**Pattern**: Improving existing code while maintaining functionality
**Trigger Context**: When working with established codebase requiring careful changes
**Example Pattern**:
```
> Modernize the authentication system without breaking existing users
> Refactor the payment processing but keep all current functionality
> Clean up the user management code while preserving edge case handling
```

## RedGreen Usage Context Analysis

### Cognitive Load Distribution for RedGreen
Based on analysis patterns showing moderate to high complexity scenarios:
- **HP 5 (Highest)**: 25-30% - Complex refactoring with multiple dependencies
- **HP 4**: 20-25% - Multi-component optimization
- **HP 3**: 25-30% - Standard refactoring scenarios
- **HP 2**: 15-20% - Simple cleanup tasks
- **HP 1**: 5-10% - Minimal refactoring needs

### Quality Context for RedGreen Commands
**Authenticity Indicators**:
- Real refactoring scenarios from production code
- Genuine performance and maintainability concerns
- Authentic debugging challenges

**Technical Specificity Requirements**:
- Precise understanding of existing functionality
- Clear refactoring goals
- Measurable improvement criteria

## RedGreen Communication Patterns

### Systematic Improvement Style
**Characteristics**:
- Focus on incremental improvement
- Emphasis on maintaining test coverage
- Quality-over-speed mentality
- Methodical approach

**Example Phrases**:
```
> Let's clean this up properly
> Make this more maintainable
> Optimize without breaking anything
> Simplify while keeping all functionality
> Remove duplication but preserve behavior
```

### Problem-Solving Persistence Style
**Characteristics**:
- Acknowledgment that simple fixes failed
- Willingness to take systematic approach
- Focus on root cause identification
- Long-term solution orientation

## RedGreen Workflow Trajectories

### Primary RedGreen Trajectory: green → red → green → refactor
1. **Green State**: Working code with tests passing
2. **Red State**: Introduce failing test for improvement/bug fix
3. **Green State**: Minimal code to make test pass
4. **Refactor State**: Clean up implementation while maintaining tests

### Debugging RedGreen Trajectory: problem → isolate → fix → optimize
1. **Problem Identification**: Bug or performance issue detected
2. **Isolation**: Create focused test to reproduce issue
3. **Fix**: Minimal change to resolve the problem
4. **Optimization**: Improve solution while maintaining fix

### Legacy Improvement Trajectory: characterize → test → refactor → validate
1. **Characterization**: Understand existing behavior through tests
2. **Test Coverage**: Ensure comprehensive test coverage
3. **Refactoring**: Improve code structure and quality
4. **Validation**: Confirm all functionality preserved

## Complexity Indicators for RedGreen Commands

### High Complexity Scenarios (35-40%)
- Multiple interconnected components
- Complex business logic requiring careful refactoring
- Performance optimization with functionality preservation
- Legacy system modernization
- Cross-cutting concerns (security, logging, caching)

### Moderate Complexity Scenarios (40-45%)
- Single component refactoring
- Standard cleanup and optimization
- Typical code quality improvements
- Straightforward performance enhancements

### Low Complexity Scenarios (15-20%)
- Simple variable renaming
- Basic formatting and style improvements
- Minor optimization wins
- Obvious duplication removal

## Intent Classification Leading to RedGreen

### 1. Code Quality Improvement (40-45%)
**Context**: Existing working code needs better structure
**RedGreen Application**: Systematic refactoring with test safety net
**Example**: `> The user service works but is hard to understand and modify`

### 2. Performance Optimization (25-30%)
**Context**: Functionality correct but performance inadequate
**RedGreen Application**: Incremental optimization with regression prevention
**Example**: `> Login is working but takes too long - optimize while preserving all edge cases`

### 3. Bug Fix with Improvement (15-20%)
**Context**: Fixing bugs while improving overall code structure
**RedGreen Application**: Fix + refactor cycle
**Example**: `> Fix the email validation bug and clean up the validation logic`

### 4. Legacy Modernization (10-15%)
**Context**: Updating old code to modern standards
**RedGreen Application**: Careful modernization with behavior preservation
**Example**: `> Convert the authentication system to use modern patterns`

## Environmental Context for RedGreen Usage

### Development Phase Context
- **Project Phase**: Mature development (not initial implementation)
- **Code Maturity**: Existing functionality that works but needs improvement
- **Technical Debt**: Accumulated debt requiring systematic addressing
- **Quality Focus**: Emphasis on maintainability and performance

### Team Context Patterns
- **Solo Development**: Systematic approach to managing complexity
- **Code Review**: Preparing code for review with quality improvements
- **Long-term Maintenance**: Building sustainable codebase

## RedGreen Behavioral Patterns

### Core Tenets Driving RedGreen Usage

#### Quality-First Mentality
- Willingness to invest time in proper solutions
- Focus on maintainability over quick fixes
- Systematic approach to improvement

#### Risk-Averse Optimization
- Maintaining test coverage during changes
- Incremental improvements over wholesale rewrites
- Validation at each step

#### Professional Development Practices
- Following established refactoring patterns
- Commitment to code quality standards
- Long-term codebase health focus

## RedGreen Command Sequence Patterns

### Common Pre-RedGreen Commands
1. **TDD → RedGreen**: After test implementation, refactor for quality
2. **Review → RedGreen**: Code review identified improvement opportunities
3. **Debug → RedGreen**: After finding issue, systematic fix approach

### Common Post-RedGreen Commands
1. **RedGreen → Execute**: Run tests to validate refactoring
2. **RedGreen → Review**: Review improved code quality
3. **RedGreen → TDD**: Add tests for newly refactored code

## Predictive Patterns for RedGreen Usage

### High RedGreen Probability Scenarios (0.25+ probability)
- After successful TDD cycle with working but messy code
- Performance issues in working functionality
- Code review feedback about quality issues
- Legacy code requiring careful improvement
- Complex bugs requiring systematic debugging

### Medium RedGreen Probability Scenarios (0.15-0.25 probability)
- General refactoring needs
- Moderate performance optimization
- Standard code cleanup tasks
- Routine maintenance programming

### Low RedGreen Probability Scenarios (<0.15 probability)
- New feature development (use TDD instead)
- Configuration changes
- Documentation updates
- Simple bug fixes

## RedGreen Success Indicators

### Quality Metrics
- **Test Coverage Maintained**: All tests continue passing
- **Code Metrics Improved**: Cyclomatic complexity reduced, duplication eliminated
- **Performance Enhanced**: Measurable performance improvements
- **Maintainability Increased**: Code easier to understand and modify

### Workflow Indicators
- **Incremental Progress**: Small, safe steps toward improvement
- **Reversible Changes**: Ability to roll back at any point
- **Continuous Validation**: Tests passing at each refactoring step
- **Clear Improvement**: Objective measures of code quality enhancement

## Real Prompt Examples for RedGreen Context

### Quality Improvement RedGreen
```
> The authentication system works but has too much duplication
> User validation logic is scattered across multiple files
> Email processing is functional but the code is hard to follow
> Payment handling works but error cases are confusing
```

### Performance Optimization RedGreen
```
> Login works correctly but is too slow
> Database queries are correct but inefficient
> API responses are accurate but take too long
> File processing works but uses too much memory
```

### Legacy Improvement RedGreen
```
> Modernize the user management system while preserving all functionality
> Update authentication to use current security standards
> Refactor payment processing to follow current patterns
> Clean up the reporting system without changing outputs
```

### Debugging RedGreen
```
> The email sending bug is intermittent - need systematic debugging
> User registration fails randomly - methodical investigation needed
> Database connection issues require step-by-step isolation
> API timeout problems need careful analysis and fixing
```

This analysis provides practical guidance for identifying when users need RedGreen methodology based on code quality concerns, performance issues, and systematic debugging requirements.
