# MVP Header Compliance Handoff Command

Creates a structured handoff for implementing MVP header compliance tracking in the main application.

## Task Overview

**Goal**: Track and enforce the mandatory branch header protocol from CLAUDE.md in the MVP application.

## Implementation Requirements

### 1. Header Compliance Tracking
- Monitor Claude interactions for missing branch headers
- Track compliance rates per session
- Generate alerts for violations

### 2. MVP Integration Points
- Add header validation to existing Claude workflows
- Integrate with current UI notification system
- Maintain session-based compliance tracking

### 3. Database Schema
- Create compliance tracking table in Firestore
- Store session data with header compliance status
- Track violation patterns and improvement over time

### 4. Testing Requirements
- Unit tests for header detection logic
- Integration tests with mock Claude responses
- UI tests for compliance indicators

## Files to Modify

### Backend Files
- `mvp_site/claude_service.py` - Add header validation
- `mvp_site/firestore_service.py` - Add compliance tracking
- `mvp_site/constants.py` - Add compliance constants

### Frontend Files
- `mvp_site/static/js/claude_interface.js` - Add compliance UI
- `mvp_site/templates/` - Update templates for compliance indicators

### Test Files
- `mvp_site/test_claude_service.py` - Add compliance tests
- `mvp_site/test_firestore_service.py` - Add tracking tests

## Worker Prompt

```
🎯 WORKER PROMPT (Copy-paste ready)

TASK: MVP Header Compliance Tracking
SETUP:
1. Switch to worktree: cd /path/to/worktree_roadmap
2. Checkout handoff branch: git checkout handoff-mvp-header-compliance
3. Read specification: roadmap/scratchpad_handoff_mvp_header_compliance.md

GOAL: Implement branch header compliance tracking for Claude interactions in MVP

IMPLEMENTATION:
1. Add header validation logic to claude_service.py
2. Create Firestore schema for compliance tracking
3. Add UI indicators for compliance status
4. Implement session-based compliance monitoring
5. Add comprehensive test coverage

SUCCESS CRITERIA:
- Header compliance detection works for all Claude responses
- Compliance rates are tracked and stored in Firestore
- UI shows compliance status to users
- All tests pass (unit, integration, UI)
- Documentation updated with compliance features

TIMELINE: 4-6 hours
FILES: claude_service.py, firestore_service.py, claude_interface.js, test files

START: Read the handoff scratchpad for complete technical details
```

## Technical Specifications

### Header Detection Logic
```python
def validate_header_compliance(response_text):
    """
    Validate if Claude response contains mandatory branch header.
    
    Expected format: [Local: <branch> | Remote: <upstream> | PR: <number> <url>]
    """
    header_pattern = r'^\[Local: .+ \| Remote: .+ \| PR: .+\]'
    return re.match(header_pattern, response_text.strip()) is not None
```

### Compliance Tracking Schema
```python
compliance_data = {
    'session_id': str,
    'timestamp': datetime,
    'has_header': bool,
    'response_preview': str,  # First 100 chars
    'compliance_rate': float,  # Running average
    'violation_count': int
}
```

### UI Integration
- Add compliance indicator in Claude chat interface
- Show compliance percentage in session stats
- Display violation alerts when headers are missing

## Next Steps

1. Create handoff branch with complete specification
2. Generate scratchpad with detailed implementation plan
3. Create PR for review and assignment
4. Provide worker prompt for immediate task handoff