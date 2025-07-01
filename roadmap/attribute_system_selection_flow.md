# Attribute System Selection Flow

## Current Gap
The implementation has `attribute_system` in game state but no way to decide which system to use.

## Proposed Solution: LLM-Guided Selection

### Flow Diagram
```
Player Prompt
    ↓
Gemini Analysis
    ↓
Initial Story + System Recommendation
    ↓
Backend Saves Choice
    ↓
All Future AI Uses That System
```

### Implementation Steps

#### 1. Update Calibration Instruction
Add to `calibration_instruction.md`:
```markdown
## Attribute System Selection

Based on the player's prompt and campaign concept, recommend the most appropriate attribute system:

**Choose "destiny" if:**
- Modern, sci-fi, or non-fantasy settings
- Player mentions complex social interactions
- Psychological realism is important
- Non-combat focus

**Choose "dnd" if:**
- Traditional fantasy setting
- Player mentions D&D specifically
- Combat-heavy campaign
- Player seems new to TTRPGs

Include in your initial response:
[RECOMMENDED_SYSTEM: destiny] or [RECOMMENDED_SYSTEM: dnd]
```

#### 2. Update gemini_service.py
```python
def get_initial_story(prompt, ...):
    # ... existing code ...
    
    response_text = _get_text_from_response(response)
    
    # Extract recommended system
    import re
    system_match = re.search(r'\[RECOMMENDED_SYSTEM: (dnd|destiny)\]', response_text)
    recommended_system = system_match.group(1) if system_match else 'dnd'
    
    # Clean the marker from the response
    clean_response = re.sub(r'\[RECOMMENDED_SYSTEM: (?:dnd|destiny)\]', '', response_text).strip()
    
    return {
        'story': clean_response,
        'recommended_attribute_system': recommended_system
    }
```

#### 3. Update main.py
```python
@app.route('/api/campaigns', methods=['POST'])
def create_campaign_route(user_id):
    # ... existing code ...
    
    # Get initial story with system recommendation
    story_result = gemini_service.get_initial_story(prompt, ...)
    
    # Use LLM recommendation unless explicitly overridden
    attribute_system = data.get('attribute_system') or story_result['recommended_attribute_system']
    
    # Create game state with chosen system
    initial_game_state = GameState(
        custom_campaign_state={'attribute_system': attribute_system}
    ).to_dict()
    
    campaign_id = firestore_service.create_campaign(
        user_id, title, prompt, story_result['story'], 
        initial_game_state, selected_prompts, use_default_world
    )
```

## Alternative: Simple Heuristics

If we don't want to modify the API, use simple rules in main.py:

```python
def guess_attribute_system(prompt, selected_prompts):
    """Simple heuristic to choose system based on prompt"""
    prompt_lower = prompt.lower()
    
    # Check for explicit mentions
    if 'd&d' in prompt_lower or 'dungeons' in prompt_lower:
        return 'dnd'
    
    # Check for genre indicators
    destiny_keywords = ['sci-fi', 'modern', 'cyberpunk', 'space', 'future', 
                       'psychological', 'social', 'intrigue', 'politics']
    
    if any(keyword in prompt_lower for keyword in destiny_keywords):
        return 'destiny'
    
    # Check selected prompts
    if 'destiny' in selected_prompts:
        return 'destiny'
    
    # Default to D&D
    return 'dnd'
```

## Recommendation

Implement the **LLM-guided selection** because:
1. More intelligent analysis of player intent
2. Can consider subtle cues in the prompt
3. Consistent with AI-first design philosophy
4. Easy to override if player disagrees

The LLM is already analyzing the prompt to create the campaign - having it also recommend the attribute system is a natural extension.