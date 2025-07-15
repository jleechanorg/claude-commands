# MVP Header Compliance Tracking - Handoff Scratchpad

**Branch**: `handoff-mvp-header-compliance`
**Status**: Ready for implementation
**Estimated Time**: 4-6 hours
**Priority**: High

## Problem Statement

The CLAUDE.md file mandates that every Claude response must start with a branch header in the format:
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

This is currently tracked manually and violations are frequent. We need to implement automated tracking and enforcement in the MVP application.

## Analysis Completed

### Current State
- Header protocol exists in CLAUDE.md but no automated enforcement
- Manual tracking leads to frequent violations
- No visibility into compliance rates across sessions
- No integration with existing Claude workflows in MVP

### Key Requirements Identified
1. **Header Detection**: Regex-based validation of response headers
2. **Compliance Tracking**: Session-based monitoring and storage
3. **UI Integration**: Visual indicators for compliance status
4. **Data Persistence**: Firestore schema for compliance metrics
5. **Testing Coverage**: Unit, integration, and UI tests

## Implementation Plan

### Phase 1: Backend Foundation (2 hours)

#### 1.1 Header Validation Logic
**File**: `mvp_site/claude_service.py`
```python
def validate_header_compliance(response_text):
    """Validate mandatory branch header in Claude response."""
    header_pattern = r'^\[Local: .+ \| Remote: .+ \| PR: .+\]'
    return re.match(header_pattern, response_text.strip()) is not None

def parse_header_components(response_text):
    """Extract branch, remote, and PR info from header."""
    # Implementation to parse header components
    pass
```

#### 1.2 Compliance Tracking Service
**File**: `mvp_site/firestore_service.py`
```python
def track_header_compliance(session_id, response_text, has_header):
    """Track header compliance for session."""
    compliance_data = {
        'session_id': session_id,
        'timestamp': datetime.utcnow(),
        'has_header': has_header,
        'response_preview': response_text[:100],
        'created_at': datetime.utcnow()
    }
    db.collection('header_compliance').add(compliance_data)

def get_session_compliance_rate(session_id):
    """Calculate compliance rate for session."""
    # Implementation to calculate running compliance rate
    pass
```

#### 1.3 Constants and Configuration
**File**: `mvp_site/constants.py`
```python
# Header compliance constants
HEADER_COMPLIANCE_COLLECTION = 'header_compliance'
HEADER_PATTERN = r'^\[Local: .+ \| Remote: .+ \| PR: .+\]'
MIN_COMPLIANCE_RATE = 0.8  # 80% compliance threshold
```

### Phase 2: Frontend Integration (1.5 hours)

#### 2.1 Compliance UI Components
**File**: `mvp_site/static/js/claude_interface.js`
```javascript
function updateComplianceStatus(hasHeader, complianceRate) {
    const indicator = document.getElementById('compliance-indicator');
    indicator.className = hasHeader ? 'compliant' : 'non-compliant';
    indicator.textContent = `Header Compliance: ${(complianceRate * 100).toFixed(1)}%`;
}

function showComplianceAlert(message) {
    // Show user-friendly compliance alert
}
```

#### 2.2 Template Updates
**File**: `mvp_site/templates/base.html`
- Add compliance indicator to header/status bar
- Include compliance styles in CSS

### Phase 3: Testing Coverage (1.5 hours)

#### 3.1 Unit Tests
**File**: `mvp_site/test_claude_service.py`
```python
def test_header_validation_valid():
    response = "[Local: main | Remote: origin/main | PR: none]\nContent here"
    assert validate_header_compliance(response) == True

def test_header_validation_invalid():
    response = "Content without header"
    assert validate_header_compliance(response) == False
```

#### 3.2 Integration Tests
**File**: `mvp_site/test_firestore_service.py`
```python
def test_track_header_compliance():
    # Test compliance tracking with mock Firestore
    pass

def test_session_compliance_calculation():
    # Test compliance rate calculation
    pass
```

#### 3.3 UI Tests
**File**: `mvp_site/testing_ui/test_compliance_ui.py`
```python
def test_compliance_indicator_display():
    # Test UI compliance indicator shows correctly
    pass
```

### Phase 4: Integration and Deployment (1 hour)

#### 4.1 Claude Service Integration
- Integrate header validation into existing Claude response processing
- Add compliance tracking to all Claude interactions
- Ensure backward compatibility

#### 4.2 Error Handling
- Graceful handling of malformed responses
- Fallback behavior for compliance tracking failures
- User-friendly error messages

## Files to Modify

### Backend Files
- `mvp_site/claude_service.py` - Add header validation and compliance tracking
- `mvp_site/firestore_service.py` - Add compliance data storage methods
- `mvp_site/constants.py` - Add compliance-related constants
- `mvp_site/main.py` - Integrate compliance tracking in routes

### Frontend Files
- `mvp_site/static/js/claude_interface.js` - Add compliance UI logic
- `mvp_site/static/style.css` - Add compliance indicator styles
- `mvp_site/templates/base.html` - Add compliance indicator to template

### Test Files
- `mvp_site/test_claude_service.py` - Add header validation tests
- `mvp_site/test_firestore_service.py` - Add compliance tracking tests
- `mvp_site/testing_ui/test_compliance_ui.py` - Add UI compliance tests

## Testing Requirements

### Unit Tests
- Header validation logic (valid/invalid formats)
- Compliance rate calculation
- Header component parsing

### Integration Tests
- Firestore compliance data storage
- Session compliance tracking
- End-to-end compliance workflow

### UI Tests
- Compliance indicator display
- Compliance rate updates
- Alert system functionality

## Success Criteria

1. **Header Detection**: 100% accurate detection of header presence/absence
2. **Compliance Tracking**: All Claude interactions logged with compliance status
3. **UI Integration**: Visual compliance indicators working in all relevant pages
4. **Data Persistence**: Compliance data stored and retrievable from Firestore
5. **Test Coverage**: All new functionality covered by appropriate tests
6. **Performance**: No noticeable impact on Claude response processing time

## Dependencies

- Existing Claude service infrastructure
- Firestore service for data persistence
- Current UI framework and styling
- Testing infrastructure (unit, integration, UI)

## Risk Assessment

### Low Risk
- Header regex validation (straightforward pattern matching)
- Firestore data storage (established pattern)

### Medium Risk
- UI integration without disrupting existing workflows
- Performance impact of compliance tracking

### Mitigation Strategies
- Implement compliance tracking asynchronously
- Use caching for compliance rate calculations
- Gradual rollout with feature flags

## Next Steps

1. Create handoff branch: `git checkout -b handoff-mvp-header-compliance`
2. Implement backend validation logic
3. Add Firestore compliance tracking
4. Create UI components for compliance display
5. Add comprehensive test coverage
6. Integration testing with existing Claude workflows
7. Create PR for review and deployment

## Notes

- This implementation focuses on tracking and visibility rather than enforcement
- Future enhancements could include automatic header insertion
- Consider adding compliance reporting dashboard in admin interface
- Compliance data could be used for improving Claude training/prompts