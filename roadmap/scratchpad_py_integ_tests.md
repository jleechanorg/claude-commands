# Scratchpad - Python Integration Tests Plan

## User's Requirements (Crystal Clear)

### What to Mock (ONLY THESE):
1. **Raw Gemini API call** - The actual external HTTP call to Google's Gemini API
   - Mock at: `google.genai.Client.models.generate_content()`
   - Mock at: `google.genai.Client.models.count_tokens()`

2. **Raw Firestore calls** - The actual external calls to Firebase Firestore
   - Mock at: `firebase_admin.firestore.client()`
   - Mock at: `firebase_admin.auth.verify_id_token()`

### What NOT to Mock (MUST GO THROUGH REAL CODE):
- ❌ DO NOT mock `main.py` functions
- ❌ DO NOT mock `firestore_service.py` functions
- ❌ DO NOT mock `gemini_service.py` functions
- ❌ DO NOT mock `game_state.py` functions
- ❌ DO NOT mock any internal application logic

### Current Problem:
The tests are failing because:
1. We're trying to mock at the service level instead of the raw API level
2. The mocks are returning Mock objects that can't be JSON serialized
3. Token counting is returning MagicMock objects instead of numbers

### The Plan:

#### Step 1: Fix Current Mocking Strategy
- Remove all service-level mocks
- Only mock the actual external API calls (google.genai and firebase_admin)
- Ensure all mocks return proper Python objects (not Mock/MagicMock instances)

#### Step 2: Fix Token Counting Mock
- Make `client.models.count_tokens()` return a proper object with `total_tokens` as an integer
- Example: `MockTokenCount(total_tokens=1000)`

#### Step 3: Fix Gemini Response Mock
- Make `client.models.generate_content()` return a proper response object
- The response must have a `.text` attribute containing the JSON response string
- Example: `MockResponse(text='{"narrative": "...", ...}')`

#### Step 4: Fix Firestore Mocks
- Ensure all Firestore document mocks return proper dictionaries
- No Mock objects should be in the returned data
- Timestamps should be strings, not datetime objects

#### Step 5: Test Flow Verification
The tests should verify this complete flow:
1. HTTP Request → Flask route in main.py
2. main.py → calls gemini_service functions (NOT MOCKED)
3. gemini_service → calls google.genai API (MOCKED HERE)
4. main.py → calls firestore_service functions (NOT MOCKED)
5. firestore_service → calls firebase_admin (MOCKED HERE)
6. Response flows back through all layers

## Confirmation Needed

Before I proceed, please confirm:
1. Is this understanding correct?
2. Should I fix the existing tests to follow this pattern?
3. The goal is true end-to-end integration testing with only external API mocking?

## Next Steps (pending confirmation):
1. Update test files to remove intermediate mocks
2. Fix all Mock objects to return serializable data
3. Ensure tests verify the complete application flow
4. Push and verify CI passes
