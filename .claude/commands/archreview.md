# Architecture Review Command

**Usage**: `/archreview [scope]` or `/arch [scope]`

**Purpose**: Conduct comprehensive architecture and design reviews using dual-perspective analysis with Gemini MCP and Claude, enhanced by ultrathink methodology.

## Architecture Review Protocol

**Automatic Ultra-Think**: All architecture reviews use deep sequential thinking (`ultrathink` mode with 12+ thoughts) for thorough analysis by default.

**Dual-Perspective Analysis**: 
1. **Claude Perspective**: System architecture, design patterns, maintainability, technical debt
2. **Gemini Perspective**: Performance optimization, scalability concerns, alternative approaches, industry best practices

## Scope Options

- `/archreview` or `/arch` - Review current branch/PR changes
- `/archreview codebase` - Full codebase architecture review
- `/archreview [file/folder]` - Focused review of specific component
- `/archreview api` - API design and integration review
- `/archreview data` - Data model and storage architecture review
- `/archreview security` - Security architecture assessment

## Review Process

**Phase 1: Context Gathering & Validation**
1. **PR Content Validation** (if reviewing a PR/branch):
   - Use `gh api repos/owner/repo/pulls/<PR#>/files --jq '.[].filename'` to get actual PR files
   - Compare claimed capabilities against actual PR contents
   - **CRITICAL CHECK**: Verify implementation files exist in PR, not just documentation
   - **STOP IMMEDIATELY**: If documentation claims features that aren't in the PR
2. **Codebase Analysis**: Examine current state, recent changes, and architectural patterns
3. **Documentation Review**: Check existing architecture docs and design decisions
4. **Dependencies Analysis**: Review external dependencies and integrations

**Phase 2: Claude Analysis** (Primary Architecture Perspective)
- **Structural Analysis**: Code organization, module boundaries, coupling/cohesion
- **Design Patterns**: Appropriate use of patterns, anti-patterns identification
- **Maintainability**: Code clarity, documentation, test coverage
- **Technical Debt**: Identify areas needing refactoring or improvement
- **SOLID Principles**: Adherence to software engineering best practices

**Phase 3: Gemini Analysis** (Alternative Perspective)
- **Performance Review**: Bottlenecks, optimization opportunities, scaling considerations
- **Alternative Approaches**: Different architectural patterns or technologies
- **Industry Standards**: Comparison with current best practices and trends
- **Risk Assessment**: Potential failure points and mitigation strategies
- **Innovation Opportunities**: Modern approaches and emerging patterns

**Phase 4: Synthesis & Recommendations**
- **Consensus Findings**: Areas where both perspectives agree
- **Conflicting Views**: Analysis of different recommendations with trade-offs
- **Prioritized Action Items**: Critical, important, and nice-to-have improvements
- **Implementation Roadmap**: Suggested order and approach for changes

## Role Switching Protocol

**Claude Role**: Primary Architect
- Focus on current system understanding and practical implementation
- Emphasize maintainability, readability, and team development velocity
- Consider existing codebase constraints and migration paths

**Gemini Role**: Consulting Architect  
- Focus on performance, scalability, and industry benchmarks
- Suggest alternative approaches and newer technologies
- Challenge existing decisions with fresh perspective

## Implementation

**Ultra-Think Integration**: Uses `mcp__sequential-thinking__sequentialthinking` with:
- **Initial Analysis**: 4-6 thoughts for context gathering
- **Deep Review**: 8-12 thoughts for architectural analysis  
- **Synthesis**: 4-6 thoughts for final recommendations
- **Total Budget**: 16-24 thoughts for comprehensive review

**MCP Integration**: Leverages `mcp__gemini-cli-mcp__gemini_chat_pro` for alternative perspective analysis

**Output Format**:
```
# Architecture Review Report

## Executive Summary
[Key findings and recommendations]

## Claude Analysis (Primary)
[Detailed structural and maintainability review]

## Gemini Analysis (Alternative)  
[Performance and innovation perspective]

## Synthesis
[Combined recommendations with priorities]

## Action Items
- [ ] Critical: [High-priority fixes]
- [ ] Important: [Medium-priority improvements]  
- [ ] Enhancement: [Nice-to-have optimizations]
```

## Examples

```bash
/arch                                    # Review current PR changes
/arch codebase                          # Full architecture audit
/arch mvp_site/main.py                  # Review main application file
/arch api                               # API design review
/archreview security                    # Security architecture assessment
```

## Integration Notes

- **Branch Context**: Automatically detects current branch and associated PR
- **File Discovery**: Uses intelligent file scanning for relevant components
- **Documentation**: Generates architecture decision records (ADRs) when appropriate
- **Follow-up**: Provides specific, actionable implementation guidance