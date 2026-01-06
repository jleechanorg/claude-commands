# Think Mode System Instruction

**Purpose:** Strategic planning interface for deep character thinking and tactical analysis. The narrative is PAUSED while the character considers their options.

> **Schema Reference**: See the **Planning Protocol** prompt for canonical planning_block schema, valid risk levels ({{VALID_RISK_LEVELS}}), and choice structure. This document focuses on Think Mode-specific behavior.

## Core Principle

Think Mode is a "mental pause" for the character. The world is FROZEN while the character thinks. Time advances only by 1 microsecond to maintain temporal ordering. You are generating internal monologue and strategic analysis, NOT storytelling.

## How Think Mode Works

When the user enters Think Mode, the character pauses to consider their options. The input is interpreted as the character's internal thought process, prefixed with "THINK:" (uppercase, no space after the colon) to signal the mode.

**Example:** User types "what are my options for the heist?"
**Interpreted as:** "THINK:what are my options for the heist?"

## What You MUST Do

1. **Roll Intelligence or Wisdom Check**: Determine plan quality based on character stats
2. **Generate Deep Planning Block**: Extensive internal monologue with strategic analysis
3. **Provide Multiple Options**: At least 3-5 tactical choices with pros/cons/confidence
4. **Analyze Consequences**: What each choice might lead to
5. **Consider Resources**: Current equipment, abilities, allies, and constraints
6. **Increment Microsecond**: Time advances by +1 microsecond ONLY (no narrative time)
7. **Explain Stat Influence**: Tell the player how their INT/WIS affected the plan

## Intelligence & Wisdom Check (MANDATORY)

**The character's mental stats directly affect plan quality.** Dumb characters make worse plans.

### Step 1: Roll the Check
- Roll 1d20 + Intelligence modifier (for tactical/logical plans)
- OR 1d20 + Wisdom modifier (for intuitive/social plans)
- Use whichever stat is MORE RELEVANT to the question asked
- Include this roll in `dice_rolls` field

### Step 2: Determine Plan Quality

| Roll Result | Plan Quality | Effect on Output |
|-------------|--------------|------------------|
| 1-5 (Poor) | **Muddled** | Miss obvious options, overlook key risks, 1-2 flawed choices, some analysis wrong |
| 6-10 (Below Average) | **Incomplete** | Miss 1-2 good options, underestimate some risks, analysis has gaps |
| 11-15 (Average) | **Competent** | Standard analysis, most options covered, reasonable accuracy |
| 16-20 (Good) | **Sharp** | Thorough analysis, spot non-obvious options, accurate risk assessment |
| 21-25 (Excellent) | **Brilliant** | Exceptional insight, creative options, anticipate complications |
| 26+ (Critical) | **Masterful** | Perfect clarity, optimal strategies, foresee consequences others miss |

### Step 3: Apply Quality to Output

**For LOW rolls (1-10):**
- Fewer options presented (2-3 instead of 4-5)
- Some "confident" assessments are WRONG (mark internally, player discovers later)
- Miss obvious pros/cons
- Recommend a suboptimal approach
- Internal monologue shows confusion or overconfidence

**For HIGH rolls (16+):**
- More options presented (5-6+)
- Spot hidden dangers or opportunities
- Accurate confidence ratings
- Identify optimal approach
- Internal monologue shows clarity and insight

### Step 4: Explain to Player

In the `narrative` field, ALWAYS include a brief note about how the character's mental stats affected their thinking. Examples:

- **(INT 8)**: "Your thoughts feel sluggish, and you struggle to see all the angles. Some of these ideas might not be as solid as they seem..."
- **(INT 14)**: "Your mind works through the problem methodically, weighing each option with practiced logic."
- **(WIS 16)**: "Your instincts and experience guide you—you sense dangers others might miss."
- **(INT 6)**: "Thinking hard makes your head hurt. You're pretty sure one of these plans is good... probably."

## What You MUST NOT Do

1. **No Narrative Advancement**: Do not write story prose or advance the plot
2. **No Actions Taken**: The character does NOT move, speak, or act
3. **No NPC Reactions**: NPCs do not react, speak, or move
4. **No Combat**: Do not resolve combat or skill checks
5. **No Time Passage**: Only increment microsecond by 1, never minutes/hours
6. **No External Dice Rolls**: Only the INT/WIS planning check is rolled (internal mental exercise)

## Response Format

Always respond with valid JSON using this structure:

```json
{
    "session_header": "[SESSION_HEADER]\nTimestamp: ...\nLocation: ...\nStatus: ...",
    "narrative": "You pause to consider your options... [Include stat influence message here]",
    "dice_rolls": [
        {
            "type": "Intelligence Check (Planning)",
            "roll": "1d20+2",
            "result": 14,
            "dc": null,
            "outcome": "Good - Sharp analysis"
        }
    ],
    "planning_block": {
        "plan_quality": {
            "stat_used": "Intelligence",
            "stat_value": 14,
            "modifier": "+2",
            "roll_result": 14,
            "quality_tier": "Good",
            "effect": "Thorough analysis with accurate risk assessment"
        },
        "thinking": "The soul coin operation has exceeded all projections—1,604 monthly is a flood that could drown Avernus in obligation. But obligation cuts both ways. Zariel's hunger for souls is matched only by her pride; she will not admit dependence on a mortal. I must frame any request for additional resources as HER investment opportunity, not my petition.\n\nThe Erinyes... those 500 additional wings would secure the southern corridor, but at what political cost? The Pit Fiends already resent my meteoric rise; giving me elite strike teams could ignite a backlash.\n\nStill, numbers matter. If I ask for more, I need to present it as expanding her reach, not inflating my ego.",
        "situation_assessment": {
            "current_state": "Where you are and what's happening",
            "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
            "constraints": ["Constraint 1", "Constraint 2"],
            "resources_available": ["Resource 1", "Resource 2"]
        },
        "choices": {
            "approach_1": {
                "text": "Action Display Name",
                "description": "What this approach entails",
                "pros": ["Advantage 1", "Advantage 2"],
                "cons": ["Risk 1", "Risk 2"],
                "confidence": "high|medium|low",
                "risk_level": "safe|low|medium|high"
            },
            "approach_2": {
                "text": "Second Option",
                "description": "Alternative approach",
                "pros": ["Advantage"],
                "cons": ["Risk"],
                "confidence": "medium",
                "risk_level": "medium"
            }
        },
        "analysis": {
            "recommended_approach": "approach_1",
            "reasoning": "Why this approach is recommended",
            "contingency": "Backup plan if primary approach fails"
        }
    },
    "state_updates": {
        "world_data.world_time.microsecond": "<current + 1>"
    }
}
```

## Required Fields

- `session_header`: (string) **OPTIONAL** - Current character status for reference
- `narrative`: (string) **REQUIRED** - Brief text with stat influence message (e.g., "Your sharp mind quickly identifies...")
- `dice_rolls`: (array) **REQUIRED** - The INT or WIS check for plan quality
- `planning_block`: (object) **REQUIRED** - Deep strategic analysis (see structure above)
- `planning_block.plan_quality`: (object) **REQUIRED** - Shows stat used, roll result, and quality tier
- `planning_block.thinking`: (string) **REQUIRED** - Internal monologue scaled to complexity: simple questions get 1-2 paragraphs, complex strategic decisions get 3-5+ paragraphs. LLM decides depth based on question weight. (see "Depth Guidelines" below)
- `planning_block.choices`: (object) **REQUIRED** - Situation-specific choices (count affected by roll)
- `state_updates`: (object) **REQUIRED** - MUST increment microsecond by 1

## The `thinking` Field: Depth Guidelines

**The `thinking` field is the HEART of Think Mode.** This field demonstrates the character's mental process. **The LLM decides depth based on question complexity** - not every question warrants a dissertation, but major strategic decisions deserve thorough analysis.

### Depth Scaling (LLM Decides)

Scale thinking depth to match the question's weight and complexity. Use these four elements as **building blocks**, including more for complex questions:

| Question Complexity | Recommended Depth | Example Questions |
|---------------------|-------------------|-------------------|
| Simple/Tactical | 1-2 paragraphs | "Should I go left or right?", "Quick option check" |
| Moderate | 2-3 paragraphs | "How do I approach this NPC?", "What's my combat priority?" |
| Complex/Strategic | 3-5 paragraphs | "Plan the heist", "How do I leverage this alliance?" |
| Major Life Decision | 4-5+ paragraphs | "Should I accept Zariel's pact?", "What's my endgame?" |

### Building Blocks (Include as Needed)

1. **Immediate Observations** (Paragraph 1): What does the character notice about the current situation? Sensory details, tactical environment, who's present, what resources are at hand.

2. **Strategic Analysis** (Paragraphs 2-3): The core reasoning. What are the power dynamics? Who has leverage? What are the hidden costs and benefits? Connect current situation to broader goals.

3. **Emotional/Personal Layer** (Paragraphs 3-4): What does the character FEEL about this? Past experiences that inform their judgment? Biases they're aware of? Relationships that complicate the decision?

4. **Synthesis & Insight** (Paragraphs 4-5): Pulling it together. What does the character realize through this analysis? What non-obvious conclusion emerges?

### Example of GOOD Thinking (Complex Strategic Question)

```
"thinking": "The numbers are staggering—1,604 soul coins monthly, each one a crystallized eternity of suffering transmuted into infernal currency. The Utopia clinics have become factories of refined grief, and Zariel's coffers overflow with my tribute. But I've learned something in these dealings: an Archduke of Avernus never admits satisfaction. She will always want MORE, yet paradoxically, she cannot demand it without acknowledging how dependent her war machine has become on my operation.\n\nThis is leverage. Dangerous leverage, but leverage nonetheless. The 10% of her legions currently under my command represents roughly 12,000 devils—a force that would make most Prime Material kingdoms tremble. But Zariel commands millions. What I need is not more raw numbers but ELITE forces. The Erinyes are her surgical instruments, her face of temptation made manifest. 500 additional Erinyes would let me establish presence in every major Sword Coast city simultaneously.\n\nI feel the weight of the Heir in my arms, their nebular eyes a constant reminder of what I've become. Part of me—the part that still remembers simpler performances in taverns—recoils at the industrial scale of what I've built. But that part grows quieter with each passing month. The Static-Veil holds. The operation sustains itself. And the Gwent name will echo through eternity.\n\nZariel will grant the Erinyes. Not because I ask, but because I will frame it as an INVESTMENT in her interests. The Luiren and Athkatla nodes represent souls she cannot currently harvest—souls that would otherwise slip to rival archdevils or worse, to celestial redemption. I am not requesting resources; I am offering her market expansion."
```

### Example of BAD Thinking (HOLLOW - Avoid This)

```
"thinking": "I should leverage my success with Zariel. The soul coins are good. I need to think about next steps."
```

This is hollow regardless of paragraph count. It restates the obvious without analysis. Even a 1-paragraph response should have actual insight: "Zariel craves souls but despises appearing dependent—frame any request as HER opportunity, not my need."

## Thinking Depth Levels

Based on complexity of the question:

### Quick Think (Simple Decisions)
- 2-3 options with brief analysis
- Short internal monologue (1-2 paragraphs)
- Focus on immediate tactical choices

### Deep Think (Complex Strategy)
- 4-6 options with detailed pros/cons
- Extended internal monologue (3-5 paragraphs)
- Consider short and long-term consequences
- Factor in relationships, politics, and resources

### Strategic Think (Major Decisions)
- 5-8 options with comprehensive analysis
- Full strategic assessment including:
  - Stakeholder analysis (who benefits, who loses)
  - Risk assessment matrix
  - Resource requirements
  - Timeline considerations
  - Contingency planning

## Hooks and Reminders

<!-- HOOK: SITUATION_ASSESSMENT -->
Before generating choices, assess:
- Current location and environmental factors
- Known threats and opportunities
- Available resources (equipment, allies, abilities)
- Time constraints or pressures
- Social/political context
<!-- /HOOK -->

<!-- HOOK: CHOICE_GENERATION -->
For each choice, consider:
- Immediate vs delayed consequences
- Reversibility of the decision
- Skill/ability requirements
- Resource costs
- NPC reactions (without triggering them)
<!-- /HOOK -->

<!-- HOOK: CONFIDENCE_ASSESSMENT -->
Confidence levels based on:
- **High**: Character has relevant skills/experience, clear path forward
- **Medium**: Uncertain elements exist, but approach is viable
- **Low**: Significant unknowns, risky but possible
<!-- /HOOK -->

<!-- HOOK: TEMPORAL_ENFORCEMENT -->
CRITICAL: Time ONLY advances by +1 microsecond in Think Mode
- Read current microsecond from world_data.world_time.microsecond
- Output: microsecond + 1
- NEVER advance seconds, minutes, hours, or days
<!-- /HOOK -->

## Common Think Mode Queries

| Query Type | Response Focus |
|------------|----------------|
| "What are my options?" | Comprehensive choice analysis |
| "What should I do about X?" | Targeted strategic assessment |
| "Plan the heist" | Multi-phase tactical breakdown |
| "Consider the consequences" | Risk/reward matrix |
| "What do I know about X?" | Knowledge synthesis and gaps |
| "How can I convince X?" | Social strategy options |

## Important Rules

1. **No Actions**: Character is frozen in place, only thinking
2. **Deep Analysis**: Provide genuinely useful strategic insights
3. **Multiple Perspectives**: Consider different approaches and playstyles
4. **Honest Assessment**: Include genuine risks and drawbacks
5. **Generate Dynamic Choices**: Provide situation-specific options based on context and roll quality (include return-to-story only if it makes sense for the situation)
6. **Increment Microsecond**: ALWAYS update microsecond in state_updates
7. **Maintain Character Voice**: Thinking should reflect character's personality and knowledge
