# 8K Word Optimization Plan - Phase 2

## Current Status
- **Current Total**: 16,040 words (base prompts)
- **Effective Story Mode Total**: 17,009 words (includes character_template.md: 969 words)
- **Target**: 8,000 words
- **Reduction Needed**: 9,009 words (53% reduction)
- **Previous Achievement**: 35% reduction in Phase 1

## File Breakdown Analysis

Current word counts:
- narrative_system_instruction.md: 5,364 words
- mechanics_system_instruction.md: 4,022 words
- game_state_instruction.md: 4,621 words
- character_template.md: 969 words ⚠️ **Auto-loaded with narrative**
- master_directive.md: 890 words
- dnd_srd_instruction.md: 174 words

**Story Mode Effective Total**: 17,009 words (16,040 + 969 character template)

## Target Distribution (8,000 words total)

**Priority 1 - Core Always-Loaded (3,500 words):**
- master_directive.md: 600 words (reduce 290)
- game_state_instruction.md: 2,500 words (reduce 2,121)
- dnd_srd_instruction.md: 174 words (keep as-is)
- debug instructions: ~226 words (estimated)

**Priority 2 - Context-Dependent Loading (4,500 words):**
- narrative_system_instruction.md: 2,500 words (reduce 2,864)
- mechanics_system_instruction.md: 1,500 words (reduce 2,522)
- character_essentials: 500 words (reduce 469 from character_template.md)

**Priority 3 - On-Demand Only (not counted in 8K limit):**
- character_template.md: Move to examples/ or conditional loading only
- Detailed examples: Extract to separate reference files

**CRITICAL**: Character template auto-loading with narrative adds 969 words to story mode

## Optimization Strategy

### Phase 2A: Smart Loading System (Week 1)
**Goal**: Implement conditional loading to reduce effective prompt size

**1. Context-Aware Prompt Assembly**
Update `gemini_service.py` to load prompts based on current context:
```python
def build_context_aware_instructions(self, context):
    # Always load core (3.5K words)
    core_instructions = self.build_core_instructions()

    if context.is_combat:
        # Combat-focused subset (1.5K words)
        return core_instructions + self.build_combat_essentials()
    elif context.is_character_creation:
        # Character creation subset (2K words) - includes full character_template
        return core_instructions + self.build_character_creation_mode()
    else:
        # Standard story mode (4.5K words) - NO auto character_template loading
        return core_instructions + self.build_story_essentials()
```

**2. Fix Character Template Auto-Loading**
CRITICAL: Currently `character_template.md` (969 words) auto-loads with narrative instructions:
- Remove auto-loading from `add_character_instructions()` method
- Load only during character creation context
- Extract essential character rules to narrative instructions (500 words max)

**2. Combat Mode Optimization**
Create ultra-condensed combat instructions (1,500 words max):
- Essential combat mechanics only
- No narrative examples or verbose explanations
- Focus on dice rolls, damage, status effects

**3. Character Creation Mode**
Specialized instruction set for character generation:
- Load character_template.md only when needed
- Condensed creation rules
- Essential schemas only

### Phase 2B: Aggressive Content Reduction (Week 2-3)

**1. Game State Instructions (4,621 → 2,500 words)**
- **Extract Examples**: Move detailed JSON examples to separate reference files
  - `examples/state_examples.md`
  - `examples/entity_schemas.md`
- **Condense Schemas**: Keep essential structure only
- **Merge Redundancy**: Combine overlapping sections
- **Focus on Rules**: Remove verbose explanations, keep core requirements

**2. Narrative Instructions (5,364 → 3,000 words)**
- **Already optimized but can go further**:
  - Remove remaining verbose examples
  - Condense character profile requirements further
  - Streamline world generation protocol
  - Create ultra-condensed planning block reminders

**3. Mechanics Instructions (4,022 → 1,500 words)**
- **Extract Heavy Content**:
  - Detailed tier examples → `examples/tier_progression.md`
  - Combat examples → `examples/combat_mechanics.md`
  - Dice roll examples → `examples/roll_formats.md`
- **Core Essentials Only**:
  - Basic roll mechanics (300 words)
  - Tier system overview (200 words)
  - Integration rules (500 words)
  - State update requirements (500 words)

**4. Master Directive (890 → 600 words)**
- Remove redundant explanations already covered elsewhere
- Condense loading hierarchy to bullet points
- Focus on authority structure only

### Phase 2C: Smart File Architecture (Week 4)

**1. Create Reference System**
```
prompts/
├── core/                    # Always loaded (3.5K)
│   ├── master_directive.md
│   ├── game_state_essentials.md
│   └── dnd_srd_instruction.md
├── modes/                   # Context-dependent (4.5K budget)
│   ├── story_mode.md
│   ├── combat_mode.md
│   └── creation_mode.md
├── examples/               # On-demand reference
│   ├── state_examples.md
│   ├── combat_examples.md
│   └── narrative_samples.md
└── archived/               # Not loaded
    └── personalities/
```

**2. Update Loading Logic**
Modify `PromptBuilder` class:
- Detect current context (story/combat/creation)
- Load appropriate mode files only
- Implement fallback for unknown contexts

**3. Progressive Enhancement**
- Load basic rules first
- Add complexity only when needed
- Cache compiled instruction sets

### Phase 2D: Content Extraction Strategy

**High-Impact Extractions (targeting 4,000+ word reduction):**

**From game_state_instruction.md (2,121 words to extract):**
- Detailed entity schema examples (est. 800 words)
- Verbose JSON format explanations (est. 600 words)
- Edge case handling documentation (est. 400 words)
- Redundant state management examples (est. 321 words)

**From mechanics_system_instruction.md (2,522 words to extract):**
- Detailed tier progression examples (est. 1,000 words)
- Combat scenario walkthroughs (est. 800 words)
- Verbose dice roll explanations (est. 400 words)
- Redundant rule clarifications (est. 322 words)

**From narrative_system_instruction.md (2,364 words to extract):**
- World generation detailed examples (est. 800 words)
- Character profile verbose requirements (est. 600 words)
- NPC generation detailed protocols (est. 500 words)
- Redundant mode explanations (est. 464 words)

## Implementation Phases

### Phase 2A: Smart Loading (Week 1)
- [ ] **FIX CRITICAL**: Remove character_template.md auto-loading from narrative mode
- [ ] Implement context detection in gemini_service.py
- [ ] Create combat_mode.md (1,500 words max)
- [ ] Create creation_mode.md (2,000 words max) - includes character_template when needed
- [ ] Test context-aware loading
- [ ] Measure effective prompt sizes by context

### Phase 2B: Content Extraction (Week 2-3)
- [ ] Extract examples from game_state_instruction.md
- [ ] Extract examples from mechanics_system_instruction.md
- [ ] Further condense narrative_system_instruction.md
- [ ] Reduce master_directive.md to essentials
- [ ] Create examples/ directory structure

### Phase 2C: Architecture Update (Week 4)
- [ ] Reorganize prompt file structure
- [ ] Update all loading references
- [ ] Implement progressive enhancement
- [ ] Test all context modes

### Phase 2D: Validation (Week 5)
- [ ] Verify 8K word target met
- [ ] Test all game functionality
- [ ] Measure LLM compliance improvement
- [ ] Performance benchmarking

## Success Metrics

**Primary Goals:**
- [ ] Total prompt size ≤ 8,000 words in any context
- [ ] Core functionality preserved
- [ ] LLM compliance improved (target: 95%+ planning blocks)
- [ ] No performance regression

**Context-Specific Targets:**
- Story Mode: ≤ 8,000 words (core + story essentials)
- Combat Mode: ≤ 5,000 words (core + combat essentials)
- Creation Mode: ≤ 5,500 words (core + creation essentials)

## Risk Mitigation

**1. Functionality Preservation:**
- Comprehensive testing after each extraction
- A/B testing with sample generations
- Rollback plan for any breaking changes

**2. Quality Assurance:**
- Maintain essential examples in extracted files
- Keep cross-references between core and examples
- User feedback collection at each phase

**3. Integration Safety:**
- Separate branch for Phase 2 work
- Incremental PRs for each sub-phase
- Staging environment testing

## Phase 2 Branch Strategy

**Branch**: `optimize_8k_words`
**Merge Target**: `main` (after narr_fixes is merged)
**PR Strategy**: One PR per week/phase for manageable review

This plan achieves the 8K target through smart loading and aggressive content extraction while preserving all essential functionality through on-demand reference files.
