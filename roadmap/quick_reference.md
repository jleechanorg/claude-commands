# Quick Reference Card

## Slash Commands

### Development Workflow
- `/tdd` or `/rg` - Test-driven development (red-green-refactor)
- `/test` - Run comprehensive test suite with reporting
- `/optimize` - Code/file optimization following user preferences
- `/integrate` - Git integration workflow (fresh branch from main)

### Project Management  
- `/milestones N` - Break work into N specific milestones
- `/milestones suggest` - Analyze and suggest optimal milestone breakdown
- `/scratchpad` - Create/update work-in-progress planning documents

### Analysis & Review
- `/context` or `/est` - Analyze current session context usage
- `/review` or `/copilot` - Process GitHub Copilot/CodeRabbit feedback

## Essential Commands

### Testing
```bash
# Run all tests
./run_tests.sh

# Run specific test (from project root)
TESTING=true vpython mvp_site/test_integration.py

# Run test method
TESTING=true vpython -m unittest mvp_site.test_module.TestClass.test_method
```

### Development
```bash
# Run application
vpython mvp_site/main.py

# Deploy
./deploy.sh         # to dev
./deploy.sh stable  # to stable
```

### Git Workflow
```bash
# Update from main (integrate pattern)
git checkout main && git pull && git branch -D dev && git checkout -b dev

# Create PR
gh pr create --title "Title" --body "Description"
```

## Key Rules

### Always From Project Root
- ❌ `cd mvp_site && vpython test.py`
- ✅ `vpython mvp_site/test.py`

### Gemini SDK
- ❌ `from google.generativeai import ...`
- ✅ `from google import genai`

### No False Green Checkmarks
- ❌ ✅ "Ready but not tested"
- ✅ ✅ "Tested and working"

## Documentation Structure

```
rules.mdc           → Primary protocol
project_overview.md → Tech details
planning_protocols.md → Planning approaches
lessons.mdc         → Recent lessons only
```

## Common Paths
- `/roadmap/` - Project planning
- `/mvp_site/` - Main application
- `/prototype/` - Experimental code
- `/.cursor/rules/` - Documentation

---
*For full details, see `.cursor/rules/rules.mdc`*