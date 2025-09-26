# Repository Scaffolding Command

## Overview
This command scaffolds essential development scripts from the claude-commands repository into any target repository and provides intelligent adaptation instructions to the LLM.

## Command Logic

1. **Copy Core Scripts**: Copy the following scripts from claude-commands to the target repository:

   ### Root Level Scripts:
   - `create_worktree.sh` → Copy to project root
   - `integrate.sh` → Copy to project root
   - `schedule_branch_work.sh` → Copy to project root

   ### Scripts Directory:
   - `claude_mcp.sh` → Copy to `scripts/`
   - `claude_start.sh` → Copy to `scripts/`
   - `codebase_loc.sh` → Copy to `scripts/`
   - `coverage.sh` → Copy to `scripts/`
   - `create_snapshot.sh` → Copy to `scripts/`
   - `loc.sh` → Copy to `scripts/`
   - `loc_simple.sh` → Copy to `scripts/`
   - `push.sh` → Copy to `scripts/`
   - `resolve_conflicts.sh` → Copy to `scripts/`
   - `run_lint.sh` → Copy to `scripts/`
   - `run_tests_with_coverage.sh` → Copy to `scripts/`
   - `setup-github-runner.sh` → Copy to `scripts/`
   - `setup_email.sh` → Copy to `scripts/`
   - `sync_branch.sh` → Copy to `scripts/`

## Execution Instructions

When this command is run:

```bash
# 1. Create scripts directory if it doesn't exist
mkdir -p scripts

# 2. Copy all specified scripts from claude-commands repository
# Note: Replace CLAUDE_COMMANDS_PATH with actual path to claude-commands repo
cp "$CLAUDE_COMMANDS_PATH/create_worktree.sh" ./
cp "$CLAUDE_COMMANDS_PATH/integrate.sh" ./
cp "$CLAUDE_COMMANDS_PATH/schedule_branch_work.sh" ./

cp "$CLAUDE_COMMANDS_PATH/scripts/claude_mcp.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/claude_start.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/codebase_loc.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/coverage.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/create_snapshot.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/loc.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/loc_simple.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/push.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/resolve_conflicts.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/run_lint.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/run_tests_with_coverage.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/setup-github-runner.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/setup_email.sh" ./scripts/
cp "$CLAUDE_COMMANDS_PATH/scripts/sync_branch.sh" ./scripts/

# 3. Make all scripts executable
chmod +x *.sh scripts/*.sh
```

## LLM Adaptation Instructions

After copying the scripts, the LLM should analyze the target repository and adapt the scripts according to these guidelines:

### 1. **Technology Stack Detection**
- Examine `package.json`, `Cargo.toml`, `requirements.txt`, `go.mod`, etc.
- Identify the primary programming language and framework
- Detect testing frameworks (Jest, pytest, Go test, etc.)
- Identify linting tools (ESLint, pylint, golangci-lint, etc.)

### 2. **Script Adaptations Required**

#### `run_lint.sh` adaptations:
- **Node.js/TypeScript**: Update to use `npm run lint` or `npx eslint`
- **Python**: Update to use `flake8`, `black`, `ruff`, or `pylint`
- **Go**: Update to use `golangci-lint run`
- **Rust**: Update to use `cargo clippy`
- **Java**: Update to use `checkstyle` or `spotbugs`

#### `run_tests_with_coverage.sh` adaptations:
- **Node.js/TypeScript**: Update to use `npm test` with `jest --coverage` or `nyc`
- **Python**: Update to use `pytest --cov=.` or `coverage run -m pytest`
- **Go**: Update to use `go test -coverprofile=coverage.out ./...`
- **Rust**: Update to use `cargo test` with `cargo tarpaulin`
- **Java**: Update to use Maven/Gradle with JaCoCo

#### `coverage.sh` adaptations:
- Update coverage report generation commands based on detected tools
- Update coverage report paths and formats
- Configure coverage thresholds appropriate for the project

### 3. **Repository-Specific Customizations**

#### CI/CD Integration:
- If `.github/workflows/` exists, suggest integrating scripts into GitHub Actions
- If `.gitlab-ci.yml` exists, suggest GitLab CI integration
- If other CI systems detected, provide appropriate integration suggestions

#### Git Hooks:
- Suggest setting up pre-commit hooks using `setup-github-runner.sh` as a template
- Adapt hook scripts to run the repository's specific linting and testing commands

#### Documentation Updates:
- If `README.md` exists, suggest adding a "Development Scripts" section
- Document how to run each script and what it does
- Provide examples of common development workflows

### 4. **Configuration File Updates**

#### Package Manager Scripts:
- **Node.js**: Add script shortcuts to `package.json` scripts section
- **Python**: Suggest adding scripts to `pyproject.toml` or `setup.py`
- **Rust**: Add script shortcuts to `Cargo.toml`

#### Example `package.json` additions:
```json
{
  "scripts": {
    "scaffold:lint": "./scripts/run_lint.sh",
    "scaffold:test": "./scripts/run_tests_with_coverage.sh",
    "scaffold:coverage": "./scripts/coverage.sh",
    "scaffold:loc": "./scripts/loc.sh"
  }
}
```

### 5. **Environment Variable Configurations**
- Update scripts to use repository-specific environment variables
- Configure paths relative to the project structure
- Update any hardcoded references to be configurable

### 6. **Dependencies and Prerequisites**
- Check if required tools are installed (git, curl, etc.)
- Suggest installation commands for missing dependencies
- Provide alternative implementations for missing tools

## Post-Scaffolding Checklist

After running the scaffold command, the LLM should:

1. ✅ Test each adapted script to ensure it works with the target repository
2. ✅ Create or update documentation explaining the scaffolded scripts
3. ✅ Suggest which scripts should be integrated into CI/CD pipelines
4. ✅ Identify any additional scripts that might be needed for this specific project
5. ✅ Recommend a development workflow using the scaffolded scripts

## Usage Example

```bash
# Run the scaffold command in any repository
/scaffold

# The LLM will:
# 1. Copy all the scripts from claude-commands
# 2. Analyze the target repository
# 3. Adapt scripts to match the technology stack
# 4. Update configurations and documentation
# 5. Provide guidance on usage and integration
```

## Benefits

- **Consistency**: Standardized development scripts across all repositories
- **Productivity**: Common development tasks automated and accessible
- **Quality**: Consistent linting, testing, and coverage practices
- **Flexibility**: Scripts adapted to each repository's specific needs
- **Knowledge Transfer**: Best practices embedded in every scaffolded repository