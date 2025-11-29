# README for AI Assistants

## Critical System Architecture - READ THIS FIRST

### 1. JSON Mode is INTENTIONAL
- **The system uses JSON mode for ALL Gemini API responses** - this is NOT a bug
- Gemini returns structured JSON like:
  ```json
  {
    "narrative": "The actual story text users should see",
    "entities_mentioned": ["NPC1", "NPC2"],
    "state_updates": { ... },
    "debug_info": { ... }
  }
  ```
- The `narrative` field must be extracted for display to users
- Raw JSON should NEVER be shown to users

### 2. Data Flow
```
Gemini API (returns JSON)
    → llm_service.py (parses JSON, extracts narrative)
    → main.py (receives GeminiResponse object)
    → firestore_service.py (saves narrative text)
    → Frontend (displays narrative with "Scene #X" prefix)
```

### 3. Common Misconceptions
- ❌ "JSON in logs means malformed JSON" - NO, it means the system is working
- ❌ "parse_structured_response should return plain text" - NO, it extracts from valid JSON
- ❌ "JSON mode is optional" - NO, it's required for state management
- ✅ Users should ONLY see the narrative text, never the JSON structure

### 4. Before Attempting Any Fix
1. **Verify the issue with actual user output** - what exactly are they seeing?
2. **Trace the ENTIRE data flow** - where is the narrative extraction failing?
3. **Understand that JSON responses are EXPECTED** - the bug is in processing, not parsing
4. **Test end-to-end** - unit tests alone are insufficient

### 5. Key Files and Their Roles
- `narrative_response_schema.py`: Defines JSON structure and parsing logic
- `llm_service.py`: Calls Gemini API and processes responses
- `main.py`: Orchestrates the flow and saves to database
- `app.js`: Frontend that adds "Scene #" prefix to displayed text

### 6. Debugging Checklist
- [ ] Is Gemini returning valid JSON? (Check logs)
- [ ] Is parse_structured_response extracting the narrative? (Add logging)
- [ ] Is GeminiResponse.narrative_text containing just narrative or full JSON?
- [ ] Is main.py passing the correct field to firestore?
- [ ] Is the frontend receiving narrative or JSON?

### 7. Testing Requirements
- Always test with REAL API calls, not just mocks
- Create a campaign and trigger the exact user scenario
- Verify the displayed text matches expected narrative format
- Check that state updates still work (they depend on JSON mode)

## DO NOT
- Remove JSON mode
- Try to "fix" valid JSON parsing
- Assume JSON in logs means an error
- Declare fixes without end-to-end testing
- Make assumptions about the architecture

## ALWAYS
- Understand the system design first
- Ask clarifying questions about expected behavior
- Test the exact user scenario
- Verify fixes with actual UI output
- Consider the full data pipeline

## Current Known Issues

### JSON Display Bug (as of 2025-07-07)
**Symptom**: Users see raw JSON like `Scene #2: {"narrative": "..."}` instead of formatted text
**NOT the cause**: Malformed JSON, parsing errors, or JSON mode being broken
**Likely cause**: Valid JSON not being processed correctly somewhere in the pipeline
**Investigation needed**:
- Where exactly is the narrative extraction failing?
- Is it in llm_service, main.py, or somewhere else?
- Why does parse_structured_response work in tests but not in production?
