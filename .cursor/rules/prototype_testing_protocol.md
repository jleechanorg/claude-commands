# Prototype Testing Protocol

## Standard Testing Approach

### Always Run From Project Root

**CRITICAL**: All Python tests for the prototype must be run from the project root directory to ensure proper import resolution.

### Import Pattern

```python
# At the start of any test file:
import sys
import os

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import prototype modules as a package
import prototype.validator as validator
import prototype.validators.token_validator as token_validator
# etc.
```

### Why This Works

1. **Package Structure**: The prototype uses relative imports (`from ..validator import`)
2. **Python Resolution**: Python needs to understand the package hierarchy
3. **Project Root**: Running from root allows Python to see `prototype` as a package
4. **Absolute Imports**: We import using `prototype.module` syntax

### Testing Commands

```bash
# Always from project root:
python3 test_prototype_working.py

# With vpython (if available):
vpython test_prototype_working.py

# With environment variable:
TESTING=true python3 test_prototype_working.py
```

### What NOT to Do

- ❌ Don't run tests from within the prototype directory
- ❌ Don't use relative imports in test files
- ❌ Don't try to fix the relative imports in the prototype code
- ❌ Don't run files directly with `python3 prototype/some_file.py`

### Standard Test Template

```python
#!/usr/bin/env python3
"""Test description"""

import sys
import os

# Setup imports from project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import as package
import prototype.validators.token_validator as token_validator

# Run tests...
```

### Key Insight

The prototype's relative imports are not a bug - they're a proper package structure. The solution is to always treat it as a package by running from the project root, not to "fix" the imports.