# /reviewdeep Command

**Command Summary**: Comprehensive multi-perspective review through parallel execution with significant speed optimization (2.4x overall improvement) and **SOLO DEVELOPER SECURITY FOCUS**

**Purpose**: Deep analysis combining code review, architectural assessment, and ultra thinking for complete evaluation with practical security focus for solo developers (filters out enterprise paranoia, emphasizes real vulnerabilities)

## Usage
```
/reviewdeep                           # Review current branch/PR (default)
/reviewdeep <pr_number|file|feature>  # Review specific target
/reviewd                              # Short alias for current branch/PR
/reviewd <pr_number|file|feature>     # Short alias with specific target
```

## Command Composition

**`/reviewdeep` = Parallel execution of Technical Track (`/cerebras` analysis) + Strategic Track (`/arch` + Claude synthesis) + `/reviewe` + MCP integrations + SOLO DEVELOPER SECURITY FILTERING**

The command executes dual parallel review tracks by default with mandatory MCP integration for comprehensive analysis with significant speed improvement (2.4x overall). **Solo developer security focus**: Filters out enterprise paranoia, focuses on real exploitable vulnerabilities, and includes trusted source detection. Speed is always prioritized.

## Execution Flow

**The command delegates to `/execute` for intelligent orchestration of components:**

```markdown
/execute Perform enhanced parallel multi-perspective review:
1. /guidelines                    # Centralized mistake prevention consultation
2. PARALLEL EXECUTION:
   Track A (Technical - Fast):    /cerebras comprehensive technical analysis [target] (SOLO DEV FOCUS)
                                  - Security vulnerability scanning (real vulnerabilities only)
                                  - Trusted source detection (GitHub API, package managers)
                                  - Architecture pattern analysis
                                  - Performance bottleneck identification
                                  - Filter out enterprise paranoia (JSON schema validation for trusted APIs)
   Track B (Technical - Deep):    /arch [target] + Independent code-review subagent synthesis + gemini-consultant + codex-consultant
                                  - System design and scalability analysis
                                  - Integration patterns and dependencies
                                  - Code quality and maintainability assessment
                                  - Comprehensive multi-dimensional analysis (Gemini CLI consultation)
                                  - Multi-stage deep code analysis (Codex CLI consultation)
   Track C (AI Research):         Perplexity MCP comprehensive review [target] (gpt-5 model)
                                  - OWASP security standards and latest vulnerability research
                                  - Industry best practices and proven approaches
                                  - Performance optimization and benchmarking insights
                                  - Emerging security patterns and prevention techniques
                                  - Real-world code review expertise from security communities
3. /reviewe [target]             # Enhanced code review with security analysis
4. Synthesis & PR guidelines     # Combine all three tracks + generate docs/pr-guidelines/{PR_NUMBER}/guidelines.md
```

The `/execute` delegation ensures optimal execution with:
- **Always-Parallel Review Tracks**: Default simultaneous execution of technical (/cerebras), architectural (/arch), and AI research (Perplexity) analysis for significant speed improvement
- **Guidelines Generation**: Automatically creates `docs/pr-guidelines/{PR_NUMBER}/guidelines.md` with PR-specific mistake prevention patterns
- **Guidelines Integration**: Consults existing `docs/pr-guidelines/base-guidelines.md` (general patterns) and generates PR-specific guidelines
- **Anti-Pattern Application**: Analyzes review findings to document new mistake patterns and solutions
- **Intelligent Synthesis**: Combines technical and strategic findings into comprehensive recommendations
- Progress tracking via TodoWrite
- Auto-approval for review workflows
- Optimized parallel execution for maximum speed

Each command is executed with the same target parameter passed to `/reviewdeep`.

### 1. `/reviewe` - Enhanced Review with Official Integration

**🚨 POSTS COMPREHENSIVE COMMENTS**
- **Official Review**: Built-in Claude Code `/review` command provides baseline analysis
- **Enhanced Analysis**: Multi-pass security analysis with code-review subagent (SOLO DEV FOCUSED)
- **Security Focus**: Real vulnerabilities for solo developers: command injection, credential exposure, path traversal, SQL injection, XSS
- **Filtered Out**: Enterprise concerns like JSON schema validation for trusted APIs, theoretical attack vectors
- **Bug Detection**: Runtime errors, null pointers, race conditions, resource leaks
- **Performance Review**: N+1 queries, inefficient algorithms, memory leaks
- **Context7 Integration**: Up-to-date API documentation and framework best practices
- **ALWAYS POSTS** expert categorized comments (🔴 Critical, 🟡 Important, 🔵 Suggestion, 🟢 Nitpick)
- **ALWAYS POSTS** comprehensive security and quality assessment summary
- Provides actionable feedback with specific line references and fix recommendations

### 2. `/arch` - Architectural Assessment
- Dual-perspective architectural analysis
- System design patterns and scalability considerations
- Integration points and long-term maintainability
- Structural soundness and design quality evaluation

### 3. **Technical Track (Parallel)** - `/cerebras` Fast Analysis
- **Security Analysis**: Practical vulnerability scanning (solo dev focus), trusted source detection, real threat assessment
- **Architecture Analysis**: Design patterns, scalability concerns, structural integrity
- **Performance Analysis**: Bottleneck identification, optimization opportunities, resource usage
- **Solo Developer Context**: Filters enterprise paranoia, focuses on exploitable vulnerabilities
- **Speed Advantage**: Technical analysis track achieves 4.4x improvement (33s vs 146s for technical review component)

### 4. **Technical Deep Track (Parallel)** - `/arch` + Independent Code-Review Subagent + Comprehensive External AI Analysis
- **Architectural Assessment**: System design patterns and long-term maintainability
- **Scalability Analysis**: Performance implications and optimization opportunities
- **Integration Analysis**: Cross-system dependencies and technical compatibility
- **Code Quality Assessment**: Technical debt, maintainability, and refactoring opportunities
- **Independent Analysis**: Uses code-review subagent for objective, unbiased assessment
- **Comprehensive Multi-Dimensional Analysis**: gemini-consultant agent providing CodeRabbit/GitHub Copilot-style review covering correctness, architecture, security, performance, and PR goal alignment
- **Multi-Stage Deep Code Analysis**: codex-consultant agent using BugBot/DeepCode methodologies for advanced bug detection, security vulnerability analysis, performance review, and architectural quality assessment

### 5. **Context7 + GitHub + Gemini MCP Integration** - Expert Knowledge Analysis (ALWAYS REQUIRED)
- **Context7 MCP**: Real-time API documentation and framework-specific expertise
- **GitHub MCP**: Primary for PR, files, and review comment operations
- **Developer Perspective**: Code quality, maintainability, performance, security vulnerabilities
- **Architect Perspective**: System design, scalability, integration points, architectural debt
- **Business Analyst Perspective**: Business value, user experience, cost-benefit, ROI analysis
- **Framework Expertise**: Language-specific patterns and up-to-date best practices

### 6. **Perplexity MCP Integration** - Research-Based Analysis (ALWAYS REQUIRED)
- **Security Standards**: OWASP guidelines and latest vulnerability research
- **Industry Best Practices**: Current standards and proven approaches
- **Technical Challenges**: Common pitfalls and expert recommendations
- **Performance Optimization**: Industry benchmarks and optimization techniques
- **Emerging Patterns**: Latest security vulnerabilities and prevention techniques

## Analysis Flow

```
INPUT: PR/Code/Feature
    ↓
/EXECUTE ORCHESTRATION:
    ├─ Plans optimal parallel workflow
    ├─ Auto-approves review tasks
    └─ Tracks progress via TodoWrite
    ↓
EXECUTE: /guidelines
    └─ Centralized mistake prevention consultation
    ↓
PARALLEL EXECUTION (Speed Optimized):
    ├─ Track A (Technical - Fast): /cerebras analysis
    │   ├─ Security vulnerability scanning
    │   ├─ Architecture pattern analysis
    │   └─ Performance bottleneck identification
    ├─ Track B (Technical - Deep): /arch + Independent code-review subagent + gemini-consultant + codex-consultant
    │   ├─ System design and scalability assessment
    │   ├─ Integration patterns and dependencies
    │   ├─ Code quality and maintainability analysis
    │   ├─ Comprehensive multi-dimensional analysis (Gemini CLI consultation)
    │   └─ Multi-stage deep code analysis (Codex CLI consultation)
    └─ Track C (AI Research): Perplexity MCP review (gpt-5)
        ├─ OWASP security standards and vulnerability research
        ├─ Industry best practices and optimization insights
        └─ Emerging security patterns and prevention techniques
    ↓
EXECUTE: /reviewe [target]
    ├─ Runs official /review → Native Claude Code review
    └─ Runs enhanced analysis → Multi-pass security & quality review
    └─ Posts GitHub PR comments
    ↓
SYNTHESIS & GUIDELINES:
    ├─ Combines technical and strategic findings from all tracks
    ├─ **MANDATORY Agent Output Integration**:
    │   ├─ Gemini CLI Consultation Summary (correctness, architecture, security findings)
    │   ├─ Codex CLI Deep Analysis Summary (bugs, vulnerabilities, performance issues)
    │   └─ External AI Perspective Synthesis (alternative viewpoints and validation)
    ├─ Generates prioritized recommendations across all analysis dimensions
    └─ Creates docs/pr-guidelines/{PR_NUMBER}/guidelines.md with agent insights
    ↓
MCP INTEGRATION (automatic within each track):
    ├─ Context7 MCP → Up-to-date API documentation
    ├─ Gemini MCP → Multi-role AI analysis
    └─ Perplexity MCP → Research-based security insights
    ↓
OUTPUT: Comprehensive multi-perspective analysis with significant speed improvement (2.4x overall)
```

## 🛡️ Solo Developer Security Focus

### **Trusted Source Detection & Context-Aware Analysis**

The `/reviewdeep` command now implements intelligent context detection to distinguish between trusted and untrusted data sources, providing security analysis appropriate for solo developers:

### **Trusted Sources (Reduced Enterprise Paranoia)**
- **GitHub API responses** - Skip JSON schema validation for official GitHub API endpoints
- **Package managers** - npm, PyPI, Maven, NuGet from official registries
- **CDN providers** - cdnjs, unpkg, jsdelivr, and other established CDNs
- **Official documentation** - Framework docs, language specifications
- **Verified open source** - Projects with good reputation and security track record

### **Untrusted Sources (Full Security Analysis)**
- **User input** - Web forms, file uploads, command line arguments
- **External APIs** - Third-party services without verification
- **Dynamic code** - eval(), exec(), and code generation
- **File system access** - User-controlled paths and file operations
- **Database queries** - Dynamic SQL with user input

### **Security Focus Areas (Solo Developer Priorities)**

#### ✅ **ALWAYS ANALYZED** - Real Security Vulnerabilities
1. **Command Injection** - Unsanitized user input in system commands, shell=True risks
2. **Credential Exposure** - Hardcoded secrets, API keys in code, .env file issues
3. **Path Traversal** - User-controlled file paths, directory traversal vulnerabilities
4. **SQL Injection** - Dynamic queries without parameterization
5. **XSS Vulnerabilities** - Unsanitized output in web applications
6. **Authentication Flaws** - Session handling, password storage issues
7. **CSRF Vulnerabilities** - Missing CSRF tokens in state-changing operations

#### ❌ **FILTERED OUT** - Enterprise Paranoia (For Trusted Sources Only)
1. **JSON Schema Validation** - For trusted APIs like GitHub, npm registry
2. **Excessive Input Validation** - For verified package responses
3. **Theoretical Attack Vectors** - Low-probability scenarios with negligible real-world risk
4. **Complex Retry Patterns** - Over-engineered error handling for simple use cases
5. **Enterprise Compliance** - SOX, HIPAA, PCI-DSS unless specifically requested
6. **Over-Architected Security** - Complex patterns for simple solo developer needs

### **Context Detection Logic**

```markdown
IF data_source IN trusted_sources:
    SKIP enterprise_paranoia_checks
    FOCUS ON implementation_vulnerabilities
    VALIDATE integration_points_only
ELSE:
    APPLY full_security_analysis
    REPORT all_vulnerability_categories
    PROVIDE detailed_risk_assessment
END
```

### **Solo Developer Configuration**

**Default Behavior**: `--solo-dev-focus` (automatically applied)
- Practical security analysis for solo developers
- Trusted source detection enabled
- Enterprise paranoia filtering active

**Override Options**:
- `--enterprise-mode` - Full enterprise-level analysis (disables filtering)
- `--trust-level [strict|moderate|lenient]` - Adjust trusted source thresholds
- `--include-theoretical` - Include low-probability theoretical risks

## What You Get

### Comprehensive Coverage (Speed Optimized)
- **Technical Fast Track**: Security analysis, architecture patterns, performance optimization (/cerebras speed)
- **Technical Deep Track**: System design, scalability analysis, code quality assessment (Claude synthesis)
- **Combined Analysis**: Merged technical findings with prioritized technical recommendations

### Multi-Perspective Analysis (Parallel Execution)
- **Technical Perspective**: From `/review` + `/cerebras` - code quality, security, performance analysis
- **Design Perspective**: From `/arch` - structural and architectural concerns
- **Technical Synthesis**: From independent code-review subagent - scalability, maintainability, and technical integration
- **AI-Enhanced Analysis**: From Gemini MCP - multi-role expert perspectives
- **Research-Backed Insights**: From Perplexity MCP - industry best practices and standards
- **Speed Optimization**: Technical track achieves 4.4x improvement (33s vs 146s); overall execution ~5-8 minutes vs previous 12+ minutes

### Actionable Output
**🚨 POSTS TO GITHUB PR**
- **POSTS** specific inline code comments with improvement suggestions directly to PR
- **POSTS** general review comment with comprehensive findings summary to PR
- Architectural recommendations with design alternatives
- Reasoned conclusions with prioritized action items

## Implementation Protocol

**When `/reviewdeep` is invoked, it delegates to `/execute` for orchestration:**

```markdown
/execute Perform enhanced parallel review with comprehensive multi-perspective analysis:

Step 1: Execute guidelines consultation
/guidelines

Step 2: PARALLEL EXECUTION (Speed Optimized):
Track A (Technical - Fast): /cerebras comprehensive technical analysis [target]
  - Security vulnerability assessment
  - Architecture pattern evaluation
  - Performance bottleneck analysis
Track B (Technical - Deep): /arch [target] + Independent code-review subagent
  - System design and scalability analysis
  - Technical integration patterns
  - Code quality and maintainability recommendations

Step 3: Execute enhanced review and post comments
/reviewe [target]

Step 4: Synthesize parallel findings
Combine fast and deep technical analysis into prioritized technical recommendations

Step 5: Generate PR-specific guidelines from combined findings
Create docs/pr-guidelines/{PR_NUMBER}/guidelines.md with documented patterns and solutions
```

**The `/execute` delegation provides**:
- Automatic workflow planning and optimization
- Built-in progress tracking with TodoWrite
- Intelligent parallelization where applicable
- Resource-efficient execution

**Important**: Each command must be executed with the same target parameter. If no target is provided, all commands operate on the current branch/PR.

## Examples

```bash
# Review current branch/PR with solo developer security focus (most common usage)
/reviewdeep
# This executes: /guidelines → PARALLEL(/cerebras technical + /arch deep) → /reviewe → synthesis + SOLO DEV FILTERING
/reviewd

# Review a specific PR with solo developer context detection
/reviewdeep 592
# Automatically detects trusted sources (GitHub API calls) and filters enterprise paranoia
/reviewd #592

# Review a file with context-aware security analysis
/reviewdeep ".claude/commands/pr.py"
# Analyzes real vulnerabilities, skips theoretical concerns for solo developers
/reviewd "GitHub integration feature"

# Override for enterprise-level analysis (when needed)
/reviewdeep --enterprise-mode "security-critical-feature"
# Disables trusted source filtering, applies full enterprise security checks
```

## When to Use

- **Major architectural changes** - Need both code and design analysis (with solo developer focus)
- **High-risk implementations** - Require thorough multi-angle examination (real vulnerabilities only)
- **Performance-critical code** - Need technical + strategic assessment
- **Security-sensitive features** - Practical vulnerability analysis (filters enterprise paranoia)
- **Complex integrations** - Architectural + implementation concerns (trusted source detection)
- **Before production deployment** - Complete readiness evaluation (solo developer appropriate)
- **GitHub API integrations** - Automatically applies trusted source context
- **Package dependency reviews** - Focuses on real security issues, not theoretical concerns

## Comparison with Individual Commands

- **`/review`**: Official built-in code review (basic)
- **`/reviewe`**: Enhanced review (official + advanced analysis)
- **`/arch`**: Architectural assessment only
- **`/cerebras`**: Fast technical analysis (security, architecture, performance)
- **`/reviewdeep`**: Parallel execution of technical + strategic tracks for comprehensive analysis with significant speed improvement + SOLO DEVELOPER SECURITY FOCUS (filters enterprise paranoia)

## Benefits of Always-Parallel Execution + Solo Developer Security Focus

- **Performance Improvement**: Technical analysis track achieves 4.4x speedup (33s vs 146s); full review execution reduced from 12+ minutes to 5-8 minutes
- **Speed-First**: Prioritizes fast execution while maintaining comprehensive coverage
- **Solo Developer Optimized**: Filters out enterprise paranoia, focuses on real exploitable vulnerabilities
- **Context-Aware**: Automatically detects trusted sources (GitHub API, npm registry) and adjusts analysis accordingly
- **Practical Security**: Emphasizes command injection, credential exposure, path traversal over theoretical concerns
- **Comprehensive**: No blind spots - covers technical precision and deep technical analysis simultaneously

## 🔄 **MANDATORY Agent Output Synthesis Protocol**

When `/reviewdeep` completes parallel execution, the final synthesis MUST include:

### **External AI Consultation Integration**

**1. Gemini CLI Analysis Summary**
- **Architecture Findings**: SOLID principles adherence, design pattern usage, scalability issues
- **Security Assessment**: OWASP compliance, vulnerability detection, authentication analysis
- **Performance Evaluation**: Bottleneck identification, algorithmic efficiency, resource usage
- **Correctness Validation**: Logic accuracy, edge case handling, PR goal fulfillment
- **Code Quality**: Maintainability, complexity metrics, technical debt assessment

**2. Codex CLI Deep Analysis Summary**
- **Multi-Stage Bug Detection**: Logic errors, race conditions, memory leaks, boundary issues
- **Security Vulnerability Analysis**: OWASP Top 10 patterns, input validation gaps, injection vectors
- **Performance Issues**: Algorithmic complexity problems, resource cleanup, scalability concerns
- **Architectural Quality**: Design pattern implementation, SOLID violations, coupling issues
- **Production-Critical Findings**: Issues that could impact system stability

**3. External AI Perspective Synthesis**
- **Alternative Viewpoints**: Different model perspectives on implementation approaches
- **Validation Results**: Cross-verification of findings between different AI models
- **Consensus Analysis**: Areas where both agents agree vs. divergent opinions
- **Priority Assessment**: Combined ranking of issues by severity and impact

### **Integration Requirements**

**MANDATORY Output Format**:
```
## 🤖 External AI Consultation Results

### Gemini CLI Multi-Dimensional Analysis
[Detailed summary of architecture, security, performance, correctness findings]

### Codex CLI Deep Code Analysis  
[Detailed summary of bug detection, vulnerability analysis, performance issues]

### Cross-Model Validation
[Areas of agreement, divergent perspectives, priority recommendations]

### External AI Priority Issues
[Top 5 issues identified across both consultations with remediation suggestions]
```

This ensures that the valuable insights from external AI models are captured, synthesized, and presented as part of the comprehensive review output.
- **Efficient**: Always leverages /cerebras's speed for technical analysis while maintaining independent code-review subagent's objective insights
- **Flexible**: Individual commands can still be used separately when full analysis isn't needed, enterprise mode available when needed
- **Maintainable**: Parallel execution improves performance without breaking existing functionality
- **AI-Enhanced**: Mandatory MCP integration provides expert-level analysis beyond traditional code review
- **Optimal Resource Usage**: Maximizes AI capabilities through parallel processing while reducing noise

## Review Principles & Philosophy

### Core Principles (Applied During Analysis) - Solo Developer Focus
- **Verify Before Modify**: Ensure bugs are reproduced and root causes understood before suggesting fixes
- **Incremental and Isolated Changes**: Recommend small, atomic modifications that can be tested independently
- **Test-Driven Resolution**: Suggest writing tests for bug scenarios before implementing fixes
- **Practical Security**: Focus on real vulnerabilities (command injection, credential exposure) over theoretical concerns
- **Context-Aware Analysis**: Distinguish trusted sources (GitHub API, npm registry) from untrusted user input
- **Solo Developer Appropriate**: Filter enterprise paranoia, focus on exploitable vulnerabilities
- **Defensive Validation**: Recommend input checks for untrusted sources, skip excessive validation for trusted APIs
- **Fail Fast, Fail Loud**: No silent fallbacks - errors should be explicit and actionable

### Development Tenets (Beliefs That Guide Reviews) - Solo Developer Context
- **Bugs Are Opportunities**: Each issue is a chance to enhance robustness, not just patch symptoms
- **Prevention Over Cure**: Prioritize practices that avoid bugs (code reuse, proper abstractions)
- **Simplicity Wins**: Simpler code is less error-prone - avoid over-engineering and enterprise paranoia
- **Practical Security First**: Real vulnerabilities matter more than theoretical compliance concerns
- **Trust Context Matters**: GitHub API responses don't need JSON schema validation, user input does need sanitization
- **CI Parity Is Sacred**: All code must run deterministically in CI vs local environments
- **Solo Developer Realism**: Balance security with development velocity appropriate for solo/small teams
- **Continuous Learning**: Document patterns from failures to prevent recurrence

### Quality Goals (What Reviews Aim For)
- **Zero Regressions**: Ensure changes don't introduce new bugs
- **High Code Coverage**: Recommend 80-90% test coverage for critical paths
- **Maintainable Codebase**: Fixes should improve readability and modularity
- **Fast MTTR**: Issues should be resolvable within hours with proper documentation
- **Reduced Bug Density**: Lower bugs per 1000 lines through preventive patterns

### 6. **Testing & CI Safety Analysis** (Enhanced from /reviewe)
Building on the code-level checks from `/reviewe`, this phase analyzes system-wide patterns:

- **Subprocess Discipline at Scale**: System-wide timeout enforcement patterns
- **Skip Pattern Elimination**: Zero tolerance policy enforcement across entire codebase
- **CI Parity Validation**: Test infrastructure consistency analysis
- **Resource Management Patterns**: System-level cleanup strategies
- **Input Sanitization Architecture**: Security patterns across all entry points
- **Error Handling Philosophy**: Consistent error propagation strategies

## 🚨 CRITICAL: PR Guidelines Generation Protocol

### **Automatic Guidelines Creation**
`/reviewdeep` automatically generates PR-specific guidelines based on review findings:

**PR Context Detection**:
- **Primary**: Auto-detect PR number from current branch context via GitHub API
- **Fallback 1**: Extract from branch name patterns (e.g., `pr-1286-feature`, `fix-1286-bug`)
- **Fallback 2**: If no PR context, create branch-specific guidelines in `docs/branch-guidelines/{BRANCH_NAME}/guidelines.md`
- **Fallback 3**: If outside any PR/branch context (e.g., file/feature targets), skip guidelines generation and continue with analysis only
- **Manual Override**: Accept explicit PR number via `/reviewdeep --pr 1286`
- **Graceful Degradation**: Never fail /reviewdeep execution due to guidelines generation issues - log warning and proceed

**File Location**:
- **With PR**: `docs/pr-guidelines/{PR_NUMBER}/guidelines.md` (e.g., `docs/pr-guidelines/1286/guidelines.md`)
- **Without PR**: `docs/branch-guidelines/{BRANCH_NAME}/guidelines.md` (e.g., `docs/branch-guidelines/feature-auth/guidelines.md`)

**Generation Process**:
1. **Analyze Review Findings**: Extract patterns from `/reviewe`, `/arch`, and `/thinku` analysis
2. **Identify Mistake Patterns**: Document specific issues found in the PR
3. **Create Solutions**: Provide ❌ wrong vs ✅ correct examples with code snippets
4. **Generate Anti-Patterns**: Structure findings as reusable anti-patterns for future prevention
5. **Document Context**: Include PR-specific context and historical references

### **Guidelines Content Structure**
Generated guidelines file includes:

```markdown
# PR #{PR_NUMBER} Guidelines - {PR_TITLE}

## 🎯 PR-Specific Principles
- Core principles discovered from this PR's analysis

## 🚫 PR-Specific Anti-Patterns
### ❌ **{Pattern Name}**
{Description of wrong pattern found}
{Code example showing the problem}

### ✅ **{Correct Pattern}**
{Description of correct approach}
{Code example showing the solution}

## 📋 Implementation Patterns for This PR
- Specific patterns and best practices discovered
- Tool selection guidance based on what worked

## 🔧 Specific Implementation Guidelines
- Actionable guidance for similar future work
- Quality gates and validation steps
```

### **Integration with Review Process**
- **Step 4 of /reviewdeep**: Guidelines generation happens after analysis phases
- **Evidence-Based**: Only document patterns with concrete evidence from review
- **PR-Specific Focus**: Tailor guidelines to specific PR context and findings
- **Historical Reference**: Include specific line numbers, file references, and commit SHAs
- **Actionable Content**: Provide specific ❌/✅ examples that can prevent future mistakes

### **File Format Requirements**
- **Directory**: `docs/pr-guidelines/{PR_NUMBER}/` (consistent with base guidelines organization)
- **Filename**: `guidelines.md` (standardized name)
- **PR Number Extraction**: Auto-detect from current branch context or GitHub API
- **Example Paths**:
  - `docs/pr1286/guidelines.md`
  - `docs/pr592/guidelines.md`
  - `docs/pr1500/guidelines.md`

## MCP Integration Requirements

### 🚨 MANDATORY MCP Usage
- **Context7 MCP**: ALWAYS required for up-to-date API documentation and framework expertise
- **Gemini MCP**: ALWAYS required for multi-role AI analysis
- **Perplexity MCP**: ALWAYS required for research-based security and best practice insights
- **No Fallback Mode**: All MCP integrations are mandatory, not optional
- **Error Handling**: Proper timeout and retry logic for MCP calls
- **Expert Integration**: Context7 provides current API docs, Gemini provides analysis, Perplexity provides research

### Implementation Notes
- Uses `mcp__gemini-cli-mcp__gemini_chat_pro` for primary analysis
- Uses `mcp__perplexity-ask__perplexity_ask` for research insights
- Integrates MCP responses into comprehensive review output
- Maintains existing command composition while adding AI enhancement layer

## 🚀 Performance Optimization

### **Parallel Execution Architecture**
`/reviewdeep` now leverages parallel execution for dramatic speed improvements while maintaining comprehensive analysis quality.

### **Performance Benchmarks**

**Technical Analysis Component**:
- **Previous Sequential Technical**: 146 seconds (iterative technical analysis)
- **New Parallel Technical**: 33 seconds (/cerebras fast technical analysis)
- **Technical Track Speedup**: 4.4x faster for technical analysis component

**Full Review Execution**:
- **Previous Complete Review**: 12+ minutes (sequential /reviewe + /arch + /thinku workflow)
- **New Parallel Complete Review**: 5-8 minutes (parallel tracks + synthesis)
- **Overall Improvement**: ~2.4x faster for complete review workflow
- **Quality Maintained**: Comprehensive coverage through dual-track analysis

### **Optimization Strategy**
**Technical Track (Fast)**:
- Uses `/cerebras` for rapid technical analysis
- Security vulnerability scanning
- Architecture pattern evaluation
- Performance bottleneck identification
- Execution time: 2-3 minutes

**Technical Deep Track (Comprehensive)**:
- Uses `/arch` + Independent code-review subagent
- System design and scalability assessment
- Technical integration analysis
- Code quality and maintainability recommendations
- Execution time: 2-3 minutes

**Total Execution**: 5-8 minutes vs previous 12+ minutes (2.4x overall improvement)

### **Fallback Mechanism**
If `/cerebras` is unavailable, the command gracefully falls back to parallel execution using independent code-review subagent for Track A while maintaining Track B. Sequential execution is only used as final fallback.

### **Implementation Notes**
- Leverages `/execute`'s existing parallel execution capabilities
- Maintains all MCP integrations as mandatory requirements
- Preserves backward compatibility with existing usage patterns
- No breaking changes to command interface or output format
- Proven performance improvement based on comparative analysis evidence
