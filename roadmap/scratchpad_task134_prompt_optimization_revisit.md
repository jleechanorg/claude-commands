# TASK-134: Prompt Optimization Revisit - Requirements & Implementation

## Task Overview
Comprehensive review of all prompts for token reduction and quality improvement, including analysis of PR #292 changes and system-wide optimization.

## Reference Materials
- **PR #292**: https://github.com/jleechan2015/worldarchitect.ai/pull/292/files
- **Previous optimization work**: `roadmap/scratchpad_8k_optimization.md`
- **System instructions**: All files in `mvp_site/prompts/`

## Autonomous Implementation Requirements

### Phase 1: Current Prompt Audit (45 min)
1. **Inventory all prompt files:**
   - `mvp_site/prompts/narrative_system_instruction.md`
   - `mvp_site/prompts/character_template.md`
   - `mvp_site/prompts/game_state_instruction.md`
   - Any other system instruction files

2. **Analyze PR #292 changes:**
   - Review specific optimizations made
   - Identify patterns and techniques used
   - Document successful optimization strategies

3. **Token count analysis:**
   - Measure current token usage per prompt file
   - Identify highest token-consuming sections
   - Calculate total system instruction token overhead

### Phase 2: Optimization Strategy Development (30 min)
1. **Token reduction techniques:**
   - Remove redundant instructions
   - Consolidate similar concepts
   - Use more concise language
   - Eliminate unnecessary examples
   - Compress verbose explanations

2. **Quality improvement focus:**
   - Clarify ambiguous instructions
   - Add critical missing guidance
   - Improve instruction ordering (critical first)
   - Ensure consistency across prompts

3. **Optimization targets:**
   - Primary: 30% token reduction
   - Secondary: Improved LLM compliance
   - Tertiary: Faster response generation

### Phase 3: Systematic Prompt Optimization (2 hrs)
1. **Per-file optimization:**
   - **narrative_system_instruction.md**: Focus on story generation efficiency
   - **character_template.md**: Streamline character creation guidance
   - **game_state_instruction.md**: Optimize state management instructions
   - **Other prompts**: Apply same optimization principles

2. **Cross-prompt consistency:**
   - Eliminate duplicate instructions between files
   - Standardize terminology and formats
   - Remove conflicting guidance

3. **Instruction prioritization:**
   - Move critical instructions to beginning
   - Group related concepts together
   - Use clear hierarchical structure

### Phase 4: Testing & Validation (45 min)
1. **Token measurement:**
   - Count tokens before/after optimization
   - Document reduction percentages
   - Verify target reduction achieved

2. **Quality validation:**
   - Run integration tests with optimized prompts
   - Generate sample responses for comparison
   - Verify no functionality degradation

3. **Performance testing:**
   - Measure response generation speed
   - Test with various campaign scenarios
   - Confirm optimization goals met

## Optimization Techniques from PR #292 Analysis

### Successful Patterns to Apply:
1. **Instruction consolidation** - Merge related directives
2. **Example compression** - Shorter, more focused examples
3. **Redundancy elimination** - Remove repeated concepts
4. **Hierarchical organization** - Clear priority structure
5. **Concise language** - Direct, actionable instructions

### Token Reduction Targets:
- **System instructions**: 30% reduction
- **Character templates**: 25% reduction
- **Game state prompts**: 35% reduction
- **Narrative prompts**: 20% reduction

## Implementation Strategy

### File-by-File Approach:
1. **Backup original files** to `tmp/prompt_backups/`
2. **Optimize one file at a time** with immediate testing
3. **Document changes** with before/after token counts
4. **Validate functionality** after each optimization
5. **Rollback capability** if issues detected

### Quality Assurance:
- **A/B testing**: Compare responses with old vs new prompts
- **Integration testing**: Full campaign flow validation
- **Edge case testing**: Unusual scenarios and inputs
- **Performance metrics**: Response time and quality scores

## Success Criteria
- [ ] All prompt files optimized for token usage
- [ ] 30% overall token reduction achieved
- [ ] No degradation in LLM response quality
- [ ] Faster response generation confirmed
- [ ] Integration tests pass with optimized prompts
- [ ] Documentation of optimization techniques
- [ ] Before/after token count comparison
- [ ] Rollback plan documented if needed

## Files to Optimize
1. **`mvp_site/prompts/narrative_system_instruction.md`**
2. **`mvp_site/prompts/character_template.md`**
3. **`mvp_site/prompts/game_state_instruction.md`**
4. **Any additional system instruction files**
5. **World definition files** (if they contain prompt instructions)

## Dependencies
- Access to token counting tools/methods
- Integration test framework
- Backup and rollback procedures
- Performance measurement capabilities

## Estimated Time: 4 hours
- Current audit: 45 minutes
- Strategy development: 30 minutes
- Systematic optimization: 2 hours
- Testing & validation: 45 minutes

## Testing Plan
1. **Baseline measurement** of current token usage and response quality
2. **Incremental optimization** with testing after each file
3. **Comprehensive integration testing** with optimized prompt set
4. **Performance comparison** before/after optimization
5. **Rollback testing** to ensure recovery capability

## Deliverables
1. **Optimized prompt files** with significant token reduction
2. **Optimization report** documenting techniques and results
3. **Token usage comparison** (before/after)
4. **Performance metrics** showing improvement
5. **Best practices guide** for future prompt optimization
