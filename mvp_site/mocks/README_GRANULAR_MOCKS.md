# Granular Mock Control

This document explains the granular mock control feature that allows you to mock Firebase and Gemini services independently.

## Overview

You can now control mocking of Firebase and Gemini services separately using environment variables:
- `USE_MOCK_FIREBASE` - Controls Firebase/Firestore mocking
- `USE_MOCK_GEMINI` - Controls Gemini AI service mocking

## Environment Variables

### Individual Service Control
```bash
# Mock only Gemini (recommended for testing)
export USE_MOCK_FIREBASE=false
export USE_MOCK_GEMINI=true

# Mock only Firebase
export USE_MOCK_FIREBASE=true
export USE_MOCK_GEMINI=false

# Mock both services
export USE_MOCK_FIREBASE=true
export USE_MOCK_GEMINI=true

# Use real services (costs money!)
export USE_MOCK_FIREBASE=false
export USE_MOCK_GEMINI=false
```

### Legacy Support
The original `USE_MOCKS` variable still works:
```bash
# This mocks BOTH services (backward compatible)
export USE_MOCKS=true
```

Note: Individual flags override `USE_MOCKS` if set explicitly.

## Using run_ui_tests.sh

The UI test runner now supports three modes:

### 1. Mock Gemini + Real Firebase (Default)
```bash
./run_ui_tests.sh mock-gemini
# or just:
./run_ui_tests.sh
```
- ✅ No AI costs (Gemini mocked)
- ✅ Real database operations (Firebase real)
- ✅ Best for most testing scenarios

### 2. Mock Everything
```bash
./run_ui_tests.sh mock
```
- ✅ No external API calls
- ✅ Works offline
- ✅ No costs
- ⚠️  Database operations are not persisted

### 3. Real Everything
```bash
./run_ui_tests.sh real
```
- ⚠️  Uses real Gemini API (costs money!)
- ⚠️  Uses real Firebase
- ✅ Most accurate testing

## Why Granular Control?

1. **Cost Savings**: Mock expensive AI calls while using real database
2. **Realistic Testing**: Test with real Firebase persistence but mock AI responses
3. **Offline Development**: Mock external services when working offline
4. **Debugging**: Isolate issues by mocking only specific services

## Implementation Details

The mock services provide the same interface as real services:
- `MockGeminiClient` returns predefined AI responses
- `MockFirestoreClient` uses in-memory storage
- Both track operation counts for testing

## Testing

Run the granular control tests:
```bash
USE_MOCK_GEMINI=true USE_MOCK_FIREBASE=false python mvp_site/tests/test_granular_mock_control.py
```

## Common Use Cases

### Development (Recommended)
```bash
# Mock AI but use real database
export USE_MOCK_GEMINI=true
export USE_MOCK_FIREBASE=false
```

### CI/CD Pipeline
```bash
# Mock everything for fast, free tests
export USE_MOCK_GEMINI=true
export USE_MOCK_FIREBASE=true
```

### Integration Testing
```bash
# Use real services
export USE_MOCK_GEMINI=false
export USE_MOCK_FIREBASE=false
```
