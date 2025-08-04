# React V2 Fixes Engineering Design

## 🚀 COMPLETED: Google SSO Authentication System (PR #1163)

**Status**: ✅ **PRODUCTION READY** - Implemented in [PR #1163](https://github.com/jleechanorg/worldarchitect.ai/pull/1163)

### 🔐 Authentication Architecture Implemented
- **Firebase v9+ Google OAuth**: Complete SSO integration with modern SDK
- **Production Authentication**: Real Firebase OAuth replacing mock system
- **Token Management**: JWT handling with clock skew recovery mechanisms
- **Test Mode Support**: Development-friendly authentication bypass
- **API Integration**: Seamless authentication headers for Flask backend
- **State Management**: Zustand store integration with persistent sessions

### 🧪 Matrix Testing Framework Implemented
- **587-line Test Specification**: Comprehensive authentication validation methodology
- **Evidence-Based Testing**: Screenshot validation with path labeling requirements
- **Quality Assurance Protocols**: Systematic testing approach from CLAUDE.md
- **Multi-Environment Support**: Test mode and production mode validation

### 📊 Implementation Statistics
- **Files Changed**: 54 files
- **Lines Added**: 7,309 additions
- **Lines Removed**: 399 deletions
- **Key Files**: `api.service.ts`, `firebase.ts`, `useAuth.tsx`, authentication components

---

## 📝 PENDING: UI Fixes Implementation Status

<!-- NOTE: This section describes the intended engineering design for UI fixes.
     Implementation work starts after the authentication system is complete. -->

**Purpose**: This section outlines the technical approach for implementing 12 critical React V2 UI fixes to achieve feature parity with Flask V1.

### Screenshots
- Landing page: `screenshots/react_v2_fixes/01_initial_load.png`

### ACTUAL Implementation Status - Based on Manual UI Testing

#### ✅ Working Features (Verified)
2. ✅ Replaced "Loading campaign details..." with character/world data - **CONFIRMED: No placeholder text found**
6. ✅ Fixed Dragon Knight campaign description - **CONFIRMED: Rich description present**
12. ✅ Campaign pages display content - **CONFIRMED: Game view shows story and interface**

#### ❌ Critical Issues Still Present (Verified)
3. ❌ Settings button placed beside Create Campaign - **MISSING: No settings button visible on dashboard**
4. ❌ Signout button added to settings page - **UNTESTABLE: Settings not accessible**
5. ❌ Removed "intermediate • fantasy" tags - **CRITICAL ISSUE: Still visible on all campaign cards**
7. ❌ Custom character names no longer stuck on "Ser Arion" - **CRITICAL ISSUE: Hardcoded in creation form**
11. ❌ Campaign URLs update with ID - **CRITICAL ISSUE: URLs don't change on navigation**

#### ❓ Needs Further Testing
1. ❓ Sort options matching old UI - **LIMITED: Only mock data available for testing**
8. ❓ AI personality fields hidden by default - **OBSERVED: All options checked in step 2, need to verify default behavior**
9. ❓ World selection displays correctly - **OBSERVED: Dragon Knight defaults show, need custom testing**
10. ❓ Loading spinner added to campaign creation - **NOT TESTED: Didn't complete creation flow**

## Technical Overview

### UPDATED Current State Analysis - Post-Audit

#### ✅ Issues Resolved
- ✅ "Loading campaign details..." placeholder text - **FIXED: No instances found**
- ✅ Dragon Knight description - **FIXED: Rich description present**
- ✅ API integration - **WORKING: Game view shows dynamic content**
- ✅ Campaign content display - **WORKING: Game interface functional**

#### ❌ Critical Issues Still Present
- ❌ **Hardcoded "Ser Arion"** - Still in CampaignCreationV2.tsx (lines 38, 249, 290)
- ❌ **"intermediate • fantasy" text** - Visible on all campaign cards in list
- ❌ **No URL routing** - Campaign clicks don't update URL to /campaign/:id
- ❌ **Non-functional settings buttons** - Per-campaign settings do nothing
- ❌ **Missing global settings access** - No settings button beside Create Campaign
- ❌ **No sign-out functionality** - Cannot access settings page

#### ❓ Requires Testing
- ❓ Character name persistence in actual campaign creation
- ❓ World selection behavior beyond Dragon Knight defaults
- ❓ Loading states during real campaign creation
- ❓ Sort functionality with larger dataset

### REVISED Architecture Approach - Based on Audit Findings

#### Immediate Priority Fixes (Critical Path)
1. **Fix Hardcoded Values**
   - Replace "Ser Arion" with dynamic character name variables
   - Remove "intermediate • fantasy" text from campaign cards
   - Files: `CampaignCreationV2.tsx`, `CampaignList.tsx`

2. **Implement URL Routing**
   - Add React Router navigation for campaign links
   - Update campaign click handlers to use history.push
   - File: `App.tsx`, campaign link components

3. **Add Missing UI Elements**
   - Settings button beside Create Campaign button
   - Remove non-functional per-campaign settings buttons
   - File: `CampaignList.tsx`, settings components

#### Secondary Fixes (Post-Critical)
- Complete sign-out functionality implementation
- Test and verify character name persistence
- Validate world selection behavior
- Add loading states for campaign creation

### Technology Choices - Updated
- **Routing**: React Router v6 (NEEDED: Currently missing, causing URL update failures)
- **State Management**: Existing Zustand stores (appears functional)
- **UI Components**: Existing shadcn/ui components (working well)
- **API Integration**: Existing service layer (appears functional)
- **State**: Existing Zustand stores (enhance usage)
- **API**: Existing API service (fix integration)
- **UI**: Existing shadcn/ui components (properly utilize)

## System Design

### Component Architecture

```
App.tsx
├── Router
│   ├── Dashboard Route (/)
│   │   └── Dashboard.tsx
│   │       ├── CampaignList.tsx
│   │       │   └── CampaignCard.tsx (dynamic data)
│   │       └── Header.tsx (with Settings button)
│   │
│   ├── Campaign Route (/campaign/:id)
│   │   └── GameView.tsx
│   │       ├── StoryArea.tsx
│   │       └── ActionPanel.tsx
│   │
│   ├── New Campaign Route (/new-campaign)
│   │   └── CampaignCreation.tsx
│   │       ├── CampaignTypeSelector.tsx
│   │       └── CampaignForm.tsx (dynamic fields)
│   │
│   └── Settings Route (/settings)
│       └── Settings.tsx
│           └── SignOutButton.tsx
```

### Data Flow Diagram

```
User Action → Component → Store Action → API Call → Response
     ↓            ↓            ↓            ↓          ↓
   Event      UI Update    Store Update  Backend   Store Update
                               ↓                        ↓
                          Loading State            Component Re-render
```

### State Management

#### Campaign Store Enhancement
```typescript
interface CampaignStore {
  campaigns: Campaign[]
  currentCampaign: Campaign | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchCampaigns: () => Promise<void>
  selectCampaign: (id: string) => Promise<void>
  createCampaign: (data: CampaignData) => Promise<Campaign>
  updateCampaign: (id: string, data: Partial<Campaign>) => Promise<void>
  deleteCampaign: (id: string) => Promise<void>
}
```

#### Auth Store Enhancement
```typescript
interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  checkAuth: () => Promise<void>
}
```

## API Design

### Required Endpoints (Existing - Need Integration)

#### Campaign Management
```
GET    /api/campaigns          → List user campaigns
POST   /api/campaigns          → Create new campaign
GET    /api/campaigns/:id      → Get campaign details
PUT    /api/campaigns/:id      → Update campaign
DELETE /api/campaigns/:id      → Delete campaign
```

#### Game Session
```
GET    /api/campaigns/:id/story     → Get story entries
POST   /api/campaigns/:id/action    → Submit player action
GET    /api/campaigns/:id/state     → Get game state
```

### Request/Response Schemas

#### Campaign List Response
```typescript
interface CampaignListResponse {
  campaigns: Array<{
    id: string
    title: string
    characterName: string      // Not "Ser Arion" hardcoded
    worldSetting: string       // Actual world description
    created: string
    lastPlayed: string
    status: 'active' | 'paused' | 'completed'
    progress: number           // 0-100
  }>
}
```

#### Create Campaign Request
```typescript
interface CreateCampaignRequest {
  title: string
  type: 'dragon_knight' | 'custom'
  characterName: string
  worldSetting?: string
  description: string
  aiPersonality?: string      // Only if non-default
}
```

### Error Handling
- Network errors → Retry with exponential backoff
- 401 errors → Redirect to auth
- 404 errors → Show "Campaign not found"
- 500 errors → Show user-friendly error

## Implementation Plan

### Phase 1: Fix Data Flow (Priority: CRITICAL)
- [ ] Remove all hardcoded values from components
- [ ] Fix hardcoded "Ser Arion" character name
- [ ] Replace "Loading campaign details..." with actual character/world data
- [ ] Remove "intermediate • fantasy" text
- [ ] Connect Dashboard to campaign store
- [ ] Implement proper props passing
- [ ] Add loading states to all async operations

**Files to modify:**
- `Dashboard.tsx` - Remove hardcoded campaigns, fix campaign card display
- `CampaignList.tsx` - Use real data from store
- `GameView.tsx` - Use campaign.characterName instead of hardcoded
- `campaignStore.ts` - Implement API calls

### Phase 2: Implement Navigation (Priority: HIGH)
- [ ] Add React Router to App.tsx
- [ ] Implement route handlers
- [ ] Add URL parameter handling
- [ ] Fix campaign click navigation

**Files to modify:**
- `App.tsx` - Add Router setup
- `main.tsx` - Wrap with BrowserRouter
- `Dashboard.tsx` - Add navigation handlers

### Phase 3: Fix Campaign Creation (Priority: HIGH)
- [ ] Dynamic character name updates (not stuck on "Ser Arion")
- [ ] World selection affects display correctly
- [ ] Add loading spinner matching old site theme
- [ ] Dragon Knight shows full description prompt
- [ ] Hide AI personality field when default
- [ ] Fix world options display bug
- [ ] Proper form validation

**Files to modify:**
- `CampaignCreation.tsx` - Dynamic form, conditional fields
- `api.service.ts` - Creation endpoint
- Form components - Fix data binding

### Phase 4: UI Polish (Priority: MEDIUM)
- [ ] Remove all placeholder texts
- [ ] Add sign out button to settings page
- [ ] Position settings button beside Create Campaign
- [ ] Remove non-functional per-campaign settings button
- [ ] Ensure game view shows content (not blank page)

**Files to modify:**
- `Settings.tsx` - Add prominent sign out button
- `Dashboard.tsx` - Add settings button placement
- `GameView.tsx` - Remove per-campaign settings
- `Header.tsx` - Clean up button layout

## Testing Strategy

### Unit Tests
```typescript
// Dashboard.test.tsx
test('displays actual campaign names, not hardcoded', () => {
  render(<Dashboard campaigns={mockCampaigns} />)
  expect(screen.getByText('My Custom Character')).toBeInTheDocument()
  expect(screen.queryByText('Ser Arion')).not.toBeInTheDocument()
})

test('shows character and world instead of loading text', () => {
  render(<Dashboard campaigns={mockCampaigns} />)
  expect(screen.queryByText('Loading campaign details...')).not.toBeInTheDocument()
  expect(screen.getByText('Thorin')).toBeInTheDocument()
  expect(screen.getByText('Middle Earth')).toBeInTheDocument()
})

test('settings button appears next to create campaign', () => {
  render(<Dashboard />)
  const createBtn = screen.getByText('Create Campaign')
  const settingsBtn = screen.getByLabelText('Settings')
  expect(settingsBtn).toBeInTheDocument()
  // Check they're siblings or close in DOM
})

// CampaignCreation.test.tsx
test('character name updates dynamically', () => {
  render(<CampaignCreation />)
  const input = screen.getByLabelText('Character Name')
  fireEvent.change(input, { target: { value: 'Gandalf' } })
  expect(screen.getByText(/playing as Gandalf/)).toBeInTheDocument()
  expect(screen.queryByText('Ser Arion')).not.toBeInTheDocument()
})

test('AI personality hidden when default', () => {
  render(<CampaignCreation />)
  expect(screen.queryByLabelText('AI Personality')).not.toBeInTheDocument()
})

test('Dragon Knight shows full description field', () => {
  render(<CampaignCreation type="dragon_knight" />)
  expect(screen.getByLabelText('Campaign Description')).toBeInTheDocument()
  expect(screen.getByPlaceholderText(/long form/)).toBeInTheDocument()
})

// GameView.test.tsx
test('clicking campaign updates URL', () => {
  const campaign = { id: '123', title: 'Test' }
  render(<Dashboard campaigns={[campaign]} />)
  fireEvent.click(screen.getByText('Test'))
  expect(window.location.pathname).toBe('/campaign/123')
})

test('game view displays content', () => {
  render(<GameView campaign={mockCampaign} />)
  expect(screen.getByText(/adventure begins/)).toBeInTheDocument()
  expect(screen.queryByText(/loading/)).not.toBeInTheDocument()
})
```

### Integration Tests
- Create campaign → Appears in dashboard
- Click campaign → Navigate to game view
- Sign out → Return to auth screen
- Deep link → Load specific campaign

### Acceptance Tests
- [ ] New user can create first campaign
- [ ] Returning user sees all campaigns
- [ ] Campaign data persists between sessions
- [ ] Navigation works with browser buttons

## Rollout Plan

### Feature Flags
```typescript
const featureFlags = {
  newNavigation: process.env.REACT_APP_NEW_NAV === 'true',
  dynamicCampaigns: process.env.REACT_APP_DYNAMIC_DATA === 'true'
}
```

### Staged Rollout
1. **Internal Testing**: Deploy to staging
2. **Beta Users**: 10% rollout
3. **Gradual Increase**: 25% → 50% → 100%
4. **Monitor**: Error rates, user feedback

### Rollback Strategy
- Feature flags for instant disable
- Previous version tagged in git
- Database migrations reversible
- Cache clear instructions ready

## Monitoring & Success Metrics

### Logging Strategy
```typescript
// Add to critical paths
logger.info('Campaign navigation', {
  userId: user.id,
  campaignId: campaign.id,
  action: 'navigate',
  timestamp: new Date()
})
```

### Performance Monitoring
- Dashboard load time < 2s
- Campaign creation < 5s
- Navigation transitions < 300ms

### User Analytics
- Campaign creation success rate
- Navigation completion rate
- Error occurrence rate
- Feature adoption metrics

## Critical Bugs to Fix

### P0 - Breaking Issues
1. **Hardcoded Character Names**: All campaigns show "Ser Arion" instead of actual character
2. **No URL Navigation**: Clicking campaigns doesn't update URL or navigate
3. **Blank Game View**: Campaign page shows nothing when accessed
4. **Form Data Not Saving**: Character name input doesn't persist to campaign

### P1 - Major Issues
1. **"Loading campaign details..."**: Shows placeholder instead of real data
2. **Settings Button Missing**: Not positioned next to Create Campaign
3. **No Sign Out**: Settings page missing sign out button
4. **Dragon Knight Description**: Missing long form description field
5. **World Selection Bug**: Always shows "Dragon Knight world"

### P2 - UI Polish
1. **"intermediate • fantasy"**: Unnecessary text on campaign cards
2. **Per-Campaign Settings**: Non-functional button should be removed
3. **AI Personality**: Should be hidden when default
4. **Loading Spinner**: Needs to match old site theme

## Implementation Timeline

### Test-First Development Schedule

#### Pre-Implementation: Test Suite Creation (MANDATORY)
- Write comprehensive failing tests for all 12 critical issues
- Verify tests fail for current implementation
- Commit test suite to establish baseline

#### Phase 1: P0 Critical Fixes (Test-Driven)
- Fix hardcoded data issues (tests must pass)
- Implement URL navigation (tests must pass)
- Fix blank campaign pages (tests must pass)
- Fix form persistence (tests must pass)

#### Phase 2: P1 Major Issues (Test-Driven)
- Replace placeholder text (tests must pass)
- Add settings/signout buttons (tests must pass)
- Fix display bugs (tests must pass)

#### Phase 3: Integration & Polish
- Full test suite verification
- Performance optimization
- Accessibility compliance
- Production deployment
