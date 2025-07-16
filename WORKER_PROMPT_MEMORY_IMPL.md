# 🤖 WORKER PROMPT: Memory MCP Header Compliance Implementation

## Task Context
You are implementing a behavioral compliance engine using Memory MCP to solve the header protocol violation problem. This replaces an over-engineered system (PR #591) with a focused MVP approach.

## Your Mission
Create a header compliance engine that automatically detects missing headers, auto-corrects them, and learns patterns via Memory MCP to reduce user friction by 90%.

## Background
- **Problem**: User constantly types `/header` command (~10x per day) due to CLAUDE.md compliance failures
- **Root Cause**: Static documentation doesn't create behavioral change
- **Solution**: Dynamic enforcement with Memory MCP learning
- **Success Metric**: Reduce user `/header` commands from 10/day to <1/day (90% reduction)

## Files Available
- `roadmap/scratchpad_handoff_memory_impl.md` - Complete implementation plan
- `roadmap/scratchpad_memory_mvp.md` - MVP design specifications  
- `roadmap/detailed_roadmap_behavioral_automation.md` - Future expansion roadmap
- `HANDOFF_MEMORY_IMPL.md` - Technical handoff documentation
- `claude_command_scripts/git-header.sh` - Existing header generation script

## Primary Implementation Task

**File to Create**: `.claude/scripts/header_compliance_engine.py`

```python
# Core architecture (expand this):
class HeaderComplianceEngine:
    def __init__(self):
        self.memory_mcp = MemoryMCPClient()
        self.git_header_script = "./claude_command_scripts/git-header.sh"
    
    def process_response(self, response_text, context):
        # 1. Check compliance: regex for header pattern
        # 2. Auto-correct: use git-header.sh if missing
        # 3. Learn: store patterns in Memory MCP
        # 4. Return: corrected response
        pass
    
    def check_header_compliance(self, response_text):
        # Regex: r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'
        pass
    
    def auto_correct_header(self, response_text):
        # Use existing git-header.sh script
        pass
    
    def log_violation_to_memory(self, violations, context):
        # Memory MCP integration for learning
        pass
```

## Memory MCP Schema to Implement

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
  },
  "relations": [
    ("header_violation", "occurs_in", "context_type"),
    ("auto_correction", "reduces", "user_friction")
  ]
}
```

## Implementation Priorities

**Week 1 (MVP)**:
1. **Day 1-2**: Core engine + Memory MCP integration
2. **Day 3**: Testing suite (`.claude/scripts/test_header_compliance.py`)
3. **Day 4**: Claude Code integration research
4. **Day 5**: End-to-end validation

**Success Criteria**:
- Working header detection + auto-correction
- Memory MCP stores violation patterns
- <100ms processing overhead
- Ready for user testing

## Technical Requirements

### Header Detection
- **Pattern**: `r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'`
- **Missing**: Auto-insert using `git-header.sh`
- **Present**: No action needed

### Memory MCP Integration
- Store each violation with timestamp and context
- Track success/failure patterns
- Learn user behavior patterns over time
- Enable future adaptive behavior

### Performance Requirements
- **Processing time**: <100ms per response
- **Memory usage**: Minimal overhead
- **Reliability**: Graceful fallback if Memory MCP unavailable

## Testing Strategy

**Unit Tests**:
```python
def test_header_detection():
    # Test missing header detection
    # Test valid header recognition
    # Test edge cases
    
def test_auto_correction():
    # Test header insertion
    # Test git-header.sh integration
    # Test malformed responses
    
def test_memory_integration():
    # Test violation logging
    # Test pattern retrieval
    # Test learning progression
```

**Integration Tests**:
- End-to-end compliance checking
- Memory MCP storage/retrieval
- Performance benchmarking

## Critical Success Factors

1. **Focus Ruthlessly**: Headers only - no scope creep
2. **Use Existing Tools**: `git-header.sh` script already works
3. **Measure Objectively**: Track user `/header` command frequency
4. **Start Simple**: Regex + subprocess + Memory MCP
5. **Performance First**: <100ms is non-negotiable

## Risk Mitigation

**Technical Risks**:
- Memory MCP down → Local JSON fallback
- Integration complexity → Start with standalone script
- Performance impact → Async processing

**Scope Risks**:
- Feature creep → Strict header-only focus
- Over-engineering → Simple implementation only

## Expected Deliverables

**End of Week 1**:
- Working `header_compliance_engine.py`
- Test suite with >90% coverage
- Memory MCP integration functional
- Basic Claude Code integration (or clear integration path)
- Performance validated (<100ms)

**Success Measurement**:
- Demo: Auto-detect and correct missing headers
- Memory: Store and retrieve violation patterns
- Performance: Sub-100ms response processing
- Ready: For user acceptance testing

## Context for Implementation

**This is NOT**:
- A complex learning system (that failed in PR #591)
- General purpose AI behavioral modification
- Complete CLAUDE.md replacement (yet)

**This IS**:
- Focused MVP proving behavioral automation concept
- Simple regex + subprocess + Memory MCP
- Measurable solution to specific user frustration
- Foundation for future behavioral improvements

## Key Insight

You're proving that **dynamic behavioral enforcement beats static documentation** for rule compliance. Success here justifies replacing the entire 2500-line CLAUDE.md with adaptive behavioral systems.

**User's Pain**: Constantly typing `/header` because AI forgets rules
**Your Solution**: Make the system automatically enforce the rule
**Success Metric**: User stops typing `/header` (90% reduction)

Start with `header_compliance_engine.py` implementation and focus on the core detection/correction loop. Everything else is secondary to proving this behavioral automation concept works.