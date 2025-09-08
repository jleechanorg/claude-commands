# Base Development Guidelines

## Import Validation Rules (CI/CD Compliance)

### 🚨 CRITICAL: IMP002 Import Positioning Requirements

**Rule:** ALL imports must be at the absolute top of file with ZERO intervening code.

#### ❌ Pattern That FAILS (Flagged as "Inline Import")
```python
import standard_modules
sys.path.insert(0, os.path.dirname(__file__))  # ← This breaks the rule!
from local_modules import Class                 # ← Flagged as IMP002 violation
```

#### ✅ Pattern That WORKS (Compliant)
```python
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))  # Path setup with minimal imports

import standard_modules                         # All other imports grouped together
from local_modules import Class                 # Local imports immediately after
```

**Key Insight:** The import validator considers ANY code between imports as making subsequent imports "inline" - even single-line sys.path setup. The solution is to do path setup with minimal imports first, then group ALL remaining imports together.

### IMP001 Rule
- No try/except blocks around imports
- Imports must fail fast if dependencies are missing

### Best Practices
1. Group ALL imports at the very top
2. Handle path setup as single line immediately before local imports
3. No comments or logic between import groups
4. Test both local and CI environments for compatibility

## Lessons Learned

### Import Validation Miss (2025-09-08)
**What Happened:** Fixed local test failures but missed that CI import validation still showed 8 violations due to intervening code between imports.

**Root Cause:** Pattern with comments/logic between standard imports and local imports makes validator flag local imports as "inline".

**Resolution:** Simplified to single-line sys.path setup immediately before local imports.

**Memory Aid:** "ALL imports together at top, then everything else"
