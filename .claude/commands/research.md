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

### Phase 1: Execution Standards

**Action Steps:**
1. ✅ **Verified Sources**: Use WebFetch to confirm content before citing
2. ✅ **Access Tracking**: Document which sources were successfully read vs failed
3. ❌ **Unverified Citations**: Never present search result URLs as evidence without reading
4. ❌ **Assumption Claims**: Never claim source content based on search descriptions

### Phase 1: Research Planning (`/thinku`)

**Action Steps:**
**Ultra-depth Thinking Process**:
1. Analyze the research topic systematically
2. Define specific research questions and objectives
3. Identify potential information sources and search strategies
4. Anticipate knowledge gaps and validation needs
5. Plan integration approach for multiple information sources

### Phase 2: Multi-source Information Gathering (`/perp`)

**Action Steps:**
**Comprehensive Search Execution**:
1. **Claude WebSearch**: Current information and recent developments
2. **DuckDuckGo**: Privacy-focused alternative perspectives and sources
3. **Perplexity**: AI-powered synthesis and academic analysis
4. **Gemini**: Development-focused technical consultation
5. Cross-validate information across all four engines
6. Extract and organize findings by source and credibility

### Phase 3: Deep Analysis Integration (`/thinku` + findings)

**Action Steps:**
**Sequential Thinking Applied to Research Results**:
1. Synthesize findings from all information sources
2. Identify patterns, trends, and contradictions
3. Evaluate source credibility and information recency
4. Generate insights beyond individual source limitations
5. Develop evidence-based conclusions and recommendations

### Phase 4: Structured Documentation

**Action Steps:**
**Research Summary with Methodology Transparency**:
1. **Research Planning**: Show `/thinku` analysis process
2. **Information Sources**: Document `/perp` search results by engine
3. **Analysis Integration**: Present `/thinku` synthesis of findings
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
2. **`/perp`** - Multi-engine search across Claude, DuckDuckGo, Perplexity, and Gemini

### Research Methodology

1. **Research Planning** (`/thinku`) - Deep analytical thinking to:
   - Define research scope and objectives
   - Identify key questions and hypotheses
   - Plan search strategies and information sources
   - Anticipate potential challenges and gaps

2. **Information Gathering** (`/perp`) - Comprehensive multi-source search:
   - Claude WebSearch for current information
   - DuckDuckGo for privacy-focused results
   - Perplexity for AI-powered synthesis
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
Searching across Claude, DuckDuckGo, Perplexity, and Gemini for: "microservices authentication patterns"

📊 Claude WebSearch Results:
[Latest industry trends and documentation]

🔍 DuckDuckGo Results:
[Privacy-focused technical resources and alternatives]

🧠 Perplexity Analysis:
[AI-synthesized current best practices and comparisons]

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
   - DuckDuckGo: [Community practices and tools]
   - Perplexity: [AI synthesis of best practices]

2. Service-to-Service Authentication
   - Claude: [Industry standards and recent updates]
   - DuckDuckGo: [Alternative implementations and community tools]
   - Perplexity: [Comparative analysis of authentication methods]
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
- ✅ **Multi-source Verification** - Cross-reference information across four search engines
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
