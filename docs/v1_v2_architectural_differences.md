# V1/V2 Architectural Differences Reference

**Purpose**: Technical reference for understanding the fundamental architectural differences between V1 (Flask/server-side) and V2 (React/client-side) implementations.

## 🏗️ Core Architecture Comparison

### V1 Architecture (Server-Side Rendering)
- **Framework**: Flask with Jinja2 templates
- **Data Loading**: Server-side data fetching before page render
- **State Management**: Server maintains session state
- **File Locations**: `mvp_site/frontend_v1/`

### V2 Architecture (Client-Side React SPA)
- **Framework**: React with TypeScript
- **Data Loading**: Client-side API calls after component mount
- **State Management**: React state hooks and context
- **File Locations**: `mvp_site/frontend_v2/`

## 🔍 Critical Implementation Differences

### Campaign Data Loading

#### V1 Implementation
```javascript
// File: mvp_site/frontend_v1/app.js
let resumeCampaign = async (campaignId, retryCount = 0) => {
  showSpinner('loading');
  try {
    const { data } = await fetchApi(`/api/campaigns/${campaignId}`);
    // Process complete campaign data immediately
    data.story.forEach((entry) => {
      appendToStory(entry.actor, entry.text, entry.mode, debugMode, entry.user_scene_number, entry);
    });
  } catch (error) {
    console.error('Failed to resume campaign:', error);
  }
};
```

#### V2 Implementation (Fixed)
```typescript
// File: mvp_site/frontend_v2/src/components/GamePlayView.tsx
useEffect(() => {
  const loadCampaignData = async () => {
    try {
      // Load existing campaign data (like V1 does)
      const campaignData = await apiService.getCampaign(campaignId)
      
      // Convert existing story entries to V2 format
      if (campaignData.story && Array.isArray(campaignData.story) && campaignData.story.length > 0) {
        const convertedStory = campaignData.story.map((entry: any, index: number) => ({
          id: `story-${index}`,
          type: entry.mode === 'god' ? 'narration' : 'action' as 'narration' | 'action',
          content: entry.text || entry.narrative || '',
          timestamp: entry.timestamp || new Date().toISOString(),
          author: entry.actor === 'user' ? 'player' : (entry.actor === 'gemini' ? 'ai' : 'system') as 'player' | 'ai' | 'system'
        }))
        setStory(convertedStory)
      }
    } catch (error) {
      console.error('Failed to load campaign data:', error)
    }
  }
  loadCampaignData()
}, [campaignId])
```

### Data Format Conversion

#### V1 Format
```javascript
{
  "actor": "gemini" | "user" | "system",
  "text": "Story content text",
  "mode": "god" | "character",
  "timestamp": "ISO date string"
}
```

#### V2 Format
```typescript
interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system' | 'choices'
  content: string
  timestamp: string
  author: 'player' | 'ai' | 'system'
  choices?: string[]
}
```

#### Conversion Logic
```typescript
const convertV1ToV2Format = (v1Entry: any): StoryEntry => ({
  id: `story-${index}`,
  type: v1Entry.mode === 'god' ? 'narration' : 'action',
  content: v1Entry.text || v1Entry.narrative || '',
  timestamp: v1Entry.timestamp || new Date().toISOString(),
  author: v1Entry.actor === 'user' ? 'player' : 
          v1Entry.actor === 'gemini' ? 'ai' : 'system'
})
```

## 🚨 Common Integration Issues

### Missing API Calls
**Problem**: V2 components assume data is available without explicit loading
**Solution**: Add `apiService.getCampaign(campaignId)` calls in appropriate useEffect hooks

### Data Format Mismatches
**Problem**: V1 and V2 expect different data structures
**Solution**: Implement format conversion functions when loading V1 data into V2 components

### Authentication Timing
**Problem**: V1 server-side auth vs V2 client-side token management
**Solution**: Ensure proper JWT token handling in V2 API service calls

### State Initialization
**Problem**: V1 initializes with server state, V2 needs explicit initialization
**Solution**: Add proper loading states and data fetching in V2 component lifecycle

## 🛠️ Debugging Patterns

### Quick Identification Checklist
1. **Data Loading**: Does V2 component make the same API calls as V1?
2. **Format Conversion**: Are data formats properly converted between versions?
3. **Authentication**: Are auth tokens properly included in V2 API calls?
4. **State Management**: Is component state properly initialized in V2?

### Common Fix Patterns
1. **Add Missing API Calls**: Identify V1 API calls and replicate in V2 useEffect
2. **Implement Format Conversion**: Create conversion functions for V1→V2 data format
3. **Fix Authentication Flow**: Ensure JWT tokens are included in V2 API service
4. **Initialize State Properly**: Add loading states and error handling to V2 components

## 📁 Key File Locations

### V1 Core Files
- `mvp_site/frontend_v1/app.js` - Main application logic
- `mvp_site/frontend_v1/api.js` - API service functions
- `mvp_site/frontend_v1/index.html` - Main HTML template

### V2 Core Files
- `mvp_site/frontend_v2/src/components/GamePlayView.tsx` - Main game interface
- `mvp_site/frontend_v2/src/services/api.service.ts` - API service class
- `mvp_site/frontend_v2/src/App.tsx` - React application root

### Backend Integration
- `mvp_site/main.py` - Flask backend with API endpoints
- `mvp_site/api/` - API route definitions
- `mvp_site/services/` - Backend service implementations

## 🎯 Best Practices

### For V1→V2 Migration
1. **Map API Calls**: Identify all V1 API calls and ensure V2 equivalents exist
2. **Data Format Planning**: Plan data format conversions before implementation
3. **Authentication Strategy**: Ensure consistent auth token handling
4. **State Management**: Plan React state management for V1 server state equivalents

### For Debugging V1/V2 Issues
1. **Side-by-Side Comparison**: Always compare equivalent components directly
2. **Data Flow Tracing**: Follow data from API → Backend → Frontend in both versions
3. **Format Verification**: Check data format consistency throughout the pipeline
4. **Authentication Verification**: Ensure auth flows work identically in both versions

## 📚 Related Documentation

- **CLAUDE.md**: Cross-Version Systematic Debugging Protocol
- **debugging_guide.md**: Systematic debugging methodologies
- **.cursor/rules/lessons.mdc**: V1/V2 debugging breakthrough technical details

---

**Note**: This reference should be consulted whenever debugging V1/V2 integration issues or implementing cross-version functionality.