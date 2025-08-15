# V2 Planning Blocks Implementation Roadmap

**Created**: 2025-08-15  
**Purpose**: Detailed implementation strategy for V2 planning blocks based on PR #1221/#1270 analysis  
**Status**: 🎯 READY FOR EXECUTION

## Table of Contents

### Strategic Analysis
1. [Strategic Approach: Split from PR #1270](#-strategic-approach-split-from-pr-1270-updated-recommendation)
2. [Complete Open PR Analysis & Decisions](#-complete-open-pr-analysis--decisions)
3. [Revised Execution Strategy](#-revised-execution-strategy)

### Implementation Plan  
4. [Optimal PR Splitting Strategy (FROM PR #1270)](#-optimal-pr-splitting-strategy-from-pr-1270)
   - [Phase 1: Infrastructure & Types (PR A)](#phase-1-infrastructure--types-pr-a---foundation)
   - [Phase 2A: Planning Block Component (PR B)](#phase-2a-planning-block-component-pr-b---core-feature)  
   - [Phase 2B: API Services (PR C)](#phase-2b-api-services-pr-c---backend-integration)
   - [Phase 3: UI Integration (PR D)](#phase-3-ui-integration-pr-d---component-assembly)
   - [Phase 4: Testing & Documentation (PR E)](#phase-4-testing--documentation-pr-e---validation)

### Execution Details
5. [Updated Implementation Execution Plan](#-updated-implementation-execution-plan-pr-1270-splitting)
6. [Success Criteria & Validation](#-success-criteria--validation)
7. [Risk Mitigation](#-risk-mitigation)
8. [Parallel Development Opportunities](#-parallel-development-opportunities)
9. [Final Implementation Checklist](#-final-implementation-checklist-pr-1270-splitting)

### Technical Details
10. [Detailed File-by-File Breakdown for Each Split PR](#-detailed-file-by-file-breakdown-for-each-split-pr)
    - [Phase 1: Infrastructure & Types PR](#-phase-1-infrastructure--types-pr---foundation-layer)
    - [Phase 2A: Planning Block Component PR](#-phase-2a-planning-block-component-pr---core-feature)
    - [Phase 2B: API Services PR](#-phase-2b-api-services-pr---backend-integration)
    - [Phase 3: UI Integration PR](#-phase-3-ui-integration-pr---component-assembly)
    - [Phase 4: Testing & Documentation PR](#-phase-4-testing--documentation-pr---validation)
11. [4-Phase Splitting Rationale](#-summary-4-phase-splitting-rationale)

---  

## 🎯 STRATEGIC APPROACH: Split from PR #1270 (UPDATED RECOMMENDATION)

### 🔄 **ANALYSIS REVERSAL**: PR #1270 is Superior for Splitting
**Key Discovery**: After comprehensive analysis, PR #1270 is significantly better than PR #1221:
- **30% Smaller**: 73 files vs 103 files - more manageable scope
- **Better Architecture**: Clean separation of concerns, modern React patterns
- **Enhanced Implementation**: PlanningBlock.tsx is 312 lines vs 112 lines (3x more complete)
- **Production Quality**: Includes comprehensive testing, API improvements, dead code cleanup
- **Superior Organization**: Natural architectural boundaries for splitting

### ✅ **NEW RECOMMENDATION**: True Split Strategy from PR #1270
- PR #1270 contains a **complete, modern implementation** with better architecture
- Clean separation allows for easy splitting into focused PRs
- Enhanced security, testing, and production-ready features
- Sequential integration with clear dependencies

## 🏗️ OPTIMAL PR SPLITTING STRATEGY (FROM PR #1270)

### **Phase 1: Infrastructure & Types (PR A)** - Foundation
**Dependencies**: None  
**Size**: 8 files  
**Review Complexity**: Low  

**Files to Extract from PR #1270**:
```
.gitignore (cleanup)
package.json, package-lock.json (root dependencies)
mvp_site/frontend_v2/package.json, package-lock.json (frontend deps)
mvp_site/frontend_v2/src/services/api.types.ts (enhanced types)
mvp_site/frontend_v2/vite.config.ts (build config)
tools/localserver.sh (dev tooling)
```

**Purpose**: Establish foundation infrastructure and enhanced TypeScript types

### **Phase 2A: Planning Block Component (PR B)** - Core Feature
**Dependencies**: Phase 1 (types & infrastructure)  
**Size**: 3 files  
**Review Complexity**: Medium  

**Files to Extract from PR #1270**:
```
mvp_site/frontend_v2/src/components/PlanningBlock.tsx (312 lines - complete implementation)
mvp_site/frontend_v2/src/pages/ComponentTestPage.tsx (testing page)
docs/planning_blocks_*.png (visual documentation)
```

### **Phase 2B: API Services (PR C)** - Backend Integration
**Dependencies**: Phase 1 (types)  
**Size**: 5 files  
**Review Complexity**: Medium  

**Files to Extract from PR #1270**:
```
mvp_site/frontend_v2/src/services/api.service.ts (clock skew, retry logic)
mvp_site/frontend_v2/src/services/api-with-mock.service.ts (enhanced mocking)
mvp_site/frontend_v2/src/services/mock.service.ts (test improvements)
mvp_site/frontend_v2/src/services/campaignService.ts (campaign integration)
mvp_site/main.py (backend integration points)
```

### **Phase 3: UI Integration (PR D)** - Component Assembly
**Dependencies**: Phase 1, 2A, 2B  
**Size**: 8 files  
**Review Complexity**: High  

**Files to Extract from PR #1270**:
```
mvp_site/frontend_v2/src/components/GamePlayView.tsx (206 additions - main integration)
mvp_site/frontend_v2/src/components/GameView.tsx (planning block integration)
mvp_site/frontend_v2/src/components/CampaignCreation.tsx (enhancements)
mvp_site/frontend_v2/src/components/CampaignCreationV2.tsx (improvements)
mvp_site/frontend_v2/src/AppWithRouter.tsx (routing updates)
mvp_site/static/v2/index.html (frontend config)
mvp_site/frontend_v2/src/hooks/useAuth.tsx (auth improvements)
mvp_site/frontend_v2/src/pages/CampaignPage.tsx (page integration)
```

### **Phase 4: Testing & Documentation (PR E)** - Validation
**Dependencies**: All previous phases  
**Size**: 15+ files  
**Review Complexity**: Low  

**Files to Extract from PR #1270**:
```
mvp_site/tests/test_v2_frontend_red_green.py (comprehensive frontend tests)
mvp_site/tests/test_v2_frontend_verification.py (verification suite)
mvp_site/tests/test_firebase_auth_red_green.py (auth testing)
testing_ui/core_tests/test_planning_blocks_playwright.py (E2E tests)
docs/v2_campaign_creation_test_report.md (test documentation)
docs/v2_frontend_status_screenshot.html (status reporting)
docs/pr1270/guidelines.md (implementation guidelines)
docs/file_ownership_matrix.md (project organization)
.claude/commands/split.md (splitting documentation)
```

## 🔍 COMPLETE OPEN PR ANALYSIS & DECISIONS

### **✅ KEEP & MERGE - Valuable PRs (Foundation First)**
1. **PR #1297** - foundation: comprehensive security, validation, and type safety improvements
   - **Why Keep**: Essential security foundation, no conflicts
   - **Priority**: MERGE FIRST - required foundation

2. **PR #1298** - fix: robust PORT environment variable parsing across codebase  
   - **Why Keep**: Infrastructure fix, no conflicts
   - **Priority**: MERGE SECOND

3. **PR #1299** - security: fix test mode authentication bypass vulnerability in production
   - **Why Keep**: Critical security fix, no conflicts  
   - **Priority**: MERGE THIRD

### **🔄 KEEP BUT NEEDS EVALUATION - Recreation PRs with Value**

#### **PR #1270** - feat: Add V2 API type definitions for planning blocks (73 files, +4221/-2392)
- **Status**: MASSIVE RECREATION (not just types despite title)
- **Contains**: Complete V2 implementation including PlanningBlock.tsx, security fixes, cleanup
- **Value**: Has working implementation + security improvements + cleanup
- **Decision**: **EVALUATE vs PR #1221** - may have better implementation than original
- **Action**: Compare implementation quality before deciding

#### **PR #1271** - feat: Add V2 planning blocks API service integration (1 file, +74/-82)
- **Status**: Focused API service improvements
- **Contains**: Clock skew detection, auth improvements, planning block parsing
- **Value**: Good API reliability improvements
- **Decision**: **KEEP** - valuable API service enhancements
- **Action**: Can merge after foundation PRs

#### **PR #1272** - feat: Add V2 PlanningBlock React component (1 file, +112/0)
- **Status**: Clean single-component PR
- **Contains**: Just the PlanningBlock.tsx component
- **Value**: Focused, reviewable implementation
- **Decision**: **EVALUATE vs PR #1221 & #1270** - may be cleaner than alternatives
- **Action**: Compare component implementations

#### **PR #1273** - test: Add V2 planning blocks test suite (1 file, +153/0)
- **Status**: Pure test addition
- **Contains**: Planning blocks test coverage
- **Value**: Valuable test coverage addition
- **Decision**: **KEEP** - good test coverage regardless of implementation source
- **Action**: Merge after implementation PRs

### **❌ ABANDON - Superseded PRs**
1. **PR #1221** - feat: Implement V2 planning blocks feature (103 files, +8153/-2270)
   - **Status**: TOO LARGE and inferior implementation compared to PR #1270
   - **Decision**: **CLOSE** - PR #1270 has better architecture and smaller scope
   - **Action**: Reference for requirements only, implementation superseded by #1270

### **📋 OTHER OPEN PRS (Non-Planning Blocks)**
- **PR #1301** - Copilot command skip detection bug (KEEP - independent fix)
- **PR #1293** - /exportcommands improvements (KEEP - independent feature)  
- **PR #1294** - Zero-tolerance skip pattern ban (KEEP - independent improvement)
- **PR #1284** - GitHub Actions Security fixes (KEEP - critical security)
- **Various other PRs** - Evaluate independently, not related to planning blocks

## 🎯 REVISED EXECUTION STRATEGY

### **CONFIRMED**: PR #1270 is Superior to PR #1221
- **30% Smaller Scope**: 73 files vs 103 files - more manageable
- **Enhanced Security**: Includes security improvements + cleanup that PR #1221 lacks  
- **Modern Architecture**: Clean separation of concerns, production-ready patterns
- **Complete Implementation**: PlanningBlock.tsx 312 lines vs 112 lines (3x more complete)
- **Better Testing**: Comprehensive test suite with red-green methodology
- **Dead Code Cleanup**: Removes unused e-commerce components

## 🚀 UPDATED IMPLEMENTATION EXECUTION PLAN (PR #1270 SPLITTING)

### **Week 1: Foundation PRs First**
**Days 1-2**: Foundation PRs (Sequential)
- **PR #1297**: Merge comprehensive security improvements
- **PR #1298**: Merge PORT environment parsing fix  
- **PR #1299**: Merge test mode auth security fix
- **Rationale**: Build secure foundation before feature work

**Days 3-5**: Begin PR #1270 Splitting Strategy
- **Phase 1**: Create Infrastructure & Types PR (8 files)
- **Scope**: Dependencies, build config, enhanced TypeScript types
- **Review**: Low complexity, foundation layer
- **Action**: Immediate merge after review

### **Week 2: Core Implementation**
**Days 1-2**: Phase 2A - Planning Block Component
- **Create PR**: PlanningBlock.tsx (312 lines) + ComponentTestPage + docs
- **Review**: Medium complexity, core feature implementation
- **Dependencies**: Phase 1 (types & infrastructure)

**Days 3-5**: Phase 2B - API Services  
- **Create PR**: Enhanced API service with clock skew, retry logic
- **Review**: Medium complexity, backend integration
- **Parallel**: Can develop alongside Phase 2A

### **Week 3: Integration & Validation**
**Days 1-3**: Phase 3 - UI Integration
- **Create PR**: GamePlayView integration (206 additions) + routing updates
- **Review**: High complexity, component assembly
- **Dependencies**: Phases 1, 2A, 2B

**Days 4-5**: Phase 4 - Testing & Documentation
- **Create PR**: Comprehensive test suite + documentation
- **Review**: Low complexity, validation layer
- **Includes**: Red-green tests, Playwright E2E, guidelines

### **Week 4: Finalization**
**Days 1-2**: Integration Testing
- Comprehensive end-to-end testing with existing campaigns
- Visual parity validation with V1 interface
- Performance benchmarking vs current V2

**Days 3-5**: Cleanup & Documentation
- Close PR #1270 (replaced by 4 focused PRs)
- Close PR #1221 (superseded by better implementation)
- Update V2 implementation status
- Create migration guide and deployment plan

## 🎯 SUCCESS CRITERIA & VALIDATION

### **Phase Completion Criteria**
- [ ] **Phase 1**: All TypeScript types compile without errors
- [ ] **Phase 2A**: Planning blocks render interactive buttons (not placeholder)
- [ ] **Phase 2B**: All 5 supporting components display correct data with proper styling
- [ ] **Phase 3**: Complete GamePlayView integration with all 6 components working
- [ ] **Phase 4**: Backend API properly serves planning block data

### **End-to-End Validation**
- [ ] Visual parity with V1 screenshots
- [ ] All 6 components display correct data from API
- [ ] Planning blocks are interactive with proper risk level styling
- [ ] Backward compatibility with existing V1 campaigns
- [ ] No performance regressions
- [ ] Mobile responsiveness maintained

## 🚨 RISK MITIGATION

### **Technical Risks**
1. **Complex Dependencies**: Mitigated by clear phase separation
2. **Integration Conflicts**: Mitigated by sequential merging strategy
3. **Breaking Changes**: Mitigated by TypeScript and comprehensive testing
4. **Performance Impact**: Mitigated by component-level optimization

### **Process Risks**
1. **Review Bottlenecks**: Mitigated by small, focused PRs (<10 files each)
2. **Context Loss**: Mitigated by detailed extraction documentation
3. **Scope Creep**: Mitigated by strict adherence to requirements from PR #1221

## 📊 PARALLEL DEVELOPMENT OPPORTUNITIES

### **Development Teams**
- **Team A**: Phase 1 + 2A (Types + Planning Block Component)
- **Team B**: Phase 2B (Supporting Components)
- **Team C**: Phase 3 + 4 (Integration + Backend)

### **Timeline Optimization**
- Phase 1 → Phase 2A and 2B (parallel)
- Phase 2A + 2B → Phase 3
- Phase 3 → Phase 4
- **Total Time**: 3 weeks instead of 5 weeks sequential

## 🎯 FINAL IMPLEMENTATION CHECKLIST (PR #1270 SPLITTING)

### **Pre-Implementation**
- [ ] Merge PR #1297, #1298, #1299 (foundation security changes) first
- [x] **DECISION MADE**: PR #1270 confirmed superior - use as splitting source
- [ ] Begin 4-phase splitting strategy from PR #1270 codebase

### **Implementation (4 Phases from PR #1270)**
- [ ] **Phase 1**: Infrastructure & Types (8 files) - Foundation layer
- [ ] **Phase 2A**: Planning Block Component (3 files) - Core feature
- [ ] **Phase 2B**: API Services (5 files) - Backend integration  
- [ ] **Phase 3**: UI Integration (8 files) - Component assembly
- [ ] **Phase 4**: Testing & Documentation (15+ files) - Validation
- [ ] Test each phase independently with existing campaigns
- [ ] Maintain V1/V2 API compatibility throughout
- [ ] Verify visual parity with V1 interface

### **Post-Implementation**
- [ ] Close PR #1270 (replaced by 4 focused PRs)
- [ ] Close PR #1221 (superseded by superior #1270 implementation)  
- [ ] Update V2 implementation status and documentation
- [ ] Create deployment guide for production rollout
- [ ] Performance benchmarking vs current V2 baseline

---

**Status**: 🎯 Ready for immediate execution with PR #1270 as source  
**Next Action**: Merge foundation PRs #1297-1299, then begin Phase 1 splitting  
**Key Success Factor**: Split PR #1270's superior architecture into reviewable chunks  

**Strategic Advantage**: This approach transforms a 73-file complex PR into 4 focused, reviewable PRs (average 18 files each) while preserving the enhanced implementation, security improvements, and modern React architecture that makes PR #1270 superior to PR #1221.

---

# 📈 SUB-MILESTONE BREAKDOWN: 45 Git Commits (~100 Lines Each)

## Phase 1: Infrastructure & Types (10 Sub-Milestones)

### P1.1: Root Package Configuration (~75 lines)
**Files**: `.gitignore` (3), `package.json` (5), root configs  
**Commit**: `feat(infra): add root package configuration and gitignore patterns`  
**Test**: Verify package.json valid, gitignore patterns work

### P1.2: Frontend Package Dependencies (~450 lines)
**Files**: `mvp_site/frontend_v2/package.json` (4), `mvp_site/frontend_v2/package-lock.json` (442)  
**Commit**: `feat(infra): update frontend dependencies for V2 planning blocks`  
**Test**: `npm install` succeeds, no dependency conflicts

### P1.3: Build Configuration (~100 lines)
**Files**: `mvp_site/frontend_v2/vite.config.ts` (31), `package-lock.json` (71)  
**Commit**: `feat(infra): enhance Vite build config with TypeScript support`  
**Test**: `npm run build` succeeds, TypeScript compilation works

### P1.4: TypeScript Type Definitions (~45 lines)
**Files**: `mvp_site/frontend_v2/src/services/api.types.ts` (23-3), `mvp_site/frontend_v2/src/env.d.ts` (21)  
**Commit**: `feat(types): add V2 planning block TypeScript definitions`  
**Test**: TypeScript types compile, interfaces validate correctly

### P1.5: Development Tooling (~40 lines)
**Files**: `tools/localserver.sh` (41-1)  
**Commit**: `feat(dev): enhance local server script with better error handling`  
**Test**: Local server starts successfully, error handling works

### P1.6: Firebase Configuration Setup (~150 lines)
**Files**: `.env.example` (50), Firebase config templates  
**Commit**: `feat(firebase): add environment configuration for Firebase integration`  
**Test**: Environment variables load, Firebase config validates

### P1.7: Firebase Credentials Management (~100 lines)
**Files**: `scripts/firebase_credentials.py` (~100)  
**Commit**: `feat(firebase): add Firebase credential management script`  
**Test**: Script runs without errors, credentials validate

### P1.8: Firebase Integration Library (~150 lines)
**Files**: `mvp_site/frontend_v2/src/lib/firebase.ts` (~150)  
**Commit**: `feat(firebase): implement Firebase client library for V2`  
**Test**: Firebase client initializes, auth methods work

### P1.9: Firebase Admin Setup (~100 lines)
**Files**: Firebase admin configuration files  
**Commit**: `feat(firebase): add Firebase admin SDK configuration`  
**Test**: Admin SDK initializes, permissions validate

### P1.10: Firebase Testing Setup (~80 lines)
**Files**: Basic Firebase test configuration  
**Commit**: `test(firebase): add basic Firebase testing infrastructure`  
**Test**: Firebase test suite runs, mock auth works

## Phase 2A: Planning Block Component (7 Sub-Milestones)

### P2A.1: Planning Block Component Structure (~100 lines)
**Files**: `mvp_site/frontend_v2/src/components/PlanningBlock.tsx` (first 100 lines)  
**Commit**: `feat(component): add PlanningBlock component structure and props`  
**Test**: Component renders without crashing, props validate

### P2A.2: Planning Block Choice Rendering (~100 lines)
**Files**: `mvp_site/frontend_v2/src/components/PlanningBlock.tsx` (next 100 lines)  
**Commit**: `feat(component): implement planning block choice button rendering`  
**Test**: Choice buttons render, click handlers attached

### P2A.3: Risk Level Styling (~100 lines)
**Files**: `mvp_site/frontend_v2/src/components/PlanningBlock.tsx` (next 100 lines)  
**Commit**: `feat(component): add risk level color coding and visual feedback`  
**Test**: Risk levels display correct colors, visual feedback works

### P2A.4: Interactive State Management (~12 lines)
**Files**: `mvp_site/frontend_v2/src/components/PlanningBlock.tsx` (final 12 lines)  
**Commit**: `feat(component): complete planning block interaction logic`  
**Test**: State updates correctly, user interactions work

### P2A.5: Component Test Page Structure (~100 lines)
**Files**: `mvp_site/frontend_v2/src/pages/ComponentTestPage.tsx` (first 100 lines)  
**Commit**: `feat(testing): add component test page structure`  
**Test**: Test page loads, basic layout renders

### P2A.6: Mock Data Integration (~100 lines)
**Files**: `mvp_site/frontend_v2/src/pages/ComponentTestPage.tsx` (next 100 lines)  
**Commit**: `feat(testing): integrate mock data for component testing`  
**Test**: Mock data loads, component displays test scenarios

### P2A.7: Test Page Completion & Documentation (~129 lines)
**Files**: `mvp_site/frontend_v2/src/pages/ComponentTestPage.tsx` (final 129 lines), `docs/planning_blocks_focused.png`  
**Commit**: `feat(testing): complete component test page with visual documentation`  
**Test**: Full test page works, documentation accessible

## Phase 2B: API Services (9 Sub-Milestones)

### P2B.1: Enhanced API Service Base (~90 lines)
**Files**: `mvp_site/frontend_v2/src/services/api.service.ts` (57-36)  
**Commit**: `feat(api): enhance API service with clock skew detection and retry logic`  
**Test**: API calls succeed, retry logic triggers, clock skew handled

### P2B.2: Mock Service Integration (~25 lines)
**Files**: `mvp_site/frontend_v2/src/services/api-with-mock.service.ts` (3-4), campaign updates  
**Commit**: `feat(api): improve mock service integration and campaign service`  
**Test**: Mock/real API switching works, campaign service responds

### P2B.3: Mock Data Foundation (~100 lines)
**Files**: `mvp_site/frontend_v2/src/services/mock.service.ts` (first 100 lines)  
**Commit**: `feat(mock): add comprehensive mock service foundation`  
**Test**: Basic mock responses work, data structure validates

### P2B.4: Planning Block Mock Scenarios (~100 lines)
**Files**: `mvp_site/frontend_v2/src/services/mock.service.ts` (next 100 lines)  
**Commit**: `feat(mock): implement realistic planning block mock scenarios`  
**Test**: Mock planning blocks display, scenarios vary correctly

### P2B.5: Mock Service Completion (~105 lines)
**Files**: `mvp_site/frontend_v2/src/services/mock.service.ts` (remaining lines)  
**Commit**: `feat(mock): complete mock service with varied risk levels and D&D scenarios`  
**Test**: All risk levels work, D&D scenarios display properly

### P2B.6: Backend Integration Foundation (~100 lines)
**Files**: `mvp_site/main.py` (first 100 lines of changes)  
**Commit**: `feat(backend): enhance Flask backend with planning block support foundation`  
**Test**: Backend starts, basic planning block endpoints respond

### P2B.7: Backend API Completion (~74 lines)
**Files**: `mvp_site/main.py` (remaining), `mvp_site/static/v2/index.html` (9-7)  
**Commit**: `feat(backend): complete backend planning block integration and HTML config`  
**Test**: Full backend API works, HTML serves correctly

### P2B.8: World Logic Recreation Part 1 (~200 lines)
**Files**: `mvp_site/world_logic.py` (first 200 lines from PR #1221)  
**Commit**: `feat(backend): recreate core world logic from PR #1221 - part 1`  
**Test**: Basic world logic functions work, no import errors

### P2B.9: World Logic Completion (~300 lines)
**Files**: `mvp_site/world_logic.py` (remaining 300 lines)  
**Commit**: `feat(backend): complete world logic recreation with planning block integration`  
**Test**: Full world logic works, planning blocks integrate properly

## Phase 3: UI Integration (2 Sub-Milestones)

### P3.1: Core Game Integration (~25 lines net, ~200 gross)
**Files**: `GamePlayView.tsx` (206-8), `GameView.tsx` (4-9), `AppWithRouter.tsx` (4), `useAuth.tsx` (5-5)  
**Commit**: `feat(integration): integrate planning blocks into game view and routing`  
**Test**: Planning blocks appear in game, routing works, auth persists

### P3.2: UI Cleanup & Campaign Integration (~25 lines net, ~400 gross)
**Files**: `HomePage.tsx` (160-333), `CampaignCreation.tsx` (18-2), `CampaignCreationV2.tsx` (34-11), minor updates  
**Commit**: `feat(integration): clean up UI components and enhance campaign creation`  
**Test**: Clean UI loads, campaign creation works, no broken links

## Phase 4: Testing & Documentation (18 Sub-Milestones)

### P4.1-P4.3: Frontend Red-Green Testing (~95 lines each)
**Files**: `mvp_site/tests/test_v2_frontend_red_green.py` (284 lines split)  
**Commits**: 
- `test(frontend): add V2 frontend red-green test foundation` 
- `test(frontend): implement planning block component testing`
- `test(frontend): complete frontend integration testing`  
**Tests**: Red-green methodology, component tests pass, integration validates

### P4.4-P4.5: Frontend Verification Testing (~106 lines each)
**Files**: `mvp_site/tests/test_v2_frontend_verification.py` (212 lines split)  
**Commits**:
- `test(verification): add V1/V2 API compatibility testing`
- `test(verification): complete feature parity validation`  
**Tests**: V1/V2 compatibility verified, feature parity confirmed

### P4.6-P4.7: Firebase Authentication Testing (~120 lines each)
**Files**: `mvp_site/tests/test_firebase_auth_red_green.py` (240 lines split)  
**Commits**:
- `test(firebase): implement Firebase authentication testing foundation`
- `test(firebase): complete auth integration with planning blocks`  
**Tests**: Firebase auth works, planning block sessions persist

### P4.8-P4.12: Playwright E2E Testing (~82 lines each)
**Files**: `testing_ui/core_tests/test_planning_blocks_playwright.py` (411 lines split)  
**Commits**:
- `test(e2e): add Playwright test foundation for planning blocks`
- `test(e2e): implement planning block interaction testing` 
- `test(e2e): add visual feedback and choice testing`
- `test(e2e): implement screenshot comparison testing`
- `test(e2e): complete end-to-end test validation`  
**Tests**: E2E flows work, interactions validate, screenshots match

### P4.13-P4.14: Test Documentation (~116 lines each)
**Files**: `docs/v2_campaign_creation_test_report.md` (232 lines split)  
**Commits**:
- `docs(testing): add comprehensive test report foundation`
- `docs(testing): complete test validation and performance metrics`  
**Tests**: Documentation accurate, metrics validate performance

### P4.15: Visual Status Documentation (~172 lines)
**Files**: `docs/v2_frontend_status_screenshot.html`  
**Commit**: `docs(status): add interactive V2 frontend status report`  
**Test**: Status report loads, interactive elements work

### P4.16: Implementation Guidelines (~137 lines)
**Files**: `docs/pr1270/guidelines.md` (37), `docs/file_ownership_matrix.md` (100)  
**Commit**: `docs(dev): add development guidelines and file ownership matrix`  
**Test**: Guidelines accessible, ownership matrix validates

### P4.17: Process Documentation (~162 lines)
**Files**: `.claude/commands/split.md`  
**Commit**: `docs(process): document PR splitting strategy for future use`  
**Test**: Documentation complete, examples work

### P4.18: Development Notes & Cleanup (~190 lines)
**Files**: `roadmap/scratchpad_pr-split-type-definitions.md` (188), `scripts/server-utils.sh` (2), removals  
**Commit**: `docs(dev): add technical notes and perform final cleanup`  
**Test**: Clean codebase, no broken references, notes accessible

## Summary: 45 Sub-Milestones with TDD Integration

**Total**: 45 commits averaging ~100 lines each  
**TDD Pattern**: Red (test fails) → Green (implementation) → Refactor (cleanup)  
**Validation**: Every sub-milestone has specific test criteria  
**Safety**: Each commit can be independently tested and rolled back

---

# 📋 DETAILED FILE-BY-FILE BREAKDOWN FOR EACH SPLIT PR

## 🔧 **PHASE 1: INFRASTRUCTURE & TYPES PR** - Foundation Layer
**Files**: 9 files | **Review Complexity**: Low | **Dependencies**: None

### **Root Configuration Files**

**1. `.gitignore`** (3 additions)
- **Purpose**: Updates .gitignore patterns for V2 build artifacts and logging cleanup
- **Changes**: Adds patterns to ignore V2-specific generated files and development artifacts
- **Why Phase 1**: Infrastructure foundation - must be established before any code changes

**2. `package.json`** (5 additions)
- **Purpose**: Root-level package configuration for project-wide dependencies
- **Changes**: Adds workspace configuration and development tooling dependencies
- **Why Phase 1**: Defines project structure that subsequent phases depend on

**3. `package-lock.json`** (71 additions)
- **Purpose**: Locks exact versions of root dependencies for reproducible builds
- **Changes**: New dependency tree with exact version specifications
- **Why Phase 1**: Must be established before frontend package changes to avoid conflicts

### **Frontend Build Configuration**

**4. `mvp_site/frontend_v2/package.json`** (4 additions)
- **Purpose**: Frontend-specific dependencies and build scripts
- **Changes**: Adds TypeScript development dependencies and enhanced build configuration
- **Why Phase 1**: Required for TypeScript compilation in subsequent phases

**5. `mvp_site/frontend_v2/package-lock.json`** (442 additions)
- **Purpose**: Locks frontend dependency versions including new TypeScript and testing libraries
- **Changes**: Major dependency updates for enhanced development experience
- **Why Phase 1**: Establishes stable foundation for component development

**6. `mvp_site/frontend_v2/vite.config.ts`** (31 additions)
- **Purpose**: Enhanced Vite build configuration with TypeScript support and development optimizations
- **Changes**: Adds type checking, enhanced dev server configuration, and build optimizations
- **Why Phase 1**: Build system must be configured before component compilation

### **TypeScript Type Definitions**

**7. `mvp_site/frontend_v2/src/services/api.types.ts`** (23 additions, 3 deletions)
- **Purpose**: Enhanced TypeScript interfaces for API responses including planning block types
- **Changes**: Adds PlanningBlockData, PlanningBlockChoice interfaces and enhanced API response types
- **Why Phase 1**: Type foundation that all subsequent components depend on

**8. `mvp_site/frontend_v2/src/env.d.ts`** (21 additions)
- **Purpose**: Environment type definitions for Vite and development configuration
- **Changes**: Adds type safety for environment variables and development modes
- **Why Phase 1**: Required for TypeScript compilation across all components

### **Development Tooling**

**9. `tools/localserver.sh`** (41 additions, 1 deletion)
- **Purpose**: Enhanced local development server script with improved error handling
- **Changes**: Adds better process management, port detection, and development mode configuration
- **Why Phase 1**: Development infrastructure needed for testing subsequent phases

---

## ⚛️ **PHASE 2A: PLANNING BLOCK COMPONENT PR** - Core Feature
**Files**: 3 files | **Review Complexity**: Medium | **Dependencies**: Phase 1

### **Core Planning Block Implementation**

**1. `mvp_site/frontend_v2/src/components/PlanningBlock.tsx`** (312 additions)
- **Purpose**: Complete interactive planning block component with choice buttons and risk level styling
- **Changes**: Brand new 312-line React component implementing the core V2 planning blocks feature
- **Key Features**: Interactive choice buttons, risk level color coding (safe/low/medium/high), custom action support, AI thinking display
- **Why Phase 2A**: This is the primary deliverable - the core feature that makes V2 planning blocks functional
- **Dependencies**: Requires api.types.ts from Phase 1 for PlanningBlockData interfaces

### **Component Testing Infrastructure**

**2. `mvp_site/frontend_v2/src/pages/ComponentTestPage.tsx`** (329 additions)
- **Purpose**: Dedicated testing page for isolated planning block component development and verification
- **Changes**: New testing environment that allows developers to test planning blocks without full game context
- **Features**: Mock data injection, component isolation, visual verification tools
- **Why Phase 2A**: Essential for component development and QA - allows testing before integration
- **Dependencies**: Uses PlanningBlock component, so must be in same PR

### **Visual Documentation**

**3. `docs/planning_blocks_focused.png`** (image file)
- **Purpose**: Visual documentation showing the focused planning block component in action
- **Changes**: Screenshot evidence of planning block rendering and interaction
- **Why Phase 2A**: Provides visual proof of concept and helps with code review understanding
- **Importance**: Critical for reviewers to understand the visual output of the 312-line component

---

## 🔗 **PHASE 2B: API SERVICES PR** - Backend Integration
**Files**: 6 files | **Review Complexity**: Medium | **Dependencies**: Phase 1

### **Enhanced API Service Layer**

**1. `mvp_site/frontend_v2/src/services/api.service.ts`** (57 additions, 36 deletions)
- **Purpose**: Enhanced API service with clock skew detection, retry logic, and planning block parsing
- **Changes**: Adds intelligent retry mechanisms, timestamp synchronization, and robust error handling
- **Key Features**: Exponential backoff for retries, clock skew compensation, planning block JSON parsing
- **Why Phase 2B**: Backend integration layer that planning blocks depend on for data fetching
- **Dependencies**: Uses enhanced types from Phase 1

**2. `mvp_site/frontend_v2/src/services/api-with-mock.service.ts`** (3 additions, 4 deletions)
- **Purpose**: API service wrapper that provides seamless switching between real and mock backends
- **Changes**: Improves mock detection and fallback logic for development environments
- **Why Phase 2B**: Testing infrastructure that supports planning block development
- **Integration**: Works with enhanced api.service.ts

**3. `mvp_site/frontend_v2/src/services/mock.service.ts`** (205 additions, 27 deletions)
- **Purpose**: Comprehensive mock service providing realistic planning block data for development
- **Changes**: Adds sophisticated planning block mock responses with multiple choice scenarios
- **Key Features**: Realistic D&D scenarios, varied risk levels, multiple choice formats
- **Why Phase 2B**: Essential for development and testing without requiring backend changes
- **Dependencies**: Implements interfaces from Phase 1 types

**4. `mvp_site/frontend_v2/src/services/campaignService.ts`** (10 additions, 7 deletions)
- **Purpose**: Campaign management service enhanced with planning block integration
- **Changes**: Updates campaign creation and management to support planning block features
- **Why Phase 2B**: Campaign context is required for planning block functionality
- **Integration**: Uses enhanced API service layer

### **Backend Integration Point**

**5. `mvp_site/main.py`** (109 additions, 35 deletions)
- **Purpose**: Python Flask backend enhancements for planning block support and improved error handling
- **Changes**: Adds planning block response formatting, enhanced Firebase integration, better error responses
- **Key Features**: Structured planning block JSON output, improved authentication handling, better logging
- **Why Phase 2B**: Backend changes needed to properly serve planning block data to frontend
- **Critical**: This is the only backend file in the entire split - keeps backend changes minimal

### **Static Asset Configuration**

**6. `mvp_site/static/v2/index.html`** (9 additions, 7 deletions)
- **Purpose**: V2 frontend HTML template with enhanced meta tags and configuration
- **Changes**: Adds better viewport configuration, enhanced CSP headers, improved loading states
- **Why Phase 2B**: Required for proper V2 frontend serving with backend integration
- **Integration**: Works with main.py backend changes

---

## 🎨 **PHASE 3: UI INTEGRATION PR** - Component Assembly
**Files**: 24 files | **Review Complexity**: High | **Dependencies**: Phases 1, 2A, 2B

### **Primary Integration Point**

**1. `mvp_site/frontend_v2/src/components/GamePlayView.tsx`** (206 additions, 8 deletions)
- **Purpose**: Main game interface enhanced with planning block integration and improved UX
- **Changes**: Major overhaul adding planning block rendering, better state management, enhanced user interactions
- **Key Features**: Planning block display logic, choice handling, visual feedback, error handling
- **Why Phase 3**: This is where planning blocks get integrated into the actual game experience
- **Dependencies**: Requires PlanningBlock component (Phase 2A) and enhanced API services (Phase 2B)

**2. `mvp_site/frontend_v2/src/components/GameView.tsx`** (4 additions, 9 deletions)
- **Purpose**: Game view container simplified and enhanced for better planning block integration
- **Changes**: Removes redundant code and improves data flow to GamePlayView
- **Why Phase 3**: Simplification needed for clean planning block integration
- **Integration**: Works with enhanced GamePlayView

### **Application Structure Updates**

**3. `mvp_site/frontend_v2/src/AppWithRouter.tsx`** (4 additions)
- **Purpose**: App routing enhanced with component test page and improved navigation
- **Changes**: Adds routes for planning block testing and development tools
- **Why Phase 3**: Routing changes needed for complete application integration
- **Dependencies**: References ComponentTestPage from Phase 2A

**4. `mvp_site/frontend_v2/src/hooks/useAuth.tsx`** (5 additions, 5 deletions)
- **Purpose**: Authentication hook enhanced with better error handling and Firebase integration
- **Changes**: Improves authentication state management and error recovery
- **Why Phase 3**: Authentication improvements needed for reliable planning block sessions
- **Integration**: Works with enhanced main.py backend

### **Campaign Creation Enhancements**

**5. `mvp_site/frontend_v2/src/components/CampaignCreation.tsx`** (18 additions, 2 deletions)
- **Purpose**: Campaign creation enhanced with planning block preference settings
- **Changes**: Adds user preferences for planning block display and interaction modes
- **Why Phase 3**: Campaign settings need to support planning block configuration
- **Integration**: Uses enhanced campaign service from Phase 2B

**6. `mvp_site/frontend_v2/src/components/CampaignCreationV2.tsx`** (34 additions, 11 deletions)
- **Purpose**: V2-specific campaign creation with modern React patterns and planning block integration
- **Changes**: Major improvements to form handling, validation, and user experience
- **Why Phase 3**: V2 campaign creation must support planning block features from the start
- **Dependencies**: Uses enhanced types and services from previous phases

### **Page-Level Integration**

**7. `mvp_site/frontend_v2/src/pages/CampaignCreationPage.tsx`** (1 addition, 1 deletion)
- **Purpose**: Campaign creation page updated for enhanced component integration
- **Changes**: Minor routing and state management improvements
- **Why Phase 3**: Page-level changes needed for complete integration

**8. `mvp_site/frontend_v2/src/pages/CampaignPage.tsx`** (2 additions, 2 deletions)
- **Purpose**: Campaign page enhanced with planning block support
- **Changes**: Updates page layout and data flow for planning block integration
- **Why Phase 3**: Campaign pages must display planning blocks properly

**9. `mvp_site/frontend_v2/src/pages/SettingsPage.tsx`** (1 addition, 1 deletion)
- **Purpose**: Settings page with planning block preference options
- **Changes**: Adds user preference controls for planning block features
- **Why Phase 3**: User customization needed for planning block experience

### **UI Component Updates**

**10. `mvp_site/frontend_v2/src/components/Dashboard.tsx`** (14 additions, 14 deletions)
- **Purpose**: Dashboard enhanced with planning block activity summaries and quick access
- **Changes**: Adds planning block statistics, recent activity, and navigation improvements
- **Why Phase 3**: Dashboard must reflect planning block usage and provide quick access

**11. `mvp_site/frontend_v2/src/components/HomePage.tsx`** (160 additions, 333 deletions)
- **Purpose**: Major homepage redesign removing e-commerce elements and focusing on D&D features
- **Changes**: Removes 333 lines of e-commerce code, adds 160 lines of D&D-focused content
- **Why Phase 3**: Homepage must properly represent the planning block features and D&D focus
- **Clean-up**: Removes irrelevant e-commerce remnants for cleaner user experience

### **Minor Component Updates**

**12-24. Various UI Components** (1 addition, 1 deletion each)
- **Files**: ErrorBoundary.tsx, LandingPage.tsx, MockModeToggle.tsx, SearchPage.tsx, etc.
- **Purpose**: Minor TypeScript and import updates for consistency with new architecture
- **Changes**: Mostly import path updates and TypeScript compliance improvements
- **Why Phase 3**: These updates ensure compatibility with the new planning block architecture
- **Batch Reason**: All minor updates grouped together to avoid dependency fragmentation

### **State Management Updates**

**25. `mvp_site/frontend_v2/src/stores/gameStore.ts`** (1 addition, 1 deletion)
- **Purpose**: Game state store enhanced with planning block state management
- **Changes**: Adds planning block state persistence and synchronization
- **Why Phase 3**: State management critical for planning block functionality

**26. `mvp_site/frontend_v2/src/stores/themeStore.ts`** (8 additions, 8 deletions)
- **Purpose**: Theme store updated with planning block-specific styling support
- **Changes**: Adds theme variables for planning block risk levels and interactive states
- **Why Phase 3**: Visual consistency requires theme integration

**27. `mvp_site/frontend_v2/src/types.ts`** (1 addition, 20 deletions)
- **Purpose**: Core types file cleaned up with planning block types moved to api.types.ts
- **Changes**: Removes redundant type definitions, references enhanced api.types.ts
- **Why Phase 3**: Type organization cleanup needed after Phase 1 foundation

**28. `mvp_site/frontend_v2/src/types/theme.ts`** (1 addition, 1 deletion)
- **Purpose**: Theme types enhanced with planning block styling definitions
- **Changes**: Adds type safety for planning block visual elements
- **Why Phase 3**: TypeScript support for planning block theming

**29. `mvp_site/frontend_v2/src/utils/errorHandling.ts`** (1 addition, 1 deletion)
- **Purpose**: Error handling utilities enhanced with planning block-specific error types
- **Changes**: Adds error handling for planning block parsing and interaction failures
- **Why Phase 3**: Robust error handling needed for planning block user experience

---

## 🧪 **PHASE 4: TESTING & DOCUMENTATION PR** - Validation
**Files**: 31 files | **Review Complexity**: Low | **Dependencies**: Phases 1-3

### **Comprehensive Test Suite**

**1. `mvp_site/tests/test_v2_frontend_red_green.py`** (284 additions)
- **Purpose**: Comprehensive red-green test methodology for V2 frontend validation
- **Changes**: Complete test suite covering planning block functionality, API integration, component rendering
- **Key Features**: Red-green testing, component isolation, integration validation, visual regression testing
- **Why Phase 4**: Complete validation of all planning block functionality implemented in previous phases
- **Dependencies**: Tests all components from Phases 2A-3

**2. `mvp_site/tests/test_v2_frontend_verification.py`** (212 additions)
- **Purpose**: Verification test suite ensuring V1/V2 API compatibility and feature parity
- **Changes**: Tests API compatibility, data format consistency, backward compatibility
- **Why Phase 4**: Ensures planning block implementation doesn't break existing functionality
- **Critical**: Validates that V1 campaigns still work with V2 backend

**3. `mvp_site/tests/test_firebase_auth_red_green.py`** (240 additions)
- **Purpose**: Firebase authentication testing with red-green methodology
- **Changes**: Comprehensive auth testing including planning block session management
- **Why Phase 4**: Authentication critical for planning block user sessions and data persistence
- **Integration**: Tests auth flow with planning block features

**4. `testing_ui/core_tests/test_planning_blocks_playwright.py`** (411 additions)
- **Purpose**: End-to-end Playwright testing for planning block user interactions
- **Changes**: Complete E2E test suite covering planning block clicks, choices, visual feedback
- **Key Features**: Browser automation, visual testing, interaction validation, screenshot comparison
- **Why Phase 4**: User interaction testing that can only be done after full integration
- **Dependencies**: Requires complete planning block implementation from all previous phases

### **Documentation & Guidelines**

**5. `docs/v2_campaign_creation_test_report.md`** (232 additions)
- **Purpose**: Comprehensive test report documenting campaign creation with planning blocks
- **Changes**: Detailed test results, screenshots, performance metrics, compatibility analysis
- **Why Phase 4**: Documentation of test results and validation evidence
- **Evidence**: Provides proof that planning blocks work end-to-end

**6. `docs/v2_frontend_status_screenshot.html`** (172 additions)
- **Purpose**: Visual status report with interactive HTML showing V2 frontend capabilities
- **Changes**: Interactive demo of planning block functionality with embedded examples
- **Why Phase 4**: Visual documentation for stakeholders and future developers
- **Demo**: Allows reviewers to see planning blocks in action

**7. `docs/pr1270/guidelines.md`** (37 additions)
- **Purpose**: Development guidelines specific to planning block implementation patterns
- **Changes**: Coding standards, component patterns, testing requirements, integration guidelines
- **Why Phase 4**: Ensures future planning block development follows established patterns
- **Standards**: Documents the architectural decisions made in previous phases

**8. `docs/file_ownership_matrix.md`** (100 additions)
- **Purpose**: File ownership documentation preventing conflicts in future development
- **Changes**: Clear ownership mapping for all planning block related files
- **Why Phase 4**: Project organization and conflict prevention
- **Management**: Helps coordinate future development work

**9. `docs/planning_blocks_final_corrected.png`** (image)
- **Purpose**: Final visual documentation of corrected planning block implementation
- **Changes**: Screenshot showing proper planning block rendering and interaction
- **Why Phase 4**: Visual proof of successful implementation
- **Evidence**: Used in documentation and testing validation

### **Development Tools & Scripts**

**10. `.claude/commands/split.md`** (162 additions)
- **Purpose**: Documentation of the PR splitting strategy and implementation process
- **Changes**: Complete guide for future PR splitting based on this successful approach
- **Why Phase 4**: Process documentation for future development
- **Knowledge**: Preserves the splitting strategy for future use

**11. `roadmap/scratchpad_pr-split-type-definitions.md`** (188 additions)
- **Purpose**: Technical notes and analysis from the PR splitting process
- **Changes**: Developer notes, technical decisions, lessons learned
- **Why Phase 4**: Technical documentation and knowledge preservation
- **Learning**: Helps future developers understand the splitting decisions

**12. `scripts/server-utils.sh`** (2 additions, 2 deletions)
- **Purpose**: Server utility scripts enhanced for planning block development workflow
- **Changes**: Minor improvements to development server management
- **Why Phase 4**: Development tooling improvements discovered during implementation
- **Tools**: Better developer experience for planning block work

### **Asset Management**

**13. `mvp_site/static/v2/image_reference/twin_dragon.png`** (image)
- **Purpose**: Reference image for planning block visual themes and D&D atmosphere
- **Changes**: New reference asset for visual consistency
- **Why Phase 4**: Visual assets discovered as needed during implementation
- **Design**: Supports planning block visual design consistency

### **Clean-up Operations** (18 files)

**14-31. Removed Files**
- **Files**: CartPage.tsx, ProductPage.tsx, calendar.tsx, command.tsx, drawer.tsx, mock-integration-example.tsx, xss-security-demo.html, react-mcp-logs.json, react-mcp-logs.txt
- **Purpose**: Removal of unused e-commerce and development artifacts
- **Changes**: Complete removal of files no longer needed
- **Why Phase 4**: Clean-up operations that reduce codebase complexity
- **Benefits**: Smaller bundle size, reduced maintenance burden, cleaner codebase
- **Safety**: These removals can only be done after confirming no dependencies exist

---

# 🎯 **SUMMARY: 4-PHASE SPLITTING RATIONALE**

**Total Files**: 73 files across 4 phases
**Average PR Size**: ~18 files each
**Review Complexity**: Graduated from Low → Medium → High → Low

**Phase Dependencies**:
- **Phase 1** → **Phases 2A & 2B** (parallel)
- **Phases 2A & 2B** → **Phase 3**  
- **Phase 3** → **Phase 4**

**Why This Organization Works**:
1. **Clean Dependencies**: Each phase builds naturally on the previous
2. **Focused Reviews**: Each PR has a clear, single purpose
3. **Parallel Development**: Phases 2A and 2B can be developed simultaneously
4. **Risk Management**: Issues in later phases don't block earlier foundational work
5. **Rollback Safety**: Each phase can be reverted independently if needed