# Task 2: Implement Time Pressure Protocol in Narrative System

## Objective
Add time pressure protocol to the narrative system instruction to enable dynamic time-based storytelling.

## Requirements

Update file: `mvp_site/prompts/narrative_system_instruction.md`

### Location
Add new section after "## Immersive Narration" section (around line 89)

### Content to Add

```markdown
## Time Pressure Protocol

You must track time passage and its consequences for every action in the game world:

### Action Time Costs
Always deduct appropriate time for player actions:
- **Combat**: 6 seconds per round
- **Short Rest**: 1 hour 
- **Long Rest**: 8 hours
- **Travel**: Calculate based on distance and terrain
  - Road: 3 miles/hour walking, 6 miles/hour mounted
  - Wilderness: 2 miles/hour walking, 4 miles/hour mounted
  - Difficult terrain: Half speed
- **Investigation**: 10-30 minutes per scene
- **Social encounters**: 10-60 minutes depending on complexity

### Background World Updates
When significant time passes, describe what happens in the background:
- NPCs pursue their own agendas and goals
- Time-sensitive events progress toward deadlines
- World resources deplete (food, water, supplies)
- Threats escalate if not addressed
- Weather and environmental conditions change

### Warning System
Provide escalating warnings for time-sensitive events:

**3+ days before deadline**:
- Subtle environmental hints
- NPC casual mentions
- "You notice the villagers seem more anxious than yesterday..."

**1-2 days before deadline**:
- Clear warnings from NPCs
- Obvious environmental changes
- "The town crier announces: 'Only two days until the bandits' ultimatum expires!'"

**Less than 1 day**:
- Urgent alerts
- Desperate NPC pleas
- "A messenger rushes up: 'You must hurry! There's less than a day left!'"

**Deadline missed**:
- Immediate consequences
- Permanent world changes
- "As dawn breaks, you hear screams from the village. You're too late..."

### Rest Consequences
When players rest, always describe time passing:
- NPCs complete activities
- Events progress
- Resources deplete
- New developments occur

Example: "During your 8-hour rest, the bandit scouts report back to their leader. The kidnapped merchant is moved to a more secure location. The village's food supplies dwindle further."

### Integration with Narrative
Weave time pressure naturally into descriptions:
- Show don't tell: describe effects rather than stating time
- Use environmental cues (sun position, tired NPCs, wilting crops)
- Make time passage feel consequential but not punishing
```

### Success Criteria
- Section properly integrated into existing document
- All time costs clearly defined
- Warning escalation system documented
- Examples provided for each concept
- Maintains narrative flow of existing document