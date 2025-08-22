# Configuration Review Checklist for Review Commands

## 🚨 Critical Configuration Checks

### Hook Registration Verification
```bash
# Check all hook files
for hook in .claude/hooks/*.{py,sh}; do
  hook_name=$(basename "$hook")
  if ! grep -q "$hook_name" .claude/settings.json; then
    echo "❌ UNREGISTERED: $hook_name not in settings.json"
  fi
done
```

### GitHub Actions Workflow Checks
- [ ] All new actions use SHA-pinned versions
- [ ] Workflow files reference all necessary scripts
- [ ] Environment variables properly configured

### Integration Points
- [ ] New files registered in appropriate config files
- [ ] API endpoints added to route mappings
- [ ] Database migrations included if schema changed
- [ ] Test files added to test suite configuration

### Claude-Specific Checks
- [ ] `.claude/hooks/*` → Registered in `.claude/settings.json`
- [ ] `.claude/triggers/*` → Referenced by appropriate hooks
- [ ] `.claude/commands/*` → Documented in slash_commands.md
- [ ] Memory MCP entities → Proper schema and relations

### Deployment Readiness
- [ ] All configuration files updated
- [ ] Environment variables documented
- [ ] Dependencies added to requirements.txt/package.json
- [ ] CI/CD pipeline updated if needed

## Integration Verification Pattern

**For ANY new file added:**
1. ❓ Does this file need registration somewhere?
2. ❓ What config file should reference it?
3. ❓ Will it execute automatically or need manual setup?
4. ❓ Are there cross-file dependencies?

## Examples of Common Misses

### Hook Registration Miss
```
Created: .claude/hooks/my_hook.py ✅
Registered: .claude/settings.json ❌ MISSED!
Result: Hook never executes
```

### Route Registration Miss
```
Created: mvp_site/api/new_endpoint.py ✅
Registered: mvp_site/main.py routes ❌ MISSED!
Result: Endpoint unreachable
```

### Test Registration Miss
```
Created: mvp_site/tests/test_new_feature.py ✅
Registered: Test discovery pattern ❌ MISSED!
Result: Tests never run
```

## Review Command Enhancement

The `/reviewdeep` command should add:
```python
import json, os, glob
from pathlib import Path
from typing import Iterable, Any, Set, List

def _iter_strings(node: Any) -> Iterable[str]:
    """Recursively extract all string values from a nested structure."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _iter_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_strings(v)

def check_configuration_consistency(
    hooks_dir: str = ".claude/hooks",
    settings_path: str = ".claude/settings.json",
) -> List[str]:
    """Check if all hook files are registered in settings.json."""
    issues: List[str] = []
    hook_paths = glob.glob(os.path.join(hooks_dir, "*.py")) + glob.glob(os.path.join(hooks_dir, "*.sh"))
    hook_names: Set[str] = {Path(p).name for p in hook_paths}

    if not os.path.exists(settings_path):
        return [f"{settings_path} not found"]

    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    # Extract all hook references from settings
    registered: Set[str] = {
        Path(s).name
        for s in _iter_strings(settings)
        if ".claude/hooks/" in s or s.startswith("hooks/")
    }

    # Check for unregistered hooks
    for name in sorted(hook_names):
        if name not in registered:
            issues.append(f"Hook {name} not registered in {settings_path}")

    return issues
```

## Lesson Learned

**Review commands must check not just code quality, but also:**
- Configuration completeness
- Integration wiring
- Cross-file dependencies
- Deployment readiness

This would have caught the missing hook registration immediately!