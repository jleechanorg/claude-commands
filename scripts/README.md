# Development Scripts

This directory contains scripts that automate virtual environment setup for seamless development workflow.

## Quick Setup for Fresh Branches

For developers working on fresh branches from main who don't want to manually activate venv:

```bash
# One-time setup for any fresh branch
./scripts/setup-dev-env.sh
```

This automatically:
- Creates virtual environment if missing
- Installs all Python dependencies
- Sets up git hooks that work with venv
- Configures pre-commit to run automatically

## Git Hooks with Automatic Venv

After running the setup, git commits will automatically:
- Activate virtual environment
- Install missing dependencies
- Run code quality checks
- Work on any fresh branch without manual venv activation

## Available Scripts

### `setup-dev-env.sh`
Complete development environment setup for fresh branches.
- Creates venv if missing
- Installs dependencies from `mvp_site/requirements.txt`
- Sets up pre-commit hooks
- Configures everything needed for development

### `install-git-hooks.sh`
Installs enhanced git hooks that automatically handle virtual environment activation.
- Creates robust pre-commit hook
- Handles fresh branch scenarios
- Auto-installs dependencies when needed

### `venv-pre-commit.sh`
Wrapper script for pre-commit that ensures venv is activated.
- Used internally by git hooks
- Can be called directly if needed

## Usage Examples

```bash
# Fresh clone/branch setup (one-time)
git checkout -b my-feature-branch
./scripts/setup-dev-env.sh

# Normal git workflow (venv handled automatically)
git add .
git commit -m "My changes"  # Pre-commit runs automatically with venv

# Run tests (venv handled automatically)
./run_tests.sh
```

## Integration with Existing Workflow

These scripts enhance existing scripts like `run_tests.sh` which already handle venv activation. The key improvement is that git hooks now work seamlessly on fresh branches without requiring manual `source venv/bin/activate` steps.

## Benefits

- ✅ Fresh branches work immediately after `./scripts/setup-dev-env.sh`
- ✅ No more "forgot to activate venv" errors
- ✅ Git hooks work reliably across different environment
- ✅ Developers can focus on code instead of environment setup
- ✅ Compatible with existing scripts and workflow
