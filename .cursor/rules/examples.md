# CLAUDE.md Examples

## Git Workflow Examples

### Commit Message Format
```
M{milestone} Step {step}.{sub_bullet}: {Brief description}

- {Implementation detail 1}
- {Key result or finding}
- Saved progress to tmp/milestone_{milestone}_step_{step}.{sub_bullet}_progress.json

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Safe Branch Creation Pattern
```bash
git checkout main
git pull origin main
git checkout -b feature-branch-name
# This creates an untracked branch, forcing explicit remote setup
```

## Code Examples

### Import Statements (Correct)
```python
# All imports at top of file
import os
import sys
from typing import Dict, List

import flask
from firebase_admin import firestore

from game_state import GameState
from numeric_field_converter import NumericFieldConverter
```

### Import Statements (Incorrect)
```python
def process_data():
    import json  # ❌ NEVER import inside functions
    return json.dumps(data)

class MyClass:
    def method(self):
        from utils import helper  # ❌ NEVER import inside methods

if condition:
    import special_module  # ❌ NEVER conditional imports
```

### Python Execution (Correct)
```bash
# From project root
python3 prototype/some_file.py
vpython mvp_site/test_file.py
TESTING=true vpython mvp_site/test_integration.py
```

### Python Execution (Incorrect)
```bash
cd prototype && python3 file.py  # ❌ Breaks imports
cd mvp_site && python3 test.py   # ❌ Breaks imports
```

## Testing Examples

### User Request Analysis
User says "run tests" → Check if feature is integrated → If not, say "The feature needs integration first. Should I integrate it before testing?"

### Temporary Fix Example
❌ BAD: "I copied the files, deployment works now"
✅ GOOD: "⚠️ TEMPORARY FIX: I manually copied world/ to fix deployment. This WILL BREAK on next deploy from fresh clone. Creating permanent fix to deploy.sh now..."

## Slash Command Response Examples

### /context Response
```
Session Context Usage: ~75-85% used
- System messages: ~10-15%
- File operations: ~30-40%
- Conversation: ~25-35%
- Tool outputs: ~10-15%

Remaining: ~15-25% (good for a few more operations)
Recommendation: Approaching limits, consider fresh session for major work
```

### /milestones Response
```
Based on task complexity, I suggest 4 milestones:

Milestone 1: Foundation Setup (Low complexity)
- Set up base infrastructure
- Create initial test framework
- Success: Basic tests passing

Milestone 2: Core Implementation (High complexity)
- Implement main feature logic
- Add error handling
- Success: Feature works end-to-end

Milestone 3: Integration (Medium complexity)
- Connect to existing systems
- Update documentation
- Success: Feature integrated with main app

Milestone 4: Polish & Deploy (Low complexity)
- Add edge case handling
- Performance optimization
- Success: Production-ready code
```

## Markdown Output Example
When asked for "markdown format", provide raw unrendered text in code block:
```markdown
# Example PR Description
- Change 1
- Change 2
```

## Empty String Handling
❌ BAD: `if value:` - Skips empty strings which may be valid
✅ GOOD: `if value is not None:` - Preserves empty strings
