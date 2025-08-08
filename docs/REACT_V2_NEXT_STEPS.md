# React V2 - Next Priority Fixes

**Based on**: Visual testing evidence + Gap analysis + User impact  
**Date**: 2025-08-08

## 🚨 IMMEDIATE PRIORITY: Settings & Sign-Out Access

### Fix #1: Add Global Settings Button
**Why Critical**: Users cannot sign out - security issue

**Implementation**:
```jsx
// Location: mvp_site/frontend_v2/src/components/Header.tsx (or similar)

// Add beside Create Campaign button:
<button className="btn btn-secondary" onClick={navigateToSettings}>
  <i className="fas fa-cog"></i> Settings
</button>
```

**Files to modify**:
- Header component
- Routing configuration
- Settings page component (create new)

### Fix #2: Implement Settings Page with Sign-Out
**Components needed**:
1. Settings page route
2. Sign-out button
3. Firebase auth integration for sign-out
4. Redirect to login after sign-out

**Code location**: `mvp_site/frontend_v2/src/pages/Settings.tsx` (new file)

## 📍 HIGH PRIORITY: URL Routing

### Fix #3: Campaign Click Navigation
**Current**: Clicking campaigns doesn't update URL  
**Target**: URL should change to `/campaign/:id`

**Implementation**:
```jsx
// In CampaignCard component
const handleCampaignClick = (campaignId) => {
  navigate(`/campaign/${campaignId}`);
};
```

**Testing**:
1. Click campaign card
2. Verify URL updates
3. Test browser back/forward
4. Test deep linking

## 🎯 QUICK WINS (Can do immediately)

### Fix #4: Clean up per-campaign settings buttons
**Decision needed**:
- Option A: Remove gear icons from campaign cards (simpler)
- Option B: Implement campaign-specific settings (more work)

**Recommendation**: Remove for now, add in future update

## 📋 Implementation Order

### Sprint 1 (30 minutes) - Critical Security
1. Add settings button to header
2. Create settings page with sign-out
3. Test sign-out flow
4. Verify redirect to login

### Sprint 2 (30 minutes) - Navigation
1. Implement React Router v6 properly
2. Add campaign click navigation
3. Test URL updates
4. Verify browser history works

### Sprint 3 (15 minutes) - Cleanup
1. Remove/hide per-campaign settings buttons
2. Clean up any console errors
3. Final testing

## 🧪 Testing Checklist

### After Sprint 1:
- [ ] Settings button visible in header
- [ ] Settings page accessible
- [ ] Sign-out button works
- [ ] User redirected after sign-out

### After Sprint 2:
- [ ] Campaign URLs update on click
- [ ] Browser back/forward works
- [ ] Deep links function
- [ ] No navigation errors

### After Sprint 3:
- [ ] UI is clean and consistent
- [ ] No console errors
- [ ] All critical features work

## 💻 Commands to Start

```bash
# Terminal 1: Backend
cd /home/jleechan/projects/worldarchitect.ai/worktree_human
./run_local_server.sh

# Terminal 2: Frontend
cd mvp_site/frontend_v2
npm run dev

# Access: http://localhost:3002
```

## 📊 Success Metrics

1. **User can sign out** - Critical security requirement
2. **URLs update on navigation** - Core UX requirement
3. **No broken UI elements** - Professional appearance
4. **Zero console errors** - Clean implementation

## 🚀 Ready to Start?

The highest priority is adding the settings button and sign-out functionality. This unblocks a critical security issue where users cannot sign out of their accounts.

**Estimated time to fix all critical issues**: 75-90 minutes

**Tools needed**:
- React components
- React Router v6
- Firebase Auth SDK
- CSS for styling