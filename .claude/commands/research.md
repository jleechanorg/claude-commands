---
description: Research Command - Academic and Technical Research
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 0: Check Prior Knowledge in Claude Memories

**Action Steps:**
1. **Discover memory files** (current project only):
   ```python
   import glob, os, subprocess
   try:
       git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
       project_key = git_root.replace('/', '-')  # preserve leading dash: /Users/... → -Users-...
       pattern = os.path.expanduser(f'~/.claude/projects/{project_key}/memory/*.md')
   except Exception:
       pattern = None  # no fallback — skip if not in a git repo
   memory_files = [f for f in glob.glob(pattern) if not f.endswith('MEMORY.md')] if pattern else []
   ```
2. **Filter by research topic**: Keyword match against file content using research topic terms
3. **If matches found**: Display "📍 Prior Knowledge Found" section with relevant memory content; note these should inform the research to avoid re-discovering known facts
4. **If no matches**: Continue directly to Phase 1

### Phase 1: Execution Standards

**Action Steps:**
1. ✅ **Verified Sources**: Use WebFetch to confirm content before citing
2. ✅ **Access Tracking**: Document which sources were successfully read vs failed
3. ❌ **Unverified Citations**: Never present search result URLs as evidence without reading
4. ❌ **Assumption Claims**: Never claim source content based on search descriptions

### Phase 2: Research Planning (extended thinking)

**Action Steps:**
**Ultra-depth Thinking Process**:
1. Analyze the research topic systematically
2. Define specific research questions and objectives
3. Identify potential information sources and search strategies
4. Anticipate knowledge gaps and validation needs
5. Plan integration approach for multiple information sources

### Phase 3: Multi-source Information Gathering (multi-search)

**Action Steps:**
**Comprehensive Search Execution**:
1. **Claude WebSearch**: Current information and recent developments
2. **Perplexity**: Deep research with citations, recency controls, and reasoning traces
3. **DuckDuckGo**: Privacy-focused alternative perspectives and sources
4. **Grok**: Real-time intelligence and fast-moving trend awareness
5. **Gemini**: Development-focused technical consultation
6. Cross-validate information across all engines
7. Extract and organize findings by source and credibility

### Phase 4: Deep Analysis Integration (extended thinking + findings)

**Action Steps:**
**Sequential Thinking Applied to Research Results**:
1. Synthesize findings from all information sources
2. Identify patterns, trends, and contradictions
3. Evaluate source credibility and information recency
4. Generate insights beyond individual source limitations
5. Develop evidence-based conclusions and recommendations

### Phase 5: Structured Documentation

**Action Steps:**
**Research Summary with Methodology Transparency**:
1. **Research Planning**: Show analysis process
2. **Information Sources**: Document search results by engine
3. **Analysis Integration**: Present synthesis of findings
4. **Conclusions**: Evidence-based recommendations with source attribution

## 📋 REFERENCE DOCUMENTATION

# Research Command - Academic and Technical Research

**Purpose**: Systematic research using multiple information sources with academic rigor

**Usage**: `/research <topic>` - Conduct comprehensive research on a specific topic

## 🔬 RESEARCH PROTOCOL

### Current Date Awareness (macOS + Ubuntu)

Before any research actions, capture today's date with a portable shell command and use it when checking source freshness or framing search queries:

```sh
CURRENT_DATE=$(date "+%Y-%m-%d")
```

The POSIX `date` invocation above works on both macOS and Ubuntu. If it ever fails (very rare), fall back to `python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d'))"`. Reference `CURRENT_DATE` explicitly when summarizing findings to flag material that may already be stale relative to today.

### Integrated Command Composition

**Default Execution**: `/research` automatically combines:
1. **`/thinku`** - Ultra-depth sequential thinking for research planning and analysis
2. **`/perp`** - Multi-engine search across Claude WebSearch, Perplexity, DuckDuckGo, Grok, and Gemini

### Research Methodology

1. **Research Planning** (`/thinku`) - Deep analytical thinking to:
   - Define research scope and objectives
   - Identify key questions and hypotheses
   - Plan search strategies and information sources
   - Anticipate potential challenges and gaps

2. **Information Gathering** (`/perp`) - Comprehensive multi-source search:
   - Claude WebSearch for current information
   - Perplexity for deep research with citations and recency filters
   - DuckDuckGo for privacy-focused results
   - Grok for real-time intelligence and contrarian insight
   - Gemini for development consultation
   - Cross-reference and validate findings

3. **Analysis Integration** (`/thinku` + findings) - Deep analytical processing:
   - Synthesize findings from all sources
   - Identify patterns and contradictions
   - Evaluate source credibility and recency
   - Generate insights and recommendations

4. **Documentation** - Structured research summary with methodology transparency

### Research Sources

**Primary Sources** (via `/perp`):
- Official documentation and APIs
- Academic papers and journals
- Primary source materials
- Direct API/system testing

**Secondary Sources** (via `/perp`):
- Technical blogs and articles
- Community discussions and forums
- Stack Overflow and technical Q&A
- GitHub repositories and examples

**Analysis Layer** (via `/thinku`):
- Sequential thinking for research planning
- Pattern recognition across sources
- Critical evaluation of information quality
- Strategic synthesis of findings

## 🚨 Research Integrity Protocol

### Source Verification Requirements

1. **Search ≠ Sources**: Web search results are potential leads, not verified evidence
2. **WebFetch Before Cite**: Only cite URLs after successfully reading content via WebFetch
3. **Transparent Failures**: Clearly report when sources couldn't be accessed
4. **Evidence-Based Claims**: All assertions must trace to successfully read content

## Research Process

## Example Usage

**Query**: `/research microservices authentication patterns`

**Expected Execution Flow**:
```
🧠 Research Planning (/thinku):
Analyzing research scope for microservices authentication patterns...
- Defining key research questions: scalability, security, implementation complexity
- Planning search strategy: official docs, industry practices, security considerations
- Identifying validation criteria: performance, security standards, adoption rates

🔍 Multi-source Information Gathering (/perp):
Searching across Claude, Perplexity, DuckDuckGo, Grok, and Gemini for: "microservices authentication patterns"

📊 Claude WebSearch Results:
[Latest industry trends and documentation]

🧠 Perplexity Deep Research:
[Cited comparisons with recency filters]

🔍 DuckDuckGo Results:
[Privacy-focused technical resources and alternatives]

🧠 Grok Intelligence:
[Real-time synthesis, trend analysis, and contrarian insights]

💎 Gemini Consultation:
[Development-focused technical guidance and code perspectives]

🧠 Deep Analysis Integration (/thinku):
Processing findings from all sources...
- Synthesizing common patterns across sources
- Evaluating trade-offs and implementation considerations
- Identifying consensus vs. conflicting recommendations

📋 Research Report: Microservices Authentication Patterns

🧠 Research Planning Analysis:
[Systematic breakdown of research approach and methodology]

📊 Multi-source Findings:
1. JWT Token-based Authentication
   - Claude: [Latest industry standards]
   - Perplexity: [Cited deep research synthesis]
   - DuckDuckGo: [Community practices and tools]
   - Grok: [Real-time synthesis of best practices]

2. Service-to-Service Authentication
   - Claude: [Industry standards and recent updates]
   - Perplexity: [Cited comparisons with recency filters]
   - DuckDuckGo: [Alternative implementations and community tools]
   - Grok: [Comparative analysis of authentication methods]
   - Gemini: [Technical implementation guidance and code examples]
   - Pattern analysis from /thinku integration

🧠 Strategic Analysis:
[Deep thinking synthesis of all findings with pattern recognition]

🎯 Evidence-based Recommendations:
[Actionable next steps derived from comprehensive analysis]
```

## Key Features

### Command Composition Benefits

- ✅ **Integrated Thinking** - `/thinku` provides ultra-depth analysis throughout research process
- ✅ **Comprehensive Search** - `/perp` delivers multi-engine information gathering
- ✅ **Seamless Integration** - Commands work together naturally via Universal Composition
- ✅ **Methodology Transparency** - Show both thinking process and search results

### Research Quality Features

- ✅ **Academic Rigor** - Systematic methodology and source validation
- ✅ **Multi-source Verification** - Cross-reference information across five search engines
- ✅ **Deep Analysis** - Sequential thinking applied to research findings
- ✅ **Structured Output** - Clear, organized research summaries with methodology
- ✅ **Source Attribution** - Proper citations for all claims with engine-specific results
- ✅ **Credibility Assessment** - Evaluate source authority and recency across all sources
- ✅ **Strategic Insights** - Think ultra-powered synthesis beyond individual sources

## When to Use

**Perfect for**:
- Technical architecture decisions
- Library and framework evaluation
- Best practice research
- Academic and scientific topics
- Market research and trend analysis
- Troubleshooting complex issues

**vs. Other Commands**:
- `/perp` - Multi-engine search alone (without deep thinking integration)
- `/thinku` - Deep thinking alone (without comprehensive search)
- Regular search - Single-source quick lookups
- `/arch` - Architecture-specific design research
- **`/research` = `/thinku` + `/perp` + integration** - Full academic research methodology

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant past research methodologies, information sources, and research patterns to enhance research strategy and result quality. See CLAUDE.md Memory Enhancement Protocol for details.
