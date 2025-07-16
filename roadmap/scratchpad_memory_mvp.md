# Header Compliance MVP - Memory MCP Implementation

## Project Goal
Replace CLAUDE.md static rule compliance with dynamic behavioral enforcement using Memory MCP. Focus on header compliance as proof of concept.

## Problem Statement
- User always has to type `/header` command (system failure)
- CLAUDE.md header protocol has ~80% violation rate despite explicit rules
- Static documentation doesn't create behavioral change

## MVP Scope (Ruthlessly Focused)
**Single Behavior**: Git header compliance only
- **Input**: Response text before sending
- **Check**: Presence of `[Local: branch | Remote: upstream | PR: number url]` format
- **Action**: Auto-insert header if missing
- **Learning**: Store violation patterns in Memory MCP
- **Success**: 90% reduction in user `/header` commands

## Success Metrics
**Baseline (Current)**:
- User `/header` commands: ~10 per day
- My header compliance rate: ~20%
- User frustration: High (explicitly mentioned)

**MVP Targets (3 weeks)**:
- User `/header` commands: <1 per day (-90%)
- My header compliance rate: >95%
- System auto-correction accuracy: >99%
- User satisfaction: "I haven't typed `/header` in days"

## Technical Architecture

### Core Components
```python
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
    
    def check_header_compliance(self, text):
        header_pattern = r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'
        if not re.match(header_pattern, text.strip()):
            return ['missing_header']
        return []
    
    def auto_correct_header(self, text):
        header = subprocess.check_output(self.git_header_script, shell=True)
        return f"{header.strip()}\n\n{text}"
```

### Memory MCP Schema
```json
{
  "entities": {
    "header_compliance_tracker": {
      "type": "behavioral_tracker",
      "violation_count": 0,
      "success_count": 0,
      "last_violation": "timestamp",
      "contexts": ["urgent", "normal", "debugging"],
      "user_feedback": ["accepted", "corrected"]
    }
  },
  "relations": [
    ("header_violation", "occurs_in", "context_type"),
    ("auto_correction", "reduces", "user_friction"),
    ("compliance_improvement", "measured_by", "command_reduction")
  ]
}
```

## Implementation Roadmap

### Week 1: Core Engine (Days 1-5)
**Deliverables**:
- [ ] Basic header detection regex
- [ ] Auto-correction using existing git-header.sh script
- [ ] Memory MCP integration for violation logging
- [ ] Standalone testing with sample responses

**Files to Create**:
- `/.claude/scripts/header_compliance_engine.py`
- `/.claude/scripts/test_header_compliance.py`

### Week 2: Integration & Validation (Days 6-10)
**Deliverables**:
- [ ] Hook into Claude Code response pipeline
- [ ] Real-time compliance checking
- [ ] User interaction testing
- [ ] Performance optimization (<100ms overhead)

**Integration Points**:
- Find Claude Code's response generation hook
- Add pre-response compliance checking
- Ensure graceful fallback if Memory MCP unavailable

### Week 3: Learning & Refinement (Days 11-15)
**Deliverables**:
- [ ] Pattern analysis from Memory MCP data
- [ ] Context-aware learning (when do violations happen most?)
- [ ] User preference adaptation
- [ ] Success measurement and validation

## Risk Mitigation

### Technical Risks
1. **Memory MCP Unavailable**: Graceful degradation to local JSON storage
2. **Performance Impact**: Async processing, <100ms target
3. **Integration Complexity**: Start with external script, then integrate
4. **False Positives**: Conservative detection to avoid correction fatigue

### Adoption Risks
1. **User Resistance**: Make warnings helpful, not annoying
2. **Over-Engineering**: Focus solely on headers until proven successful
3. **Maintenance Burden**: Simple architecture, minimal dependencies

## Future Expansion Path

Once header compliance achieves 90% success:

### Phase 2: Test Execution Claims
- Check: Do I claim tests pass without showing output?
- Pattern: "tests complete" without actual test results
- Auto-correct: Require test output before completion claims

### Phase 3: Evidence-Based Debugging  
- Check: Do I show actual errors before proposing fixes?
- Pattern: Suggesting fixes without showing specific error messages
- Auto-correct: Prompt for error evidence before solution proposals

### Phase 4: Response Length Optimization
- Check: Am I being too verbose for simple questions?
- Pattern: Long responses to simple queries
- Auto-correct: Adapt response length to query complexity

### Phase 5: Complete CLAUDE.md Replacement
- Dynamic rule system replacing all static documentation
- Behavioral learning for all critical compliance areas
- Context-aware adaptation to user preferences

## Expected ROI

**Development Investment**: 2-3 weeks
**User Value**: 
- Eliminate daily frustration point (header commands)
- Proof that behavioral automation works
- Foundation for complete rule automation

**System Value**:
- Validate Memory MCP-based learning approach
- Create reusable pattern for other behavioral improvements
- Demonstrate measurable compliance improvement

**Long-term Value**:
- Complete replacement of static CLAUDE.md with dynamic system
- Adaptive AI behavior based on user patterns
- Scalable framework for behavioral compliance

## Definition of Success

**Objective Measures**:
- User `/header` commands drop by 90% within 3 weeks
- System auto-correction accuracy >99%
- Header compliance rate >95%
- Response processing overhead <100ms

**Qualitative Success**:
- User stops mentioning header compliance issues
- User requests expansion to other behaviors
- Reduced friction in daily interactions
- User quote: "I haven't typed `/header` in days!"

## Next Steps

1. **Immediate**: Create basic header compliance engine
2. **Day 1-2**: Test with sample responses and Memory MCP integration
3. **Day 3-5**: Find Claude Code integration point
4. **Week 2**: Live testing with user interactions
5. **Week 3**: Success measurement and validation

This MVP proves that behavioral automation beats static documentation for rule compliance. Success here justifies complete CLAUDE.md replacement with dynamic learning system.