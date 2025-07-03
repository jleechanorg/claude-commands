# Prompt Loading Logic - Test Planning

## Overview
Need to test which prompt files are loaded based on user checkbox selections during campaign creation.

## Checkbox Options
1. **Narrative** (id: `prompt-narrative`, value: `narrative`)
2. **Mechanics** (id: `prompt-mechanics`, value: `mechanics`)

## Loading Logic

### Base Files (Always Loaded)
1. `master_directive.md` - Loading hierarchy
2. `game_state_instruction.md` - State management
3. `dnd_srd_instruction.md` - D&D 5E rules

### Conditional Files

#### When Narrative Selected
- `narrative_system_instruction.md` - Storytelling protocol

#### When Mechanics Selected  
- `mechanics_system_instruction.md` - Dice, combat, **character creation**
- Character creation triggers at campaign start

#### Template Files (Context-Dependent)
- `character_template.md` - Loaded when needed for NPC development

## Test Cases

### Case 1: Both Checkboxes Selected (Default)
- **Input**: narrative=True, mechanics=True
- **Expected Files Loaded**:
  - master_directive.md
  - game_state_instruction.md
  - dnd_srd_instruction.md
  - narrative_system_instruction.md
  - mechanics_system_instruction.md
- **Character Creation**: Yes (because mechanics enabled)

### Case 2: Only Narrative Selected
- **Input**: narrative=True, mechanics=False
- **Expected Files Loaded**:
  - master_directive.md
  - game_state_instruction.md
  - dnd_srd_instruction.md
  - narrative_system_instruction.md
- **Character Creation**: No

### Case 3: Only Mechanics Selected
- **Input**: narrative=False, mechanics=True
- **Expected Files Loaded**:
  - master_directive.md
  - game_state_instruction.md
  - dnd_srd_instruction.md
  - mechanics_system_instruction.md
- **Character Creation**: Yes

### Case 4: No Checkboxes Selected
- **Input**: narrative=False, mechanics=False
- **Expected Files Loaded**:
  - master_directive.md
  - game_state_instruction.md
  - dnd_srd_instruction.md
- **Character Creation**: No

## API Endpoint
The `/api/campaigns` POST endpoint accepts:
```json
{
  "prompt": "campaign description",
  "title": "campaign title",
  "selected_prompts": ["narrative", "mechanics"],
  "custom_options": ["companions", "defaultWorld"]
}
```

## Code Location
- Backend logic likely in `main.py` or `gemini_service.py`
- Need to find where `selected_prompts` is processed
- Look for prompt file loading logic

## Test Strategy
1. Create unit test that mocks the campaign creation
2. Use temporary directory for test prompt files
3. Assert correct files are loaded for each permutation
4. Verify character creation triggers only when mechanics enabled
5. Check that base files are always loaded

## Additional Considerations
- Custom options (companions, defaultWorld) don't affect prompt loading
- Character template is loaded on-demand, not during initial setup
- Need to mock file system operations to avoid touching real prompt files