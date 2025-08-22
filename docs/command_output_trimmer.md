# Command Output Trimmer Hook

## Overview

The Command Output Trimmer Hook is a smart compression system that intercepts verbose slash command outputs and applies intelligent compression rules while preserving essential information. This helps manage context consumption and improves readability.

## Features

### Smart Command Detection
- **Automatic Pattern Recognition**: Detects command type from output patterns
- **Command-Specific Rules**: Tailored compression for each command type
- **Fallback Support**: Generic compression for unrecognized commands

### Compression Rules by Command Type

#### `/test` Commands
- ✅ **Preserves**: Error messages, failures, tracebacks, test summaries
- 🗜️ **Compresses**: Progress dots, repetitive "PASSED" messages
- 📊 **Limits**: Maximum 3 passed test details shown
- 🎯 **Focus**: Critical debugging information

#### `/pushl` Commands  
- ✅ **Preserves**: PR links, status messages, branch information
- 🗜️ **Compresses**: Git operation details (enumerating, counting, delta compression)
- 📊 **Limits**: Maximum 5 git operation lines
- 🎯 **Focus**: PR creation success and links

#### `/copilot` Commands
- ✅ **Preserves**: Phase markers, results, completion status
- 🗜️ **Compresses**: Timing calculations and verbose progress
- 📊 **Limits**: Maximum 2 timing detail lines
- 🎯 **Focus**: Autonomous operation progress

#### `/coverage` Commands
- ✅ **Preserves**: Percentage data, total coverage, summary lines
- 🗜️ **Compresses**: Detailed file listings
- 📊 **Limits**: Maximum 10 individual file entries
- 🎯 **Focus**: Overall coverage metrics

#### `/execute` Commands
- ✅ **Preserves**: TODO states (✅❌🔄), checklist items, task status
- 🗜️ **Compresses**: Verbose explanations and reasoning
- 📊 **Limits**: Maximum 3 explanation lines
- 🎯 **Focus**: Task completion status

#### Generic Fallback
- ✅ **Preserves**: First 20 + last 10 lines, important patterns (errors, links, issues)
- 🗜️ **Compresses**: Middle content with compression indicators
- 📊 **Limits**: Maximum 5 important middle lines
- 🎯 **Focus**: Beginning, end, and critical information

## Installation & Configuration

### 1. Hook Integration

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash(*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if [ -x \".claude/hooks/command_output_trimmer.py\" ]; then echo \"$CLAUDE_TOOL_OUTPUT\" | .claude/hooks/command_output_trimmer.py; else echo \"$CLAUDE_TOOL_OUTPUT\"; fi'",
            "description": "Smart compression for verbose command outputs"
          }
        ]
      }
    ]
  },
  "output_trimmer": {
    "enabled": true,
    "compression_threshold": 0.2,
    "log_statistics": true,
    "custom_rules": {
      "test": {
        "max_passed_tests": 3,
        "preserve_summary": true
      },
      "pushl": {
        "max_git_lines": 5,
        "keep_pr_links": true
      }
    }
  }
}
```

### 2. Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `true` | Enable/disable output trimming |
| `compression_threshold` | `0.2` | Minimum compression ratio to report |
| `log_statistics` | `true` | Log compression stats to file |
| `custom_rules` | `{}` | Override default compression rules |

### 3. Custom Rule Configuration

Override compression behavior per command:

```json
{
  "output_trimmer": {
    "custom_rules": {
      "test": {
        "max_passed_tests": 5,
        "preserve_summary": true,
        "keep_failures": true
      },
      "coverage": {
        "max_file_lines": 15,
        "preserve_totals": true
      }
    }
  }
}
```

## Usage Examples

### Before Compression (Test Output)
```
============================== test session starts ==============================
platform linux -- Python 3.11.9, pytest-7.4.4
collected 45 items

tests/test_auth.py::test_login_success PASSED                    [ 2%]
tests/test_auth.py::test_login_failure PASSED                    [ 4%]
tests/test_auth.py::test_logout PASSED                           [ 6%]
tests/test_models.py::test_user_creation PASSED                  [ 8%]
tests/test_models.py::test_user_validation FAILED               [10%]
... [30 more PASSED lines] ...

================================== FAILURES ==================================
__________________________ test_user_validation __________________________
def test_user_validation():
>       assert user.is_valid()
E       AssertionError: User validation failed

========================= 43 passed, 1 failed =========================
```

### After Compression (Test Output)
```
============================== test session starts ==============================
platform linux -- Python 3.11.9, pytest-7.4.4
collected 45 items

tests/test_auth.py::test_login_success PASSED                    [ 2%]
tests/test_auth.py::test_login_failure PASSED                    [ 4%]
tests/test_auth.py::test_logout PASSED                           [ 6%]
... [additional passed tests compressed] ...

================================== FAILURES ==================================
__________________________ test_user_validation __________________________
def test_user_validation():
>       assert user.is_valid()
E       AssertionError: User validation failed

========================= 43 passed, 1 failed =========================

🗜️  **Output Compressed**: 45→15 lines, 1,234 bytes saved (73.2%)
```

## Monitoring & Statistics

### Compression Logs

Statistics are logged to:
```
<project_root>/tmp/worldarchitect.ai/<branch>/compression.log
```

Example log entry:
```json
{
  "timestamp": "2025-08-20T10:30:45.123456",
  "command_type": "test",
  "original_lines": 120,
  "compressed_lines": 25,
  "bytes_saved": 3456,
  "compression_ratio": 0.734
}
```

### Compression Reports

When compression saves >20% space, a report is appended:
```
🗜️  **Output Compressed**: 120→25 lines, 3,456 bytes saved (73.4%)
```

## Testing

### Unit Tests
```bash
# Run comprehensive test suite
python3 .claude/hooks/tests/test_command_output_trimmer.py

# Run specific test categories
python3 -m unittest test_command_output_trimmer.TestCommandOutputTrimmer.test_compress_test_output_preserve_errors
```

### Integration Tests
```bash
# Run full integration test suite
.claude/hooks/tests/test_trimmer_integration.sh

# Test with specific command type
echo "test output..." | .claude/hooks/command_output_trimmer.py
```

### Performance Testing
```bash
# Generate large test output and measure performance
time echo "$(for i in {1..1000}; do echo "Line $i: content"; done)" | .claude/hooks/command_output_trimmer.py > /dev/null
```

## Error Handling

### Graceful Degradation
- **Parse Errors**: Falls back to original output
- **Settings Issues**: Uses default configuration
- **Hook Failures**: Bypasses compression, preserves output
- **Resource Limits**: Applies conservative compression

### Debugging

Enable debug mode:
```bash
export CLAUDE_TRIMMER_DEBUG=1
```

Check error logs:
```bash
tail -f <project_root>/tmp/worldarchitect.ai/<branch>/compression.log
```

## Performance Characteristics

### Benchmarks
- **Small Output** (<1KB): ~5ms processing time
- **Medium Output** (1-10KB): ~15ms processing time  
- **Large Output** (>10KB): ~50ms processing time
- **Memory Usage**: <10MB for typical command outputs

### Optimization Features
- **Pattern Caching**: Compiled regex patterns cached for reuse
- **Lazy Processing**: Only compresses when savings threshold met
- **Stream Processing**: Handles large outputs without loading entirely into memory

## Advanced Configuration

### Custom Pattern Matching

Add custom patterns for command detection:

```json
{
  "output_trimmer": {
    "custom_patterns": {
      "deploy": {
        "detection": ["deployment", "docker build", "cloud run"],
        "preserve": ["deployed to", "build successful", "error"],
        "compress": ["downloading", "extracting", "building layer"]
      }
    }
  }
}
```

### Integration with Other Hooks

Chain with other post-processing hooks:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": ".claude/hooks/command_output_trimmer.py"},
          {"type": "command", "command": ".claude/hooks/output_formatter.py"},
          {"type": "command", "command": ".claude/hooks/stats_collector.py"}
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Common Issues

1. **Hook Not Running**
   - Verify executable permissions: `chmod +x .claude/hooks/command_output_trimmer.py`
   - Check settings.json syntax with `json_pp < .claude/settings.json`

2. **No Compression Applied**
   - Check if `enabled: false` in settings
   - Verify output meets compression threshold
   - Review log file for errors

3. **Important Content Missing**
   - Adjust compression rules for specific command types
   - Add custom patterns for important content
   - Increase line limits in configuration

4. **Performance Issues**
   - Enable lazy processing for large outputs
   - Reduce pattern complexity
   - Check available system memory

### Support

For issues or feature requests, check:
- Hook test suite: `.claude/hooks/tests/`
- Error logs: `tmp/worldarchitect.ai/<branch>/compression.log`
- Configuration validation: `python3 -c "import json; json.load(open('.claude/settings.json'))"`