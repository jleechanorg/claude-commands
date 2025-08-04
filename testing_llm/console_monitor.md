# Console Error Monitoring Orchestrator

**Shared orchestrator for console error monitoring across all test specifications**

This orchestrator provides reusable console error monitoring functionality to avoid protocol duplication across test files, as per CLAUDE.md guidelines.

## Usage

Reference this orchestrator in your test specifications instead of duplicating the console monitoring code:

```markdown
## Console Error Monitoring

→ See `testing_llm/console_monitor.md` for shared console error monitoring implementation
```

## Real-Time Console Error Detection

**Automated Console Monitoring Setup**:
```javascript
// Add console error capture at start of test
window.testErrorLog = [];
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = function(...args) {
    window.testErrorLog.push({
        type: 'error',
        timestamp: new Date().toISOString(),
        message: args.join(' ')
    });
    originalConsoleError.apply(console, args);
};

console.warn = function(...args) {
    window.testErrorLog.push({
        type: 'warning',
        timestamp: new Date().toISOString(),
        message: args.join(' ')
    });
    originalConsoleWarn.apply(console, args);
};

// Function to check for critical errors based on test context
window.getCriticalErrors = function(errorPatterns) {
    const criticalErrors = window.testErrorLog.filter(entry =>
        entry.type === 'error' && errorPatterns.some(pattern =>
            entry.message.includes(pattern)
        )
    );
    return criticalErrors;
};
```

## Common Error Patterns

### Authentication Test Patterns
```javascript
const authErrorPatterns = [
    'firebase', 'authentication', 'oauth', '401',
    'token', 'CORS', 'Network Error'
];
```

### Campaign Test Patterns
```javascript
const campaignErrorPatterns = [
    'TypeError', 'undefined', 'null', 'failed to fetch',
    'Network request failed', '500', '404'
];
```

### Navigation Test Patterns
```javascript
const navigationErrorPatterns = [
    'Router', 'navigation', 'route', 'history',
    'Cannot read property', 'path'
];
```

## Expected Clean Console

**Acceptable Informational Messages**:
```javascript
✅ "Download the React DevTools for a better development experience"
✅ "React DevTools extension detected"
✅ "[HMR] Waiting for update signal from WDS..."
✅ "Consider adding an error boundary"
```

## Console Error Analysis Function

**Generic Validation Function**:
```javascript
function validateConsoleErrors(testCaseName, errorPatterns) {
    const criticalErrors = window.getCriticalErrors(errorPatterns);
    const totalErrors = window.testErrorLog.filter(entry => entry.type === 'error').length;

    console.log(`🔍 Console Error Analysis for ${testCaseName}:`);
    console.log(`   Total console errors: ${totalErrors}`);
    console.log(`   Critical errors: ${criticalErrors.length}`);

    if (criticalErrors.length > 0) {
        console.error('❌ CRITICAL: Test-specific errors found in console:');
        criticalErrors.forEach(error => {
            console.error(`   [${error.timestamp}] ${error.message}`);
        });
        return false;
    }

    if (totalErrors === 0) {
        console.log('✅ Console is clean - no errors detected');
        return true;
    } else {
        console.warn(`⚠️  Found ${totalErrors} non-critical console errors`);
        window.testErrorLog.filter(entry => entry.type === 'error').forEach(error => {
            console.warn(`   [${error.timestamp}] ${error.message}`);
        });
        return totalErrors < 3; // Allow minor non-critical errors
    }
}

// Reset error log between test cases
function resetConsoleErrorLog() {
    window.testErrorLog = [];
    console.log('🔄 Console error log reset for new test case');
}
```

## Integration Example

```javascript
// In your test file
// 1. Setup monitoring
eval(consoleMonitoringSetup); // From this orchestrator

// 2. Define test-specific patterns
const myTestPatterns = ['specific', 'error', 'patterns'];

// 3. Run test
// ... test execution ...

// 4. Validate
const isClean = validateConsoleErrors('My Test Case', myTestPatterns);

// 5. Reset for next test
resetConsoleErrorLog();
```

## Benefits

- **DRY Compliance**: Single source of truth for console monitoring
- **Maintainability**: Update monitoring logic in one place
- **Flexibility**: Tests define their own error patterns
- **Consistency**: All tests use same monitoring approach
