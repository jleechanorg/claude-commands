# Architecture Review Command

**Usage**: `/archreview [scope]` or `/arch [scope]`

**Purpose**: Conduct focused architecture and design reviews for solo MVP development using tri-perspective analysis with Gemini MCP, Perplexity (GPT-5), and Claude.

## Solo MVP Development Context

**Target User**: Solo developer working on single MVP project
- **No Team Concerns**: Skip team velocity, skill assessments, coordination
- **No Backward Compatibility**: MVP stage allows breaking changes
- **Speed Over Polish**: Prioritize rapid iteration and feature delivery
- **Pragmatic Decisions**: Focus on "good enough" solutions that ship quickly

## Architecture Review Protocol

**Default Thinking Mode**: Architecture reviews use sequential thinking (4-6 thoughts) by default.
**Ultra-Think Upgrade**: When combined with `/thinku`, automatically upgrades to deep analysis (12+ thoughts).

**Quad-Perspective Analysis**:
1. **Claude Perspective**: System architecture, design patterns, maintainability, technical debt
2. **Gemini Perspective**: Performance optimization, scalability concerns, alternative approaches, industry best practices
3. **Cursor Perspective**: Unconventional insights, real-world practicality, contrarian analysis, creative solutions
4. **Perplexity (GPT-5) Perspective**: Latest architectural patterns, cutting-edge best practices, modern framework recommendations, state-of-the-art security approaches

## Scope Options

- `/archreview` or `/arch` - Review current branch/PR changes
- `/archreview codebase` - Full codebase architecture review
- `/archreview [file/folder]` - Focused review of specific component
- `/archreview api` - API design and integration review
- `/archreview data` - Data model and storage architecture review
- `/archreview security` - Security architecture assessment

## Review Process

### Phase 1: Context Gathering & Memory-Enhanced Validation
1. **Memory MCP Search with Query Optimization**: Enhanced query memory for architectural patterns using optimization engine
   - **Query Optimization**: Uses universal composition with `/memory search` for improved architectural pattern discovery
   - **Smart Search Strategy**: Transform compound architecture queries into optimized single-word searches
   - **Enhanced Pattern Discovery**: Improve search success from ~30% to 70%+ for better architectural insights
   - **Result Merging**: Combine multiple optimized searches for comprehensive architecture analysis
   - Search for: architecture decisions, design patterns, performance insights, solo developer patterns
   - Extract context from enhanced search results for better architectural analysis
   - Log findings: "📚 Found X relevant architectural memories"
2. **PR Content Validation** (if reviewing a PR/branch):
   - Use `gh api repos/owner/repo/pulls/<PR#>/files --jq '.[].filename'` to get actual PR files
   - Compare claimed capabilities against actual PR contents
   - **CRITICAL CHECK**: Verify implementation files exist in PR, not just documentation
   - **STOP IMMEDIATELY**: If documentation claims features that aren't in the PR
3. **Memory-Enhanced Codebase Analysis**: Examine current state using insights from memory
4. **Documentation Review**: Check existing architecture docs against memory patterns
5. **Dependencies Analysis**: Review external dependencies with memory context

### Phase 2: PARALLEL AI ANALYSIS (Claude + Gemini + Cursor + Perplexity GPT-5)
**Execute in parallel for maximum speed:**

**Track A - Claude Analysis (MVP Pragmatism):**
- **Structural Analysis**: Simple organization, clear module boundaries
- **Design Patterns**: Avoid over-engineering, use simple patterns that work
- **Maintainability**: Code clarity for single developer, minimal documentation
- **Technical Debt**: Only flag debt that blocks current features
- **MVP Principles**: Ship fast, iterate quickly, avoid premature optimization

**Track B - Gemini Analysis (Performance & Alternatives):**
- **Performance Review**: Only critical bottlenecks, not micro-optimizations
- **Alternative Approaches**: Simpler patterns and proven technologies
- **Industry Standards**: What's actually used in production MVPs
- **Risk Assessment**: Focus on user-facing failures, not edge cases
- **Innovation Opportunities**: Avoid shiny objects, stick to proven solutions

**Track C - Cursor Analysis (Unconventional Insights):**
- **Implementation**: Use `cursor-consultant` agent for Cursor's real-time perspective via the Cursor CLI
- **Reality Check**: What will actually break in production vs theoretical concerns
- **Unconventional Solutions**: Creative approaches that conventional analysis misses
- **Contrarian Assessment**: Challenge established best practices and assumptions
- **Practical Innovation**: Real-world optimizations and non-obvious improvements
- **Direct Feedback**: Unfiltered assessment of architectural decisions

**Track D - Perplexity GPT-5 Analysis (Cutting-Edge Insights):**
- **Implementation**: `mcp__perplexity-ask__perplexity_ask(messages=[{role: "user", content: architecture_query, model: "gpt-5"}])`
- **Latest Patterns**: Modern architectural patterns from 2024-2025
- **Security Standards**: Most recent security best practices and vulnerabilities
- **Framework Evolution**: Latest updates in frameworks and tools
- **Performance Optimization**: State-of-the-art optimization techniques
- **Future-Proofing**: Architectural decisions that prepare for scaling

### Phase 3: Quad-Perspective Synthesis & MVP-Focused Recommendations
All four AI perspectives synthesized for MVP shipping priorities:
- **MVP ROI**: Time to ship vs feature value for users
- **Complexity Assessment**: Can one developer maintain this?
- **Ship vs Perfect**: Balance "good enough" vs "done right"
- **User Impact**: Does this actually help users or just feel clever?
- **Implementation Speed**: Quick wins vs long-term architecture
- **Breaking Change Freedom**: Take advantage of MVP flexibility
- **Next Feature Readiness**: Will this help or hinder next features?

### Phase 5: Memory MCP Integration (Capture New Learnings)
Store new architectural insights discovered during review:
- **New Decision Capture**: Store key architectural decisions with rationale and trade-offs
- **Pattern Documentation**: Record successful and failed design patterns discovered
- **Performance Insights**: Capture performance-related decisions and outcomes
- **MVP Lessons**: Document new solo developer learnings and pragmatic approaches
- **Relation Building**: Connect new learnings to existing memory patterns from Phase 1

## Role Switching Protocol

**Phase 2: Claude Primary / Gemini Consultant (MVP Pragmatism)**
- **Claude leads**: Current system understanding, solo developer constraints
- **Claude focus**: Rapid iteration, single-person maintainability, shipping speed
- **Gemini supports**: "Performance concerns?", "Simpler pattern exists?", "MVP examples?"
- **Dynamic**: Claude proposes MVP approach, Gemini suggests optimizations

**Phase 3: Gemini Primary / Claude Consultant (Reality Grounding)**
- **Gemini leads**: Optimization opportunities, cleaner solutions
- **Gemini focus**: Performance gains, scalability for growth, best practices
- **Claude supports**: "Too complex for MVP?", "Can ship without this?", "Solo maintainable?"
- **Dynamic**: Gemini optimizes, Claude ensures MVP practicality

**Phase 4: Equal Partnership (Shipping Focus)**
- **Both evaluate**: MVP shipping readiness
- **Joint focus**: Speed, simplicity, user value
- **Key questions**:
  - "Can one person build and maintain this?"
  - "Does this help users or just satisfy engineering perfectionism?"
  - "Can we ship without this refinement?"
  - "Will this block or enable next features?"

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

**MCP Integration**:
- **Gemini MCP**: `mcp__gemini-cli-mcp__gemini_chat_pro` for alternative perspective analysis
- **Memory MCP**: `mcp__memory-server__*` for capturing architectural insights and design decisions

**Memory MCP Workflow**:
1. **Pre-Analysis Memory Search**: Query memory for relevant architectural patterns, decisions, and learnings BEFORE starting review
2. **Context Enhancement**: Integrate found memories into analysis for more informed architectural assessment
3. **Pattern Recognition**: Identify similar architectural challenges and successful solutions from memory
4. **Decision History**: Reference previous architectural decisions and their outcomes
5. **Post-Analysis Capture**: Store new architectural insights, design patterns, and performance learnings
6. **Relation Building**: Connect new decisions to existing architectural patterns and outcomes
7. **Entity Types**: `architecture_decision`, `design_pattern`, `performance_insight`, `mvp_tradeoff`, `solo_dev_pattern`

**Output Format**:
```
# MVP Architecture Review Report

## Executive Summary
[MVP shipping readiness and key blockers]

## Phase 1: Memory-Enhanced Context & Current State
### 📚 Architectural Memory Context
[Relevant patterns and decisions from memory search]
### Current System Analysis
[System understanding enhanced with memory insights]

## Phase 2: Claude-Led Analysis (MVP Pragmatism)
### Primary Analysis (Claude)
[Solo maintainability, shipping speed, simplicity]
### Consultant Insights (Gemini)
[Performance red flags, simpler alternatives]

## Phase 3: Gemini-Led Analysis (Reality Check)
### Primary Analysis (Gemini)
[Optimization opportunities, cleaner patterns]
### Consultant Reality Check (Claude)
[MVP complexity limits, solo developer constraints]

## Phase 4: Joint MVP Assessment
### Shipping Readiness
[Can this ship to users this week?]
### Solo Maintainability
[Can one developer handle this complexity?]
### MVP Recommendations
[Focus on shipping, iterate later]

### Phase 5: Architectural Learnings Captured
#### Key Decisions Stored
[Architectural decisions captured in memory for future reference]
#### Patterns Identified
[Design patterns and approaches documented]
#### Solo Developer Insights
[MVP-specific learnings for solo development context]

### Action Items
- [ ] Ship Blockers: [Must fix before users see this]
- [ ] Quick Wins: [Easy improvements while building]
- [ ] Post-MVP: [Save for after initial user feedback]
```

## Examples

```bash
/arch                                    # Review current changes for MVP readiness
/arch codebase                          # Full MVP architecture health check
/arch mvp_site/main.py                  # Review core app file for solo maintainability
/arch api                               # API design - simple and shippable?
/archreview security                    # Security for MVP (basics, not enterprise)
```

## MVP Integration Notes

- **Shipping Focus**: All recommendations prioritize getting to users quickly
- **Solo Developer**: Assumes single person building and maintaining
- **Breaking Changes OK**: MVP stage allows architectural pivots
- **User Value Priority**: Engineering perfectionism takes backseat to user needs
- **Iteration Mindset**: Build, ship, learn, and improve rather than perfect then ship
