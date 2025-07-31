# API Services Documentation

This directory contains the TypeScript API service layer for communicating with the WorldArchitect.AI Flask backend.

## Files

- **api.service.ts** - Main API service class with all API methods
- **api.types.ts** - TypeScript type definitions for all API requests/responses
- **index.ts** - Barrel export for convenient importing
- **API_MISSING_ENDPOINTS.md** - Documentation of endpoints needed but not yet implemented

## Usage

### Import the service

```typescript
import { apiService } from '../services';

// Or import specific types
import { Campaign, InteractionRequest, User } from '../services';
```

### Authentication

The service handles authentication automatically using Firebase Auth. In test mode, it bypasses authentication.

```typescript
// Check if user is authenticated
if (apiService.isAuthenticated()) {
  // User is logged in
}

// Listen to auth state changes
const unsubscribe = apiService.onAuthStateChanged((user) => {
  if (user) {
    console.log('User logged in:', user.email);
  } else {
    console.log('User logged out');
  }
});

// Login/logout
await apiService.login();
await apiService.logout();
```

### Campaign Operations

```typescript
// Get all campaigns
const campaigns = await apiService.getCampaigns();

// Get campaign details with story
const { campaign, story, game_state } = await apiService.getCampaign(campaignId);

// Create a new campaign
const campaignId = await apiService.createCampaign({
  title: 'My Adventure',
  character: 'A brave knight',
  setting: 'Medieval kingdom',
  description: 'Epic quest to save the realm'
});

// Update campaign title
await apiService.updateCampaign(campaignId, {
  title: 'My Epic Adventure'
});

// Delete campaign (NOT IMPLEMENTED IN BACKEND)
try {
  await apiService.deleteCampaign(campaignId);
} catch (error) {
  console.error('Delete not supported');
}
```

### Game Interactions

```typescript
// Send user input
const response = await apiService.sendInteraction(campaignId, {
  input: 'I want to explore the dungeon',
  mode: 'character' // or 'god' for GM mode
});

// Response includes narrative and game state updates
console.log(response.narrative);
console.log(response.state_updates);
```

### User Settings

```typescript
// Get current settings
const settings = await apiService.getUserSettings();

// Update settings
await apiService.updateUserSettings({
  debug_mode: true,
  gemini_model: 'gemini-2.5-flash'
});
```

### Export Campaigns

```typescript
// Export as PDF, DOCX, or TXT
const blob = await apiService.exportCampaign(campaignId, 'pdf');

// Create download link
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'campaign.pdf';
a.click();
URL.revokeObjectURL(url);
```

## Error Handling

All API methods throw errors with proper types:

```typescript
try {
  const campaigns = await apiService.getCampaigns();
} catch (error) {
  if (error instanceof Error) {
    console.error('Error message:', error.message);

    // ApiError includes additional fields
    if ('traceback' in error) {
      console.error('Server traceback:', error.traceback);
    }
    if ('status' in error) {
      console.error('HTTP status:', error.status);
    }
  }
}
```

## Test Mode

The service automatically detects test mode from URL parameters:

```
http://localhost:3000?test_mode=true&test_user_id=test-user-123
```

In test mode:
- Authentication is bypassed
- All requests include test headers
- Login/logout methods throw errors

## TypeScript Types

All API responses are fully typed. Import types as needed:

```typescript
import {
  Campaign,
  GameState,
  StoryEntry,
  InteractionResponse,
  User
} from '../services';

// Use in components
const [campaigns, setCampaigns] = useState<Campaign[]>([]);
const [currentUser, setCurrentUser] = useState<User | null>(null);
```

## Clock Skew Handling

The service automatically retries failed authentication requests that may be due to clock skew between client and server. This is transparent to the caller.

## Missing Endpoints

See API_MISSING_ENDPOINTS.md for documentation on endpoints that the frontend needs but aren't implemented in the backend yet. The service methods exist but throw errors indicating they're not implemented.
