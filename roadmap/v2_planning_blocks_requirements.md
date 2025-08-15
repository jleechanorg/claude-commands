# V2 Planning Blocks Requirements Specification

**Extracted From**: PR #1221 roadmap/V2_REQUIREMENTS_SPECIFICATION.md  
**Date**: 2025-08-15  
**Status**: ✅ COMPLETE REQUIREMENTS EXTRACTED  

## 🎯 MISSION CRITICAL: V2 Planning Blocks Feature Requirements

### **Executive Summary**
V2 is missing **13 critical features** compared to V1's sophisticated gameplay interface. The planning blocks feature is just one component of a larger V2 parity gap that severely degrades user experience.

### **Core Problem Statement**
- V2 provides significantly degraded user experience vs V1
- Missing core gameplay features, no offline support, limited error handling
- Basic React patterns vs V1's sophisticated 3,690+ line modular architecture
- **CRITICAL**: Planning blocks show placeholder text instead of interactive UI

## 📋 PHASE 1: CRITICAL GAMEPLAY FEATURES (Priority 1)

### 1. **Enhanced Planning Blocks Component** 🎯 PRIMARY TARGET
- **Current Issue**: V2 shows "[Internal thoughts and analysis - see planning block]" placeholder
- **API Field**: `planning_block` as PlanningBlockData JSON from InteractionResponse
- **Required Features**:
  - Interactive buttons for each choice
  - Risk level badges (safe=green, low=blue, medium=orange, high=red)
  - Choice descriptions and analysis
  - Custom action input option
  - Thinking/context sections with gray italic text

#### **JSON Structure from Backend**:
```json
{
  "planning_block": {
    "thinking": "The player is in God Mode, considering companion suggestions...",
    "context": "Your companions have offered their distinct ideas for the party's next steps",
    "choices": {
      "choice1": {
        "text": "Combine elements from multiple suggestions",
        "description": "Create a new plan by blending aspects of the ideas proposed",
        "risk_level": "low"
      },
      "choice2": {
        "text": "Go with Arion's suggestion", 
        "description": "Head towards areas known for skirmishes",
        "risk_level": "medium"
      }
    }
  }
}
```

#### **Implementation Requirements**:
- **File**: Enhance existing `src/components/PlanningBlock.tsx`
- **Integration**: Fix `GamePlayView.tsx` to properly load planning blocks from existing story entries
- **Key Fix**: Convert entries with planning_block field to type='planning' with planningData
- **Styling**: Light blue background (`bg-blue-50 border-blue-200`) matching V1's `#e7f3ff`

### 2. **Session Header Display Component**
- **API Field**: `session_header` from InteractionResponse
- **Parse and Display**: Timestamp, location, character status, HP, XP, gold, conditions, exhaustion, inspiration
- **Format**: `[SESSION_HEADER] Timestamp: 1492 DR, Ches 1st, Morning Location: The Lower Dura Docks...`
- **Component**: Create `src/components/SessionHeader.tsx`

### 3. **Resources Display Component**
- **API Field**: `resources` from InteractionResponse
- **Display**: HD, Spells, Ki, Rage, Potions, Exhaustion counts
- **Styling**: Yellow background (`bg-amber-50 border-amber-200`) to match V1's `#fff3cd`
- **Icon**: 📊 Resources: prefix
- **Component**: Create `src/components/ResourcesDisplay.tsx`

### 4. **Dice Rolls Display Component**
- **API Field**: `dice_rolls` from InteractionResponse
- **Display**: Recent dice rolls with results, modifiers, totals, reasons
- **Styling**: Green background (`bg-green-50 border-green-200`) to match V1's `#d4edda`
- **Icon**: 🎲 Dice Rolls: prefix
- **Component**: Create `src/components/DiceRollsDisplay.tsx`

### 5. **God Mode Response Component**
- **API Field**: `god_mode_response` from InteractionResponse
- **Display**: DM analysis and meta-game information
- **Styling**: Purple/blue background to distinguish from regular content
- **Icon**: 🔮 God Mode Response: prefix
- **Component**: Create `src/components/GodModeResponse.tsx`

### 6. **Location Display Enhancement**
- **Integration**: With Session Header component
- **Feature**: Highlight location changes with 📍 icon
- **Tracking**: Compare previous vs current location from session header

## 🏗️ TECHNICAL ARCHITECTURE REQUIREMENTS

### **React V2 Component Structure**
```typescript
interface StoryEntry {
  actor: 'user' | 'gemini';
  text: string;
  mode?: string;
  session_header?: string;
  resources?: string;
  dice_rolls?: string[];
  planning_block?: PlanningBlockData;
  god_mode_response?: string;
  location_confirmed?: string;
  user_scene_number?: number;
}

interface PlanningBlockData {
  thinking?: string;
  context?: string;
  choices: Record<string, PlanningBlockChoice>;
}

interface PlanningBlockChoice {
  text: string;
  description: string;
  risk_level?: 'low' | 'medium' | 'high' | 'safe';
  analysis?: {
    pros: string[];
    cons: string[];
    confidence: string;
  };
}
```

### **Integration Points**
1. **GamePlayView.tsx Enhancement**:
   - Import and use all 6 new/enhanced components
   - Parse structured fields from API responses
   - Fix planning block loading from existing story entries

2. **No API Changes Required**:
   - V2 already receives all necessary data
   - Frontend-only implementation scope
   - Maintain v1/v2 API compatibility

## 🚨 CRITICAL CONSTRAINTS & REQUIREMENTS

### **API Compatibility Constraint**
- **ARCHITECTURAL PRINCIPLE**: All React V2 fixes must maintain v1/v2 API compatibility
- **No Backend Changes**: Python Flask backend must remain unchanged
- **Frontend-Only Scope**: All fixes implemented through React components only
- **Testing**: Both v1 and v2 must work with identical backend

### **Visual Parity Requirements**
- **Styling**: Must match V1 layout and information density exactly
- **Color Scheme**: 
  - Session Header: Default styling
  - Resources: Yellow (`#fff3cd`)
  - Dice Rolls: Light green (`#e8f4e8`)
  - Planning Blocks: Light blue (`#e7f3ff`)
  - God Mode: Default with preformatted text

### **Backward Compatibility**
- All features must work with existing V1 campaigns
- No breaking changes to existing API responses
- Maintain mobile responsiveness

## 🎯 ACCEPTANCE CRITERIA

### **Phase 1 Success Criteria**
- [ ] Planning blocks render as interactive buttons (not placeholder text)
- [ ] Session header displays all character information identical to V1
- [ ] Resources section shows all D&D 5e resource tracking with yellow styling
- [ ] Dice rolls section displays game mechanics feedback with green styling
- [ ] God mode responses display DM analysis with distinctive styling
- [ ] Location changes highlighted and tracked with 📍 icon
- [ ] Visual styling matches V1 layout and information density
- [ ] All features work with existing V1 campaigns

### **Technical Success Criteria**
- [ ] TypeScript type safety for all new components
- [ ] React Error Boundary handling for graceful failures
- [ ] Performance matches or exceeds V1 (no regressions)
- [ ] Mobile responsiveness maintained
- [ ] All tests pass with new component integration

## 🚀 IMPLEMENTATION PRIORITY

### **Immediate (Week 1)**: Planning Blocks Fix
1. Fix existing PlanningBlock component to render actual JSON data
2. Update GamePlayView.tsx to properly parse planning_block field
3. Test with existing campaigns to ensure backward compatibility

### **Short Term (Week 2)**: Complete Phase 1
1. Implement remaining 5 components (SessionHeader, ResourcesDisplay, etc.)
2. Integrate all components into GamePlayView
3. Ensure visual parity with V1 screenshots

### **Validation Strategy**
- Test with multiple existing campaigns
- Verify all API response fields are properly parsed and displayed
- Ensure no regressions in existing functionality
- Mobile responsiveness validation

---

**Status**: ✅ Complete requirements extracted from PR #1221  
**Next**: Create optimal PR splitting strategy and implementation roadmap  
**Source**: roadmap/V2_REQUIREMENTS_SPECIFICATION.md from PR #1221