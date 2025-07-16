# Handoff: Memory MCP Header Compliance Implementation

## Handoff Context
**From**: Architecture & Planning Phase  
**To**: Implementation Phase (`memory_impl` context)
**Branch**: feature/cognitive-enhancement-system (will need new branch for clean implementation)
**Goal**: Implement header compliance MVP using Memory MCP

## What's Been Completed ✅

### 1. Architecture Analysis
- **Issue Identified**: Original PR #591 was over-engineered with fundamental flaws
- **LLM Feedback**: Confidence math problems, testing theater, documentation obsession
- **Decision**: Abandon complex system, focus on MVP proving behavioral automation concept

### 2. MVP Definition  
- **Core Problem**: User always types `/header` command (80% violation rate)
- **Target Solution**: Auto-detect missing headers, auto-insert, learn patterns via Memory MCP
- **Success Metric**: 90% reduction in user `/header` commands within 3 weeks

### 3. Planning Documents Created
- `roadmap/scratchpad_memory_mvp.md` - Detailed MVP implementation plan
- `roadmap/detailed_roadmap_behavioral_automation.md` - 6-phase roadmap for complete CLAUDE.md replacement
- `PR_MEMORY_MVP_DESCRIPTION.md` - PR description ready for creation

## Implementation Tasks for memory_impl Context

### Priority 1: Core Header Compliance Engine

**File to Create**: `.claude/scripts/header_compliance_engine.py`
```python
# Core architecture already designed:
class HeaderComplianceEngine:
    def __init__(self):
        self.memory_mcp = MemoryMCPClient()
        self.git_header_script = "./claude_command_scripts/git-header.sh"
    
    def process_response(self, response_text, context):
        # 1. Check compliance  
        violations = self.check_header_compliance(response_text)
        
        # 2. Auto-correct if needed
        if violations:
            corrected = self.auto_correct_header(response_text) 
            self.log_violation_to_memory(violations, context)
            return corrected
            
        return response_text
```

**Key Implementation Details**:
- Header regex: `r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'`
- Use existing `claude_command_scripts/git-header.sh` for generation
- Memory MCP schema defined in planning docs
- Graceful fallback if Memory MCP unavailable

### Priority 2: Memory MCP Integration

**Memory Schema** (from planning):
```json
{
  "entities": {
    "header_compliance_tracker": {
      "type": "behavioral_tracker", 
      "violation_count": 0,
      "success_count": 0,
      "contexts": ["urgent", "normal", "debugging"],
      "user_feedback": ["accepted", "corrected"]
    }
  }
}
```

**Relations to Create**:
- `("header_violation", "occurs_in", "context_type")`
- `("auto_correction", "reduces", "user_friction")`
- `("compliance_improvement", "measured_by", "command_reduction")`

### Priority 3: Integration Testing

**File to Create**: `.claude/scripts/test_header_compliance.py`
- Test header detection accuracy
- Test auto-correction functionality  
- Test Memory MCP storage/retrieval
- Verify performance (<100ms target)

### Priority 4: Claude Code Integration

**Critical Research Needed**:
- Find Claude Code's response generation pipeline hook point
- Determine how to intercept responses before user sees them
- Implement pre-response compliance checking
- Ensure minimal performance impact

## Technical Specifications

### Success Metrics (MVP)
- **Primary**: User `/header` commands drop from ~10/day to <1/day (90% reduction)
- **Technical**: Header compliance rate >95%, auto-correction accuracy >99%
- **Performance**: Processing overhead <100ms per response
- **Qualitative**: User satisfaction, reduced compliance friction

### Memory MCP Integration Points
```python
# Store violation patterns
memory_mcp.create_entities([{
    "type": "header_violation",
    "timestamp": datetime.now().isoformat(),
    "context": "urgent|normal|debugging", 
    "auto_corrected": True,
    "user_reaction": "accepted|rejected"
}])

# Track success patterns  
memory_mcp.create_relations([
    ("compliance_improvement", "measured_by", "reduced_header_commands"),
    ("auto_correction", "successful_in", "context_type")
])
```

### Risk Mitigation
1. **Memory MCP Down**: Local JSON fallback storage
2. **Performance Impact**: Async processing with caching
3. **False Positives**: Conservative regex, user override capability
4. **Integration Complexity**: Start with standalone script, then integrate

## Files Ready for Implementation

### Planning Documents ✅
- `roadmap/scratchpad_memory_mvp.md` - Complete implementation roadmap
- `roadmap/detailed_roadmap_behavioral_automation.md` - Future expansion path
- `PR_MEMORY_MVP_DESCRIPTION.md` - PR description ready

### Existing Resources to Use ✅  
- `claude_command_scripts/git-header.sh` - Header generation script (already works)
- Memory MCP client (available in Claude Code)
- Git status checking utilities

### Files to Create 🔨
- `.claude/scripts/header_compliance_engine.py` - Core engine
- `.claude/scripts/test_header_compliance.py` - Test suite
- Integration hook into Claude Code pipeline (location TBD)

## Implementation Timeline (Week 1)

**Days 1-2**: Core engine + Memory MCP integration
**Days 3-4**: Testing and validation
**Day 5**: Claude Code integration research and initial implementation

## Expected Challenges

1. **Finding Integration Point**: Claude Code response pipeline hook
2. **Memory MCP Learning**: First real usage of Memory MCP for behavioral patterns
3. **Performance Optimization**: Ensuring <100ms processing overhead
4. **User Experience**: Making auto-correction invisible when working correctly

## Success Indicators

**Week 1 End**: 
- Working header compliance engine
- Memory MCP integration functional
- Basic testing complete
- Integration path identified

**Week 2 End**:
- Live integration with Claude Code
- Real user testing 
- Performance optimization
- Initial compliance improvement measured

**Week 3 End**:
- 90% reduction in user `/header` commands achieved
- MVP success proven
- Ready for Phase 2 expansion

## Context Switch Instructions

When switching to `memory_impl` context:
1. **Focus**: Implementation only, planning is complete
2. **Start With**: Core header compliance engine creation
3. **Use**: All planning documents as specification
4. **Goal**: Working MVP within 1 week
5. **Measure**: User `/header` command frequency as primary success metric

This handoff provides complete implementation roadmap based on architecture analysis and user needs assessment. The MVP scope is intentionally minimal to prove the behavioral automation concept before expanding to other compliance areas.

**Key Insight**: This approach replaces hoping the AI reads 2500-line static docs with dynamic behavioral enforcement that actually changes behavior measurably.