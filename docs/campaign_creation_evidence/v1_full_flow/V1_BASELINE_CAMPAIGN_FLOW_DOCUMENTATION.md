# V1 Baseline Campaign Creation Flow Documentation

## Overview
This document captures the complete V1 campaign creation and character creation flow as it works in the baseline Flask implementation. This serves as the definitive reference for implementing V2.

## Complete User Journey

### Step 1: Home/Dashboard Page
**Screenshot**: `v1_flow_step01_home_page.png`
- User starts at campaign list page showing existing campaigns
- Large blue "Start New Campaign" button visible
- URL: `http://localhost:5005/?test_mode=true&test_user_id=test-user-123`

### Step 2: Campaign Basics (Step 1 of 3)
**Screenshot**: `v1_flow_step02_campaign_basics.png`
- **Form Fields**:
  - Campaign Title: Pre-filled with "My Epic Adventure"
  - Campaign Type: Two options (Dragon Knight Campaign selected by default, Custom Campaign)
  - Character: Pre-filled with "Ser Arion"
  - Setting/world: Long text about World of Assiah
  - Campaign description prompt: Expandable section
- **Progress Indicator**: Shows Step 1 of 3 (Basics, AI Style, Launch)
- **Navigation**: Previous (disabled), Next button
- URL: `http://localhost:5005/new-campaign`

### Step 3: AI Style (Step 2 of 3)
**Screenshot**: `v1_flow_step03_ai_style.png`
- **Three Options** (all checkboxes, all checked by default):
  1. Default Fantasy World - "Use the Celestial Wars/Assiah setting"
  2. Mechanical Precision - "Rules accuracy, combat mechanics"
  3. Starting Companions - "Generate complementary party members"
- **Progress Indicator**: Shows Step 2 of 3
- **Navigation**: Previous, Next buttons

### Step 4: Launch (Step 3 of 3)
**Screenshot**: `v1_flow_step04_launch_ready.png`
- **Campaign Summary** shows:
  - Title: My Epic Adventure
  - Character: Ser Arion
  - Description: Brief campaign summary
  - AI Personalities: Narrative, Mechanics
  - Options: Companions, Dragon Knight World
- **Big Green Button**: "Begin Adventure!"
- **Progress Indicator**: Shows Step 3 of 3

### Step 5: Campaign Building Process
**Screenshot**: `v1_flow_step05_building_adventure.png`
- **Loading Screen** with status messages:
  - "📜 Writing your destiny..."
  - "🏗️ Building Your Adventure..."
  - Progress indicators for: Characters, Factions, World, Story
  - **Observed Progression**:
    - 🔄 Characters (initially processing)
    - ⏳ Factions, World, Story (waiting)
    - Progress updates with different status messages like "⚔️ Establishing factions...", "🌍 Defining world rules..."

### Step 6: Campaign Interface Landing
**Screenshot**: `v1_flow_step06_campaign_interface.png`
- **CRITICAL TRANSITION**: After building completes, user lands on campaign-specific URL
- **URL**: `http://localhost:5005/game/UurCuEgcr3rf4YDXjmfM` (unique campaign ID)
- **Interface Shows**:
  - Campaign title "My Epic Adventure" with edit icon
  - Debug mode indicator
  - Back to Dashboard button
  - **Character creation has NOT started yet** - this is campaign setup phase
  - Shows Scene #1 with character creation options

### Step 7: Character Creation Options
**Screenshot**: `v1_flow_step07_character_sheet_generated.png`
- **Three Character Creation Options**:
  1. AI Generated Character - "Let the system design a D&D 5e character based on the provided lore"
  2. Custom Character Concept - "Work with the system to create custom mechanics for unique abilities"
  3. Standard D&D Character - "Choose from standard D&D 5e races and classes"
- User selects AI Generated Character
- System generates complete D&D 5e character sheet with full stats, equipment, backstory

### Step 8: Character Approval & Gameplay Start
**Screenshot**: `v1_flow_step08_gameplay_begun.png`
- **Character Sheet Display**: Full D&D character details
- **Three Final Options**:
  1. Make changes to this character
  2. **Play as this character** (selected)
  3. Design a completely different character
- **GAMEPLAY BEGINS**: Scene #3 shows actual story narration
- **Story Content**: Rich narrative about Ser Arion's moral dilemma
- **Action Options**: Four specific actions user can take in the story
- **Interface Elements**: Character/God mode toggle, input field for actions

## Key Flow Insights

### V1 Flow Pattern
**Campaign Creation → Campaign Interface → Character Creation → Gameplay**

This is different from what tests currently capture. The flow continues well beyond just creating the campaign entry.

### Character Creation is Separate from Campaign Creation
- Campaign creation (Steps 1-3) sets up the world, story, and AI preferences
- Character creation happens AFTER landing on the campaign page
- Character creation involves multiple sub-steps and AI generation

### Rich AI Generation Process
- Building process shows progressive status updates (Characters → Factions → World → Story)
- Character generation creates full D&D 5e stats, equipment, and backstory
- System maintains context between campaign setup and character creation

### Interactive Gameplay Interface
- Final state shows actual RPG interface with:
  - Session headers with character stats
  - Story narration with scene numbers
  - Multiple choice action buttons
  - Character/God mode toggles
  - Text input for custom actions

## Implementation Requirements for V2

### Must Implement
1. **Multi-step campaign wizard** (3 steps: Basics, AI Style, Launch)
2. **Progressive loading/building phase** with status indicators
3. **Campaign-specific URLs** and navigation after creation
4. **Character creation workflow** separate from campaign creation
5. **AI character generation** with full D&D stats
6. **Interactive story interface** with action buttons and narrative display

### V2 Gaps Identified
Current V2 tests only verify campaign creation up to the campaign list. The flow needs to continue through:
- Character creation phase
- AI generation processes
- Story interface with interactive elements
- Action selection and narrative progression

### User Experience Expectations
Users expect the flow to continue seamlessly from campaign creation through character creation to actual gameplay, not just return to a campaign list.

## Files Referenced
- Screenshots saved in: `docs/campaign_creation_evidence/v1_full_flow/`
- Test URL: `http://localhost:5005?test_mode=true&test_user_id=test-user-123`
- Campaign URL pattern: `http://localhost:5005/game/{campaign_id}`

---
**Documentation Date**: August 4, 2025
**V1 Flask Server**: Port 5005
**V2 React Server**: Port 3000
**Evidence Collection**: Complete end-to-end flow captured
