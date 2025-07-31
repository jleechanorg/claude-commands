# API Compatibility Followup Tasks

## Problem Summary
The MCP redesign broke backward compatibility by changing the campaigns API response format:
- **Old**: `[campaigns...]` (direct array)
- **New**: `{"campaigns": [...], "success": true}` (wrapped object)

Our tests didn't catch this because mocks used the old format while production used the new format.

## Prevention Strategies

### 1. Response Format Contract Tests
- [ ] Create JSON Schema definitions for all API endpoints
- [ ] Validate both mock and production responses against schemas
- [ ] Fail tests if response format doesn't match schema

### 2. Mock-Production Parity Checker
- [ ] Enhanced `/testi` command that:
  - Runs tests with mocks
  - Runs same tests with production API
  - Compares response structures
  - Reports any format differences
- [ ] Add `--compare-responses` flag to integration tests

### 3. Frontend Contract Tests
- [ ] Test that validates frontend assumptions about API responses
- [ ] Use actual frontend destructuring patterns in tests
- [ ] Example: `const { data: campaigns } = response` should be tested

### 4. API Breaking Change Detection
- [ ] CI job that compares main branch responses vs PR responses
- [ ] Use snapshot testing for API responses
- [ ] Alert on any response format changes

### 5. Response Documentation
- [ ] Auto-generate API documentation from actual responses
- [ ] Include example responses in docs
- [ ] Version API changes explicitly

## Implementation Priority

1. **Immediate**: Add response format validation to existing tests
2. **Short-term**: Create mock-production parity tests
3. **Medium-term**: Set up CI breaking change detection
4. **Long-term**: Full API contract testing framework

## Code Examples

### Response Format Validation Test
```python
def test_campaigns_response_format():
    """Ensure campaigns endpoint returns expected format."""
    # Mock response
    mock_response = mock_get_campaigns()

    # Production response
    prod_response = real_api_get_campaigns()

    # Both should have same structure
    assert_same_structure(mock_response, prod_response)

    # Validate against schema
    schema = {
        "type": "object",
        "properties": {
            "campaigns": {"type": "array"},
            "success": {"type": "boolean"}
        },
        "required": ["campaigns", "success"]
    }
    validate(prod_response, schema)
```

### Frontend Contract Test
```python
def test_frontend_campaigns_destructuring():
    """Test that frontend destructuring patterns work."""
    response = api.get('/api/campaigns')

    # Simulate frontend destructuring
    try:
        # This is what frontend does
        data = response.json()
        campaigns = data['campaigns']  # or data if old format

        # Must be iterable for forEach
        assert hasattr(campaigns, '__iter__')
        assert isinstance(campaigns, list)
    except (KeyError, TypeError) as e:
        pytest.fail(f"Frontend destructuring would fail: {e}")
```

## Testing Commands Enhancement

### Current State
- `/testi` - Runs integration tests (doesn't compare mock vs production)
- `/testui` - Runs UI tests with browser automation
- `/testhttp` - Runs HTTP tests

### Proposed Additions
- `/testi --compare` - Run tests and compare mock vs production responses
- `/testi --contract` - Validate API contracts
- `/testi --snapshot` - Generate/compare response snapshots

## Next Steps

1. Implement `test_response_parity.py` that compares mock vs production
2. Add response format validation to all API tests
3. Document expected response formats in API docs
4. Set up CI job for API compatibility checking

## Notes
- The JavaScript fix we implemented handles both formats gracefully
- We should decide: keep backward compatibility or standardize on new format
- All new API endpoints should have response format tests from day 1
