# Meta-Rules Detailed Documentation

Detailed explanations and evidence for core meta-rules referenced in CLAUDE.md.

## NO FAKE IMPLEMENTATIONS (🚨 MANDATORY)

**CRITICAL ANTI-PATTERN**: Always audit existing functionality before implementing new code

### Specific Violations to Avoid:
- ❌ NEVER create files with "# Note: In the real implementation" comments
- ❌ NEVER write placeholder code that doesn't actually work  
- ❌ NEVER create demonstration files instead of working implementations
- ❌ NEVER create Python intelligence files when .md files handle the logic
- ❌ NEVER duplicate systematic protocols that already exist in other .md files
- ❌ NEVER reimplement existing command functionality (use orchestration instead)

### Required Practices:
- ✅ ALWAYS audit existing commands and .md files before writing new implementations
- ✅ ALWAYS build real, functional code that works immediately
- ✅ ALWAYS enhance existing systems rather than creating fake parallel ones
- ✅ ALWAYS check if functionality exists: Read existing commands, Grep for patterns

### Evidence and Examples:
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Evidence**: PR #820 - 563+ lines of fake code removed (fixpr.py, commentreply.py, copilot.md duplication)
- **Evidence**: orchestrate_enhanced.py with placeholder comments frustrated user
- **Rule**: If you can't implement it properly, don't create the file at all

## ORCHESTRATION OVER DUPLICATION (🚨 MANDATORY)

### Core Principle:
Orchestrators delegate to existing commands, never reimplement their functionality

### Implementation Pattern:
- ✅ Pattern: New commands should be orchestrators, not implementers
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating their logic
- ✅ Add command summary at top of orchestrator .md files to prevent confusion
- ❌ NEVER copy systematic protocols from other .md files into new commands
- ❌ NEVER duplicate GitHub API commands that already exist in other commands

### Evidence:
- **Evidence**: PR #812 (https://github.com/WorldArchitectAI/repo/pull/812) - 120 lines of duplicate systematic protocol removed from copilot.md
- **Architecture**: copilot = orchestrator, not implementer

## NO OVER-ENGINEERING

### Core Prevention Strategy:
Prevent building parallel inferior systems vs enhancing existing ones

### Key Questions to Ask:
- ✅ ALWAYS ask "Can the LLM handle this naturally?" before building parsers/analytics systems
- ✅ ALWAYS try enhancing existing systems before building parallel new ones  
- ✅ ALWAYS prioritize user workflow integration over technical sophistication

### Specific Prohibitions:
- ❌ NEVER build parallel command execution systems - enhance Claude Code CLI instead
- ❌ NEVER build complex parsing when LLM can understand intent naturally
- ❌ NEVER add analytics/tracking beyond core functionality needs

### Pattern and Evidence:
- **Pattern**: Trust LLM capabilities, enhance existing systems, prioritize immediate user value
- **Evidence**: Command composition over-engineering (PR #737) - a parallel command execution system was built instead of enhancing the existing Claude Code CLI. This led to unnecessary complexity, duplication of functionality, and reduced maintainability.
- **Evidence**: Orchestration parallel development (PR #790) - created .claude/commands/orchestrate.py instead of enhancing existing orchestration/ directory with Redis infrastructure. Fixed by migrating LLM features TO the mature system and deleting parallel implementation.
- **Root Causes**: LLM capability underestimation, perfectionist engineering, integration avoidance, demo-driven development, insufficient analysis of existing infrastructure

## NO UNNECESSARY EXTERNAL APIS

### Decision Process:
Before adding ANY external API integration:
- ✅ FIRST ask "Can Claude solve this directly without external APIs?"
- ✅ ALWAYS try direct implementation before adding dependencies
- ✅ TEST the direct solution - if it works, STOP there
- ❌ NEVER default to Gemini API just because it exists in codebase
- ❌ NEVER add external LLM calls when Claude can generate responses directly

### Pattern Recognition:
- **Pattern**: Direct solution → Justify external need → Only then integrate
- **Anti-pattern**: See AI task → Immediately reach for Gemini API
- **Evidence**: GitHub comment fiasco (PR #796) - built Gemini integration that degraded to useless generic templates when Claude could have generated responses directly

## GEMINI API JUSTIFICATION REQUIREMENTS

### Valid Use Cases Only:
Gemini should ONLY be used when:
- ✅ The task requires capabilities Claude doesn't have (e.g., image generation)
- ✅ The system needs to work autonomously without Claude present
- ✅ Specific model features are required (e.g., specific Gemini models)
- ✅ User explicitly requests Gemini integration

### Prohibited Uses:
- ❌ NEVER use Gemini just for text generation that Claude can do
- ❌ NEVER add complexity without clear unique value

### Key Question:
"What can Gemini do here that Claude cannot?"

## NEVER SIMULATE INTELLIGENCE

### Core Prohibition:
When building response generation systems:
- ❌ NEVER create Python functions that simulate Claude's responses with templates
- ❌ NEVER use pattern matching to generate "intelligent" responses  
- ❌ NEVER build `_create_contextual_response()` methods that fake understanding
- ❌ NEVER generate generic replies like "I'll fix the issue" or "Thanks for the suggestion"

### Required Approach:
- ✅ ALWAYS invoke actual Claude for genuine response generation
- ✅ ALWAYS pass full comment context to Claude for analysis
- ✅ ALWAYS ensure responses address specific technical points, not patterns

### Pattern Recognition:
- **Pattern**: Collect data → Claude analyzes → Claude responds
- **Anti-pattern**: Collect data → Python templates → Fake responses
- **Violation Count**: 100+ times - STOP THIS PATTERN IMMEDIATELY

## USE LLM CAPABILITIES

### Natural Language Processing:
When designing command systems or natural language features:
- ❌ NEVER suggest keyword matching, regex patterns, or rule-based parsing
- ❌ NEVER propose "if word in text" simplistic approaches
- ✅ ALWAYS leverage LLM's natural language understanding
- ✅ ALWAYS trust the LLM to understand context, nuance, and intent

### Pattern Recognition:
- **Pattern**: User intent → LLM understanding → Natural response
- **Anti-pattern**: Keywords → Rules → Rigid behavior