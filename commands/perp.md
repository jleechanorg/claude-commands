# Perp Command - Comprehensive Multi-Search

**Purpose**: Combine multiple search engines for comprehensive results

**Usage**: `/perp <query>` - Search across Claude, DuckDuckGo, and Perplexity simultaneously

## 🔍 MULTI-ENGINE SEARCH PROTOCOL

This command combines three powerful search capabilities:
1. **Claude Default Search** (WebSearch) - Claude's built-in web search
2. **DuckDuckGo MCP** - Privacy-focused web search with content fetching
3. **Perplexity MCP** - AI-powered search with conversation capabilities

### Search Engine Details

#### 1. Claude WebSearch
**Capabilities**:
- Up-to-date web information
- Search result blocks with summaries
- Domain filtering (include/exclude)
- US-based search results

#### 2. DuckDuckGo MCP
**Capabilities**:
- Privacy-focused web search
- Content fetching from URLs
- Metadata extraction
- Felo search integration

#### 3. Perplexity MCP
**Capabilities**:
- AI-powered conversational search
- Real-time information synthesis
- Context-aware responses
- Academic and research focus

## Search Combination Strategy

**Parallel Execution**:
- All three searches run simultaneously
- Results are compared and synthesized
- Unique insights from each engine are highlighted
- Comprehensive answer combines all sources

**Result Synthesis**:
- Extract key information from each source
- Identify overlapping vs. unique findings
- Highlight conflicting information
- Provide source attribution for all claims

## Example Usage

**Query**: `/perp figure out how to talk to anthropic api with python`

**Expected Flow**:
```
🔍 Searching across multiple engines for: "figure out how to talk to anthropic api with python"

📊 Claude WebSearch Results:
[Latest Anthropic API documentation and tutorials]

🔍 DuckDuckGo Results:
[Privacy-focused search results with code examples]

🧠 Perplexity Analysis:
[AI-synthesized answer with current best practices]

🎯 Synthesized Answer:
[Combined insights from all three sources with attribution]
```

## Protocol Implementation

**Search Execution**:
1. Parse user query from `/perp` command
2. Execute all three searches in parallel:
   - `WebSearch(query=user_query)`
   - `mcp__ddg-search__web-search(query=user_query)`
   - `mcp__perplexity-ask__perplexity_ask(messages=[{role: "user", content: user_query}])`
3. Wait for all results
4. Synthesize and combine findings

**Result Processing**:
- Compare information accuracy across sources
- Identify most recent/relevant information
- Flag conflicting information for user awareness
- Provide clear source attribution

## Key Benefits

- ✅ **Comprehensive Coverage** - Three different search approaches
- ✅ **Real-time Information** - Latest data from multiple sources
- ✅ **AI Synthesis** - Perplexity provides intelligent analysis
- ✅ **Privacy Option** - DuckDuckGo for privacy-conscious searches
- ✅ **Source Diversity** - Different algorithms and data sources
- ✅ **Conflict Detection** - Identifies contradictory information

## When to Use

**Perfect for**:
- Technical research requiring multiple perspectives
- API documentation and best practices
- Current events and recent developments
- Controversial topics needing multiple viewpoints
- Academic research requiring comprehensive sources
- Troubleshooting complex technical issues

**Alternative commands**:
- Regular search for single-source needs
- Specific engine tools for targeted searches
- `/research` for academic-focused research

## Search Quality Features

**Information Validation**:
- Cross-reference facts across all three sources
- Highlight consensus vs. conflicting information
- Note recency of information from each source
- Provide confidence levels based on source agreement

**User Experience**:
- Clear section headers for each search engine
- Unified synthesis section at the end
- Source links for further reading
- Time-stamped results when available

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant past search patterns, research methodologies, and information sources to enhance search strategy and result quality. See CLAUDE.md Memory Enhancement Protocol for details.