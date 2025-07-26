# HANDOFF: Memory MCP Header Compliance Implementation

**Branch**: handoff-memory_impl
**Status**: Ready for Implementation
**Priority**: HIGH - Replaces failed PR #591
**Timeline**: 1 week MVP

## 🎯 Problem Statement

**Core Issue**: Static CLAUDE.md documentation fails to create behavioral compliance
- User constantly types `/header` command (~10x per day)
- Header protocol violation rate: ~80% despite explicit rules
- 2500-line CLAUDE.md is cognitive overload with no enforcement

**Root Cause**: Static rules don't change behavior - need dynamic enforcement with learning

## 📋 Analysis Completed

### ✅ Architecture Review
- **Original PR #591**: Over-engineered (10+ components, arbitrary confidence math, testing theater)
- **LLM Feedback**: Identified fundamental design flaws requiring complete rework
- **Decision**: Abandon complex system, prove concept with focused MVP

### ✅ MVP Definition
- **Single Behavior**: Header compliance only (prove concept before expanding)
- **Target Metric**: 90% reduction in user `/header` commands (10/day → <1/day)
- **Technology**: Memory MCP for behavioral learning + existing git-header.sh script
- **Success Criteria**: User says "I haven't typed `/header` in days"

### ✅ Technical Architecture
```python
class HeaderComplianceEngine:
    def process_response(self, response_text, context):
        # 1. Check: Missing header pattern
        # 2. Auto-correct: Insert header using git-header.sh
        # 3. Learn: Store patterns in Memory MCP
        # 4. Adapt: Improve based on user feedback
```

## 🛠️ Implementation Plan

### Phase 1: Core Engine (Days 1-2)
**File**: `.claude/scripts/header_compliance_engine.py`
```python
class HeaderComplianceEngine:
    def __init__(self):
        self.memory_mcp = MemoryMCPClient()
        self.git_header_script = "./claude_command_scripts/git-header.sh"

    def check_header_compliance(self, response_text):
        # Regex: r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'
        pattern = r'^\[Local:.*\|.*Remote:.*\|.*PR:.*\]'
        if not re.match(pattern, response_text.strip()):
            return ['missing_header']
        return []

    def auto_correct_header(self, response_text):
        # Use existing git-header.sh script
        header = subprocess.check_output(self.git_header_script, shell=True)
        return f"{header.strip()}\n\n{response_text}"

    def log_violation_to_memory(self, violations, context):
        # Store in Memory MCP for pattern learning
        self.memory_mcp.create_entities([{
            "type": "header_violation",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "auto_corrected": True
        }])
```

### Phase 2: Memory MCP Integration (Days 2-3)
**Memory Schema**:
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

### Phase 3: Integration & Testing (Days 4-5)
**Integration Points**:
- Find Claude Code response pipeline hook
- Add pre-response compliance checking
- Ensure <100ms processing overhead
- Graceful fallback if Memory MCP unavailable

**Testing Requirements**:
- Unit tests for header detection (`.claude/scripts/test_header_compliance.py`)
- Integration test with Memory MCP
- Performance testing (<100ms target)
- User acceptance testing

## 📁 Files to Create/Modify

### New Files ✅
- `.claude/scripts/header_compliance_engine.py` - Core implementation
- `.claude/scripts/test_header_compliance.py` - Test suite
- Integration hook (location TBD based on Claude Code architecture)

### Existing Resources 🔄
- `claude_command_scripts/git-header.sh` - Header generation (already works)
- Memory MCP client (available in Claude Code)
- Planning docs: `roadmap/scratchpad_memory_mvp.md`

### Documentation Updates 📝
- Update implementation progress in scratchpad
- Document integration approach once discovered
- Performance metrics and success measurement

## 🧪 Testing Strategy

### Unit Testing
```python
def test_header_detection():
    engine = HeaderComplianceEngine()

    # Test missing header
    response_without = "This is a response without header"
    assert engine.check_header_compliance(response_without) == ['missing_header']

    # Test valid header
    response_with = "[Local: main | Remote: origin/main | PR: none]\n\nResponse text"
    assert engine.check_header_compliance(response_with) == []
```

### Integration Testing
- Memory MCP storage/retrieval
- Git header script execution
- End-to-end compliance checking
- Performance measurement

### User Acceptance Testing
- Track user `/header` command frequency
- Measure auto-correction accuracy
- User satisfaction feedback
- Compliance rate improvement

## 📊 Success Metrics

### Primary Metrics
- **User `/header` commands**: 10/day → <1/day (90% reduction)
- **Header compliance rate**: 20% → 95%
- **Auto-correction accuracy**: >99%

### Technical Metrics
- **Processing time**: <100ms per response
- **Memory MCP integration**: Successful storage/retrieval
- **System reliability**: No false positives

### Qualitative Metrics
- User stops mentioning header issues
- User satisfaction with automation
- Request for expansion to other behaviors

## ⚠️ Risk Mitigation

### Technical Risks
1. **Memory MCP unavailable**: Local JSON fallback
2. **Claude Code integration complexity**: Start with standalone script
3. **Performance impact**: Async processing, caching
4. **False positives**: Conservative regex, user override

### Implementation Risks
1. **Scope creep**: Focus strictly on headers until 90% success
2. **Over-engineering**: Simple regex + existing scripts only
3. **Integration timing**: Find hook point early, validate approach

## 🔗 Dependencies

### Required Resources
- Memory MCP client access
- `claude_command_scripts/git-header.sh` script
- Claude Code response pipeline access
- Git repository information

### External Dependencies
- Memory MCP server availability
- Git commands functionality
- File system permissions for script execution

## 📅 Timeline & Milestones

**Day 1**: Core engine implementation
**Day 2**: Memory MCP integration
**Day 3**: Testing suite creation
**Day 4**: Claude Code integration research
**Day 5**: End-to-end testing and validation

**Week 1 Success**: Working header compliance with measurable improvement
**Week 2**: User validation and refinement
**Week 3**: 90% reduction in `/header` commands achieved

## 🔄 Next Phase Planning

**After MVP Success**:
- **Phase 2**: Test execution compliance (stop false "tests complete" claims)
- **Phase 3**: Evidence-based debugging (show errors before fixes)
- **Phase 4**: Response length optimization (context-aware verbosity)
- **Phase 5**: Complete CLAUDE.md replacement

## 📋 Implementation Checklist

- [ ] Create `header_compliance_engine.py` with core functionality
- [ ] Implement Memory MCP integration with defined schema
- [ ] Create comprehensive test suite
- [ ] Research Claude Code integration points
- [ ] Implement pre-response compliance checking
- [ ] Validate performance requirements (<100ms)
- [ ] Test with real user interactions
- [ ] Measure compliance improvement
- [ ] Document approach for future phases

This handoff provides complete implementation roadmap for Memory MCP-based behavioral compliance system. Focus on proving the concept with headers before expanding scope.
