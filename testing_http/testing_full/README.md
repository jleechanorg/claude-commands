# Full API Browser Tests

This directory contains browser tests that use **REAL** Firebase and Gemini APIs.

## ⚠️ WARNING

These tests:
- 💰 **Cost real money** (Gemini API charges)
- 📊 **Use API quotas**
- 💾 **Create real data** in your Firebase project
- 🔐 **Require proper credentials**

## Setup

1. **Copy environment template**:
   ```bash
   cp .env.template .env
   ```

2. **Edit `.env`** with your credentials:
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to Firebase service account key
   - `GEMINI_API_KEY`: Your Gemini API key
   - `FIREBASE_TEST_USER_EMAIL`: Test user email
   - `FIREBASE_TEST_USER_PASSWORD`: Test user password

3. **Set safety limits** in `.env`:
   - `MAX_GEMINI_CALLS_PER_TEST=5`
   - `MAX_TEST_COST_USD=0.10`

## Running Tests

### Individual Test
```bash
python3 testing_ui/testing_full/test_continue_campaign_full.py
```

### All Full API Tests
```bash
# From project root
python3 mvp_site/main.py testuif

# Or directly
python3 testing_ui/testing_full/run_all_full_tests.py
```

## Available Tests

1. **test_continue_campaign_full.py** - Tests campaign continuation with real APIs
2. **test_god_mode_full.py** - Tests god mode with real APIs
3. More tests coming...

## Cost Estimates

- Each test: ~$0.001-0.002
- Full suite: ~$0.01-0.02
- Costs vary based on prompt length and AI responses

## Safety Features

1. **Cost Tracking**: Each test tracks API usage and estimates costs
2. **Limits**: Tests stop if costs exceed limits
3. **Confirmation**: Tests require explicit confirmation before running
4. **Minimal Prompts**: Tests use short prompts to minimize costs

## Differences from Regular Tests

| Feature | Regular Tests (`/testui`) | Full API Tests (`/testuif`) |
|---------|--------------------------|----------------------------|
| Gemini API | Mock/Test mode | Real API calls |
| Firebase | Test bypass auth | Real authentication |
| Cost | Free | ~$0.001-0.002 per test |
| Port | 8086 (test) | 8080 (production) |
| Data | Temporary | Persisted in Firebase |

## Best Practices

1. **Test Sparingly**: Only run when you need to verify real API integration
2. **Monitor Costs**: Check Google Cloud Console for actual charges
3. **Clean Up**: Delete test data after runs
4. **Use Test Project**: Consider a separate Firebase project for testing
5. **Set Quotas**: Configure API quotas to prevent overuse

## Troubleshooting

### Missing Credentials
```
❌ Configuration errors:
   - GEMINI_API_KEY not set in environment
```
→ Check your `.env` file has all required values

### API Quota Exceeded
```
Gemini call limit exceeded: 6 > 5
```
→ Increase `MAX_GEMINI_CALLS_PER_TEST` or wait for quota reset

### Cost Limit Reached
```
Cost limit exceeded: $0.1001 > $0.10
```
→ Increase `MAX_TEST_COST_USD` or run fewer tests

## Contributing

When adding new full API tests:
1. Copy an existing test as template
2. Keep prompts minimal to reduce costs
3. Add cost tracking with `CostTracker`
4. Include safety confirmations
5. Update `run_all_full_tests.py` to include new test