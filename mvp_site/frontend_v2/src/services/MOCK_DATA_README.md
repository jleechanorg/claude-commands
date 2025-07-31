# Frontend v2 Mock Data System

This directory contains a comprehensive mock data system for the WorldArchitect.AI Frontend v2, enabling realistic development and testing without backend dependencies.

## Overview

The mock data system provides:
- 10 diverse campaign scenarios across different genres
- Realistic game state progressions
- User profiles with different subscription tiers
- Error simulation for robust error handling
- Network delay simulation
- Achievement and badge systems
- WebSocket event mocking for real-time features

## Files

- `mock-data.ts` - Comprehensive mock data sets
- `mock.service.ts` - Mock API service that simulates backend behavior
- `mock-integration-example.tsx` - Example React components showing integration
- `api.types.ts` - TypeScript type definitions (existing file)
- `api.service.ts` - Real API service (existing file)

## Quick Start

### 1. Enable Mock Mode in Development

```typescript
import { mockApiService } from './services/mock.service';

// In your App component
useEffect(() => {
  if (process.env.NODE_ENV === 'development') {
    mockApiService.setTestMode(true, 'user-pro');
  }
}, []);
```

### 2. Use Mock Service in Components

```typescript
import { mockApiService } from './services/mock.service';

// Get campaigns
const campaigns = await mockApiService.getCampaigns();

// Send game interaction
const response = await mockApiService.sendInteraction(campaignId, {
  input: "I attack the dragon!",
  mode: 'character'
});
```

### 3. Switch Between Mock and Real API

```typescript
// Use environment variable
const apiService = process.env.REACT_APP_USE_MOCK_API === 'true'
  ? mockApiService
  : realApiService;

// Or create a service factory
export function getApiService() {
  const useMock = process.env.NODE_ENV === 'development' ||
                  window.location.search.includes('mock=true');
  return useMock ? mockApiService : apiService;
}
```

## Mock Data Categories

### 1. Campaign Scenarios

**Fantasy Campaigns:**
- The Dragon's Hoard (Active, Mid-game)
- The Cursed Crown (Dark Fantasy, Paused)

**Sci-Fi Campaigns:**
- Neon Shadows: Tokyo 2087 (Cyberpunk, In Progress)
- Stars of Andromeda (Space Opera, Active)

**Mystery/Horror:**
- Murder at Ashwood Manor (1920s Mystery, New)
- Whispers in Darkwater (Lovecraftian Horror, Mid-game)

**Modern/Other:**
- Hidden Chicago (Urban Fantasy, Recruiting)
- After the Fall (Post-Apocalyptic, Completed)
- Vikings: The Last Raid (Historical, Planning)
- Guardians of New Liberty (Superhero, Active)

### 2. Game States

Each campaign has associated game states showing:
- Player character data (name, level, HP, MBTI type)
- NPC data with personalities
- Combat states (active battles, initiative order)
- Custom campaign states (location, items, reputation)

### 3. Story Progressions

Pre-built story sequences for:
- Initial game start
- Combat encounters with dice rolls
- Dialog interactions with NPCs
- Quest completions
- Victory scenarios
- Defeat scenarios

### 4. User Profiles

Three subscription tiers with different features:
- **Basic (Adventurer)**: 3 campaigns, basic AI, text export
- **Pro (Hero)**: Unlimited campaigns, advanced AI, all exports
- **Game Master**: Everything + multiplayer, image gen, analytics

### 5. Error Scenarios

Realistic error responses for:
- Network timeouts
- Validation errors
- Authentication failures
- Server errors (500, 503)
- Rate limiting
- Service unavailability

## Testing Features

### Error Simulation

```typescript
// Set random error rate (0-100%)
mockApiService.setErrorRate(10); // 10% chance of errors

// Trigger specific error
await mockApiService.simulateError('server_error');
```

### Network Delay Simulation

```typescript
// Delays are built-in (200-800ms by default)
// Custom delays in mock-data.ts:
await simulateNetworkDelay(1000, 2000); // 1-2 seconds
```

### User Switching

```typescript
// Switch between test users
mockApiService.setTestMode(true, 'user-basic');  // Basic tier
mockApiService.setTestMode(true, 'user-pro');    // Pro tier
mockApiService.setTestMode(true, 'user-gm');     // Game Master tier
```

## Integration Patterns

### Pattern 1: Development Toggle

```typescript
export function App() {
  const [useMock, setUseMock] = useState(true);

  return (
    <>
      {process.env.NODE_ENV === 'development' && (
        <button onClick={() => setUseMock(!useMock)}>
          {useMock ? 'Using Mock API' : 'Using Real API'}
        </button>
      )}
      <GameContent apiService={useMock ? mockApiService : apiService} />
    </>
  );
}
```

### Pattern 2: Service Abstraction

```typescript
// Create an abstract service interface
interface IApiService {
  getCampaigns(): Promise<Campaign[]>;
  sendInteraction(id: string, data: InteractionRequest): Promise<InteractionResponse>;
  // ... other methods
}

// Both mock and real services implement this interface
class ApiServiceWrapper implements IApiService {
  constructor(private service: IApiService) {}

  async getCampaigns() {
    try {
      return await this.service.getCampaigns();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
}
```

### Pattern 3: Feature Flags

```typescript
const features = {
  useMockApi: process.env.REACT_APP_USE_MOCK === 'true',
  mockErrorRate: Number(process.env.REACT_APP_MOCK_ERROR_RATE) || 5,
  mockDelay: process.env.REACT_APP_MOCK_DELAY === 'true'
};

if (features.useMockApi) {
  mockApiService.setErrorRate(features.mockErrorRate);
}
```

## Mock Data Helpers

### Generate Random Content

```typescript
import { mockData } from './mock-data';

// Get random story progression
const story = mockData.helpers.generateRandomStoryProgression();

// Get random error for testing
const error = mockData.helpers.generateRandomError();

// Check if should fail (for chaos testing)
if (mockData.helpers.shouldSimulateFailure(0.1)) {
  throw new Error('Random failure');
}
```

### Access Mock Data Directly

```typescript
import { mockCampaigns, mockUsers, mockAchievements } from './mock-data';

// Use in tests or development tools
console.log('Available campaigns:', mockCampaigns);
console.log('Test users:', Object.keys(mockUsers));
console.log('Achievements:', mockAchievements);
```

## Testing Scenarios

### Scenario 1: New User Experience
```typescript
// Start with no campaigns
mockApiService.setTestMode(true, 'user-new');
// User creates first campaign
// Show onboarding flow
```

### Scenario 2: Active Player
```typescript
// Load user with multiple campaigns
mockApiService.setTestMode(true, 'user-pro');
// Show campaign selection
// Test switching between campaigns
```

### Scenario 3: Error Handling
```typescript
// Test network failures
mockApiService.setErrorRate(50);
// Test specific errors
mockApiService.simulateError('auth_failed');
// Test retry logic
```

### Scenario 4: Real-time Features
```typescript
// Mock WebSocket events
import { mockWebSocketEvents } from './mock-data';

// Simulate player joining
emitMockEvent(mockWebSocketEvents.playerJoined);
// Simulate campaign updates
emitMockEvent(mockWebSocketEvents.campaignUpdate);
```

## Best Practices

1. **Always handle loading states** - Mock service includes realistic delays
2. **Test error scenarios** - Use error simulation during development
3. **Test different user tiers** - Switch between basic/pro/gm users
4. **Use TypeScript** - All mock data is fully typed
5. **Keep mock data realistic** - Based on actual game scenarios
6. **Update mock data** - Add new scenarios as features develop

## Troubleshooting

**Q: Mock data not loading?**
- Ensure `setTestMode(true, userId)` is called before API calls
- Check if current user is set

**Q: Want to test specific campaign state?**
- Modify `mockGameStates` in mock-data.ts
- Or create new campaign with specific initial state

**Q: Need to test long stories?**
- Add entries to `mockStoryProgressions`
- Or generate dynamically in mock service

**Q: Testing multiplayer features?**
- Use WebSocket event mocks
- Simulate multiple users with different mock service instances

## Future Enhancements

- [ ] Add mock image generation responses
- [ ] Implement mock campaign sharing
- [ ] Add analytics data mocking
- [ ] Create mock notification system
- [ ] Add mock payment/subscription flows
- [ ] Implement mock data persistence (localStorage)
