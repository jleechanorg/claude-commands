# CI Environment Replica Scripts

This directory contains three comprehensive scripts designed to replicate the GitHub Actions CI environment locally for debugging CI failures.

## Scripts Overview

### 1. `ci_local_replica.sh` - Basic CI Replication
**Purpose**: Replicates the CI environment setup exactly as defined in `.github/workflows/test.yml`

**Usage**:
```bash
./ci_local_replica.sh
```

**What it does**:
- Clears environment variables that might interfere
- Sets CI-specific environment variables
- Creates fresh virtual environment
- Installs dependencies in exact CI sequence
- Runs tests using the same commands as CI

### 2. `ci_debug_replica.sh` - Enhanced CI Replication with Debug Features
**Purpose**: Advanced CI replication with debugging capabilities and verbose output

**Usage**:
```bash
./ci_debug_replica.sh [options]
```

**Options**:
- `--debug`: Enable debug mode with detailed output
- `--verbose`: Enable verbose logging
- `--clean`: Clean all temporary files and caches
- `--preserve-venv`: Don't recreate virtual environment if it exists
- `--help`: Show help message

**Examples**:
```bash
# Basic usage
./ci_debug_replica.sh

# Debug mode with verbose output
./ci_debug_replica.sh --debug --verbose

# Preserve existing virtual environment
./ci_debug_replica.sh --preserve-venv

# Clean run with debug output
./ci_debug_replica.sh --clean --debug
```

### 3. `ci_failure_reproducer.sh` - Maximum Isolation for Failure Reproduction
**Purpose**: Creates maximum isolation to reproduce CI failures locally

**Usage**:
```bash
./ci_failure_reproducer.sh [options]
```

**Options**:
- `--isolation=MODE`: Isolation mode (full, partial, minimal)
- `--python=VERSION`: Python version to use (default: 3.11)
- `--keep-isolation`: Keep isolation directory after completion
- `--skip-system-packages`: Skip system package installation
- `--help`: Show help message

**Isolation Modes**:
- `full`: Complete isolation in temporary directory
- `partial`: Isolated Python environment only
- `minimal`: Just clean virtual environment

**Examples**:
```bash
# Full isolation (recommended for CI failure reproduction)
./ci_failure_reproducer.sh --isolation=full

# Keep isolation directory for debugging
./ci_failure_reproducer.sh --isolation=full --keep-isolation

# Use specific Python version
./ci_failure_reproducer.sh --python=3.11

# Minimal isolation for quick testing
./ci_failure_reproducer.sh --isolation=minimal
```

## CI Environment Details

### GitHub Actions Configuration
Based on `.github/workflows/test.yml`:
- **OS**: Ubuntu Latest
- **Python**: 3.11
- **Environment Variables**:
  - `CI=true`
  - `GITHUB_ACTIONS=true`
  - `TESTING=true`

### Dependency Installation Sequence
1. Create virtual environment with `python -m venv venv`
2. Upgrade pip, setuptools, wheel
3. Install pinned grpcio versions: `grpcio==1.73.1 grpcio-status==1.73.1`
4. Install protobuf: `protobuf==4.25.3`
5. Install project requirements: `pip install -r mvp_site/requirements.txt`

### Test Execution
- Uses project's `run_tests.sh` script
- Sets `TESTING=true` environment variable
- Runs from project root directory

## Troubleshooting

### Common Issues

1. **Python 3.11 Not Found**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3.11-dev
   ```

2. **Virtual Environment Issues**:
   - Scripts automatically recreate virtual environments
   - Use `--preserve-venv` to keep existing environment

3. **Permission Issues**:
   ```bash
   chmod +x *.sh
   ```

4. **CI Failures Still Not Reproduced**:
   - Try `ci_failure_reproducer.sh` with full isolation
   - Check CI logs for specific error messages
   - Consider timing or resource-related issues

### Debugging CI Failures

1. **Start with Basic Replication**:
   ```bash
   ./ci_local_replica.sh
   ```

2. **If Basic Fails, Use Debug Mode**:
   ```bash
   ./ci_debug_replica.sh --debug --verbose
   ```

3. **For Stubborn Failures, Use Maximum Isolation**:
   ```bash
   ./ci_failure_reproducer.sh --isolation=full --keep-isolation
   ```

4. **Compare Environments**:
   - Check generated environment files in `/tmp/`
   - Compare package versions with CI logs
   - Look for timing or concurrency issues

## Output Files

Scripts generate various debug files in `/tmp/`:
- `ci_replica_original_env.txt`: Original environment
- `ci_replica_final_env.txt`: Final environment after setup
- `test_output_TIMESTAMP.txt`: Test execution output
- `original_env_TIMESTAMP.txt`: Environment before changes
- `final_env_TIMESTAMP.txt`: Environment after changes

## Integration with Project

These scripts integrate with the existing project structure:
- Use existing `run_tests.sh` for test execution
- Respect project's `vpython` script
- Follow project's virtual environment conventions
- Use project's requirements.txt

## When to Use Each Script

### Use `ci_local_replica.sh` when:
- You want to quickly replicate CI environment
- Basic CI failure reproduction is needed
- You're confident about the environment setup

### Use `ci_debug_replica.sh` when:
- You need detailed debugging information
- CI failures are intermittent or complex
- You want to preserve debugging information
- You need verbose output for troubleshooting

### Use `ci_failure_reproducer.sh` when:
- CI failures are not reproducible with basic replication
- You need maximum isolation from local environment
- You want to test with exact Python version
- You need to debug in a completely clean environment

## Support

For issues or questions about these scripts:
1. Check the help output: `./script_name.sh --help`
2. Review the generated log files in `/tmp/`
3. Compare with actual CI logs from GitHub Actions
4. Ensure all dependencies are installed correctly
