# Companion Quest Arc Proof Requirements

## The Problem

Your current test output shows:
```
God Mode:
Setting: fantasy

============================================================
SCENE 1
============================================================
[Game Master narrative with no companion quest arcs visible]
```

**This doesn't prove companion quest arcs are working** because:
- ❌ No companions mentioned in narrative
- ❌ No companion dialogue
- ❌ No arc events visible in story
- ❌ No indication of companion personal quests

## What We Need to Prove

### 1. Companions Exist and Appear
**Evidence needed:**
- Companions are generated (in `npc_data` with `relationship: "companion"`)
- Companions are mentioned in narrative text
- Companions have names and personalities

**Test validation:**
```python
# Check npc_data
companions = [name for name, npc in npc_data.items() 
              if npc.get("relationship") == "companion"]
assert len(companions) > 0, "No companions generated"

# Check narrative mentions companions
assert any(comp in narrative for comp in companions), "Companions not in narrative"
```

### 2. Companion Arc Events Appear in Narrative
**Evidence needed:**
- Companion speaks with dialogue in the story
- Arc event description appears in narrative
- Player sees companion's personal quest unfolding

**Test validation:**
```python
# Check companion_arc_event exists
arc_event = game_state["custom_campaign_state"].get("companion_arc_event")
assert arc_event is not None, "No arc event generated"

# Check companion dialogue appears in narrative
companion_dialogue = arc_event.get("companion_dialogue", "")
assert companion_dialogue in narrative or similar_words_in_narrative(
    companion_dialogue, narrative
), "Companion dialogue not in narrative"
```

### 3. Arc Themes Appear in Story
**Evidence needed:**
- If arc_type is "lost_family", narrative mentions family/search themes
- If arc_type is "personal_redemption", narrative mentions mistakes/atonement
- Arc themes are woven into the story naturally

**Test validation:**
```python
arc_type = arc_event.get("arc_type")
themes = ARC_THEMES[arc_type]  # e.g., ["sister", "missing", "search"]
assert sum(1 for theme in themes if theme in narrative.lower()) >= 2, \
    "Arc themes not appearing in narrative"
```

### 4. Arc Progresses Over Multiple Turns
**Evidence needed:**
- Turn 3-5: Arc initialized (discovery phase)
- Turn 6-8: Arc develops (development phase)
- Turn 9+: Arc reaches crisis/resolution
- Progress increases: 0% → 25% → 50% → 75% → 100%

**Test validation:**
```python
progress_history = []
for turn in range(1, 20):
    # Play turn, get arc progress
    progress = arc.get("progress", 0)
    progress_history.append(progress)
    
assert progress_history[-1] > progress_history[0], "No progress made"
assert any(p >= 100 for p in progress_history), "Arc never completes"
```

### 5. Arc Completes and Affects Story
**Evidence needed:**
- Arc reaches resolution phase
- Progress reaches 100%
- Final arc event appears in narrative
- Story reflects arc completion

**Test validation:**
```python
final_arc = companion_arcs[companion_name]
assert final_arc["phase"] == "resolution", "Arc not in resolution phase"
assert final_arc["progress"] >= 100, "Arc not complete"
assert "arc_complete" in final_event.get("event_type", ""), "No completion event"
```

## Test Structure

### Narrative Validation Test
```python
# 1. Create campaign with companions
campaign = create_campaign(custom_options=["companions"])

# 2. Play 15+ turns
for turn in range(1, 16):
    response = process_action(user_input)
    narrative = extract_narrative(response)
    arc_event = extract_arc_event(response)
    
    # 3. Validate narrative contains arc content
    if arc_event:
        assert companion_dialogue_in_narrative(narrative, arc_event)
        assert arc_themes_in_narrative(narrative, arc_event)
        assert companion_mentioned_in_narrative(narrative, arc_event)

# 4. Validate arc completes
final_state = get_campaign_state()
arcs = extract_companion_arcs(final_state)
assert any(is_arc_complete(arc) for arc in arcs.values())
```

## Expected Narrative Output

**Good Example (Arc Working):**
```
You stand at the crossroads when Lyra approaches, her eyes distant.

"I need to tell you something," she says quietly. "My sister went missing 
three months ago. She had a pendant just like the one that merchant was 
wearing. I... I need to find her."

[Arc event: lost_family, discovery phase, companion_dialogue present]
```

**Bad Example (Arc Not Working):**
```
You stand at the crossroads. The wind stirs, and somewhere beyond the 
trees, a lone raven calls.

[No companions, no dialogue, no arc events]
```

## Tests Created

1. **`test_companion_quest_arcs_real_e2e.py`** - Validates data structures
2. **`test_companion_arc_lifecycle_real_e2e.py`** - Validates complete lifecycle
3. **`test_companion_arc_narrative_validation.py`** - **Validates narrative contains arcs**

## Running the Proof Test

```bash
BASE_URL=http://localhost:8080 python testing_mcp/test_companion_arc_narrative_validation.py
```

This test will:
- ✅ Check companions are generated
- ✅ Check companions appear in narrative
- ✅ Check companion dialogue appears in story
- ✅ Check arc themes appear in narrative
- ✅ Check arc events are visible to players
- ✅ Save narrative excerpts as evidence

## Success Criteria

The test proves companion quest arcs are working if:
1. ✅ Companions exist in game state
2. ✅ Companions mentioned in narrative text
3. ✅ Companion dialogue appears in story
4. ✅ Arc events appear in narrative (not just data)
5. ✅ Arc themes woven into story
6. ✅ Arc progresses over multiple turns
7. ✅ Arc completes and affects narrative

If ALL of these pass, companion quest arcs are PROVEN to be working.
