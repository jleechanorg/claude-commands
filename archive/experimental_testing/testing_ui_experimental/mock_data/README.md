# Mock Data for UI Tests

This directory contains captured Gemini API responses from real `/testuif` runs, used for fast and reliable `/testui` execution.

## Structure

### Response Files
- `wizard_responses.json` - Wizard character/setting test responses
- `campaign_creation_responses.json` - Campaign creation flow responses
- `api_structure_responses.json` - API validation responses
- `structured_fields_responses.json` - Game mechanics responses
- `continue_campaign_responses.json` - Campaign continuation responses

### Mock Service
- `mock_gemini_service.py` - Mock Gemini service implementation
- `response_patterns.json` - Common response patterns and templates

## Usage

**For /testui (fast, no cost):**
Tests automatically use mock data from this directory when `USE_MOCKS=true`

**For /testuif (real API, costs money):**
Tests use real Gemini API and optionally update mock data

## Data Capture Process

1. Run `/testuif` with real Gemini API
2. Successful responses are automatically captured
3. Mock data files are updated with new patterns
4. `/testui` uses updated data for future runs

## Benefits

- **Speed:** No API calls = instant responses
- **Cost:** Zero Gemini charges for routine testing
- **Reliability:** Deterministic, repeatable results
- **Authenticity:** Real captured data, not synthetic
