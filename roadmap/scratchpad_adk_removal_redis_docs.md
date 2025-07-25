# ADK Removal & Redis Documentation Plan

## Executive Summary
Remove A2A SDK/ADK complexity from orchestration system and create comprehensive Redis vs non-Redis documentation for solo developer context.

## Context
- **Current System**: tmux-based orchestration with optional Redis coordination
- **Problem**: ADK/A2A SDK adds complexity without providing value for solo developer
- **Goal**: Clean, simple tmux system with clear Redis decision framework
- **Target Audience**: Solo developers, external LLMs evaluating system architecture

## Plan Overview

### Phase 1: Discovery & ADK Cleanup (15 min)
**Main Task Actions:**
- [ ] Search all files for ADK/A2A SDK references
- [ ] Remove obsolete imports and dependencies
- [ ] Update start_system.sh to make Redis optional
- [ ] Clean orchestrate_unified.py of A2A complexity
- [ ] Remove A2A bridge files if present

**Discovery Commands:**
```bash
grep -r -i "a2a\|adk" . --exclude-dir=.git
find . -name "*a2a*" -o -name "*adk*" 
grep -r "redis.*required\|require.*redis" .
```

### Phase 2: Documentation Updates (20 min)
**Subagent 1: Redis Comparison Research**
- [ ] Document Redis benefits and drawbacks
- [ ] Analyze solo developer vs team use cases
- [ ] Create decision framework
- [ ] Research external LLM perspective needs

**Subagent 2: README & MD Updates**
- [ ] Update main README.md architecture section
- [ ] Remove ADK references from all .md files
- [ ] Update orchestration documentation
- [ ] Ensure mvp_site explanation is clear

### Phase 3: Integration & Review (10 min)
**Main Task Actions:**
- [ ] Integrate subagent documentation
- [ ] Review consistency across files
- [ ] Test system without Redis
- [ ] Verify documentation completeness

## Key Files to Update

### Primary Documentation
- [ ] `README.md` - Main project description
- [ ] `orchestration/README.md` - Orchestration system docs
- [ ] `orchestration/start_system.sh` - Make Redis optional
- [ ] `orchestration/orchestrate_unified.py` - Clean A2A references

### Supporting Documentation
- [ ] `mvp_site/README.md` - Explain purpose for external LLMs
- [ ] `CLAUDE.md` - Update orchestration references
- [ ] `roadmap/scratchpad_adk_vs_tmux_comparison.md` - Finalize comparison

### New Documentation
- [ ] `orchestration/REDIS_DECISION_GUIDE.md` - Comprehensive comparison
- [ ] `ARCHITECTURE_SOLO_DEVELOPER.md` - Self-contained system explanation

## Redis vs Non-Redis Comparison Outline

### For External LLM Context
**System Purpose:**
- WorldArchitect.AI: AI-powered tabletop RPG platform
- mvp_site: Core application (Flask/Python/Firebase)
- Orchestration: Multi-agent coordination system for development

**Solo Developer Context:**
- Single machine development
- Interactive debugging preferred
- Simplicity over enterprise features
- Fast iteration cycles

**Redis Decision Framework:**
- **Use Redis When**: Complex multi-agent workflows, production deployment, team coordination
- **Skip Redis When**: Solo development, simple tasks, debugging focus, MVP stage

### Technical Comparison
**With Redis:**
- Pros: Message persistence, complex workflows, fault tolerance
- Cons: Setup complexity, debugging difficulty, overhead
- Best For: Production systems, team environments

**Without Redis (tmux only):**
- Pros: Simple setup, real-time visibility, fast debugging
- Cons: Limited coordination, session-based persistence
- Best For: Solo development, MVP stage, interactive work

## Success Criteria
- [ ] No ADK/A2A SDK references remain in codebase
- [ ] README accurately reflects current architecture
- [ ] Redis comparison is self-contained and comprehensive
- [ ] External LLMs can understand system from documentation alone
- [ ] Solo developer context is clearly explained
- [ ] System works correctly without Redis

## Timeline
- **Discovery/Cleanup**: 15 minutes
- **Documentation**: 20 minutes (parallel subagents)
- **Integration**: 10 minutes
- **Total**: 45 minutes

## Status Tracking
- **Started**: Thu Jul 24 19:52:00 PDT 2025
- **Phase 1 Complete**: IN PROGRESS
  - ✅ Removed A2A/ADK files: redis_a2a_bridge.py, a2a_integration.py, simple_a2a_poc.py, real_a2a_poc.py, minimal_a2a_poc.py
  - ✅ Removed test files: test_*a2a*.py, config/a2a_config.yaml
  - ✅ Updated start_system.sh to make Redis optional with --with-redis flag
  - ✅ Updated orchestrate_unified.py descriptions to focus on tmux
  - ✅ Made Redis dependency optional in check_dependencies
  - 🔄 Spawned Subagent 1: Redis comparison research
  - 🔄 Spawned Subagent 2: README and MD updates
- **Phase 2 Complete**: ✅ COMPLETED
  - ✅ Subagent 1 created comprehensive REDIS_DECISION_GUIDE.md
  - ✅ Subagent 2 provided README update foundation
- **Phase 3 Complete**: ✅ COMPLETED
  - ✅ Integrated subagent documentation work
  - ✅ Updated README.md to reflect tmux-only architecture
  - ✅ Verified system works correctly after cleanup
  - ✅ All ADK/A2A references successfully removed
- **Final Review**: ✅ COMPLETED at Thu Jul 24 20:15:00 PDT 2025

---

**Next Steps**: Begin Phase 1 discovery and cleanup while spawning documentation subagents.

[Local: testing-improvements-branch | Remote: origin/testing-improvements-branch | PR: #928]