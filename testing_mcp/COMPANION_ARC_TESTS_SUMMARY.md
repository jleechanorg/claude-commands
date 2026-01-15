# Companion Quest Arc Tests - What They Validate

## Current Tests Overview

### 1. `test_companion_quest_arcs_real_e2e.py` (Basic Validation)

**What it tests:**
- ✅ Arc initialization by Turn 3-5
- ✅ Arc structure validation (arc_type, phase, progress fields)
- ✅ Arc event structure validation (companion, event_type, description, dialogue, callbacks)
- ✅ Basic tracking in `custom_campaign_state.companion_arcs`

**What it does NOT test:**
- ❌ Complete arc lifecycle (start → finish)
- ❌ Multiple arc events over time
- ❌ Phase progression (discovery → development → crisis → resolution)
- ❌ Arc completion (status: completed)
- ❌ Callback triggering and resolution
- ❌ Arc history tracking

**Test Duration:** ~5 turns (quick validation)

---

### 2. `test_companion_arc_lifecycle_real_e2e.py` (Lifecycle Test - NEW)

**What it tests:**
- ✅ **Arc starts** - Initialization by Turn 3-5
- ✅ **3+ arc events occur** - Multiple missions/developments happen
- ✅ **Phase progression** - Arc moves through phases (discovery → development → crisis → resolution)
- ✅ **Arc finishes** - Status marked as completed
- ✅ **Arc is done** - Final state validation
- ✅ **Progress tracking** - Progress increases over time
- ✅ **History tracking** - Arc events recorded in history

**Test Duration:** Up to 30 turns (comprehensive lifecycle)

**Lifecycle Requirements:**
1. **Start**: Arc initialized with companion
2. **3 Missions**: At least 3 arc events occur
3. **Progression**: Arc moves through at least 2 phases
4. **Finish**: Arc reaches completion (phase: resolution, progress: 100%)
5. **Done**: Arc marked as complete in state

---

## Test Comparison

| Feature | Basic Test | Lifecycle Test |
|---------|-----------|----------------|
| Arc initialization | ✅ | ✅ |
| Arc structure | ✅ | ✅ |
| Arc event structure | ✅ | ✅ |
| Multiple events | ❌ | ✅ (3+) |
| Phase progression | ❌ | ✅ |
| Arc completion | ❌ | ✅ |
| Progress tracking | ❌ | ✅ |
| History tracking | ❌ | ✅ |
| Turn count | ~5 | Up to 30 |

---

## Running the Tests

### Basic Test (Quick Validation)
```bash
BASE_URL=http://localhost:8080 python testing_mcp/test_companion_quest_arcs_real_e2e.py
```

### Lifecycle Test (Full Journey)
```bash
BASE_URL=http://localhost:8080 python testing_mcp/test_companion_arc_lifecycle_real_e2e.py
```

---

## Expected Arc Lifecycle

Based on `living_world_instruction.md`:

1. **Turn 3-5**: Arc initialized (discovery phase, ~0-25% progress)
2. **Turns 4-8**: Arc events every 2 turns (discovery phase, ~25-50% progress)
3. **Turns 9-18**: Arc events every 1-2 turns (development phase, ~50-75% progress)
4. **Turns 19-26**: Arc events (crisis phase, ~75-90% progress)
5. **Turn 27+**: Arc events (resolution phase, ~90-100% progress, completion)

**Total Duration:** ~20-30 turns for complete arc

---

## Validation Criteria

### Basic Test Passes If:
- Campaign created
- Arc initialized by turn 5
- Arc structure is valid
- Arc event structure is valid (if events occur)

### Lifecycle Test Passes If:
- Campaign created
- Arc started (initialized)
- 3+ arc events occurred
- Arc progressed through at least 2 phases
- Arc finished (completed) - *optional in non-strict mode*
- Progress increased over time
- No major progress regressions

---

## Evidence Output

Both tests save evidence to:
- `/tmp/worldarchitect.ai/<branch>/<test_name>/<timestamp>/`
- Includes: README.md, methodology.md, evidence.md, metadata.json
- SHA256 checksums for all files
- Request/response pairs for debugging
