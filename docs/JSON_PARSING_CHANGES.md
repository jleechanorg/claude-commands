# JSON Parsing Changes - PR #3458

## Summary

PR #3458 removed regex-based JSON parsing and recovery functionality, standardizing on `json.loads()` only. This document describes the behavior changes and their implications.

## Changes Made

### Removed Components

1. **`json_utils.py` module** (729 lines deleted)
   - `parse_llm_json_response()` - robust parser with incomplete JSON recovery
   - `extract_json_boundaries()` - extracted JSON from text-wrapped responses
   - `extract_nested_object()` - bracket-aware nested object extraction
   - `unescape_json_string()` - JSON string unescaping utilities
   - All regex-based recovery logic

2. **Regex fallback parsing** from `narrative_response_schema.py`
   - `NARRATIVE_PATTERN` - regex extraction of narrative field
   - `JSON_STRUCTURE_PATTERN` - cleanup of JSON structure
   - `JSON_KEY_QUOTES_PATTERN` - key quote removal
   - `JSON_COMMA_SEPARATOR_PATTERN` - comma replacement
   - `WHITESPACE_PATTERN` - whitespace normalization
   - All fallback cleanup code (135+ lines removed)

3. **Import dependencies** removed
   - `prompt_utils.py` - removed `convert_json_escape_sequences` import
   - `provider_utils.py` - removed `extract_json_boundaries` import

### New Behavior

**Standard `json.loads()` only**:
- Valid JSON → parsed successfully
- Invalid JSON → fails completely with error message
- Truncated JSON → fails completely (no partial recovery)
- Text-wrapped JSON → fails completely (no boundary extraction)
- Malformed JSON → fails completely (no regex cleanup)

## Impact

### What Still Works

✅ **Valid JSON responses** - Works exactly as before  
✅ **Markdown-wrapped JSON** - Still extracted from code blocks  
✅ **Standard JSON parsing** - Uses Python's built-in `json.loads()`

### What No Longer Works

❌ **Truncated JSON recovery** - Truncated responses fail completely  
❌ **Text-wrapped JSON** - JSON with explanatory text fails  
❌ **Malformed JSON cleanup** - No regex-based recovery  
❌ **Partial data extraction** - No recovery of partial fields

### Error Handling

When JSON parsing fails, the system now:
1. Logs an error with details
2. Returns a user-friendly error message: "Invalid JSON response received. Please try again."
3. Does NOT attempt any recovery or partial extraction

## Migration Notes

### For LLM Providers

**Before**: Providers could return:
- Truncated JSON (recovered partially)
- Text-wrapped JSON (extracted automatically)
- Malformed JSON (cleaned up with regex)

**After**: Providers MUST return:
- Complete, valid JSON
- No extra text before/after JSON
- Properly formatted JSON structure

### For Error Handling

**Before**: System attempted recovery, might return partial data

**After**: System fails fast, requires reprompting

### Recommendations

1. **Ensure LLM responses are complete** - Set appropriate token limits
2. **Validate JSON format** - Use structured output modes when available
3. **Handle errors gracefully** - Reprompt on JSON parse failures
4. **Monitor error rates** - Track JSON parse failures to identify issues

## Code References

- `mvp_site/narrative_response_schema.py` - Main parsing logic
- `mvp_site/prompt_utils.py` - Removed JSON escape sequence conversion
- `mvp_site/llm_providers/provider_utils.py` - Removed boundary extraction

## Testing

When testing, verify:
- ✅ Valid JSON responses work correctly
- ✅ Invalid JSON returns error message
- ✅ Truncated JSON fails (not silently)
- ✅ No regex fallback code remains

## Related PRs

- PR #3458: Remove regex-based JSON parsing, keep standard json.loads()
