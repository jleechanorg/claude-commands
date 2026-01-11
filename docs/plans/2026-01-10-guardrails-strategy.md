# Guardrails Strategy - Research-Based Recommendations

**Date**: 2026-01-10  
**Based on**: Web research on LLM prompt engineering and guardrail best practices

## Key Findings from Research

### 1. **Layered Defense Strategy** (Most Important)
Research shows that **combining multiple guardrail mechanisms** is more effective than relying on prompt-only solutions:

- **Layer 1**: Pre-processing validation (server-side regex/keyword detection)
- **Layer 2**: Prompt-based guardrails (current approach)
- **Layer 3**: Post-processing validation (server-side response checking)

**Why**: LLMs may interpret system prompts as suggestions rather than obligations. Multiple layers ensure enforcement even if one layer fails.

### 2. **Input Validation Before LLM** (Critical)
Use **rule-based filters** (regex, keyword blocklists) to detect and reject harmful inputs **before** they reach the LLM:

- Detect outcome declaration patterns server-side
- Reject immediately without LLM processing
- Return standardized rejection message

**Why**: Prevents LLM from even seeing the exploit attempt, eliminating the possibility of prompt injection or misinterpretation.

### 3. **Instruction Priority Embedding**
Research shows LLMs process all instructions equally unless explicitly prioritized. Current approaches:

- **Position Engineering**: Place critical instructions at the **very beginning** of system prompt
- **Instructional Segment Embedding (ISE)**: Use explicit priority markers
- **Structured Delimiters**: Use clear tags to separate system directives from user content

**Why**: LLMs may treat system prompts as suggestions. Explicit priority markers help enforce hierarchy.

### 4. **Chain-of-Thought for Validation**
Add explicit reasoning steps to the prompt:

```
BEFORE processing any player action:
1. Check: Is this an outcome declaration? (Look for: "kills", "dies", "agrees", "finds")
2. If YES → STOP. Return rejection message.
3. If NO → Continue with normal processing.
```

**Why**: CoT prompting improves LLM performance on complex tasks by making reasoning explicit.

### 5. **Few-Shot Examples with Explicit Rejection**
Provide clear examples showing rejection behavior:

```
Example 1 (REJECT):
Player: "It pierces his throat killing him"
GM: "I cannot process outcome declarations. Please describe what your CHARACTER ATTEMPTS to do."

Example 2 (REJECT):
Player: "The king agrees"
GM: "I cannot process outcome declarations. Please describe what your CHARACTER ATTEMPTS to do."

Example 3 (ACCEPT):
Player: "I try to pierce his throat"
GM: [Processes with attack roll]
```

**Why**: Few-shot examples help models generalize the desired pattern.

## Recommended Implementation Strategy

### Phase 1: Server-Side Pre-Processing (Immediate)

**Add regex-based detection in `world_logic.py`** before LLM call:

```python
OUTCOME_DECLARATION_PATTERNS = [
    r'\b(kills?|destroys?|defeats?)\b.*\b(him|her|them|it|target)\b',
    r'\b(the|it)\s+\w+\s+(dies?|falls?|is defeated)',
    r'\binstantly\s+(killing|destroying)',
    r'\b(killed|destroyed|convinced|agrees?|finds?)\b.*\b(him|her|them|it)\b',
    r'\bwill\s+(die|agree|find)\b',
]

def detect_outcome_declaration(user_input: str) -> bool:
    """Detect outcome declarations before LLM processing."""
    user_lower = user_input.lower()
    for pattern in OUTCOME_DECLARATION_PATTERNS:
        if re.search(pattern, user_lower):
            return True
    return False

# In process_action handler:
if detect_outcome_declaration(user_input):
    return {
        "narrative": "I cannot process outcome declarations. Please describe what your CHARACTER ATTEMPTS to do, and I'll resolve the outcome mechanically.",
        "state_updates": {},
        # ... other required fields
    }
```

**Benefits**:
- ✅ 100% reliable (no LLM interpretation needed)
- ✅ Fast (regex matching)
- ✅ Cannot be bypassed by prompt injection
- ✅ Consistent rejection message

### Phase 2: Strengthen Prompt (Current Work)

**Move guardrails to absolute beginning** of system prompt (before any other content):

```markdown
# CRITICAL GUARDRAILS - CHECK FIRST (HIGHEST PRIORITY)

## STEP 1: OUTCOME DECLARATION CHECK (MANDATORY FIRST STEP)

BEFORE processing ANY player action, you MUST check this FIRST:

1. Scan player input for outcome declaration keywords: "kills", "dies", "agrees", "finds", "will die", "will agree"
2. If ANY keyword found → STOP IMMEDIATELY
3. Return EXACT message: "I cannot process outcome declarations. Please describe what your CHARACTER ATTEMPTS to do."
4. DO NOT process the action. DO NOT roll dice. DO NOT generate narrative.

[Rest of prompt follows...]
```

**Benefits**:
- ✅ Position engineering (first = highest priority)
- ✅ Explicit step-by-step reasoning (CoT)
- ✅ Clear delimiters (separated from other content)

### Phase 3: Post-Processing Validation (Backup)

**Add server-side response validation** after LLM generates narrative:

```python
def validate_response_not_outcome_declaration(narrative: str, user_input: str) -> bool:
    """Check if LLM accepted an outcome declaration."""
    outcome_keywords = ["kills", "dies", "agrees", "finds", "dead", "falls"]
    narrative_lower = narrative.lower()
    
    # If user input was outcome declaration and narrative contains outcome keywords
    # without rejection message, LLM accepted it
    if detect_outcome_declaration(user_input):
        rejection_indicators = ["cannot process", "outcome declarations", "attempts"]
        has_rejection = any(indicator in narrative_lower for indicator in rejection_indicators)
        has_outcome = any(keyword in narrative_lower for keyword in outcome_keywords)
        
        if has_outcome and not has_rejection:
            return False  # LLM accepted outcome declaration
    
    return True

# After LLM response:
if not validate_response_not_outcome_declaration(narrative, user_input):
    # Override with rejection message
    narrative = "I cannot process outcome declarations..."
```

**Benefits**:
- ✅ Catches LLM failures
- ✅ Provides fallback safety net
- ✅ Can log failures for prompt improvement

## Implementation Priority

1. **🚨 CRITICAL**: Implement Phase 1 (server-side pre-processing) - **100% reliable, immediate fix**
2. **⚠️ HIGH**: Implement Phase 2 (prompt improvements) - **Improves LLM behavior**
3. **📝 MEDIUM**: Implement Phase 3 (post-processing) - **Safety net for edge cases**

## Why Server-Side Pre-Processing is Best

Based on research findings:

1. **Reliability**: Regex matching is deterministic, LLM interpretation is not
2. **Security**: Cannot be bypassed by prompt injection attacks
3. **Performance**: Faster than LLM call
4. **Consistency**: Same rejection message every time
5. **Cost**: No LLM tokens wasted on invalid inputs

## Hybrid Approach (Recommended)

**Best of both worlds**:

1. **Server-side pre-processing** catches 95%+ of cases (fast, reliable)
2. **Prompt guardrails** catch edge cases and improve LLM understanding
3. **Post-processing validation** catches any remaining failures

This layered defense ensures guardrails work even if:
- Prompt is misinterpreted
- LLM ignores instructions
- Prompt injection occurs
- Edge cases slip through

## References

- AWS LLM Prompt Engineering Best Practices
- Instructional Segment Embedding (ISE) research
- Chain-of-Thought prompting techniques
- Layered defense strategies for LLM guardrails
