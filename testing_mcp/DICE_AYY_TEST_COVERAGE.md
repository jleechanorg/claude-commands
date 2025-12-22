# DICE-ayy Test Coverage Analysis

## Executive Summary

**Gap Identified**: NO existing tests catch the DICE-ayy scenario (smart LLM skill check decisions without explicit user requests).

**Solution**: Created `test_smart_skill_checks_real_api.py` - comprehensive regression test suite for DICE-ayy gap detection.

**Status**: ✅ Coverage gap CLOSED

---

## Existing Test Analysis

### ❌ Scripts That DON'T Catch DICE-ayy

#### 1. `scripts/smoke_test_dice_code_execution.py`
**Why it misses DICE-ayy:**
```python
user_input = "I attack the goblin with my longsword. Roll to hit and damage."
#             ^^^^^^ combat keyword      ^^^^^^^^^^^^^^^ explicit dice request
```
- Has **combat keyword** "attack"
- Has **explicit dice request** "Roll to hit"
- Triggers user input detection (which works)
- Doesn't test smart LLM decisions

#### 2. `scripts/mcp-smoke-tests.mjs`
**Why it misses DICE-ayy:**
```javascript
user_input = "A goblin lunges at me! I swing my sword to defend and strike back. Roll my attack."
//                                      ^^^^^^^^^^^^^ combat                ^^^^^^^^^^^^^^^ explicit
```
- Has **combat keywords** "swing", "sword", "strike", "attack"
- Has **explicit dice request** "Roll my attack"
- Tests combat scenarios only

#### 3. `testing_mcp/test_social_encounter_real_api.py`
**Why it misses DICE-ayy:**
```python
user_input = "I stare down the guard and demand entry. Make an Intimidation check."
#                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^
user_input = "I lie smoothly about our business here. Make a Deception check."
#                                                      ^^^^^^^^^^^^^^^^^^^^^^^
```
- Has **explicit check requests** "Make a X check"
- Tests social scenarios but with explicit dice language
- Doesn't test smart LLM decisions without prompting

#### 4. `testing_mcp/test_dice_rolls_comprehensive.py`
**Why it misses DICE-ayy:**
```python
"I attack the goblin with my longsword. Resolve the attack and damage."  # Combat
"I try to sneak past the guards. Make a Stealth check."                  # Explicit
"I brace myself against dragon fire. Make a Constitution saving throw."  # Explicit
```
- All scenarios have combat keywords OR explicit check requests
- Comprehensive for known triggers, not smart decisions

---

## The DICE-ayy Gap

### What It Was

```
┌─────────────────────────────────────────────────────────────────┐
│ User Input: "Demand Lantry's Release"                           │
│ ├─ NO combat keywords (no "attack", "cast", etc.)               │
│ └─ NO explicit check request (no "Make a check")                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LLM Smart Decision: "Intimidation check appropriate"            │
│ LLM Response: "[DICE: Intimidation 1d20+9 = 25]"                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ OLD SYSTEM (Pre-DICE-ayy):                                      │
│ ├─ Only checks USER INPUT for combat keywords                   │
│ ├─ Finds none → No enforcement triggered                        │
│ └─ Result: DICE FABRICATED (not from code_execution)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ NEW SYSTEM (Post-DICE-ayy commit b51e7cb07):                    │
│ ├─ Checks user input for combat keywords (finds none)           │
│ ├─ ALSO scans LLM NARRATIVE for dice patterns                   │
│ ├─ Finds "[DICE: ...]" in narrative without code_execution      │
│ ├─ Triggers dice_integrity_violation flag                       │
│ └─ Result: REPROMPT forced, real dice rolled                    │
└─────────────────────────────────────────────────────────────────┘
```

### Production Evidence

**Campaign**: qjVpLfowsILq40DFKD6N ("Tyranny")
- 144 story entries
- 12 entries with dice
- **100% dice from text_pattern** (fabricated)
- **0% dice from code_execution** (real)

**Example Entry**:
- User: "Demand Lantry's Release"
- LLM: Added Intimidation check
- System: Didn't detect (no user input triggers)
- Result: Fabricated dice in narrative

---

## ✅ NEW Test Coverage

### `test_smart_skill_checks_real_api.py`

**Purpose**: Regression test for DICE-ayy gap - validates smart LLM skill check decisions use real dice.

**Test Scenarios** (5 total):

1. **Intimidation (implicit)**
   ```python
   user_input = "I demand the guard stand down immediately and let us pass."
   # NO combat keywords, NO "Make a check"
   # LLM must decide: Intimidation check needed
   ```

2. **Persuasion (implicit)**
   ```python
   user_input = "I try to convince the merchant to lower the price by 50 gold pieces."
   # NO combat keywords, NO "Make a check"
   # LLM must decide: Persuasion check needed
   ```

3. **Deception (implicit)**
   ```python
   user_input = "I tell the captain a convincing story about why we're here."
   # NO combat keywords, NO "Make a check"
   # LLM must decide: Deception check needed
   ```

4. **Perception (implicit)**
   ```python
   user_input = "I carefully examine the bookshelf for anything unusual."
   # NO combat keywords, NO "Make a check"
   # LLM must decide: Perception check needed
   ```

5. **Insight (implicit)**
   ```python
   user_input = "I watch the noble's reactions carefully as he speaks."
   # NO combat keywords, NO "Make a check"
   # LLM must decide: Insight check needed
   ```

### Validation Logic

For each scenario, validates:

```python
def validate_smart_skill_check(result, scenario, user_input):
    errors = []

    # 1. Test integrity: NO combat keywords in user input
    if has_combat_keywords(user_input):
        errors.append("Test contaminated - combat keywords present")

    # 2. Test integrity: NO explicit check requests
    if has_explicit_check_request(user_input):
        errors.append("Test contaminated - explicit check request")

    # 3. LLM made decision: Dice rolls exist (unless --allow-no-dice)
    if not result.get("dice_rolls"):
        errors.append("No dice rolls - LLM didn't make skill check decision")

    # 4. CRITICAL: Dice provenance depends on strategy
    # - Gemini (code_execution): code_execution evidence present
    # - Native two-phase: tool_results present (requires CAPTURE_EVIDENCE)

    # 5. Executable code parts exist (Gemini only)

    # 6. No dice integrity violation flag
    if result.get("debug_info", {}).get("dice_integrity_violation"):
        errors.append("Narrative detection triggered violation flag")

    return errors
```

**CRITICAL FAILURE**: Dice exist without the correct evidence
- Gemini: missing code_execution evidence
- Native two-phase: missing tool_results

---

## Usage Examples

### Quick Test (Existing MCP Server)

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --server-url http://127.0.0.1:8001
```

### Auto-Start Local Server (Mock Mode)

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local
```

### Real API Testing

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --real-services
```

Note: Native two-phase validation requires tool_results in the response. The local
server launched by the test enables CAPTURE_EVIDENCE automatically (tool results are always captured).

### With Evidence Collection

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --real-services --evidence

# Evidence saved to: testing_mcp/evidence/smart_skill_checks/
```

---

## Complete Test Coverage Matrix

| Test File | Combat Keywords | Explicit Checks | Smart LLM Decisions | Catches DICE-ayy |
|-----------|----------------|-----------------|---------------------|------------------|
| `smoke_test_dice_code_execution.py` | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| `mcp-smoke-tests.mjs` | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| `test_social_encounter_real_api.py` | ❌ No | ✅ Yes | ❌ No | ❌ No |
| `test_dice_rolls_comprehensive.py` | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **`test_smart_skill_checks_real_api.py`** | ❌ No | ❌ No | ✅ Yes | ✅ **YES** |

---

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: DICE-ayy Regression Test
  run: |
    cd testing_mcp
    python test_smart_skill_checks_real_api.py --start-local --real-services
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    CEREBRAS_API_KEY: ${{ secrets.CEREBRAS_API_KEY }}
```

---

## Conclusion

**Before**: ZERO tests caught DICE-ayy gap (smart LLM decisions without explicit triggers)

**After**: ✅ Complete coverage with 10 regression tests (5 scenarios × 2 models)

**Future Protection**: If DICE-ayy gap returns, this test suite will catch it immediately.

**Files Created**:
1. `testing_mcp/test_smart_skill_checks_real_api.py` - Main test suite
2. `testing_mcp/README_SMART_SKILL_CHECKS.md` - Usage documentation
3. `testing_mcp/DICE_AYY_TEST_COVERAGE.md` - This analysis document

**Related Work**:
- **DICE-ayy Fix**: commit `b51e7cb07` (2025-12-20)
- **Gap Discovery**: Tyranny campaign audit (100% fabrication rate)
- **Evidence Packages**: `/tmp/worldarchitect_mcp_evidence_20251220_174453/`
