# Split PR Command

**Purpose**: Intelligently analyze a PR for potential splitting opportunities using file dependency analysis, commit grouping, and risk assessment.

**Usage**: `/split [branch]` or `/split` (uses current branch)

## Smart Splitting Methodology

### Pre-Analysis Checks
1. **Size Threshold**: PRs < 5 commits or < 10 files rarely benefit from splitting
2. **Coherence Check**: Single-domain changes (all frontend, all docs) usually shouldn't split
3. **Risk Assessment**: Critical security fixes might need isolation from other changes

### Analysis Framework

#### Step 1: Commit Domain Classification
Analyze each commit for logical domains:
- **Security**: auth, permissions, vulnerability fixes, validation
- **Infrastructure**: deployment, scripts, configuration, tooling  
- **Frontend**: UI components, styling, client-side logic
- **Backend**: API endpoints, business logic, database operations
- **Testing**: test files, test utilities, CI/CD improvements
- **Documentation**: README, docs, comments
- **Foundation**: type definitions, core utilities, architectural changes

#### Step 2: File Dependency Analysis
```bash
# Get all files changed in the last N commits of the current branch
# Replace N with the number of commits you want to analyze (e.g., for 5 commits, use HEAD~5..HEAD)
git show --name-only --format="" HEAD~N..HEAD | sort -u

# For each commit, map files changed (example for the last 5 commits)
git show --name-only --format="=== %h %s ===" HEAD~5..HEAD

# Identify overlapping files between commits (files touched by 2+ commits in the range)
git log --name-only --format="" HEAD~N..HEAD | sort | uniq -d
```

**Critical Check**: Files appearing in multiple commits create dependencies that affect splitting strategy.

#### Step 3: Splitting Decision Matrix

**DON'T SPLIT if**:
- < 5 commits total
- All commits in same domain
- Heavy file overlap (>50% files shared)
- Changes are tightly coupled
- Time pressure (splitting adds review overhead)

**CONSIDER SPLITTING if**:
- Multiple distinct domains represented
- Security fixes mixed with other changes
- Foundation changes that others depend on
- Independent features that can be reviewed separately
- Large PR (>15 files) with logical boundaries

**ALWAYS SPLIT if**:
- Security vulnerabilities mixed with non-critical changes
- Breaking changes mixed with safe improvements
- Emergency fixes bundled with feature work

### Splitting Strategies

#### Strategy A: Foundation-First (for dependent files)
```markdown
When files overlap between commits:
1. **Foundation PR**: Base changes that others depend on
2. **Dependent PRs**: Built on foundation, cherry-picked incrementally
```

#### Strategy B: Domain Separation (for independent changes)  
```markdown
When commits have distinct file sets:
1. **Critical Domain**: Security, breaking changes (highest priority)
2. **Feature Domain**: New functionality, improvements
3. **Infrastructure Domain**: Tooling, deployment, non-user-facing
```

#### Strategy C: Risk-Based Separation
```markdown
When mixing high and low risk changes:
1. **High Risk**: Security, breaking changes, database migrations
2. **Medium Risk**: API changes, significant refactoring
3. **Low Risk**: Documentation, tests, minor improvements
```

### Implementation Workflow

#### Phase 1: Analysis
0. Ensure working tree is clean (commit or stash local changes)
1. Check if current branch has upstream PR
2. Analyze commit history and file changes
3. Detect file overlaps and dependencies
4. Classify commits by domain and risk
5. Recommend splitting strategy or suggest keeping combined

#### Phase 2: Planning
1. Create scratchpad file in `roadmap/scratchpad_[branch].md`
2. Document file count verification (splits must sum to original)
3. Provide implementation commands for chosen strategy
4. Include dependency order and merge sequence

#### Phase 3: Execution (Optional)
- Prompt user if they want to execute the split
- Create branches according to strategy
- Cherry-pick appropriate commits to each branch (use `git cherry-pick -x` to preserve provenance)
- Push branches and create PRs with proper base branches

### File Count Verification
**MANDATORY**: All split PRs must account for every file in original PR
```bash
# Original PR files
# Replace N with the number of commits in your PR (e.g., for 8 commits, use HEAD~8..HEAD)
ORIGINAL_COUNT=$(git show --name-only --format="" HEAD~N..HEAD | sort -u | wc -l)

# Sum of split PR files (accounting for overlaps)
# Example: count unique files across all split branches relative to the base branch
# Set your base branch (defaults to origin/main)
: "${PR_BASE:=origin/main}"
# List your split branches
SPLIT_BRANCHES=(split-foundation split-security split-infra)
SPLIT_COUNT=$(
  (for b in "${SPLIT_BRANCHES[@]}"; do
     git diff --name-only "${PR_BASE}...${b}"
   done) | sort -u | wc -l
)

# Must equal: ORIGINAL_COUNT == SPLIT_COUNT
```

## Smart Recommendations

### When NOT to Split
- "Single feature across multiple commits" - keep together for atomic review
- "Refactoring + tests for same component" - logical pairing
- "Bug fix + test for the bug" - should be reviewed together
- "Documentation updates for new feature" - context helps review

### When TO Split
- "Security fix + unrelated feature work" - security needs fast track
- "Breaking API change + backward compatibility layer" - separate for gradual rollout  
- "Foundation types + features using those types" - foundation first
- "Emergency hotfix + planned improvements" - different urgency levels

### Special Cases
- **Hotfix Extraction**: Pull critical fixes from feature branches
- **Foundation Dependency**: When new utilities are used by other changes
- **Security Isolation**: Separate security fixes for faster security review
- **Review Complexity**: Split large PRs to reduce cognitive load on reviewers

## Example Output

```markdown
## Split Analysis: feature-complex-pr

### File Analysis
- **Total Files**: 12
- **Commits**: 8 commits across 3 domains

### Overlapping Files Detected
- `api.service.ts` (commits: security, foundation)
- `main.py` (commits: foundation, infrastructure)

### Recommended Strategy: Foundation-First
1. **Foundation PR**: 6 files (types, core utilities)
2. **Security PR**: 4 files (1 shared with foundation)  
3. **Infrastructure PR**: 5 files (1 shared with foundation)

**File Count**: 6 + 3 + 3 = 12 unique files ✅

### Implementation Plan
[Detailed commands for creating each PR with proper dependencies]
```

**Implementation**: Analyze current PR state, generate intelligent recommendations, create scratchpad with verified file counts and dependency-aware splitting strategy.