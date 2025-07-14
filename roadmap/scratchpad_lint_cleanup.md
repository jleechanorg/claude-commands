# Lint Cleanup Scratchpad - PR #587 Issues

## 🚨 Critical Issues Introduced by This PR

### firestore_service.py
1. **Line 33**: `import os` - **UNUSED IMPORT** (added by me, not needed)
   - Remove this line completely
   - The `os` import was moved to top but then feature flag logic was moved to main.py

2. **Line 540**: Duplicate `import os` in `add_story_entry_and_read()` function
   - This is now the only place `os` is actually used
   - Keep this one, remove the one at module top

### Specific Fix Needed
```python
# REMOVE from line 33:
import os  # ❌ Remove this

# KEEP in add_story_entry_and_read() function around line 540:
import os  # ✅ Keep this one
```

## 📋 Style Issues (Lower Priority)

### Whitespace Issues
- **50+ blank lines contain whitespace** - Clean with editor find/replace
- **Trailing whitespace** on several lines
- **Too many blank lines** in multiple locations

### Code Style  
- **F-strings missing placeholders**: 3 instances
- **Indentation issues**: Several continuation lines
- **Multiple statements on one line**: Several colon statements

## 🛠️ Quick Fixes

### Critical (Must Fix)
```bash
# Remove unused import
sed -i '33d' mvp_site/firestore_service.py  # Remove line 33 import os

# Or manually edit to remove the duplicate import at top
```

### Style Cleanup (Optional)
```bash
# Remove trailing whitespace
sed -i 's/[[:space:]]*$//' mvp_site/firestore_service.py
sed -i 's/[[:space:]]*$//' mvp_site/main.py

# Fix blank lines with whitespace
sed -i '/^[[:space:]]*$/d' mvp_site/firestore_service.py
```

## ✅ Verification After Cleanup

Run these to verify fixes:
```bash
source venv/bin/activate
flake8 mvp_site/firestore_service.py --max-line-length=120 --ignore=E501,W503,W293,E303,E302
flake8 mvp_site/main.py --max-line-length=120 --ignore=E501,W503,W293,E303,E302
```

## 📝 Root Cause

The issues were introduced when I:
1. Added `import os` to module top in firestore_service.py 
2. Then moved the feature flag logic to main.py
3. Left the unused import at the top
4. Kept the local import inside the function

**Solution**: Remove the module-level `import os` since it's not used there anymore.