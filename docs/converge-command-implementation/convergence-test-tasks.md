# /converge Test Tasks Suite

**Comprehensive test cases for validating /converge system capabilities across complexity levels and command integration patterns.**

## 🎯 Test Framework Overview

**Purpose**: Validate /converge system's ability to autonomously achieve goals through systematic command orchestration
**Total Test Tasks**: 20 (across 4 complexity tiers)
**Expected Validation**: Success criteria, iteration counts, command usage patterns

---

## 📊 TIER 1: SIMPLE TASKS (5 tests)
*Single command focus, basic validation, 1-2 iterations expected*

### T1.1: File Creation and Validation
**Goal**: `Create a file called test-output.txt with "Hello Convergence" content and validate it exists`

**Expected Workflow**:
- Step 1: /goal - Define file creation success criteria
- Step 2: /plan - Strategy for file creation and validation  
- Step 3: /reviewe - Review approach (should be simple file operation)
- Step 4: Autonomous approval
- Step 5: Execute - Use Write tool directly (not /cerebras for simple task)
- Step 6: /goal --validate - Verify file exists with correct content
- Step 7: /guidelines - No issues expected
- Step 8: CONVERGED

**Success Criteria**:
- ✅ File test-output.txt exists
- ✅ File contains exact text "Hello Convergence"
- ✅ Validation evidence collected and documented

**Expected**: 1-2 iterations, ~3 minutes

### T1.2: Test Execution Validation  
**Goal**: `Run existing tests and ensure 100% pass rate`

**Expected Workflow**:
- Step 1: /goal - Define test success criteria (all tests passing)
- Step 2: /plan - Identify test command and validation approach
- Step 3: /reviewe - Review test execution strategy
- Step 4: Autonomous approval  
- Step 5: **Command**: /test - Execute test suite
- Step 6: /goal --validate - Verify all tests passed
- Step 7: /guidelines - Capture any test failure patterns
- Step 8: CONVERGED or iterate if failures found

**Success Criteria**:
- ✅ All tests execute successfully
- ✅ 100% pass rate achieved
- ✅ No test failures or errors

**Expected**: 1-3 iterations depending on current test state

### T1.3: Simple Documentation Creation
**Goal**: `Create README-test.md with project description and usage instructions`

**Expected Workflow**:
- Step 1: /goal - Define documentation success criteria
- Step 2: /plan - Strategy for content generation  
- Step 3: /reviewe - Review documentation approach
- Step 4: Autonomous approval
- Step 5: **Command**: /cerebras - Generate documentation content
- Step 6: /goal --validate - Verify README quality and completeness
- Step 7: /guidelines - Document any content issues
- Step 8: CONVERGED

**Success Criteria**:
- ✅ README-test.md file created
- ✅ Contains project description section
- ✅ Contains usage instructions section
- ✅ Content is well-formatted and clear

**Expected**: 1-2 iterations, ~5 minutes

### T1.4: Branch Status Analysis
**Goal**: `Analyze current branch status and document findings in branch-analysis.md`

**Expected Workflow**:
- Step 1: /goal - Define analysis success criteria
- Step 2: /plan - Strategy using git commands and analysis tools
- Step 3: /reviewe - Review git analysis approach
- Step 4: Autonomous approval
- Step 5: **Command**: /execute - Analyze branch state with git commands
- Step 6: /goal --validate - Verify analysis completeness
- Step 7: /guidelines - Document any analysis patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Current branch identified and documented
- ✅ Commit status analyzed
- ✅ PR status (if any) documented
- ✅ Analysis saved to branch-analysis.md

**Expected**: 1-2 iterations, ~4 minutes

### T1.5: Simple Code Generation
**Goal**: `Generate a Python calculator function with add, subtract, multiply, divide operations`

**Expected Workflow**:
- Step 1: /goal - Define calculator function success criteria
- Step 2: /plan - Strategy for code generation and validation
- Step 3: /reviewe - Review code generation approach
- Step 4: Autonomous approval
- Step 5: **Command**: /cerebras - Generate calculator.py
- Step 6: /goal --validate - Verify function completeness and syntax
- Step 7: /guidelines - Document any code generation issues
- Step 8: CONVERGED

**Success Criteria**:
- ✅ calculator.py file created
- ✅ Contains add, subtract, multiply, divide functions
- ✅ Functions have proper parameters and return values
- ✅ Code is syntactically correct Python

**Expected**: 1-2 iterations, ~4 minutes

---

## 🔧 TIER 2: MEDIUM COMPLEXITY (6 tests)
*Multi-command workflows, moderate complexity, 2-4 iterations expected*

### T2.1: Test-Driven Development Workflow
**Goal**: `Implement TDD workflow: create failing tests for StringUtils class, then implement class to make tests pass`

**Expected Workflow**:
- Step 1: /goal - Define TDD success criteria (tests first, then implementation)
- Step 2: /plan - Strategy for test creation, execution, implementation cycle
- Step 3: /reviewe - Review TDD approach and command sequence
- Step 4: Autonomous approval
- Step 5a: **Command**: /cerebras - Generate failing test_string_utils.py
- Step 6a: /goal --validate - Verify tests exist and fail as expected
- Step 7a: /guidelines - Document TDD patterns
- Step 5b: **Command**: /cerebras - Implement StringUtils class
- Step 6b: /goal --validate - Verify all tests now pass
- Step 8: CONVERGED

**Success Criteria**:
- ✅ test_string_utils.py created with comprehensive tests
- ✅ Initial test run shows failures (red phase)
- ✅ StringUtils class implementation created
- ✅ Final test run shows all tests passing (green phase)
- ✅ TDD cycle properly demonstrated

**Expected**: 2-3 iterations, ~8 minutes

### T2.2: PR Comment Processing Workflow  
**Goal**: `Process PR comments: fetch comments, analyze issues, create response plan, reply to actionable comments`

**Expected Workflow**:
- Step 1: /goal - Define PR comment processing success criteria
- Step 2: /plan - Strategy using /copilot and comment analysis
- Step 3: /reviewe - Review PR processing approach
- Step 4: Autonomous approval
- Step 5: **Command**: /copilot - Fetch and analyze PR comments
- Step 6: /goal --validate - Verify comments processed and responses generated
- Step 7: /guidelines - Document PR processing patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ All PR comments fetched and analyzed
- ✅ Actionable comments identified
- ✅ Appropriate responses generated
- ✅ Non-actionable comments documented with reasons

**Expected**: 2-4 iterations depending on PR complexity

### T2.3: Code Review and Fix Workflow
**Goal**: `Perform comprehensive code review of target file, identify issues, implement fixes, validate corrections`

**Expected Workflow**:
- Step 1: /goal - Define code review success criteria
- Step 2: /plan - Strategy using /reviewe and fix implementation
- Step 3: /reviewe - Review code review approach (meta!)
- Step 4: Autonomous approval
- Step 5a: **Command**: /reviewe - Analyze target file for issues
- Step 5b: **Command**: /execute - Implement identified fixes
- Step 6: /goal --validate - Verify issues resolved
- Step 7: /guidelines - Document code quality patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Code review completed with specific issue identification
- ✅ All identified issues addressed with fixes
- ✅ Code quality improved measurably
- ✅ No new issues introduced by fixes

**Expected**: 2-4 iterations, ~12 minutes

### T2.4: Test Suite Generation and Validation
**Goal**: `Generate comprehensive test suite for existing module, run tests, fix any failures, achieve 100% pass rate`

**Expected Workflow**:
- Step 1: /goal - Define comprehensive testing success criteria
- Step 2: /plan - Strategy for test generation, execution, and fixing
- Step 3: /reviewe - Review testing strategy and coverage approach
- Step 4: Autonomous approval  
- Step 5a: **Command**: /cerebras - Generate comprehensive test suite
- Step 5b: **Command**: /test - Execute generated tests
- Step 5c: **Command**: /execute - Fix any failing tests or implementation
- Step 6: /goal --validate - Verify 100% test pass rate
- Step 7: /guidelines - Document testing patterns and failures
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Comprehensive test suite generated covering all functions
- ✅ Tests execute without import/syntax errors
- ✅ 100% of tests pass after fixes implemented  
- ✅ Good test coverage of edge cases and normal scenarios

**Expected**: 2-4 iterations, ~10 minutes

### T2.5: Documentation and Code Integration
**Goal**: `Create API documentation for existing code, integrate with README, validate documentation accuracy`

**Expected Workflow**:
- Step 1: /goal - Define documentation integration success criteria
- Step 2: /plan - Strategy for API doc generation and README integration
- Step 3: /reviewe - Review documentation approach
- Step 4: Autonomous approval
- Step 5a: **Command**: /cerebras - Generate API documentation
- Step 5b: **Command**: /execute - Update README with API docs
- Step 6: /goal --validate - Verify documentation accuracy and integration
- Step 7: /guidelines - Document API documentation patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ API documentation generated with function signatures
- ✅ Documentation includes parameter descriptions and return values
- ✅ README updated with integrated API documentation
- ✅ Documentation is accurate and well-formatted

**Expected**: 2-3 iterations, ~8 minutes

### T2.6: Multi-File Refactoring Task
**Goal**: `Refactor code to extract utility functions into separate module, update imports, maintain functionality`

**Expected Workflow**:
- Step 1: /goal - Define refactoring success criteria (functionality preserved)
- Step 2: /plan - Strategy for safe refactoring with validation
- Step 3: /reviewe - Review refactoring approach and safety measures
- Step 4: Autonomous approval
- Step 5a: **Command**: /execute - Extract utility functions to new module
- Step 5b: **Command**: /execute - Update imports in original files
- Step 5c: **Command**: /test - Validate functionality preserved
- Step 6: /goal --validate - Verify refactoring successful
- Step 7: /guidelines - Document refactoring patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Utility functions extracted to new module
- ✅ Original files updated with correct imports
- ✅ All existing functionality preserved
- ✅ Tests still pass after refactoring
- ✅ Code structure improved

**Expected**: 3-4 iterations, ~12 minutes

---

## 🏗️ TIER 3: COMPLEX ORCHESTRATION (6 tests)
*Full system orchestration, real-world scenarios, 3-8 iterations expected*

### T3.1: Complete Feature Implementation Pipeline
**Goal**: `Implement complete user authentication feature: requirements analysis, design, implementation, testing, documentation, PR creation`

**Expected Workflow**:
- Step 1: /goal - Define complete feature delivery success criteria
- Step 2: /plan - Strategy for full feature implementation pipeline
- Step 3: /reviewe - Review end-to-end feature approach
- Step 4: Autonomous approval
- Step 5a: **Command**: /requirements-start - Gather authentication requirements
- Step 5b: **Command**: /design - Create feature design document
- Step 5c: **Command**: /cerebras - Implement authentication system
- Step 5d: **Command**: /test - Create and run comprehensive tests
- Step 5e: **Command**: /execute - Generate documentation
- Step 5f: **Command**: /pr - Create pull request
- Step 6: /goal --validate - Verify complete feature delivery
- Step 7: /guidelines - Document feature development patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Requirements document created with user stories
- ✅ Design document with architecture and implementation plan
- ✅ Authentication system implemented with security best practices
- ✅ Comprehensive test suite with 100% pass rate
- ✅ Complete documentation including API and usage examples
- ✅ Pull request created with proper description and labels

**Expected**: 4-6 iterations, ~25 minutes

### T3.2: Multi-Agent PR Processing Pipeline
**Goal**: `Process multiple PRs simultaneously: analyze comments, fix issues, update code, respond to reviews, manage CI status`

**Expected Workflow**:
- Step 1: /goal - Define multi-PR processing success criteria
- Step 2: /plan - Strategy for parallel PR management using orchestration
- Step 3: /reviewe - Review orchestration approach for PR management
- Step 4: Autonomous approval
- Step 5: **Command**: /orch - Deploy agents for parallel PR processing
- Step 6: /goal --validate - Verify all PRs processed successfully
- Step 7: /guidelines - Document PR orchestration patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ All target PRs analyzed and processed
- ✅ Comments responded to appropriately
- ✅ Code issues fixed where applicable
- ✅ CI/CD checks passing
- ✅ PR status updated appropriately

**Expected**: 4-8 iterations depending on PR complexity, ~20 minutes

### T3.3: Legacy System Integration and Testing  
**Goal**: `Integrate new component with legacy system: analyze compatibility, implement adapters, create integration tests, validate system cohesion`

**Expected Workflow**:
- Step 1: /goal - Define legacy integration success criteria
- Step 2: /plan - Strategy for safe legacy system integration
- Step 3: /reviewe - Review integration approach and risk mitigation
- Step 4: Autonomous approval
- Step 5a: **Command**: /arch - Analyze legacy system architecture
- Step 5b: **Command**: /cerebras - Implement integration adapters
- Step 5c: **Command**: /test - Create comprehensive integration tests
- Step 5d: **Command**: /execute - Validate system cohesion
- Step 6: /goal --validate - Verify successful integration
- Step 7: /guidelines - Document integration patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Legacy system compatibility analyzed and documented
- ✅ Integration adapters implemented with proper abstraction
- ✅ Integration tests covering all interaction points
- ✅ System cohesion validated with end-to-end tests
- ✅ No breaking changes to existing functionality

**Expected**: 5-7 iterations, ~30 minutes

### T3.4: Performance Optimization Workflow
**Goal**: `Analyze system performance, identify bottlenecks, implement optimizations, validate improvements with benchmarks`

**Expected Workflow**:
- Step 1: /goal - Define performance optimization success criteria
- Step 2: /plan - Strategy for performance analysis and optimization
- Step 3: /reviewe - Review performance optimization approach
- Step 4: Autonomous approval
- Step 5a: **Command**: /execute - Run performance analysis
- Step 5b: **Command**: /cerebras - Implement optimization solutions
- Step 5c: **Command**: /test - Create performance benchmarks
- Step 5d: **Command**: /execute - Validate performance improvements
- Step 6: /goal --validate - Verify measurable performance gains
- Step 7: /guidelines - Document optimization patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Performance bottlenecks identified with concrete measurements
- ✅ Optimization solutions implemented without breaking functionality
- ✅ Performance benchmarks show measurable improvements
- ✅ Optimizations validated across different scenarios
- ✅ Performance regression tests added

**Expected**: 4-6 iterations, ~25 minutes

### T3.5: Multi-Repository Synchronization
**Goal**: `Synchronize changes across multiple related repositories: identify dependencies, update versions, coordinate releases, validate compatibility`

**Expected Workflow**:
- Step 1: /goal - Define multi-repo sync success criteria
- Step 2: /plan - Strategy for coordinated repository management
- Step 3: /reviewe - Review multi-repo coordination approach
- Step 4: Autonomous approval
- Step 5a: **Command**: /execute - Analyze repository dependencies
- Step 5b: **Command**: /orch - Coordinate changes across repositories
- Step 5c: **Command**: /test - Validate cross-repository compatibility
- Step 5d: **Command**: /execute - Update version dependencies
- Step 6: /goal --validate - Verify successful synchronization
- Step 7: /guidelines - Document multi-repo patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Repository dependencies mapped and analyzed
- ✅ Changes propagated to all dependent repositories
- ✅ Version compatibility validated across repositories
- ✅ Release coordination completed successfully
- ✅ Integration tests pass across repository boundaries

**Expected**: 5-8 iterations, ~35 minutes

### T3.6: End-to-End CI/CD Pipeline Implementation
**Goal**: `Implement complete CI/CD pipeline: GitHub Actions workflow, testing stages, deployment automation, monitoring setup`

**Expected Workflow**:
- Step 1: /goal - Define CI/CD pipeline success criteria
- Step 2: /plan - Strategy for complete pipeline implementation
- Step 3: /reviewe - Review CI/CD approach and best practices
- Step 4: Autonomous approval
- Step 5a: **Command**: /cerebras - Generate GitHub Actions workflow
- Step 5b: **Command**: /execute - Configure testing stages
- Step 5c: **Command**: /execute - Set up deployment automation
- Step 5d: **Command**: /test - Validate pipeline functionality
- Step 6: /goal --validate - Verify complete CI/CD pipeline
- Step 7: /guidelines - Document CI/CD implementation patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ GitHub Actions workflow created with proper stages
- ✅ Automated testing integrated with quality gates
- ✅ Deployment automation configured for multiple environments
- ✅ Monitoring and alerting set up
- ✅ Pipeline successfully processes test commits

**Expected**: 4-7 iterations, ~30 minutes

---

## ⚠️ TIER 4: EDGE CASES & ERROR HANDLING (3 tests)
*Error conditions, recovery scenarios, system limits testing*

### T4.1: Resource Exhaustion Recovery
**Goal**: `Simulate and recover from resource exhaustion: handle API rate limits, context limits, timeout scenarios`

**Expected Workflow**:
- Step 1: /goal - Define resource exhaustion recovery success criteria
- Step 2: /plan - Strategy for resource limit testing and recovery
- Step 3: /reviewe - Review error handling and recovery approach  
- Step 4: Autonomous approval
- Step 5: **Command**: /execute - Simulate resource exhaustion scenarios
- Step 6: /goal --validate - Verify graceful degradation and recovery
- Step 7: /guidelines - Document error handling patterns
- Step 8: CONVERGED or PARTIAL (acceptable for edge case)

**Success Criteria**:
- ✅ API rate limits handled gracefully with backoff
- ✅ Context limit scenarios managed with chunking strategies
- ✅ Timeout scenarios recover with partial progress preservation
- ✅ Error messages are informative and actionable
- ✅ System recovers and continues when resources available

**Expected**: 3-5 iterations, ~15 minutes

### T4.2: Malformed Input Handling
**Goal**: `Handle malformed inputs gracefully: invalid goals, corrupted files, malformed commands, edge case data`

**Expected Workflow**:
- Step 1: /goal - Define malformed input handling success criteria
- Step 2: /plan - Strategy for robust input validation and error handling
- Step 3: /reviewe - Review input validation approach
- Step 4: Autonomous approval
- Step 5: **Command**: /execute - Test various malformed input scenarios
- Step 6: /goal --validate - Verify graceful error handling
- Step 7: /guidelines - Document input validation patterns
- Step 8: CONVERGED

**Success Criteria**:
- ✅ Invalid goal statements handled with helpful error messages
- ✅ Corrupted file scenarios detected and managed appropriately
- ✅ Malformed command parameters result in clear guidance
- ✅ Edge case data doesn't crash the system
- ✅ Recovery suggestions provided for common error patterns

**Expected**: 2-4 iterations, ~12 minutes

### T4.3: Maximum Iteration Limit Testing
**Goal**: `Test maximum iteration behavior: create goal requiring exactly 10 iterations, verify proper termination and reporting`

**Expected Workflow**:
- Step 1: /goal - Define iteration limit testing success criteria
- Step 2: /plan - Strategy for controlled iteration limit testing
- Step 3: /reviewe - Review iteration control approach
- Step 4: Autonomous approval
- Step 5: **Command**: /execute - Execute deliberately complex goal requiring 10 iterations
- Step 6: /goal --validate - Verify proper termination at limit
- Step 7: /guidelines - Document iteration management patterns
- Step 8: PARTIAL (expected outcome at iteration limit)

**Success Criteria**:
- ✅ Goal designed to require exactly 10 iterations
- ✅ System properly terminates at iteration 10
- ✅ Partial completion report generated with progress summary
- ✅ Clear indication of why limit was reached
- ✅ Continuation strategy suggested for user

**Expected**: Exactly 10 iterations, ~20 minutes

---

## 📋 Test Execution Framework

### Validation Methodology
Each test task includes:
1. **Pre-conditions**: Required system state and dependencies
2. **Expected Workflow**: Step-by-step command sequence prediction  
3. **Success Criteria**: Objective, measurable outcomes
4. **Expected Duration**: Realistic time and iteration estimates
5. **Validation Evidence**: Required proof of completion

### Test Organization by Command Focus
- **Single Command Tests**: T1.1, T1.2, T1.3, T1.4, T1.5
- **Multi-Command Workflows**: T2.1, T2.2, T2.3, T2.4, T2.5, T2.6
- **Orchestration Tests**: T3.1, T3.2, T3.3, T3.4, T3.5, T3.6
- **Error Handling Tests**: T4.1, T4.2, T4.3

### Command Coverage Analysis
**Core Commands Tested**:
- `/goal` - Used in all tests (Steps 1 & 6)
- `/plan` - Used in all tests (Step 2)  
- `/reviewe` - Used in all tests (Step 3)
- `/cerebras` - T1.3, T1.5, T2.1, T2.4, T2.5, T3.1, T3.4, T3.6
- `/test` - T1.2, T2.1, T2.4, T3.1, T3.2, T3.3, T3.6
- `/execute` - T1.4, T2.2, T2.3, T2.4, T2.5, T2.6, T3.3, T3.4, T3.5, T3.6, T4.1, T4.2, T4.3
- `/copilot` - T2.2, T3.2
- `/orch` - T3.2, T3.5
- `/guidelines` - Used in all tests (Step 7)

**Specialized Commands Tested**:
- `/requirements-start` - T3.1
- `/design` - T3.1
- `/pr` - T3.1
- `/arch` - T3.3

### Success Rate Expectations
- **Tier 1**: 100% success rate (simple tasks)
- **Tier 2**: 95% success rate (manageable complexity)  
- **Tier 3**: 85% success rate (complex orchestration)
- **Tier 4**: 70% success rate (edge cases acceptable)

### Performance Benchmarks
- **Simple Tasks**: 1-2 iterations, 3-5 minutes each
- **Medium Tasks**: 2-4 iterations, 8-12 minutes each
- **Complex Tasks**: 4-8 iterations, 20-35 minutes each
- **Edge Case Tests**: Variable iterations, 12-20 minutes each

---

## 🚀 Test Execution Guidelines

### Pre-Execution Checklist
- [ ] Clean working directory state
- [ ] All dependencies available (git, tools, API access)
- [ ] Test isolation (each test in separate environment)
- [ ] Success criteria clearly defined
- [ ] Evidence collection methods prepared

### During Execution Monitoring
- [ ] Track actual vs expected iteration counts
- [ ] Monitor command selection and usage patterns  
- [ ] Document unexpected behaviors or optimizations
- [ ] Collect evidence for each success criterion
- [ ] Note convergence patterns and efficiency gains

### Post-Execution Analysis  
- [ ] Compare actual outcomes to predicted workflows
- [ ] Analyze convergence patterns and optimization opportunities
- [ ] Document lessons learned for system improvement
- [ ] Update test expectations based on actual performance
- [ ] Identify gaps in command coverage or workflow patterns

This comprehensive test suite validates /converge across all complexity levels, command integration patterns, and error scenarios, ensuring robust autonomous goal achievement capabilities.