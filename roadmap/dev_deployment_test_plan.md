# Dev Deployment Test Plan

## Deployment Complete
URL: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app

## Test the D&D Checkbox Feature

### 1. Create Campaign with Destiny System (Default)
1. Go to the dev site
2. Create a new campaign
3. **Do NOT check** "Use D&D 6-Attribute System"
4. Enter prompt: "A cyberpunk heist in Neo-Tokyo"
5. Submit

**Expected**:
- Game state should have `custom_campaign_state.attribute_system = "destiny"`
- Character generation should use 5 aptitudes
- Social interactions use personality traits

### 2. Create Campaign with D&D System
1. Create another campaign
2. **CHECK** "Use D&D 6-Attribute System"
3. Enter prompt: "Classic D&D dungeon crawl"
4. Submit

**Expected**:
- Game state should have `custom_campaign_state.attribute_system = "dnd"`
- Character generation should use 6 attributes (STR, DEX, CON, INT, WIS, CHA)
- Social interactions use CHA

### 3. Verify State Persistence
1. Navigate away from campaign
2. Return to campaign
3. Check if attribute system is still correctly set

### 4. Check AI Behavior
1. In Destiny campaign: Ask AI to show character stats
   - Should show: Physique, Coordination, Health, Intelligence, Wisdom
2. In D&D campaign: Ask AI to show character stats
   - Should show: STR, DEX, CON, INT, WIS, CHA

## Debugging

If issues arise, check:
1. Browser console for JavaScript errors
2. Network tab for API responses
3. Game state in Firestore to verify attribute_system is saved

## Success Criteria
- [ ] Checkbox appears in campaign creation form
- [ ] Default (unchecked) creates Destiny campaign
- [ ] Checked creates D&D campaign
- [ ] Attribute system persists in game state
- [ ] AI respects the chosen system
