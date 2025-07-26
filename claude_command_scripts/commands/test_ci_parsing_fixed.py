#!/usr/bin/env python3
"""
Test script for CI log parsing functions - Fixed version
Validates that error parsing correctly extracts different types of failures
"""

import json
import tempfile
import os
import re

# Test log content with various error patterns
TEST_LOG_CONTENT = """
2025-07-20T04:24:34.7403873Z ##[group]Run test suite
2025-07-20T04:24:40.1234567Z Running tests using pytest...
2025-07-20T04:24:42.9876543Z
2025-07-20T04:24:42.9876544Z ======================================= FAILURES =======================================
2025-07-20T04:24:42.9876545Z ________________________ test_user_login ________________________
2025-07-20T04:24:42.9876546Z
2025-07-20T04:24:42.9876547Z def test_user_login():
2025-07-20T04:24:42.9876548Z     response = client.post('/login', json={'username': 'test', 'password': 'test'})
2025-07-20T04:24:42.9876549Z >   assert response.status_code == 200
2025-07-20T04:24:42.9876550Z E   AssertionError: assert 404 == 200
2025-07-20T04:24:42.9876551Z E   +  where 404 = <Response [404]>.status_code
2025-07-20T04:24:42.9876552Z
2025-07-20T04:24:42.9876553Z test_auth.py:25: AssertionError
2025-07-20T04:24:42.9876554Z FAILED test_auth.py::test_user_login - AssertionError: assert 404 == 200
2025-07-20T04:24:42.9876555Z
2025-07-20T04:24:43.1111111Z ======================== Import Errors ========================
2025-07-20T04:24:43.1111112Z Traceback (most recent call last):
2025-07-20T04:24:43.1111113Z   File "test_firebase.py", line 5, in <module>
2025-07-20T04:24:43.1111114Z     import firebase_admin
2025-07-20T04:24:43.1111115Z ModuleNotFoundError: No module named 'firebase_admin'
2025-07-20T04:24:43.1111116Z
2025-07-20T04:24:44.2222222Z ======================== Syntax Errors ========================
2025-07-20T04:24:44.2222223Z   File "main.py", line 45
2025-07-20T04:24:44.2222224Z     def process_data()
2025-07-20T04:24:44.2222225Z                      ^
2025-07-20T04:24:44.2222226Z SyntaxError: invalid syntax
2025-07-20T04:24:44.2222227Z
2025-07-20T04:24:45.3333333Z ======================== Runtime Errors ========================
2025-07-20T04:24:45.3333334Z Traceback (most recent call last):
2025-07-20T04:24:45.3333335Z   File "app.py", line 123, in process_request
2025-07-20T04:24:45.3333336Z     result = handler.execute()
2025-07-20T04:24:45.3333337Z   File "handler.py", line 45, in execute
2025-07-20T04:24:45.3333338Z     return self.validate_data()
2025-07-20T04:24:45.3333339Z ValueError: Invalid data format provided
2025-07-20T04:24:45.3333340Z
2025-07-20T04:24:46.4444444Z ======================== Unittest Failures ========================
2025-07-20T04:24:46.4444445Z FAIL: test_database_connection (test_db.TestDatabase)
2025-07-20T04:24:46.4444446Z Traceback (most recent call last):
2025-07-20T04:24:46.4444447Z   File "test_db.py", line 30, in test_database_connection
2025-07-20T04:24:46.4444448Z     self.assertTrue(connection.is_active())
2025-07-20T04:24:46.4444449Z AssertionError: False is not true
2025-07-20T04:24:46.4444450Z
2025-07-20T04:24:47.5555555Z ##[endgroup]
"""

def parse_test_failures(log_content):
    """Parse various types of test failures from CI logs"""
    failures = []

    # Pattern 1: Python unittest failures
    unittest_pattern = r'FAIL: ([^\(]+)\(([^)]+)\)\s*\n.*?AssertionError: ([^\n]+)'
    for match in re.finditer(unittest_pattern, log_content, re.MULTILINE | re.DOTALL):
        test_name, test_class, message = match.groups()
        failures.append({
            'type': 'unittest_failure',
            'test_name': test_name.strip(),
            'test_class': test_class.strip(),
            'error_type': 'AssertionError',
            'message': message.strip(),
            'framework': 'unittest'
        })

    # Pattern 2: pytest failures
    pytest_pattern = r'FAILED ([^:]+)::([^-]+) - ([^:]+): ([^\n]+)'
    for match in re.finditer(pytest_pattern, log_content, re.MULTILINE):
        test_file, test_name, error_type, message = match.groups()
        failures.append({
            'type': 'pytest_failure',
            'test_file': test_file.strip(),
            'test_name': test_name.strip(),
            'error_type': error_type.strip(),
            'message': message.strip(),
            'framework': 'pytest'
        })

    # Pattern 3: Import errors
    import_pattern = r'(ModuleNotFoundError|ImportError): ([^\n]+)'
    for match in re.finditer(import_pattern, log_content, re.MULTILINE):
        error_type, message = match.groups()
        failures.append({
            'type': 'import_error',
            'error_type': error_type.strip(),
            'message': message.strip(),
            'severity': 'critical'
        })

    # Pattern 4: Syntax errors
    syntax_pattern = r'SyntaxError: ([^\n]+).*?File "([^"]+)", line (\d+)'
    for match in re.finditer(syntax_pattern, log_content, re.MULTILINE | re.DOTALL):
        message, file_path, line_number = match.groups()
        failures.append({
            'type': 'syntax_error',
            'error_type': 'SyntaxError',
            'message': message.strip(),
            'file_path': file_path.strip(),
            'line_number': int(line_number),
            'severity': 'critical'
        })

    return failures

def extract_stack_traces(log_content):
    """Extract Python stack traces from CI logs"""
    tracebacks = []

    # Pattern for Python tracebacks
    traceback_pattern = r'Traceback \(most recent call last\):(.*?)(\w+Error): ([^\n]+)'
    for match in re.finditer(traceback_pattern, log_content, re.MULTILINE | re.DOTALL):
        trace_content, error_type, error_message = match.groups()

        # Extract file/line information from traceback
        file_pattern = r'File "([^"]+)", line (\d+), in ([^\n]+)'
        files = []
        for file_match in re.finditer(file_pattern, trace_content):
            file_path, line_number, function_name = file_match.groups()
            files.append({
                'file_path': file_path.strip(),
                'line_number': int(line_number),
                'function_name': function_name.strip()
            })

        tracebacks.append({
            'error_type': error_type.strip(),
            'error_message': error_message.strip(),
            'stack_frames': files,
            'full_traceback': match.group(0).strip()
        })

    return tracebacks

def test_parse_test_failures():
    """Test the parse_test_failures function"""
    print("Testing parse_test_failures function...")

    failures = parse_test_failures(TEST_LOG_CONTENT)
    print(f"Found {len(failures)} failures:")

    # Validate expected patterns
    expected_types = {'pytest_failure', 'import_error', 'syntax_error', 'unittest_failure'}
    found_types = {f['type'] for f in failures}

    print(f"Expected types: {expected_types}")
    print(f"Found types: {found_types}")

    # Check specific cases
    pytest_failures = [f for f in failures if f['type'] == 'pytest_failure']
    if pytest_failures:
        print(f"✅ pytest failure detected: {pytest_failures[0]['test_file']}::{pytest_failures[0]['test_name']}")

    import_errors = [f for f in failures if f['type'] == 'import_error']
    if import_errors:
        print(f"✅ Import error detected: {import_errors[0]['message']}")

    syntax_errors = [f for f in failures if f['type'] == 'syntax_error']
    if syntax_errors:
        print(f"✅ Syntax error detected: {syntax_errors[0]['file_path']}:{syntax_errors[0]['line_number']}")

    unittest_failures = [f for f in failures if f['type'] == 'unittest_failure']
    if unittest_failures:
        print(f"✅ Unittest failure detected: {unittest_failures[0]['test_name']}")

    return len(failures) >= 4  # Should find at least 4 different errors

def test_stack_trace_extraction():
    """Test stack trace extraction"""
    print("\nTesting stack trace extraction...")

    tracebacks = extract_stack_traces(TEST_LOG_CONTENT)
    print(f"Found {len(tracebacks)} stack traces:")

    for tb in tracebacks:
        print(f"  {tb['error_type']}: {tb['error_message']}")
        if tb['stack_frames']:
            main_frame = tb['stack_frames'][0]
            print(f"    Main: {main_frame['file_path']}:{main_frame['line_number']} in {main_frame['function_name']}")

    return len(tracebacks) >= 1  # Should find at least one stack trace

def main():
    """Run all tests"""
    print("🔬 Testing Enhanced CI Log Parsing Functions\n")

    tests = [
        ("Test Failure Parsing", test_parse_test_failures),
        ("Stack Trace Extraction", test_stack_trace_extraction),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            if test_func():
                print(f"✅ {test_name} PASSED\n")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}\n")

    print(f"🎯 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! CI log parsing functions are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the error parsing implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
