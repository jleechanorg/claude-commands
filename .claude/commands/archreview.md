# Architecture Review Command

**Usage**: `/archreview [scope]` or `/arch [scope]`

**Purpose**: Conduct comprehensive architecture and design reviews using dual-perspective analysis with Gemini MCP and Claude, enhanced by thinking methodology.

## Architecture Review Protocol

**Default Thinking Mode**: Architecture reviews use sequential thinking (4-6 thoughts) by default.
**Ultra-Think Upgrade**: When combined with `/thinku`, automatically upgrades to deep analysis (12+ thoughts).

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

### Phase 1: Context Gathering & Validation
1. **PR Content Validation** (if reviewing a PR/branch):
   - Use `gh api repos/owner/repo/pulls/<PR#>/files --jq '.[].filename'` to get actual PR files
   - Compare claimed capabilities against actual PR contents
   - **CRITICAL CHECK**: Verify implementation files exist in PR, not just documentation
   - **STOP IMMEDIATELY**: If documentation claims features that aren't in the PR
2. **Codebase Analysis**: Examine current state, recent changes, and architectural patterns
3. **Documentation Review**: Check existing architecture docs and design decisions
4. **Dependencies Analysis**: Review external dependencies and integrations

### Phase 2: Claude Primary, Gemini Consultant
Claude leads the analysis with Gemini providing insights:
- **Structural Analysis**: Code organization, module boundaries, coupling/cohesion
- **Design Patterns**: Appropriate use of patterns, anti-patterns identification
- **Maintainability**: Code clarity, documentation, test coverage
- **Technical Debt**: Identify areas needing refactoring or improvement
- **SOLID Principles**: Adherence to software engineering best practices
- **Gemini Input**: Performance implications and alternative patterns

### Phase 3: Gemini Primary, Claude Consultant
Gemini leads with fresh perspective, Claude provides context:
- **Performance Review**: Bottlenecks, optimization opportunities, scaling considerations
- **Alternative Approaches**: Different architectural patterns or technologies
- **Industry Standards**: Comparison with current best practices and trends
- **Risk Assessment**: Potential failure points and mitigation strategies
- **Innovation Opportunities**: Modern approaches and emerging patterns
- **Claude Input**: Practical constraints and migration considerations

### Phase 4: Joint Evaluation & Final Recommendations
Both perspectives collaborate to evaluate the proposed approach:
- **ROI Analysis**: Cost vs benefit of proposed changes
- **Complexity Assessment**: Is the solution overengineered?
- **Pros and Cons**: Balanced view of each recommendation
- **Initial vs Final**: Compare final approach against initial ideas
- **Consensus Building**: Areas where both perspectives strongly agree
- **Trade-off Analysis**: Where perspectives differ and why
- **Prioritized Roadmap**: What to implement first based on value/effort

## Role Switching Protocol

**Phase 2: Claude Primary / Gemini Consultant**
- **Claude leads**: Deep understanding of current system, practical constraints
- **Claude focus**: Maintainability, team velocity, incremental improvements
- **Gemini supports**: "What about performance?", "Consider this pattern", "Industry does X"
- **Dynamic**: Claude proposes, Gemini challenges and enhances

**Phase 3: Gemini Primary / Claude Consultant**
- **Gemini leads**: Fresh perspective, modern approaches, optimal solutions
- **Gemini focus**: Performance, scalability, cutting-edge patterns
- **Claude supports**: "That would break Y", "Migration path?", "Team skills?"
- **Dynamic**: Gemini innovates, Claude grounds in reality

**Phase 4: Equal Partnership**
- **Both evaluate**: No primary/consultant roles
- **Joint focus**: ROI, complexity, pragmatism
- **Key questions**: 
  - "Is this overengineered for the actual problem?"
  - "What's the real benefit vs cost?"
  - "Does this align with team capabilities?"
  - "Quick wins vs long-term vision?"

## Implementation

**Thinking Integration**: Uses `mcp__sequential-thinking__sequentialthinking` with:

**Default Mode** (with `/think` or standalone):
- **Total Budget**: 4-6 thoughts for complete review
- Balanced analysis across all phases

**Ultra Mode** (when combined with `/thinku`):
- **Initial Analysis**: 4-6 thoughts for context gathering
- **Deep Review**: 8-12 thoughts for architectural analysis  
- **Synthesis**: 4-6 thoughts for final recommendations
- **Total Budget**: 16-24 thoughts for comprehensive review

**MCP Integration**: Leverages `mcp__gemini-cli-mcp__gemini_chat_pro` for alternative perspective analysis

**Output Format**:
```
# Architecture Review Report

## Executive Summary
[Overview of findings from all phases]

## Phase 1: Context & Current State
[System understanding and scope definition]

## Phase 2: Claude-Led Analysis (Gemini Consulting)
### Primary Analysis (Claude)
[Structural review, patterns, maintainability]
### Consultant Insights (Gemini)
[Performance considerations, alternatives suggested]

## Phase 3: Gemini-Led Analysis (Claude Consulting)  
### Primary Analysis (Gemini)
[Modern approaches, optimizations, innovations]
### Consultant Reality Check (Claude)
[Practical constraints, migration concerns]

## Phase 4: Joint Evaluation
### ROI Assessment
[Cost vs benefit analysis of proposed changes]
### Complexity Check
[Is this overengineered? Just right? Too simple?]
### Final Recommendations
[Balanced approach considering all perspectives]

## Action Items
- [ ] Quick Wins: [High-value, low-effort changes]
- [ ] Strategic: [Important architectural improvements]  
- [ ] Future Vision: [Long-term modernization goals]
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