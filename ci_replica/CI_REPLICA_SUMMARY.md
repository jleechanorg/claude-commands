# CI Environment Replica Scripts - Summary

## Created Files

### Core Scripts
1. **`ci_local_replica.sh`** - Basic CI environment replication
2. **`ci_debug_replica.sh`** - Advanced CI replication with debugging
3. **`ci_failure_reproducer.sh`** - Maximum isolation for failure reproduction
4. **`ci_replica_launcher.sh`** - Interactive launcher for choosing scripts

### Documentation
5. **`CI_REPLICA_USAGE.md`** - Comprehensive usage guide
6. **`CI_REPLICA_SUMMARY.md`** - This summary file

## Quick Start

### Option 1: Use the Interactive Launcher (Recommended)
```bash
./ci_replica_launcher.sh
```

### Option 2: Direct Script Usage
```bash
# Basic CI replication
./ci_local_replica.sh

# Debug mode with verbose output
./ci_debug_replica.sh --debug --verbose

# Maximum isolation for stubborn failures
./ci_failure_reproducer.sh --isolation=full
```

## Key Features

### Exact CI Environment Replication
- **Python Version**: Attempts to use Python 3.11 (CI exact match)
- **Dependencies**: Installs in exact CI sequence with pinned versions
- **Environment Variables**: Sets all CI-specific variables
- **Virtual Environment**: Creates fresh environment like CI

### Debugging Capabilities
- **Environment Comparison**: Before/after environment snapshots
- **Verbose Output**: Detailed logging of all operations
- **Isolation Modes**: Multiple levels of environment isolation
- **Test Output Capture**: Saves test results for analysis

### CI Workflow Matching
Based on `.github/workflows/test.yml`:
1. Creates fresh virtual environment
2. Upgrades pip, setuptools, wheel
3. Installs pinned grpcio versions
4. Installs protobuf (conflict prevention)
5. Installs project requirements
6. Verifies vpython functionality
7. Runs tests with TESTING=true

## Common Use Cases

### 1. "My tests pass locally but fail in CI"
```bash
./ci_local_replica.sh
```

### 2. "I need to debug a complex CI failure"
```bash
./ci_debug_replica.sh --debug --verbose
```

### 3. "CI failures are intermittent and hard to reproduce"
```bash
./ci_failure_reproducer.sh --isolation=full --keep-isolation
```

### 4. "I want to compare environments"
```bash
./ci_debug_replica.sh --debug
# Check generated files in /tmp/
```

## Troubleshooting

### Python 3.11 Not Found
- Scripts will warn but continue with available Python 3.x
- For exact CI matching, install Python 3.11:
  ```bash
  sudo apt-get install python3.11 python3.11-venv python3.11-dev
  ```

### Virtual Environment Issues
- Scripts automatically recreate virtual environments
- Use `--preserve-venv` to keep existing environment

### Test Failures Still Not Reproduced
- Try maximum isolation mode
- Check CI logs for specific error messages
- Consider timing or resource constraints

## Environment Variables Set

All scripts set these CI-specific variables:
- `CI=true`
- `GITHUB_ACTIONS=true`
- `TESTING=true`
- `TEST_MODE=mock`
- `DEBUG=false`
- `RUNNER_OS=Linux`
- `RUNNER_ARCH=X64`

## Output Files

Scripts generate debug files in `/tmp/`:
- Environment snapshots
- Test output logs
- Package version comparisons
- Error analysis data

## Integration with Project

These scripts work with existing project infrastructure:
- Use project's `run_tests.sh` for test execution
- Respect project's `vpython` script
- Follow project's virtual environment conventions
- Use project's `requirements.txt`

## Success Indicators

### Tests Pass After CI Replication
- Your local environment successfully matches CI
- Any previous CI failures were environment-specific
- You can develop confidently knowing tests will pass in CI

### Tests Fail After CI Replication
- CI failure successfully reproduced locally
- You can now debug the actual issue
- Fix the problem and verify locally before pushing

## Next Steps After Running Scripts

1. **If tests pass**: Your environment now matches CI
2. **If tests fail**: Debug the reproduced failure
3. **Check output files**: Review generated logs and environment data
4. **Compare with CI logs**: Look for specific differences
5. **Iterate**: Fix issues and re-run scripts to verify

## Script Selection Guide

| Scenario | Recommended Script |
|----------|------------------|
| Quick CI check | `ci_local_replica.sh` |
| Complex debugging | `ci_debug_replica.sh --debug --verbose` |
| Hard to reproduce failures | `ci_failure_reproducer.sh --isolation=full` |
| First time user | `ci_replica_launcher.sh` |
| Environment comparison | `ci_debug_replica.sh --debug` |
| Preserve work environment | `ci_debug_replica.sh --preserve-venv` |

## Support

For issues with these scripts:
1. Check the help output: `./script_name.sh --help`
2. Review CI_REPLICA_USAGE.md for detailed documentation
3. Examine generated log files in `/tmp/`
4. Compare with actual GitHub Actions CI logs
