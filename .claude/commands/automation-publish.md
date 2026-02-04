---
description: Automation Package Publishing Command - Publish both orchestration and automation packages to PyPI
type: llm-orchestration
execution_mode: immediate
---
## EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

## CRITICAL: Both Packages Must Be Published

The `jleechanorg-pr-automation` package depends on `jleechanorg-orchestration`.
**You MUST publish BOTH packages** to ensure the CLI validation code is in sync.

## EXECUTION WORKFLOW

### Phase 1: Bump Orchestration Version

**Action Steps:**
1. Read current version from `orchestration/pyproject.toml`
2. Increment patch version (e.g., `0.1.32` → `0.1.33`)
3. Update version in `orchestration/pyproject.toml`

### Phase 2: Build and Publish Orchestration

**Action Steps:**
1. Navigate to `orchestration/` directory
2. Clean previous builds: `rm -rf dist/ build/ *.egg-info`
3. Build package: `python3 -m build`
4. Upload to PyPI: `python3 -m twine upload --repository pypi dist/jleechanorg_orchestration-*`
5. Wait 15-20 seconds for PyPI propagation

### Phase 3: Bump Automation Version

**Action Steps:**
1. Read current version from `automation/pyproject.toml`
2. Increment patch version (e.g., `0.2.112` → `0.2.113`)
3. Update version in `automation/pyproject.toml`

### Phase 4: Build and Publish Automation

**Action Steps:**
1. Navigate to `automation/` directory
2. Clean previous builds: `rm -rf dist/ build/ *.egg-info`
3. Build package: `python3 -m build`
4. Upload to PyPI: `python3 -m twine upload --repository pypi dist/jleechanorg_pr_automation-*`
5. Wait 15-20 seconds for PyPI propagation

### Phase 5: Install Both from PyPI (NOT editable)

**Action Steps:**
1. Uninstall any existing versions: `pip uninstall -y jleechanorg-orchestration jleechanorg-pr-automation`
2. Install BOTH from PyPI (specific versions):
   ```
   pip install jleechanorg-orchestration==X.Y.Z jleechanorg-pr-automation==A.B.C
   ```
3. **CRITICAL VERIFICATION** - Run from /tmp to avoid local package shadowing:
   ```
   cd /tmp && python3 -c "
   import orchestration
   import jleechanorg_pr_automation
   print('Orchestration from:', orchestration.__file__)
   print('Automation from:', jleechanorg_pr_automation.__file__)
   # Both MUST show site-packages, NOT local worktree paths
   assert 'site-packages' in orchestration.__file__, 'Orchestration not from PyPI!'
   assert 'site-packages' in jleechanorg_pr_automation.__file__, 'Automation not from PyPI!'
   print('SUCCESS: Both packages installed from PyPI')
   "
   ```

### Phase 6: Commit and Push

**Action Steps:**
1. Commit both version bumps:
   ```
   git add automation/pyproject.toml orchestration/pyproject.toml
   git commit -m "chore: Publish automation X.Y.Z and orchestration A.B.C to PyPI"
   ```
2. Push to remote: `git push origin <branch-name>`

### Phase 7: Restart PR Monitor Process

**CRITICAL**: Running Python processes don't pick up new packages automatically.
Any running `jleechanorg-pr-monitor` process must be restarted to use the new code.

**Action Steps:**
1. Kill any running pr-monitor processes:
   ```bash
   pkill -f jleechanorg-pr-monitor || true
   ```
2. Wait for processes to terminate:
   ```bash
   sleep 2
   ```
3. Verify no processes remain:
   ```bash
   pgrep -f jleechanorg-pr-monitor && echo "WARNING: Process still running" || echo "OK: No pr-monitor processes"
   ```
4. Start fresh pr-monitor with new code:
   ```bash
   nohup jleechanorg-pr-monitor --fixpr --max-prs 10 --cli-agent gemini,cursor > /tmp/pr-monitor.log 2>&1 &
   ```
5. Verify it started with new package version:
   ```bash
   sleep 3
   ps aux | grep jleechanorg-pr-monitor | grep -v grep && echo "PR Monitor restarted successfully"
   ```

## VERIFICATION CHECKLIST

After completion, verify:
- [ ] Both packages show `site-packages` path (not local worktree)
- [ ] CLI validation works: run quick test with quota-exhausted CLI
- [ ] `jleechanorg-pr-monitor --help` works

## REFERENCE DOCUMENTATION

### Purpose
Automate publishing BOTH `jleechanorg-orchestration` and `jleechanorg-pr-automation` packages:
1. Orchestration contains CLI validation code
2. Automation depends on orchestration
3. Both must be published together to stay in sync

### Why Both Packages?
- `jleechanorg-orchestration` contains `cli_validation.py` with quota detection
- `jleechanorg-pr-automation` imports from orchestration
- If only automation is published, the cron job may use stale orchestration code

### Common Failure Modes
1. **Editable install shadowing**: Local `orchestration/` directory shadows PyPI package
   - Fix: Run verification from `/tmp`, not from worktree directory
2. **PyPI propagation delay**: Package not available immediately after upload
   - Fix: Wait 15-20 seconds between upload and install
3. **Stale pip cache**: pip installs old cached version
   - Fix: Use explicit version pinning `==X.Y.Z`

### Prerequisites
- `python3` with `build` and `twine` packages installed
- PyPI credentials configured (via `PYPI_TOKEN` or `~/.pypirc`)
- Git repository with both `automation/pyproject.toml` and `orchestration/pyproject.toml`
