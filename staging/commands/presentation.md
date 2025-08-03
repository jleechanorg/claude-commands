# /presentation

**Purpose**: Create professional presentations compatible with Google Slides through an interactive outline development process with multi-phase quality assurance.

**Aliases**: `/pres`, `/slide`

## Usage

```
/presentation [topic]
/pres "AI Safety in 2025"
/presentation /think "Climate Change Solutions"
```

## Protocol

This command follows a structured multi-phase approach:

### Phase 1: Initial Outline Creation
1. Create a presentation scratchpad: `roadmap/presentation_[timestamp].md`
2. Generate initial outline based on the topic
3. Structure with title, sections, and key points

### Phase 2: Interactive Q&A Refinement
1. Present the initial outline to the user
2. Ask clarifying questions about:
   - Target audience
   - Presentation duration
   - Key messages to emphasize
   - Visual style preferences
   - Specific content requirements
3. Iterate on the outline based on feedback
4. Continue until user types "done", "proceed", or "looks good"

### Phase 3: Quality Review Chain
Execute thinking commands in sequence:
1. **First**: Run `/thinku` on the refined outline
   - Analyze structure, flow, and completeness
   - Generate hypothesis about effectiveness
   - Verify logical consistency
2. **Then**: Run `/reviewdeep` for thorough analysis
   - Multi-perspective evaluation
   - Check for gaps or weaknesses
   - Suggest improvements
3. **Finally**: Critical review
   - Challenge assumptions
   - Identify potential issues
   - Ensure clarity and impact

### Phase 4: Presentation Generation
1. Use python-pptx to create the PPTX file
2. Convert outline to slides with:
   - Professional formatting
   - Consistent styling
   - Appropriate layouts
   - Visual hierarchy
3. Save as `presentation_[topic]_[timestamp].pptx`

### Phase 5: Quality Assurance (/secondopinion)
Comprehensive quality check:
1. **Devil's Advocate Review**
   - Challenge presentation logic
   - Question assumptions
   - Identify weaknesses
2. **Gemini MCP Feedback**
   - Get AI perspective on content quality
   - Check for clarity and coherence
   - Suggest improvements
3. **Web Search Validation**
   - Verify key facts and figures
   - Check current information
   - Validate claims
4. **Perplexity Quality Check**
   - Run `/perp` on key concepts
   - Ensure accuracy and relevance
   - Get additional insights

## Example Workflow

```python
# Phase 1: Create initial outline
outline = create_initial_outline(topic)
save_to_scratchpad(outline)

# Phase 2: Interactive refinement
while not user_satisfied:
    present_outline(outline)
    ask_clarifying_questions()
    outline = refine_based_on_feedback(outline)

# Phase 3: Quality review
/thinku analyze presentation outline for completeness and flow
/reviewdeep evaluate presentation from multiple perspectives
# Critical review of assumptions and logic

# Phase 4: Generate presentation
presentation = generate_pptx_from_outline(outline)

# Phase 5: Final quality assurance
/secondopinion:
  - Devil's advocate analysis
  - Gemini MCP: "Review this presentation for clarity and impact"
  - Web search key concepts for accuracy
  - /perp validate core claims
```

## Key Characteristics

- **Interactive**: Develops outline through Q&A with user
- **Thorough**: Multi-phase quality review process
- **Compatible**: Generates PPTX files that work perfectly with Google Slides
- **Smart**: Uses AI thinking commands for quality assurance
- **Validated**: Cross-checks facts and claims

## Implementation Details

All logic is driven by this markdown file. The command:
1. Creates structured scratchpads for tracking
2. Uses inline Python code for generation (no external scripts)
3. Chains multiple commands for quality assurance
4. Leverages existing python-pptx installation
5. Follows explicit command sequences

## When to Use

- Creating professional presentations
- Need Google Slides compatibility
- Want thorough outline development
- Require fact-checked content
- Need multiple quality reviews

## Memory Enhancement

This command benefits from memory search to:
- Find previous presentation patterns
- Recall successful outline structures
- Apply learned best practices
- Avoid past mistakes

The command automatically searches memory for relevant presentation creation experiences.

## Command Composition

Can be combined with other commands:
- `/presentation /plan` - Add planning phase
- `/presentation /think` - Extra deep analysis
- `/presentation /research` - Research-heavy topics
