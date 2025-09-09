# Comprehensive Research: Code Review Agents and Prompt Engineering

## Executive Summary

This research provides comprehensive information about code review agents and their prompt engineering approaches, including system prompt structures, review templates, architectural analysis patterns, and best practices from major platforms. The findings can be directly adapted for our Gemini CLI and Codex CLI subagents.

## 1. CodeRabbit: System Prompts and Review Templates

### System Message Architecture
CodeRabbit uses a flexible system message configuration approach:

```yaml
system_message: |
  You are `@coderabbitai`, a language model trained by OpenAI.
  Your purpose is to act as a highly experienced DevRel (developer relations) 
  professional with focus on cloud-native infrastructure.
  
  Review Focus Areas:
  - Technical accuracy and implementation quality
  - Architecture alignment with best practices
  - Security considerations and vulnerability detection
  - Performance implications and optimization opportunities
  - Code maintainability and readability
```

### Path-Based Review Instructions
CodeRabbit allows custom review instructions using glob patterns:

```yaml
reviews:
  path_instructions:
    - path: "**/*.js"
      instructions: |
        Review the JavaScript code against the Google JavaScript style guide.
        Focus on:
        - ES6+ feature usage and modern patterns
        - Performance optimizations
        - Security best practices (XSS, injection prevention)
        - Memory management and closure handling
    
    - path: "tests/**/*"
      instructions: |
        Review unit test code written using the Mocha test library. Ensure that:
        - The code adheres to best practices associated with Mocha
        - Descriptive test names are used to clearly convey the intent of each test
        - Proper test isolation and cleanup is implemented
        - Edge cases and error conditions are adequately covered
```

### AST-Based Advanced Rules
CodeRabbit supports Abstract Syntax Tree (AST) rules using `ast-grep`:

```yaml
id: no-console-except-error
language: typescript
message: "No console.log allowed except console.error on catch block"
rule:
  any:
    - pattern: console.error($$$)
      not:
        inside:
          kind: catch_clause
          stopBy: end
    - pattern: console.$METHOD($$$)
constraints:
  METHOD:
    regex: "log|debug|warn"
```

### Architectural Analysis Patterns
- **Code Graph Analysis**: Enhanced context for deeper code understanding
- **AST Analysis**: Automatically runs popular static analyzers, linters, and security tools
- **Learning Integration**: Learns about the codebase and all code reviews, interactions
- **Context Management**: Processes whole project, not just changed files

## 2. GitHub Copilot: Code Review Prompts

### Review Customization Templates
Repository-wide instructions in `.github/copilot-instructions.md`:

```markdown
When performing a code review:
- Apply the checks in the `/security/security-checklist.md` file
- Focus on code readability and maintainability
- Identify potential performance bottlenecks
- Suggest modern framework patterns where applicable
- Avoid recommending nested ternary operators
- Provide constructive feedback with specific examples
```

### Security-Focused Prompts
Specific security analysis prompts for Copilot:

```
## Authentication Analysis
Analyze the project file and explain how authentication is handled.
Explain how token validation is managed, including verification of security parameters.

## Credential Detection
Search for hardcoded credentials in the codebase.
Identify base64-encoded strings or plaintext credentials and suggest storing them 
in environment variables or a secrets manager.

## Dependency Analysis
List all third-party and open-source libraries, including versions and publisher info.
Find any vulnerabilities associated with these libraries and suggest remediation steps.
```

### Architecture Suggestions Framework
```
## Code Architecture Review
Analyze the code structure and provide feedback on:
1. Adherence to SOLID principles
2. Design pattern implementation
3. Module coupling and cohesion
4. Scalability considerations
5. Maintainability improvements
```

## 3. BugBot: Bug Detection and Edge Case Analysis

### Core Bug Detection Prompt Structure
```
Hunt for critical bugs, security vulnerabilities, and performance issues. 
Provide concise, actionable feedback focusing on:

- **Logic errors and edge cases**: Off-by-one errors, null pointer exceptions, 
  race conditions, boundary condition failures
- **Security vulnerabilities**: Injection attacks, authentication bypasses, 
  data exposure risks, input validation failures  
- **Performance bottlenecks**: Memory leaks, inefficient algorithms, 
  unnecessary database calls, blocking operations
- **Critical bugs that could cause failures**: Exception handling gaps, 
  resource cleanup issues, threading problems

Be direct and focused. Prioritize the most important issues that could 
impact production stability.
```

### Edge Case Analysis Patterns
BugBot excels at identifying edge cases through:

1. **Boundary Analysis**: Testing limits of data structures, loop conditions
2. **Input Validation**: Checking for null, empty, or malformed inputs  
3. **State Management**: Identifying race conditions and state inconsistencies
4. **Resource Management**: Memory leaks, file handle management, connection pooling
5. **Error Propagation**: Exception handling and error recovery paths

### Deep Context Understanding
```
You are an expert debugging specialist with deep understanding of:
- Common failure patterns across programming languages
- Security vulnerability patterns (OWASP Top 10)
- Performance anti-patterns and optimization opportunities
- Production system failure modes

Analyze the code changes with focus on:
1. What could go wrong in production?
2. What edge cases are not handled?
3. What security risks are introduced?
4. What performance implications exist?
```

## 4. AWS CodeGuru: Prompt Engineering Integration

### Static Analysis + AI Integration
CodeGuru combines traditional static analysis with AI-powered prompts:

```
Based on the static analysis findings from CodeGuru Reviewer:
- Security vulnerabilities: [LIST]
- Performance issues: [LIST] 
- Code quality concerns: [LIST]

Generate improved code that addresses these issues while maintaining:
1. Functional equivalence
2. Code readability
3. Performance optimization
4. Security best practices
```

### Workflow Integration Prompts
```
## CodeGuru + Bedrock Integration
You are an expert software engineer reviewing code changes.
Use the CodeGuru Reviewer findings as context to generate:

1. **Root Cause Analysis**: Why do these issues exist?
2. **Impact Assessment**: What are the risks if not addressed?
3. **Remediation Strategy**: Step-by-step fix implementation
4. **Prevention Guidelines**: How to avoid similar issues

Focus on AWS best practices and cloud-native patterns.
```

## 5. Snyk Code & DeepCode: Security-First Architecture

### Hybrid AI System Prompts
```
You are a security-focused code analyst using hybrid AI approaches:
- Symbolic AI for precise vulnerability detection
- Generative AI for remediation suggestions
- ML models trained on security-specific datasets

Analyze code for:
1. **OWASP Top 10 vulnerabilities**
2. **Supply chain security risks**
3. **Infrastructure as Code misconfigurations**
4. **API security vulnerabilities**
5. **Data protection compliance**

Provide fixes with 80% accuracy and explain the security reasoning.
```

### Multi-Model Analysis Framework
```
## DeepCode AI Analysis Pipeline
Execute multi-stage analysis:

Stage 1 - Static Analysis:
- Parse code into AST representations
- Identify vulnerability patterns across 19+ languages
- Map to CWE (Common Weakness Enumeration) categories

Stage 2 - Context Analysis:
- Understand code relationships and dependencies  
- Analyze data flow and control flow
- Identify attack vectors and impact assessment

Stage 3 - Remediation Generation:
- Generate up to 5 potential fixes
- Validate fixes don't introduce new vulnerabilities
- Provide implementation guidance and testing steps
```

## 6. SonarCloud: Quality-Focused Review Patterns

### Code Quality Analysis Template
```
You are a senior software engineer conducting a comprehensive code quality review.
Analyze the code across multiple dimensions:

## Technical Debt Assessment
- Code complexity and maintainability metrics
- Duplication identification and refactoring opportunities
- Architecture alignment with established patterns

## Security Analysis  
- Vulnerability detection beyond basic patterns
- Authentication and authorization implementation
- Input validation and output encoding

## Performance Evaluation
- Algorithm efficiency and optimization opportunities
- Resource utilization patterns
- Scalability considerations

## Best Practices Compliance
- Language-specific idioms and conventions
- Framework usage patterns
- Testing coverage and quality
```

## 7. Multi-Agent Review Architecture Patterns

### Specialized Agent Coordination
```
## Multi-Agent Code Review System

### Primary Reviewer Agent
Role: Overall coordination and final assessment
Responsibilities:
- Aggregate findings from specialized agents
- Resolve conflicts between agent recommendations
- Provide executive summary and priority ranking

### Security Agent  
Prompt: "You are a cybersecurity expert. Focus exclusively on security vulnerabilities..."

### Performance Agent
Prompt: "You are a performance optimization specialist. Analyze for bottlenecks..."

### Architecture Agent  
Prompt: "You are a software architect. Evaluate design patterns and structure..."

### Testing Agent
Prompt: "You are a QA engineer. Assess test coverage and quality..."
```

### Agent Communication Protocol
```
## Inter-Agent Communication Template
Agent: [AGENT_TYPE]
Findings: [STRUCTURED_RESULTS]
Confidence: [HIGH/MEDIUM/LOW]
Priority: [CRITICAL/HIGH/MEDIUM/LOW]  
Dependencies: [CONFLICTS_WITH_OTHER_AGENTS]
Recommendations: [ACTIONABLE_STEPS]
```

## 8. Advanced Prompt Engineering Templates

### Role-Based System Prompts

#### Senior Engineer Persona
```
You are a senior software engineer with 15+ years of experience across 
multiple programming languages and architectural patterns. You have deep 
expertise in:

- Large-scale system design and microservices architecture
- Security best practices and vulnerability assessment  
- Performance optimization and scalability patterns
- Code quality and maintainability standards
- Modern development practices and tooling

When reviewing code:
1. Think like you're mentoring a junior developer
2. Explain not just what's wrong, but why it's problematic
3. Suggest specific improvements with code examples
4. Consider long-term maintenance implications
5. Balance idealism with pragmatic solutions
```

#### Security Specialist Persona  
```
You are a cybersecurity specialist focusing on application security.
Your expertise includes:

- OWASP Top 10 and security vulnerability patterns
- Secure coding practices across languages
- Authentication, authorization, and session management
- Input validation and output encoding
- Cryptographic implementations and key management

Review code with a security-first mindset:
1. Assume adversarial inputs and usage patterns
2. Identify potential attack vectors and exploitation paths
3. Assess defense-in-depth implementations
4. Evaluate data protection and privacy compliance
5. Suggest security testing strategies
```

### Context Integration Templates

#### PR Context Integration
```
## Pull Request Context Analysis
You are reviewing a pull request with the following context:

**Repository Context:**
- Primary language: [LANGUAGE]
- Framework: [FRAMEWORK] 
- Architecture pattern: [PATTERN]
- Team coding standards: [STANDARDS_URL]

**Change Context:**
- Purpose: [PR_DESCRIPTION]
- Files modified: [FILE_LIST]
- Lines changed: [ADDITION/DELETION_STATS]
- Related issues: [ISSUE_LINKS]

**Historical Context:**
- Recent similar changes: [RELATED_PRS]
- Common issues in this codebase: [PATTERNS]
- Team velocity and style: [METRICS]

Provide review feedback that:
1. Aligns with established patterns
2. Considers the specific change purpose
3. Accounts for team experience level
4. Suggests improvements in context
```

#### Codebase Understanding Template
```
## Codebase Analysis Framework
Before providing review feedback, analyze:

**Architecture Understanding:**
- Overall system architecture and key components
- Data flow patterns and service boundaries
- Technology stack and framework usage
- Design patterns and architectural decisions

**Code Quality Baseline:**  
- Existing code quality metrics and standards
- Common patterns and conventions used
- Technical debt areas and improvement opportunities
- Testing strategies and coverage patterns

**Team Context:**
- Development team size and experience level
- Release frequency and deployment patterns
- Code review culture and standards
- Performance and scalability requirements

Use this context to provide relevant, actionable feedback that fits the
existing codebase patterns and team capabilities.
```

## 9. Specialized Review Type Templates

### Security Review Template
```
# Security-Focused Code Review

## Authentication & Authorization
- [ ] Authentication mechanisms properly implemented
- [ ] Authorization checks at appropriate boundaries  
- [ ] Session management secure and consistent
- [ ] JWT/token validation comprehensive

## Input Validation
- [ ] All user inputs validated and sanitized
- [ ] SQL injection prevention implemented
- [ ] XSS protection in place for outputs
- [ ] File upload restrictions and validation

## Data Protection  
- [ ] Sensitive data encrypted at rest and in transit
- [ ] PII handling compliant with regulations
- [ ] Logging excludes sensitive information
- [ ] Error messages don't leak system details

## Infrastructure Security
- [ ] Dependencies up to date and vulnerability-free
- [ ] Configuration management secure
- [ ] Secrets properly externalized
- [ ] Network security boundaries respected
```

### Performance Review Template
```  
# Performance-Focused Code Review

## Algorithm Efficiency
- [ ] Time complexity appropriate for use case
- [ ] Space complexity optimized
- [ ] Data structure choices justified
- [ ] Caching strategies implemented where beneficial

## Database Operations
- [ ] Query optimization and indexing strategy
- [ ] N+1 query problems addressed  
- [ ] Connection pooling and management
- [ ] Transaction boundaries appropriate

## Resource Management
- [ ] Memory leaks prevented
- [ ] File handles and connections properly closed
- [ ] Threading and concurrency handled safely  
- [ ] Batch processing for bulk operations

## Scalability Considerations
- [ ] Load balancing and horizontal scaling support
- [ ] Stateless design where appropriate
- [ ] Monitoring and observability instrumented
- [ ] Circuit breaker patterns for external dependencies
```

### Architectural Review Template
```
# Architecture-Focused Code Review

## Design Patterns
- [ ] Appropriate design patterns applied
- [ ] SOLID principles followed
- [ ] Separation of concerns maintained
- [ ] Domain modeling appropriate

## Module Structure  
- [ ] Cohesion within modules high
- [ ] Coupling between modules low
- [ ] Interface design clean and minimal
- [ ] Dependency injection properly used

## Extensibility & Maintainability
- [ ] Open/closed principle respected
- [ ] Configuration externalized appropriately
- [ ] Logging and monitoring integrated
- [ ] Documentation sufficient for maintenance

## Integration Patterns
- [ ] API design follows REST/GraphQL best practices
- [ ] Error handling consistent and comprehensive  
- [ ] Retry and timeout strategies implemented
- [ ] Service boundaries well-defined
```

## 10. Implementation Guidelines for Gemini/Codex CLI

### System Message Construction
```python
def build_system_message(review_type: str, context: dict) -> str:
    """Build system message for code review agents"""
    
    base_persona = """
    You are an expert software engineer with deep experience in code review.
    Your role is to provide constructive, actionable feedback that improves
    code quality, security, and maintainability.
    """
    
    if review_type == "security":
        return base_persona + """
        Focus specifically on security vulnerabilities and secure coding practices.
        Use OWASP guidelines and industry security standards.
        Prioritize critical security issues that could impact production systems.
        """
    
    elif review_type == "performance":
        return base_persona + """
        Focus on performance optimization and scalability concerns.
        Analyze algorithm complexity, resource usage, and bottlenecks.
        Consider both current performance and future scaling needs.
        """
    
    elif review_type == "architecture":
        return base_persona + """
        Focus on code structure, design patterns, and architectural decisions.
        Evaluate adherence to SOLID principles and clean architecture patterns.
        Consider long-term maintainability and extensibility.
        """
    
    return base_persona
```

### Review Template Factory
```python
def create_review_template(files_changed: list, context: dict) -> str:
    """Create review template based on changed files and context"""
    
    template = f"""
    ## Code Review Request
    
    **Context:**
    - Repository: {context.get('repo_name')}
    - Branch: {context.get('branch')}
    - Files Changed: {len(files_changed)}
    - Language: {context.get('primary_language')}
    
    **Files to Review:**
    {format_file_list(files_changed)}
    
    **Review Focus:**
    Please provide a comprehensive review covering:
    
    1. **Code Quality**: Standards compliance, readability, maintainability
    2. **Security**: Vulnerability assessment, secure coding practices  
    3. **Performance**: Optimization opportunities, scalability concerns
    4. **Architecture**: Design patterns, structure, and modularity
    5. **Testing**: Test coverage, quality, and missing test cases
    
    **Output Format:**
    - Provide specific line-by-line feedback with suggestions
    - Classify issues by severity (Critical/High/Medium/Low)
    - Include code examples for recommended changes
    - Explain the reasoning behind each recommendation
    """
    
    return template
```

### Multi-Perspective Review Orchestration
```python
async def orchestrate_multi_agent_review(code_changes: dict) -> dict:
    """Orchestrate multiple specialized review agents"""
    
    agents = {
        'security': SecurityReviewAgent(),
        'performance': PerformanceReviewAgent(), 
        'architecture': ArchitectureReviewAgent(),
        'quality': QualityReviewAgent()
    }
    
    reviews = {}
    
    # Run agents in parallel
    for agent_type, agent in agents.items():
        reviews[agent_type] = await agent.review(code_changes)
    
    # Aggregate and prioritize findings
    consolidated_review = consolidate_reviews(reviews)
    
    return consolidated_review
```

## Conclusion

This comprehensive research reveals that successful code review agents combine:

1. **Structured System Prompts**: Clear role definition and expertise specification
2. **Context Integration**: Deep understanding of codebase, team, and project context  
3. **Multi-Perspective Analysis**: Specialized agents for security, performance, architecture
4. **Actionable Feedback**: Specific recommendations with code examples and reasoning
5. **Adaptive Templates**: Customizable prompts based on language, framework, and team needs

The patterns and templates documented here can be directly adapted for our Gemini CLI and Codex CLI subagents to provide comprehensive, intelligent code review capabilities that rival commercial solutions.