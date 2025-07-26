# Malformed JSON Response Investigation (TASK-001a)

## Problem Statement
AI occasionally returns malformed JSON responses causing parsing failures and application errors. This impacts reliability and user experience.

## Investigation Findings

### Common Failure Patterns

#### 1. Truncated Responses
- **Cause**: Token limit exceeded mid-JSON
- **Symptom**: JSON cuts off without closing brackets
- **Example**: `{"story": "Once upon a time...` (no closing)
- **Frequency**: High with large responses

#### 2. Mixed Format Responses
- **Cause**: AI switches between JSON and plain text
- **Symptom**: Valid JSON followed by narrative text
- **Example**: `{"story": "text"} And then the hero...`
- **Frequency**: Medium, especially in creative modes

#### 3. Escaped Quote Issues
- **Cause**: Improper escaping of quotes in strings
- **Symptom**: JSON parser fails on unescaped quotes
- **Example**: `{"dialog": "He said "hello" to me"}`
- **Frequency**: Medium, common in dialogue

#### 4. Structural Violations
- **Cause**: AI generates invalid JSON structure
- **Symptom**: Missing commas, extra brackets, wrong types
- **Example**: `{"a": "b" "c": "d"}` (missing comma)
- **Frequency**: Low but critical when occurs

### Root Cause Analysis

#### 1. Token Pressure
- As context grows, less space for response
- AI may start JSON correctly but run out of tokens
- More likely with complex nested structures

#### 2. Instruction Clarity
- JSON mode instructions compete with narrative instructions
- AI sometimes prioritizes story over format
- Ambiguous prompts lead to mixed outputs

#### 3. Model Limitations
- Some models better at structured output
- Temperature settings affect format compliance
- JSON mode not always strictly enforced

### Vulnerability Assessment

#### High Risk Scenarios
1. **Long narrative responses** (>2000 tokens)
2. **Complex nested state updates**
3. **Multiple planning blocks in one response**
4. **High temperature settings** (>0.7)

#### Medium Risk Scenarios
1. **Dialogue-heavy content**
2. **Mixed content types** (narrative + data)
3. **Rapid back-and-forth exchanges**

#### Low Risk Scenarios
1. **Short factual responses**
2. **Simple state updates**
3. **Low temperature settings** (<0.5)

## Recovery Strategies

### 1. Progressive Token Management
```python
def calculate_safe_token_budget(context_tokens, model_limit):
    # Reserve 20% buffer for JSON structure
    safety_margin = 0.2
    available = model_limit - context_tokens
    return int(available * (1 - safety_margin))
```

### 2. Enhanced Retry Logic
```python
def parse_with_recovery(response_text):
    strategies = [
        parse_as_json,           # Try normal parsing
        extract_json_block,      # Find JSON within text
        repair_truncated_json,   # Add missing brackets
        fallback_to_text         # Last resort
    ]

    for strategy in strategies:
        try:
            return strategy(response_text)
        except:
            continue

    raise ParseError("All recovery strategies failed")
```

### 3. JSON Structure Validation
```python
def validate_response_structure(data):
    required_fields = ["response", "state_changes", "planning_block"]

    for field in required_fields:
        if field not in data:
            data[field] = get_default_value(field)

    return data
```

### 4. Streaming Response Handler
```python
def handle_streaming_json(stream):
    buffer = ""
    depth = 0

    for chunk in stream:
        buffer += chunk
        depth += chunk.count('{') - chunk.count('}')

        if depth == 0 and buffer.strip():
            # Complete JSON object
            yield parse_json(buffer)
            buffer = ""
```

## Implementation Recommendations

### Immediate Actions
1. **Add JSON recovery functions** to response parser
2. **Implement token budgeting** for JSON responses
3. **Add response validation** before parsing
4. **Log all parsing failures** for analysis

### Short-term Improvements
1. **Response format templates** in prompts
2. **Fallback parsing strategies**
3. **Partial response recovery**
4. **User-friendly error messages**

### Long-term Solutions
1. **Streaming JSON parser** for large responses
2. **Response schema enforcement**
3. **Model-specific optimizations**
4. **Automated retry with backoff**

## Monitoring Plan

### Metrics to Track
1. **Parse failure rate** by response type
2. **Recovery strategy success rates**
3. **Token usage vs. failures correlation**
4. **Model-specific failure patterns**

### Alerting Thresholds
- Parse failure rate > 5%: Warning
- Parse failure rate > 10%: Critical
- Recovery failure > 1%: Investigation needed

## Testing Strategy

### Unit Tests
1. Test each recovery strategy
2. Validate edge cases
3. Ensure graceful degradation

### Integration Tests
1. Simulate token limit scenarios
2. Test with malformed responses
3. Verify error handling flow

### Load Tests
1. High concurrency parsing
2. Large response handling
3. Memory usage monitoring

## Conclusion

Malformed JSON responses are a manageable risk with proper handling. Implementation of progressive token management and enhanced retry logic will significantly improve reliability. The recovery strategies provide multiple fallback options to ensure graceful degradation rather than complete failure.
