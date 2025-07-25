# Claude Code Behavior Detailed Documentation

Detailed behavior rules and MCP configurations referenced in CLAUDE.md.

## Memory Enhancement Protocol (🚨 MANDATORY)

### Enhanced Commands:
Commands that require memory search and enhancement:
`/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`, `/perp`, `/research`

### High-Quality Memory Standards (⚠️ MANDATORY):
Based on Memory MCP best practices research (via Perplexity API research):

#### Required Technical Details:
- ✅ **Specific Technical Details**: Include exact error messages, file paths with line numbers (file:line), code snippets
- ✅ **Actionable Information**: Provide reproduction steps, implementation details, verification methods
- ✅ **External References**: Link to PRs, commits, files, documentation URLs for verification
- ✅ **Canonical Naming**: Use `{system}_{issue_type}_{timestamp}` format for disambiguation
- ✅ **Measurable Outcomes**: Include test results, performance metrics, quantified improvements
- ✅ **Contextual Details**: Timestamp, circumstances, specific situations that triggered learning
- ❌ **Avoid Low-Quality**: Generic statements, missing context, vague observations without actionable detail

#### Enhanced Entity Types:
Use specific, technical entity types:
- `technical_learning` - Specific solutions with code/errors/fixes
- `implementation_pattern` - Successful code patterns with reusable details
- `debug_session` - Complete debugging journeys with root causes
- `workflow_insight` - Process improvements with measurable outcomes
- `architecture_decision` - Design choices with rationale and trade-offs

#### Execution Steps:
1. ✅ **Extract specific technical terms** from command arguments (file names, error messages, PR numbers, technologies)
2. ✅ **Search Memory MCP**: Call `mcp__memory-server__search_nodes(query)` with extracted technical terms
3. ✅ **Log results transparently**: Always show "📚 Found X relevant memories"
4. ✅ **Natural integration**: If memories found, incorporate context naturally into response
5. ✅ **Capture high-quality learnings**: Use structured patterns with technical details, references, and actionable information
6. ❌ **Memory search is mandatory** for listed commands unless performance/availability exceptions apply

#### Quality Validation Before Storage:
- Contains specific technical details (error messages, file paths, code snippets)
- Includes actionable information (how to reproduce, fix, or implement)
- References external artifacts (PRs, commits, files, documentation)
- Uses canonical entity names for disambiguation
- Provides measurable outcomes (test counts, performance metrics)
- Links to related memories explicitly through relations

#### Transparency Requirements:
- Show "🔍 Searching memory..." when search begins
- Report "📚 Found X relevant memories" or "💭 No relevant memories found"
- Indicate when response is enhanced: "📚 Enhanced with memory context"

#### Performance Constraints:
- Batch all terms into single search (not multiple calls)
- Skip if search would take >100ms with notice to user
- Continue without enhancement if MCP unavailable (with notice)

#### Integration Approach:
- Use natural language understanding to weave context seamlessly
- Don't mechanically inject memory blocks
- Judge relevance using semantic understanding, not keyword matching
- Prioritize recent and relevant memories with actionable technical detail

## GitHub MCP Setup and Configuration

### Token Configuration:
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="your_token_here"`

### Private Repository Access:
**Private Repos**: Use direct functions only (no search) | `mcp__github-server__get_pull_request()`

### Restart Requirements:
**Restart After Token Change**: Remove & re-add github-server MCP

## Tool Priority Hierarchies

### GitHub Tool Priority (🚨 MANDATORY):
Tool hierarchy for GitHub operations:
- ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
- ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails or unavailable
- ✅ **TERTIARY**: Slash commands (e.g., `/copilot`) - user wants them to work but don't wait/assume completion
- ❌ NEVER wait for slash commands to complete when MCP tools can provide immediate results
- ✅ **Pattern**: Try MCP first → Fall back to `gh` CLI → Slash commands are bonus, not dependency
- Benefits: Immediate results, reliable API access, no command completion uncertainty

### Playwright MCP Default (🚨 MANDATORY):
When running in Claude Code CLI:
- ✅ ALWAYS use Playwright MCP (@playwright/mcp) for browser automation by default
- ✅ Microsoft's 2025 accessibility-tree based MCP server for AI-first automation
- ✅ Use Playwright MCP functions for structured, deterministic browser testing
- ✅ Fallback to Puppeteer MCP for Chrome-specific or stealth testing when needed
- Benefits: Accessibility-tree approach, cross-browser support, AI-optimized, session sharing

### Context7 MCP Proactive Usage (🚨 MANDATORY):
When encountering API/library issues:
- ✅ ALWAYS use Context7 MCP for accurate API documentation when facing errors
- ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs with `mcp__context7__get-library-docs`
- ✅ Search for specific error patterns, method signatures, or usage examples
- ✅ **Example**: Firestore transaction errors → Get google-cloud-firestore docs → Find correct API usage
- ❌ NEVER guess API usage or rely on outdated assumptions
- Benefits: Up-to-date docs, correct syntax, real working examples, eliminates trial-and-error

## Tool Explanation vs Execution Protocol

### Mandatory Distinction (🚨 MANDATORY):
- ✅ When user asks "does X tool do Y?", clearly state if you're explaining or executing
- ✅ If explaining capabilities, use "X tool CAN do Y" language
- ✅ If actually executing, use the tool and show results
- ❌ NEVER explain tool capabilities as if you executed them
- ⚠️ Example: "The /learn command can save to memory" vs "Saving to memory now..."

## Push Verification Protocol

### Mandatory Verification (🚨 MANDATORY):
⚠️ ALWAYS verify push success by querying remote commits after every `git push`
- Use `gh pr view` or `git log origin/branch` to confirm changes are on remote

## PR Status Interpretation

### Critical Status Understanding (🚨 MANDATORY):
GitHub PR states mean:
- **OPEN** = Work In Progress (WIP) - NOT completed
- **MERGED** = Completed and integrated into main branch  
- **CLOSED** = Abandoned or rejected - NOT completed
- ❌ NEVER mark tasks as completed just because PR exists
- ✅ ONLY mark completed when PR state = "MERGED"