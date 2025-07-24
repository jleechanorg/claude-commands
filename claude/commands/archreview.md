# Architecture Review Command

**Usage**: `/archreview [scope]` or `/arch [scope]`

**Purpose**: Conduct focused architecture and design reviews for solo MVP development using dual-perspective analysis with Gemini MCP and Claude.

## Solo MVP Development Context

**Target User**: Solo developer working on single MVP project
- **No Team Concerns**: Skip team velocity, skill assessments, coordination
- **No Backward Compatibility**: MVP stage allows breaking changes
- **Speed Over Polish**: Prioritize rapid iteration and feature delivery
- **Pragmatic Decisions**: Focus on "good enough" solutions that ship quickly

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

### Phase 2: Claude Primary, Gemini Consultant (MVP Focus)
Claude leads analysis with MVP priorities:
- **Structural Analysis**: Simple organization, clear module boundaries
- **Design Patterns**: Avoid over-engineering, use simple patterns that work
- **Maintainability**: Code clarity for single developer, minimal documentation
- **Technical Debt**: Only flag debt that blocks current features
- **MVP Principles**: Ship fast, iterate quickly, avoid premature optimization
- **Gemini Input**: Performance red flags and simpler alternatives

### Phase 3: Gemini Primary, Claude Consultant (MVP Reality Check)
Gemini leads with optimization focus, Claude provides MVP grounding:
- **Performance Review**: Only critical bottlenecks, not micro-optimizations
- **Alternative Approaches**: Simpler patterns and proven technologies
- **Industry Standards**: What's actually used in production MVPs
- **Risk Assessment**: Focus on user-facing failures, not edge cases
- **Innovation Opportunities**: Avoid shiny objects, stick to proven solutions
- **Claude Input**: "Too complex for MVP", "Ship first, optimize later"

### Phase 4: Joint Evaluation & MVP-Focused Recommendations
Both perspectives focus on MVP shipping priorities:
- **MVP ROI**: Time to ship vs feature value for users
- **Complexity Assessment**: Can one developer maintain this?
- **Ship vs Perfect**: Balance "good enough" vs "done right"
- **User Impact**: Does this actually help users or just feel clever?
- **Implementation Speed**: Quick wins vs long-term architecture
- **Breaking Change Freedom**: Take advantage of MVP flexibility
- **Next Feature Readiness**: Will this help or hinder next features?

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

**MCP Integration**: Leverages `mcp__gemini-cli-mcp__gemini_chat_pro` for alternative perspective analysis

**Output Format**:
```
# MVP Architecture Review Report

## Executive Summary
[MVP shipping readiness and key blockers]

## Phase 1: Context & Current State
[System understanding focused on shipping blockers]

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

## Action Items
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