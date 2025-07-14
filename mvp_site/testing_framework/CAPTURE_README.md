# Capture Framework Documentation

The Capture Framework enables recording of real service interactions during testing for mock validation and analysis.

## Overview

When running tests in **capture mode** (`/testerc`), the framework:
1. Records all service interactions (Firestore, Gemini API calls)
2. Stores detailed request/response data with timing information
3. Provides analysis tools to compare captured data with mock responses
4. Generates reports on service performance and error patterns

## Quick Start

### 1. Enable Capture Mode

```bash
# Use the /testerc command
/testerc

# Or set environment variables manually
export TEST_MODE=capture
export TEST_CAPTURE_DIR=/tmp/test_captures
```

### 2. Run Tests

Tests will automatically record all service interactions:

```python
from mvp_site.testing_framework.factory import get_service_provider

# This automatically uses capture mode if TEST_MODE=capture
provider = get_service_provider()

# All service calls are now captured
firestore = provider.get_firestore()
docs = firestore.collection('campaigns').get()  # <- Recorded

gemini = provider.get_gemini()
response = gemini.generate_content("Test prompt")  # <- Recorded
```

### 3. Analyze Captures

```bash
# Analyze recent captures
python -m mvp_site.testing_framework.capture_cli analyze

# Compare with existing mocks
python -m mvp_site.testing_framework.capture_cli compare capture.json mocks.json

# Generate mock baseline from captures
python -m mvp_site.testing_framework.capture_cli baseline capture.json new_mocks.json
```

## Captured Data Format

Capture files are JSON with this structure:

```json
{
  "session_id": "1689331200000",
  "timestamp": "2025-07-14T10:00:00Z",
  "total_interactions": 3,
  "interactions": [
    {
      "id": 0,
      "timestamp": "2025-07-14T10:00:01Z",
      "service": "firestore",
      "operation": "collection.get",
      "request": {
        "collection": "campaigns"
      },
      "response": {
        "document_count": 2,
        "documents": [...]
      },
      "status": "success",
      "duration_ms": 145.2
    }
  ]
}
```

## Core Components

### CaptureManager

Central class that records interactions:

```python
from mvp_site.testing_framework.capture import CaptureManager

manager = CaptureManager('/tmp/captures')

# Context manager for automatic recording
with manager.capture_interaction('firestore', 'get', {'collection': 'test'}) as interaction:
    # Make real service call
    result = firestore.collection('test').get()
    # Record response
    manager.record_response(interaction['id'], result_data)

# Save to file
manager.save_captures()
```

### Service Wrappers

Transparent wrappers that capture without changing your code:

- **CaptureFirestoreClient**: Wraps Firestore operations
- **CaptureGeminiClient**: Wraps Gemini API calls

These are automatically used when `RealServiceProvider` is in capture mode.

### Analysis Tools

```python
from mvp_site.testing_framework.capture_analysis import CaptureAnalyzer

analyzer = CaptureAnalyzer('/tmp/captures')

# Analyze performance and errors
analysis = analyzer.analyze_captures(days_back=7)
print(f"Success rate: {analysis['success_rate']:.1%}")

# Compare with mocks
comparison = analyzer.compare_with_mock('capture.json', mock_responses)
print(f"Mock accuracy: {comparison['accuracy_score']:.1%}")

# Generate report
report = analyzer.generate_report(analysis, 'report.md')
```

## Command Line Interface

### analyze

Analyze captured data for patterns and performance:

```bash
python -m mvp_site.testing_framework.capture_cli analyze --days 7 --output report.md
```

Output includes:
- Total interactions by service
- Performance metrics (avg/min/max duration)
- Error rates and types
- Most/least frequently used operations

### compare

Compare captured real data with mock responses:

```bash
python -m mvp_site.testing_framework.capture_cli compare capture.json mocks.json --verbose
```

Identifies:
- Mock responses that don't match real data
- Missing mock responses for real operations
- Data structure differences
- Accuracy percentage

### baseline

Generate initial mock responses from real capture data:

```bash
python -m mvp_site.testing_framework.capture_cli baseline capture.json new_mocks.json
```

Creates a mock responses file using the first successful response for each service operation.

### list

List available capture files:

```bash
python -m mvp_site.testing_framework.capture_cli list
```

Shows files with sizes and modification times.

### cleanup

Remove old capture files to prevent disk space issues:

```bash
python -m mvp_site.testing_framework.capture_cli cleanup --days 7
```

## Data Privacy & Security

### Automatic Sanitization

Sensitive fields are automatically redacted:

```python
request_data = {
    "username": "user123",
    "password": "secret123",  # -> "[REDACTED]"
    "api_key": "abc123",      # -> "[REDACTED]"
    "normal_field": "value"   # -> "value"
}
```

Fields containing these keywords are redacted:
- password, secret, key, token

### Storage Location

By default, captures are stored in `/tmp/test_captures/` with automatic cleanup.

**Production Note**: Never commit capture files to version control as they may contain sensitive data.

## Integration with Existing Tests

### Minimal Changes Required

Existing tests work unchanged - just change the TEST_MODE:

```python
# Before (mock mode)
TEST_MODE=mock python test_campaign.py

# After (capture mode)  
TEST_MODE=capture python test_campaign.py
```

### Service Provider Integration

The `RealServiceProvider` automatically enables capture when initialized with `capture_mode=True`:

```python
provider = RealServiceProvider(capture_mode=True)
firestore = provider.get_firestore()  # Returns CaptureFirestoreClient
gemini = provider.get_gemini()        # Returns CaptureGeminiClient
```

### Cleanup Integration

Capture data is automatically saved during provider cleanup:

```python
provider = get_service_provider('capture')
try:
    # Run tests...
    pass
finally:
    provider.cleanup()  # Saves capture data automatically
```

## Performance Considerations

### Minimal Overhead

Capture adds minimal performance overhead:
- ~1-2ms per interaction for JSON serialization
- Asynchronous file I/O for saves
- In-memory storage during test execution

### Storage Management

- Automatic cleanup of old files (configurable retention)
- Compression for large capture sessions
- Rotation to prevent disk exhaustion

## Best Practices

### 1. Strategic Capture Usage

Don't capture everything - focus on:
- High-value integration tests
- Tests that frequently break due to mock issues
- Performance-critical operations
- New API integrations

### 2. Regular Analysis

Set up automated analysis:

```bash
# Weekly cron job
0 0 * * 0 python -m mvp_site.testing_framework.capture_cli analyze --days 7 --output /tmp/weekly_report.md
```

### 3. Mock Improvement Workflow

1. Run tests in capture mode
2. Analyze differences with existing mocks
3. Update mocks based on real data
4. Verify improved test accuracy

### 4. CI/CD Integration

```yaml
# GitHub Actions example
- name: Run capture tests
  run: |
    export TEST_MODE=capture
    python -m pytest tests/integration/
    
- name: Analyze captures
  run: |
    python -m mvp_site.testing_framework.capture_cli analyze --output capture_report.md
    
- name: Cleanup old captures
  run: |
    python -m mvp_site.testing_framework.capture_cli cleanup --days 1
```

## Troubleshooting

### Common Issues

**Capture files not created**
- Check `TEST_CAPTURE_DIR` is writable
- Verify capture mode is enabled (`provider.capture_mode`)
- Ensure cleanup is called to save data

**Large capture files**
- Use shorter test runs
- Enable automatic cleanup
- Check for data loops or excessive API calls

**Missing interactions**
- Verify service calls go through wrapped clients
- Check error handling doesn't skip recording
- Ensure proper context manager usage

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Capture manager will log all interactions
manager = CaptureManager('/tmp/captures')
```

## Examples

See `examples/capture_example.py` for a complete demonstration of:
- Setting up capture mode
- Recording interactions
- Analyzing captured data
- Comparing with mocks
- CLI tool usage

Run the example:

```bash
cd mvp_site/testing_framework/examples
python capture_example.py
```

## API Reference

### CaptureManager

```python
class CaptureManager:
    def __init__(self, capture_dir: str = None)
    def capture_interaction(self, service: str, operation: str, request_data: dict)
    def record_response(self, interaction_id: int, response_data: Any)
    def save_captures(self, filename: str = None) -> str
    def get_summary(self) -> dict
```

### CaptureAnalyzer

```python
class CaptureAnalyzer:
    def __init__(self, capture_dir: str)
    def analyze_captures(self, days_back: int = 7) -> dict
    def compare_with_mock(self, capture_file: str, mock_responses: dict) -> dict
    def generate_report(self, analysis: dict, output_file: str = None) -> str
```

### Service Wrappers

All service wrappers maintain the same interface as the original clients while adding transparent capture functionality.

## Future Enhancements

- Real-time capture streaming for long-running tests
- Integration with APM tools (New Relic, DataDog)
- Automated mock generation with confidence scoring
- Machine learning-based anomaly detection
- Performance regression detection across captures