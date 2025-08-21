# Plan Command - Execute with Approval

**Purpose**: Same as `/execute` but requires user approval before implementation. **OPTIMIZED FOR MAXIMUM /CEREBRAS CODE GENERATION BATCHING** to leverage 19.6x speed advantage.

**Usage**: `/plan` - Present execution plan with maximum coding work batched for /cerebras

## 🚀 MAXIMUM /CEREBRAS BATCHING STRATEGY (PRIMARY FOCUS)

**REVOLUTIONARY SPEED**: /cerebras can generate code up to 19.6x faster (e.g., 500ms vs 10s in example scenarios) – this is the PRIMARY optimization target. *Note: These metrics are based on internal observations and may vary depending on workload and environment.*

### Batch-First Workflow Philosophy
**The planning process MUST prioritize identifying and batching ALL possible coding work for /cerebras upfront**:

1. **📋 CODING TASK INVENTORY** (First Step - MANDATORY):
   - **Scan the entire task** for ANY code generation opportunities
   - **Group similar coding tasks** that can be generated together
   - **Identify boilerplate patterns** that /cerebras excels at
   - **List ALL files/functions/classes** that need creation or major modification

2. **🎯 MAXIMUM BATCH IDENTIFICATION**:
   - **New file creation** - Perfect for /cerebras with detailed specs
   - **Function implementations** - Batch multiple functions with clear interfaces
   - **Test generation** - Batch ALL tests for multiple modules
   - **Data structures** - Create multiple related classes/interfaces
   - **Configuration files** - Generate multiple config variations
   - **Documentation** - Batch documentation for multiple components

3. **⚡ BATCH EXECUTION STRATEGY**:
   - **Front-load ALL /cerebras implementation tasks** ahead of any Claude implementation
   - Perform only minimal Claude analysis/spec creation required to enable /cerebras batching
   - **Generate code in logical groups** (all models, all tests, all configs)
   - **Minimize context switching** between generation and analysis
   - **Parallel generation** when possible for independent components

## 🚨 CRITICAL: SERENA MCP USAGE FOR PR WORK

**MANDATORY for Large PRs (50+ files)**: When working on PR analysis or fixes, ALWAYS use Serena MCP tools as primary approach:

### Serena MCP First Protocol
1. **❌ NEVER start by reading entire files** - This wastes context immediately
2. **✅ ALWAYS use Serena semantic tools first**:
   - `mcp__serena__find_symbol` - Target specific functions/classes
   - `mcp__serena__get_symbols_overview` - Understand file structure
   - `mcp__serena__search_for_pattern` - Find code patterns efficiently
   - `mcp__serena__find_referencing_symbols` - Track dependencies

### Example PR Fix Workflow
```bash
# ❌ WRONG: Reading entire files
Read --file_path="mvp_site/frontend_v2/src/App.tsx"  # Wastes 1000+ lines of context!

# ✅ RIGHT: Targeted Serena analysis
mcp__serena__search_for_pattern --pattern="\\(campaign as any\\)" --restrict_search_to_code_files=true
mcp__serena__find_symbol --name_path="handleCampaignCreate" --include_body=true
```

### Context Preservation Rules
- **First 20% of context**: Use Serena for analysis and discovery
- **Middle 60% of context**: Apply targeted fixes using Edit/MultiEdit
- **Final 20% of context**: Verification and testing
- **If context < 30%**: Split task or summarize findings

## 🧠 MEMORY INTEGRATION

**Enhanced Planning with Memory MCP**: `/plan` automatically consults Memory MCP before creating execution plans to apply learned patterns, user preferences, and corrections.

### Pre-Planning Memory Query
- **Automatic Consultation**: Queries learned patterns relevant to the task
- **Pattern Categorization**: Groups findings by type (corrections, preferences, workflows)
- **Context Integration**: Applies memory insights to planning decisions
- **Execution Strategy**: Uses memory patterns to inform parallel vs sequential choices

## 📋 GUIDELINES INTEGRATION

**Mistake Prevention System**: `/plan` automatically checks for and applies guidelines from `docs/pr-guidelines/base-guidelines.md` to prevent recurring mistakes.

### Pre-Planning Guidelines Check

**Systematic Mistake Prevention**: This command automatically consults the mistake prevention guidelines system by calling `/guidelines` directly.

**Direct Command Composition**:
1. **Execute `/guidelines`**: Call the guidelines command for comprehensive consultation
2. **Guidelines automatically handles**:
   - Read CLAUDE.md for current rules, constraints, and protocols (MANDATORY)
   - Read base guidelines from `docs/pr-guidelines/base-guidelines.md`
   - Detect PR/branch context using GitHub API, branch name patterns, and fallbacks
   - Create/read specific guidelines:
     * PR-specific: `docs/pr-guidelines/{PR_NUMBER}/guidelines.md`
     * Branch-specific: `docs/branch-guidelines/{BRANCH_NAME}/guidelines.md`  
     * Base-only: `docs/pr-guidelines/base-guidelines.md`
   - Apply guidelines context to inform planning approach
3. **Proceed with planning workflow** using guidelines context from `/guidelines` output

**Guidelines Integration**: Direct command composition - `/plan` calls `/guidelines` directly for clean separation of concerns and reliable guidelines consultation.

## 🚨 PLAN PROTOCOL

### Phase 1: /CEREBRAS BATCH INVENTORY (PRIMARY STEP - MANDATORY)

**🚀 MAXIMUM CODE GENERATION BATCHING CHECKLIST**:
```
## /CEREBRAS BATCHING PROTOCOL - SPEED-OPTIMIZED PLANNING
- [ ] 📋 COMPLETE CODING TASK INVENTORY: ✅ MANDATORY FIRST STEP
  *Required*: List EVERY possible code generation opportunity in the task
  *Examples*: New files, functions, classes, tests, configs, documentation
  *Guideline*: Aim to batch at least 80% of coding work to /cerebras, as maximizing batching leverages the 19.6x speed advantage. This percentage is a recommended target based on observed efficiency gains, but use your judgment for complex or edge cases.
- [ ] 🎯 BATCH GROUPING STRATEGY:
  - [ ] File creation batches: Group related new files
  - [ ] Function implementation batches: Group similar functions
  - [ ] Test generation batches: Group tests by module/feature
  - [ ] Configuration batches: Group related config files
  - [ ] Documentation batches: Group docs by component
- [ ] ⚡ SPEED OPTIMIZATION ANALYSIS:
  - [ ] Estimated /cerebras tasks: _____ (aim for maximum possible)
  - [ ] Estimated Claude tasks: _____ (minimize to analysis/integration only)
  - [ ] Speed benefit calculation: _____
    *Guidance*: Estimate speed benefit by considering:
      - Baseline /cerebras speedup (e.g., 19.6x for simple tasks)
      - Average task complexity (simple/complex/mixed)
      - Context switching overhead (e.g., time lost switching between tools or batches)
      - Integration time (e.g., time to merge, test, and validate batched outputs)
    *Suggested formula*: 
      Estimated speed benefit = (Baseline speedup × /cerebras task count × Complexity factor) - (Context switching overhead + Integration time)
    *Note*: Adjust 'Complexity factor' (e.g., 1 for simple, <1 for complex tasks). Document assumptions.
  - [ ] Batching efficiency: High/Medium/Low (aim for High)
- [ ] Guidelines consultation completed: ✅ `/guidelines` command executed successfully
- [ ] Anti-patterns avoided: Reference historical mistakes and solutions
- [ ] Memory consultation completed: ✅ YES
- [ ] Memory insights applied: [Count] relevant patterns found
- [ ] Context check: ___% remaining
- [ ] Complexity assessment: Simple/Complex (memory and guidelines informed)
- [ ] Tool selection validated: Serena MCP → Read tool → Bash → /cerebras (per guidelines)
- [ ] /cerebras delegation analysis: ✅ MANDATORY - Identified which parts suit /cerebras vs Claude
  *Required*: Must explicitly list tasks for /cerebras (well-specified generation) vs Claude (understanding/integration)
  *Reference*: Read CLAUDE.md "CEREBRAS-FIRST CODING PROTOCOL" section for 10-line threshold rule and delegation patterns
  *10-Line Rule*: Tasks >10 delta lines MUST use Cerebras API, ≤10 lines can use Claude direct
  *Decision Log*: Document all /cerebras delegation decisions in cerebras_decisions.md
- [ ] Execution method decision: /cerebras-First → Parallel → Sequential
  *Priority*: /cerebras batching takes precedence over parallelization decisions
  *Reference*: See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for decision criteria
- [ ] **🚀 /CEREBRAS BATCH EXECUTION PLAN** presented to user
- [ ] User approval received
```

❌ **NEVER proceed without explicit user approval marked as checked (`[x]`) in the checklist**

### Phase 2: Present Execution Plan

## 📋 /CEREBRAS-OPTIMIZED Plan Display Format

*This format prioritizes maximum code generation batching for 19.6x speed advantage.*

**🚀 /CEREBRAS-FIRST EXECUTION PLAN**:
- **Task complexity**: Simple (direct execution) or Complex (coordination needed)
- **📋 CODING TASK INVENTORY** (PRIMARY SECTION):
  - **Total coding tasks identified**: _____ tasks
  - **Batchable for /cerebras**: _____ tasks (aim for 80%+)
  - **Requires Claude analysis**: _____ tasks (minimize)
  - **Speed multiplier**: _____ (19.6x × /cerebras task percentage)

- **🎯 /CEREBRAS BATCH EXECUTION STRATEGY** (MANDATORY):
  - **Batch Group 1 - File Creation** (500ms each vs 10s):
    * List all new files to generate with detailed specs
    * Example: "User.py class with auth methods", "UserTest.py with 15 test cases"
  - **Batch Group 2 - Function Implementation** (500ms each vs 10s):
    * List functions to implement with clear interfaces
    * Example: "calculate_damage(), validate_input(), format_response()"
  - **Batch Group 3 - Test Generation** (500ms each vs 10s):
    * List test suites to generate
    * Example: "Integration tests for auth module", "Unit tests for utilities"
  - **Batch Group 4 - Configuration/Documentation** (500ms each vs 10s):
    * List configs and docs to generate
    * Example: "API documentation", "Docker configs", "Environment setup"

- **⚡ CLAUDE INTEGRATION TASKS** (Minimal - for analysis/integration only):
  - **Pre-generation analysis**: Understand existing codebase structure
  - **Spec creation**: Create detailed specifications for /cerebras
  - **Post-generation integration**: Integrate generated code into existing system
  - **Quality validation**: Review and test integrated solution

- **🚀 EXECUTION SEQUENCE** (/cerebras-optimized):
  1. **Quick Analysis Phase** (Claude): Minimal codebase understanding
  2. **Spec Creation Phase** (Claude): Detailed /cerebras specifications
  3. **MASS GENERATION Phase** (/cerebras): Execute ALL batches in parallel
  4. **Integration Phase** (Claude): Integrate and validate results

- **Expected timeline**: _____ (/cerebras batching saves _____ minutes vs traditional approach)

**Parallel Tasks Plan (if applicable)**:
- **Method**: Background processes (&), GNU parallel, xargs, or batched calls
- **Tasks**: List of independent operations to run in parallel
- **Aggregation**: How results will be combined

**Sequential Task Plan (if applicable)**:
- **Main task**: What I'll focus on
- **Task 1**: Independent analysis/research task
- **Task 2**: Documentation/testing task
- **Integration**: How results will be combined

### Phase 3: Wait for Approval

**User must explicitly approve the plan before execution**

### Phase 4: Execute Same Protocol as `/execute`

**After approval, follows identical execution protocol as `/execute`**:
- Use available tools systematically
- Execute tasks as planned (parallel or sequential)
- Work through implementation
- Integrate results and commit

## Example Flow

**`/plan` Flow** (/cerebras-optimized):
```
User: /plan implement user authentication system
Assistant: I'll create a /cerebras-optimized plan for implementing user authentication system.

[Uses /CEREBRAS BATCH INVENTORY protocol]

🚀 /CEREBRAS-FIRST EXECUTION PLAN:

📋 CODING TASK INVENTORY:
- Total coding tasks identified: 12 tasks
- Batchable for /cerebras: 10 tasks (83% - EXCELLENT batching efficiency)
- Requires Claude analysis: 2 tasks (minimal)
- Speed multiplier: 16.3x (19.6x × 83%)  
  *Note: Actual speedup may be lower due to integration overhead and context switching. This is an estimated upper bound.*

🎯 /CEREBRAS BATCH EXECUTION STRATEGY:
- **Batch Group 1 - Authentication Classes** (5 files, ~2.5 seconds vs 50 seconds):
  * User.py with login/logout methods
  * Session.py with session management
  * AuthValidator.py with input validation
  * PasswordUtils.py with hashing utilities
  * AuthExceptions.py with custom exceptions

- **Batch Group 2 - Test Suites** (3 test files, ~1.5 seconds vs 30 seconds):
  * test_user_auth.py with 15 test cases
  * test_session_management.py with 10 test cases  
  * test_auth_validators.py with 8 test cases

- **Batch Group 3 - Configuration** (2 files, ~1 second vs 20 seconds):
  * auth_config.py with security settings
  * auth_routes.py with Flask routes

⚡ CLAUDE INTEGRATION TASKS:
- Analyze existing Flask app structure (2 minutes)
- Integrate auth system with existing database (8 minutes)

🚀 EXECUTION SEQUENCE:
1. Quick Analysis (2 min): Understand current Flask structure
2. Spec Creation (3 min): Create detailed /cerebras specifications  
3. MASS GENERATION (5 min): Execute all 3 batches via /cerebras
4. Integration (8 min): Integrate with existing Flask app

**⏱️ Time Savings Calculation Breakdown**

| Task Group                | Traditional Time | /cerebras Batch Time |
|--------------------------|------------------|------------------|
| Auth Classes (5 files)   | 50 seconds       | 2.5 seconds      |
| Test Suites (3 files)    | 30 seconds       | 1.5 seconds      |
| Config Files (2 files)   | 20 seconds       | 1 second         |
| Analysis                 | 2 minutes        | 2 minutes        |
| Integration              | 8 minutes        | 8 minutes        |
| Spec Creation            | 3 minutes        | 3 minutes        |
| **TOTAL**                | **~14 min 40 sec**| **~18 min**      |

- **Traditional Total:**  
  - Auth Classes: 50s  
  - Test Suites: 30s  
  - Config Files: 20s  
  - Analysis: 2m  
  - Integration: 8m  
  - Spec Creation: 3m  
  - **Total:** 50s + 30s + 20s = 100s = 1m 40s  
    1m 40s + 2m + 8m + 3m = **14m 40s**

- **/cerebras Batch Total:**  
  - Auth Classes: 2.5s  
  - Test Suites: 1.5s  
  - Config Files: 1s  
  - Analysis: 2m  
  - Integration: 8m  
  - Spec Creation: 3m  
  - **Total:** 2.5s + 1.5s + 1s = 5s  
    5s + 2m + 8m + 3m = **13m 5s** (rounded up to ~18m for planning overhead)

- **Time Saved:**  
  - Traditional: ~55 minutes (if each file/test/config is done sequentially at 10s/file, 10s/test, 10s/config)  
  - /cerebras Batch: ~5 seconds for all code generation  
  - **Total Savings:** ~37 minutes (55m - 18m = 37m)

Timeline: ~18 minutes (/cerebras batching saves ~37 minutes vs traditional approach)

[Waits for user approval]

User: Approved  
Assistant: [Executes /cerebras-first protocol]
```

## Key Characteristics

- ✅ **🚀 /cerebras batch inventory required** (PRIMARY)
- ✅ **Maximum code generation batching** for 19.6x speed advantage
- ✅ **User approval required** before execution
- ✅ **/cerebras-optimized plan presentation** with speed analysis
- ✅ **Same execution protocol** as `/execute` after approval
- ✅ **Speed-first execution method** – "/cerebras batching → [rationale]" prioritized over parallelization
- ✅ **Batch efficiency metrics** – percentage of work delegated to /cerebras with time savings calculation

## 🚀 /QWEN BATCHING DECISION CRITERIA

**PERFECT for /cerebras** (Always batch these):
- ✅ **New file creation** with clear specifications
- ✅ **Function implementations** with defined interfaces
- ✅ **Test generation** for known code structures
- ✅ **Data structures** (classes, interfaces, schemas)
- ✅ **Configuration files** with specified parameters
- ✅ **Documentation** with clear scope and format
- ✅ **Boilerplate code** (templates, repetitive patterns)
- ✅ **Code generation from specifications** (API clients, etc.)

**REQUIRES Claude** (Cannot batch):
- ❌ **Understanding existing complex codebases**
- ❌ **Debugging with context analysis**
- ❌ **Refactoring decisions** based on existing code
- ❌ **Security-critical implementation decisions**
- ❌ **Integration with complex existing systems**
- ❌ **Performance optimization** requiring profiling

**HYBRID APPROACH** (Claude specs → /cerebras generates):
- 🔄 **Complex algorithms** (Claude designs, /cerebras implements)
- 🔄 **Database schemas** (Claude analyzes needs, /cerebras creates)
- 🔄 **API implementations** (Claude designs interface, /cerebras codes)

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant past planning approaches, execution patterns, and lessons learned to enhance plan quality and accuracy. See CLAUDE.md Memory Enhancement Protocol for details.
