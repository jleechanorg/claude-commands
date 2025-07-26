# Experiment Improvements - Version 2

## Fixed Issues from First Run

### 1. Branch Confusion
**Problem**: Test subjects created their own branches instead of using experiment branches
**Solution**:
- Added explicit "CRITICAL: Stay on Current Branch" warnings
- Clear instructions to NOT create new branches
- Emphasized staying on assigned branch throughout

### 2. Missing Result Collection
**Problem**: No clear PR creation instructions for subjects
**Solution**:
- Added step-by-step completion process
- Explicit PR creation commands: `gh pr create --title "Complete development tasks"`
- Clear commit and push instructions

### 3. Evaluator Result Collection
**Problem**: No mechanism for evaluator to submit scores
**Solution**:
- Added PR creation requirement for evaluator
- Specific instructions to create `evaluation_scores.json`
- Clear completion workflow

## Updated Instructions on All Branches

### Alpha Branch (experiment-config-alpha) - Control Group
- Original CLAUDE.md (behavioral warnings)
- Updated instructions with branch discipline
- PR creation workflow added

### Beta Branch (experiment-config-beta) - Treatment Group
- Specification-based CLAUDE.md
- Updated instructions with branch discipline
- PR creation workflow added

### Eval Branch (experiment-config-eval) - Blind Evaluator
- Standardized rubric
- PR creation requirement added
- Clear scoring format specified

## Ready for Next Run

### Updated Prompts:
```
Subject A: "Please checkout branch 'experiment-config-alpha' and follow instructions"
Subject B: "Please checkout branch 'experiment-config-beta' and follow instructions"
Evaluator: "Please checkout branch 'experiment-config-eval' and follow instructions"
```

### Expected Workflow:
1. Both subjects work on their assigned branches
2. Create test_results.md with documentation
3. Submit PRs with their work
4. Coordinator collects results and anonymizes for evaluator
5. Evaluator scores and submits PR with evaluation_scores.json
6. Coordinator reveals mapping and analyzes results

### Success Indicators:
- Both subjects create PRs from correct branches
- test_results.md files contain evidence-based documentation
- Evaluator creates PR with structured JSON scores
- Clear differentiation between specification-based vs behavioral approaches

The experiment protocol is now robust and ready for execution with proper result collection mechanisms.
