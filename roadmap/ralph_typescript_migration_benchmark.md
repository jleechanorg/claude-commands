# Goal: Ralph Benchmark - Complete TypeScript MCP Server Migration

**Agent**: Ralph (Standalone ralph-orchestrator system)
**Working Directory**: `/Users/jleechan/projects_other/worldai_ralph2` (ALREADY CREATED - you are working here)
**Source Reference**: `/Users/jleechan/projects/worktree_ralph` (Python implementation)
**Max Iterations**: 50
**Expected Duration**: 32-49 hours (conservative estimate)

## 🚨 REPOSITORY ALREADY CREATED

✅ **Repository Setup Complete**:
- Repository exists at `/Users/jleechan/projects_other/worldai_ralph2`
- Git initialized with initial commit
- Credentials copied to `.env` file
- You are ALREADY in the worldai_ralph2 directory

**Your First Action**: Initialize TypeScript project:
```bash
npm init -y
npm install typescript @types/node ts-node nodemon --save-dev
npm install express @google-cloud/firestore firebase-admin
npm install --save-dev @types/express jest @types/jest ts-jest
npx tsc --init --strict --esModuleInterop --resolveJsonModule
```

## Current Status

**Starting State**:
- ✅ Source Python server at `/Users/jleechan/projects/worktree_ralph/mvp_site/` (fully functional)
- ✅ Complete engineering design at `/Users/jleechan/projects/worktree_ralph/roadmap/mvp_site_typescript_migration_eng_design.md`
- ✅ All test cases at `/Users/jleechan/projects/worktree_ralph/testing_llm/`
- ❌ Target TypeScript repo `/Users/jleechan/projects_other/worldai_ralph2` does NOT exist yet
- ❌ No TypeScript MCP server implementation exists

**What Ralph Must Do**:
1. **Create** the fresh repo at `/Users/jleechan/projects_other/worldai_ralph2`
2. **Read and understand** the entire Python implementation at `/Users/jleechan/projects/worktree_ralph/mvp_site/`
3. **Study** the engineering design document for complete architecture details
4. **Implement** the TypeScript MCP server following ai_universe FastMCP patterns
5. **Validate** against ALL test cases in `/Users/jleechan/projects/worktree_ralph/testing_llm/`

## Tasks

### 🚨 Phase 0: Repository Creation (MANDATORY FIRST)
**Ralph MUST complete this phase BEFORE any coding**

1. **Create Repository Structure**:
   ```bash
   cd /Users/jleechan/projects_other
   mkdir -p worldai_ralph2
   cd worldai_ralph2
   git init
   git branch -M main
   echo "# WorldArchitect.AI TypeScript MCP Server (Ralph Build)" > README.md
   git add README.md
   git commit -m "Initial commit: Ralph TypeScript migration benchmark"
   ```

2. **Copy All Credentials**:
   ```bash
   # Copy environment configuration
   cp /Users/jleechan/projects/worktree_ralph/testing_http/testing_full/.env .env

   # Copy Firebase service account
   cp /Users/jleechan/projects/worktree_ralph/firebase-service-account.json .

   # Verify credentials exist
   if [ ! -f .env ]; then echo "❌ ERROR: .env not copied"; exit 1; fi
   if [ ! -f firebase-service-account.json ]; then echo "❌ ERROR: firebase credentials not copied"; exit 1; fi
   echo "✅ All credentials copied successfully"
   ```

3. **Initialize TypeScript Environment**:
   ```bash
   npm init -y
   npm install --save-dev typescript @types/node ts-node nodemon
   npm install express @google-cloud/firestore firebase-admin @ai-universe/mcp-server-utils
   npm install --save-dev @types/express jest @types/jest ts-jest
   npx tsc --init --strict --esModuleInterop --resolveJsonModule
   ```

### Phase 1: Architecture Study (4-6 hours)
**Location**: Work in `worldai_ralph2` repo, READ from `worktree_worker2`

1. **Read Complete Python Implementation**:
   - Study `/Users/jleechan/projects/worktree_ralph/mvp_site/services/`
   - Understand `/Users/jleechan/projects/worktree_ralph/mvp_site/routes/`
   - Analyze `/Users/jleechan/projects/worktree_ralph/mvp_site/models/`
   - Review authentication patterns in `/Users/jleechan/projects/worktree_ralph/mvp_site/auth/`

2. **Study Engineering Design**:
   - Read COMPLETE `/Users/jleechan/projects/worktree_ralph/roadmap/mvp_site_typescript_migration_eng_design.md`
   - Understand FastMCP architecture patterns
   - Review ai_universe MCP server patterns from PR #90
   - Note all API endpoints and their exact response formats

3. **Analyze Test Cases**:
   - Read ALL `.md` test files in `/Users/jleechan/projects/worktree_ralph/testing_llm/`
   - Document expected behaviors and edge cases
   - Identify critical user journeys to replicate

### Phase 2: Foundation Setup (4-6 hours)
**All work happens in** `/Users/jleechan/projects_other/worldai_ralph2`

1. **Create TypeScript Project Structure**:
   ```
   src/
   ├── server.ts              # HTTP server with FastMCP proxy
   ├── stdio-server.ts        # stdio entrypoint
   ├── createFastMCPServer.ts # FastMCP factory (ai_universe pattern)
   ├── tools/                 # MCP tool implementations
   ├── services/              # Business logic services
   ├── types/                 # TypeScript type definitions
   └── utils/                 # Utility functions
   ```

2. **Configure Firebase Admin SDK**:
   - Implement Application Default Credentials (ADC) support
   - Add service account JSON fallback
   - Test Firestore connection with production credentials
   - **Validation**: `npm run test-firebase` confirms connection

3. **Set Up FastMCP Server**:
   - Implement `createFastMCPServer()` factory following ai_universe PR #90
   - Configure Express integration with CORS
   - Set up health check endpoint
   - **Validation**: `curl http://localhost:3001/health` returns 200 OK

### Phase 3: Service Layer Migration (8-12 hours)

1. **FirestoreService.ts**:
   - Translate ALL Firestore operations from Python to TypeScript
   - Maintain exact document structure compatibility
   - Implement batch operations for game state updates
   - **Validation**: Unit tests pass for all CRUD operations

2. **GeminiService.ts**:
   - Migrate from Python Gemini SDK to TypeScript SDK
   - Replicate exact prompt formatting and response parsing
   - Implement retry logic and error handling
   - **Validation**: Test prompts generate identical responses to Python

3. **AuthService.ts**:
   - Replicate Firebase Auth validation exactly
   - Implement token verification and user ID extraction
   - Match error handling patterns from Python
   - **Validation**: Authentication tests pass with real Firebase tokens

4. **ValidationService.ts**:
   - Implement Zod schemas for all request/response types
   - Match Python validation logic exactly
   - **Validation**: Schema tests pass for all API payloads

### Phase 4: MCP Tool Implementation (10-15 hours)

1. **CampaignTool.ts** - Campaign CRUD operations:
   ```typescript
   // Endpoints to implement with EXACT Python parity
   GET    /api/campaigns              // List user campaigns
   GET    /api/campaigns/:id          // Get campaign details
   POST   /api/campaigns              // Create new campaign
   PATCH  /api/campaigns/:id          // Update campaign
   ```
   - **Validation**: Side-by-side comparison with Python responses

2. **InteractionTool.ts** - AI interaction processing:
   ```typescript
   POST   /api/campaigns/:id/interaction
   ```
   - Replicate exact narrative generation logic
   - Match Python response structure exactly
   - **Validation**: Test interactions produce comparable narrative quality

3. **ExportTool.ts** - Document generation:
   ```typescript
   GET    /api/campaigns/:id/export
   ```
   - Implement PDF/DOCX generation
   - Match Python export formats exactly
   - **Validation**: Exported documents are byte-for-byte comparable

4. **SettingsTool.ts** - User settings management:
   ```typescript
   GET    /api/settings
   POST   /api/settings
   ```
   - **Validation**: Settings CRUD operations match Python behavior

### Phase 5: Comprehensive Testing (6-10 hours)

1. **Unit Testing**:
   ```bash
   npm run test:unit
   ```
   - All service layer tests pass (100% coverage)
   - All utility function tests pass
   - All Zod schema validation tests pass

2. **Integration Testing**:
   ```bash
   npm run test:integration
   ```
   - Firestore integration tests pass with real database
   - Gemini API integration tests pass with real API
   - Firebase Auth integration tests pass with real tokens

3. **Side-by-Side Comparison Testing**:
   ```bash
   # Start Python server
   cd /Users/jleechan/projects/worktree_ralph
   python -m mvp_site.app &
   PYTHON_PID=$!

   # Start TypeScript server
   cd /Users/jleechan/projects_other/worldai_ralph2
   npm start &
   TYPESCRIPT_PID=$!

   # Run comparison tests
   npm run test:comparison

   # Cleanup
   kill $PYTHON_PID $TYPESCRIPT_PID
   ```
   - ✅ Response structures are identical (JSON comparison)
   - ✅ Response times are comparable (±20% acceptable)
   - ✅ Error responses match exactly

4. **Test Case Validation**:
   ```bash
   # Run ALL test cases from testing_llm/ directory
   for test_file in /Users/jleechan/projects/worktree_ralph/testing_llm/*.md; do
       echo "Testing: $test_file"
       npm run test:manual -- "$test_file"
   done
   ```
   - ✅ All test cases from `testing_llm/` pass
   - ✅ Campaign creation workflows work end-to-end
   - ✅ Interaction flows produce comparable narratives

### Phase 6: Production Validation (4-6 hours)

1. **MCP Server Startup**:
   ```bash
   cd /Users/jleechan/projects_other/worldai_ralph2
   npm run build
   npm start
   ```
   - ✅ Server starts without errors
   - ✅ Health endpoint responds: `curl http://localhost:3001/health`
   - ✅ No initialization errors in logs

2. **MCP Tools Listing**:
   ```bash
   # List all available MCP tools
   curl http://localhost:3001/tools
   ```
   - ✅ All tools listed: CampaignTool, InteractionTool, ExportTool, SettingsTool
   - ✅ Tool schemas match expected structure

3. **End-to-End Campaign Test**:
   ```bash
   # Create campaign
   curl -X POST http://localhost:3001/api/campaigns \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TEST_TOKEN" \
     -d '{"user_id":"test","title":"Ralph Test Campaign","setting":"fantasy"}'

   # Get campaign ID from response, then interact
   curl -X POST http://localhost:3001/api/campaigns/$CAMPAIGN_ID/interaction \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TEST_TOKEN" \
     -d '{"user_input":"I explore the dungeon"}'
   ```
   - ✅ Campaign created successfully in Firestore
   - ✅ Campaign document exists and has correct structure
   - ✅ Interaction generates narrative response
   - ✅ Story entries saved to Firestore correctly

4. **Firebase Console Verification**:
   - ✅ Login to Firebase Console
   - ✅ Verify campaign document exists in `campaigns` collection
   - ✅ Verify interaction entries exist in campaign's `story` subcollection
   - ✅ Verify all required fields present with correct types

### Phase 7: Commit and Documentation (2-4 hours)

1. **Git Commit Protocol**:
   ```bash
   cd /Users/jleechan/projects_other/worldai_ralph2
   git add -A
   git status  # Verify all files staged
   git commit -m "feat: complete TypeScript MCP server migration (Ralph build)

   - Implemented FastMCP server with ai_universe patterns
   - Migrated all Python services to TypeScript
   - Achieved 100% functional parity with Python implementation
   - All test cases from testing_llm/ passing
   - Production MCP server running with tools listed

   Tested with:
   - Campaign creation and interaction endpoints
   - Real Firebase/Gemini credentials
   - Side-by-side comparison with Python implementation
   - All $(ls /Users/jleechan/projects/worktree_ralph/testing_llm/*.md | wc -l) test cases passing"

   # Create benchmark results branch
   git checkout -b ralph-typescript-migration-complete
   git log --oneline | head -20  # Verify commit history
   ```

2. **Create Benchmark Report**:
   ```bash
   # Create detailed benchmark report
   cat > RALPH_BENCHMARK_REPORT.md << 'EOF'
   # Ralph Benchmark Results - TypeScript Migration

   **Completion Date**: $(date)
   **Total Iterations**: [actual]
   **Total Time**: [actual hours]
   **Commits**: $(git log --oneline | wc -l)

   ## Success Criteria Met
   - ✅ Production MCP TypeScript server running
   - ✅ All tools listed and functional
   - ✅ All test cases from testing_llm/ passing
   - ✅ Side-by-side comparison with Python: [X%] identical
   - ✅ Campaign creation verified in Firebase Console
   - ✅ Interaction endpoint verified with Gemini API

   ## Performance Metrics
   - Server startup time: [Xs]
   - Average response time: [Xms]
   - Test suite execution time: [Xs]
   - Lines of code: $(find src -name "*.ts" -exec wc -l {} + | tail -1)

   ## Key Learnings
   [Ralph agent's self-reported learnings]

   ## Challenges Faced
   [Ralph agent's challenges and resolutions]
   EOF

   git add RALPH_BENCHMARK_REPORT.md
   git commit -m "docs: add Ralph benchmark completion report"
   ```

## Success Criteria

### 🚨 MANDATORY Completion Requirements

Ralph CANNOT declare success until ALL criteria met:

✅ **Repository Setup**:
- Fresh repo created at `/Users/jleechan/projects_other/worldai_ralph2`
- Git initialized with commit history
- All credentials copied from source repo

✅ **Production Server Running**:
- Server starts without errors: `npm start` succeeds
- Health endpoint responds: `curl http://localhost:3001/health` returns 200
- No initialization errors in server logs

✅ **MCP Tools Listed**:
- `curl http://localhost:3001/tools` returns all tools
- CampaignTool, InteractionTool, ExportTool, SettingsTool all present

✅ **Functional Parity**:
- All Python API endpoints replicated in TypeScript
- Side-by-side comparison shows ≥95% response similarity
- Error handling matches Python behavior

✅ **Database Integration**:
- Campaign creation creates Firestore document
- Campaign document visible in Firebase Console
- Document structure matches Python implementation exactly

✅ **AI Integration**:
- Interaction endpoint calls Gemini API successfully
- Narrative generation produces quality comparable to Python
- Response structure matches Python exactly

✅ **Test Validation**:
- All unit tests pass: `npm run test:unit` exits 0
- All integration tests pass: `npm run test:integration` exits 0
- All test cases from `/Users/jleechan/projects/worktree_ralph/testing_llm/*.md` pass

✅ **End-to-End Validation**:
- Complete user journey works: signup → create campaign → interact → export
- All test scenarios from `testing_llm/` execute successfully
- No critical bugs or blocking issues

✅ **Commit and Documentation**:
- All changes committed with descriptive messages
- Git log shows clear development history
- Benchmark report created with actual metrics

## 🚨 CRITICAL: Work Evidence Requirements

Ralph MUST provide specific evidence for each success criterion:

1. **File Paths**: Exact paths to created files
2. **Line Numbers**: Where key functionality implemented
3. **Git Commits**: Commit SHAs for each major milestone
4. **Test Results**: Actual test output, not summaries
5. **API Responses**: Real curl output showing working endpoints
6. **Firebase Evidence**: Screenshot or console output showing campaign documents

## Autonomous Execution Protocol

Ralph should:

1. **Read Complete Context**:
   - Study ALL Python source code in `/Users/jleechan/projects/worktree_ralph/mvp_site/`
   - Read entire engineering design document
   - Review all test cases in `testing_llm/` directory

2. **Work Iteratively**:
   - Commit after each major component (service, tool, test suite)
   - Test after each implementation phase
   - Document decisions and challenges in RALPH.md

3. **Self-Correct Errors**:
   - When tests fail, analyze root cause systematically
   - Compare behavior with Python implementation
   - Fix issues before moving to next phase

4. **Validate Continuously**:
   - Run tests after each change
   - Verify API responses match Python
   - Check Firestore data structure after each operation

5. **Report Progress**:
   - Update RALPH_BENCHMARK_REPORT.md with metrics
   - Log key decisions and learnings
   - Document time spent on each phase

6. **Commit and Push When Complete**:
   ```bash
   git add -A
   git commit -m "feat: complete Ralph TypeScript migration benchmark"
   git branch ralph-complete-$(date +%Y%m%d)
   # Report final status with evidence
   ```

## 🚨 Iteration Limit Warning

Ralph has **maximum 50 iterations** to complete this benchmark.

**If approaching iteration limit**:
- Priority 1: Get production server running with basic tools
- Priority 2: Validate core campaign creation and interaction flows
- Priority 3: Pass critical test cases from testing_llm/
- Priority 4: Complete comprehensive testing

**DO NOT spend excessive iterations on**:
- Perfect code style or refactoring
- Over-engineering abstractions
- Premature optimization
- Non-critical edge cases

## 🚨 MANDATORY Commit Protocol

**After creating or modifying ANY file, immediately commit**:

```bash
git add <filename>
git commit -m "feat: add <filename>"
```

**Progress Validation (every 5 files)**:
1. Run: `git log --oneline | head -10`
2. Verify: `git status` shows clean
3. If untracked files exist, commit them before proceeding

**This prevents:**
- False claims of success without actual work
- Analysis paralysis without code generation
- Forgetting to track important changes

---

**Ralph: This is your benchmark. Show what you can build autonomously in 50 iterations. Good luck!**
