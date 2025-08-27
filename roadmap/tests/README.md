# Cerebras Script Testing

This directory contains various test scripts and documentation for the cerebras_direct.sh script enhancements.

## Files

1. **cerebras_test_suite.md** - Comprehensive test suite defining various test categories and prompts
2. **run_cerebras_comparison_test.sh** - Script to compare default mode vs light mode performance
3. **test_cerebras_security_filtering.sh** - Script to test security filtering behavior
4. **run_all_cerebras_tests.sh** - Script to run all cerebras enhancement tests

## Test Results

The following files contain the results of our tests:
1. **cerebras_comparison_test_results.md** - Results of performance comparison between default and light modes
2. **cerebras_security_filtering_test_results.md** - Results of security filtering tests

## Summary Documents

The following files contain comprehensive summaries of the work done:
1. **cerebras_script_enhancement_summary.md** - Summary of all enhancements made to the cerebras script
2. **cerebras_enhancement_final_summary.md** - Final comprehensive summary of enhancements and tests
3. **cerebras_complete_enhancement_summary.md** - Complete summary of all work done
4. **cerebras_final_verification_summary.md** - Final verification summary of all cerebras script enhancements
5. **cerebras_comprehensive_final_summary.md** - Comprehensive final summary of all work
6. **cerebras_project_completion_summary.md** - Project completion summary
7. **cerebras_project_status_complete.md** - Project status completion document

## Usage

To run the tests, execute the following scripts:
```bash
# Make scripts executable
chmod +x run_cerebras_comparison_test.sh
chmod +x test_cerebras_security_filtering.sh
chmod +x run_all_cerebras_tests.sh

# Run individual tests
./run_cerebras_comparison_test.sh
./test_cerebras_security_filtering.sh

# Run all tests
./run_all_cerebras_tests.sh
```

## Purpose

These tests were created to verify the functionality of the enhanced cerebras_direct.sh script, particularly:
1. The new --light mode flag that skips system prompts and security filtering
2. Performance differences between default mode and light mode
3. Proper handling of potentially dangerous prompts in default vs light mode