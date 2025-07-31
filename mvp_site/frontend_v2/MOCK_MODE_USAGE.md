# Frontend v2 Mock Mode Usage Guide

This guide explains how to use the mock data mode in Frontend v2, which allows development and testing without a backend connection.

## Overview

Frontend v2 includes a comprehensive mock mode that simulates all API interactions using realistic test data. This is based on patterns from the `testing_ui/` folder and provides a seamless development experience.

## Activation Methods

### 1. URL Parameters (Recommended for Testing)
```
http://localhost:3002?test_mode=true&test_user_id=test-user-basic
```

Parameters:
- `test_mode=true` - Enables mock mode
- `test_user_id` - Sets the mock user (optional)
  - `test-user-basic` - Basic adventurer account
  - `test-user-pro` - Pro hero account with more features
  - `test-user-gm` - Game Master account with all features

### 2. Environment Variable
```bash
VITE_MOCK_MODE=true npm run dev
```

### 3. Development UI Toggle
When running in development mode, you'll see a "🎭 Dev Tools" button in the bottom-right corner that allows you to:
- Toggle mock mode on/off
- Switch between different user types
- Set error rates for testing error handling
- Reset mock data to defaults

## Available Mock Data

### Users
- **Basic User** (`test-user-basic`): Standard features, limited campaigns
- **Pro User** (`test-user-pro`): Advanced features, more campaigns
- **Game Master** (`test-user-gm`): All features, admin capabilities

### Campaigns
- **The Dragon's Hoard** - Classic fantasy adventure
- **Neon Shadows: Tokyo 2087** - Cyberpunk thriller
- **Murder at Ashwood Manor** - Victorian mystery
- **Whispers in Darkwater** - Horror story
- **Hidden Chicago** - Urban fantasy

### Features

#### Realistic Game Interactions
- AI responses based on user input
- Dice roll simulations
- Combat detection and appropriate responses
- Dialog interactions with NPCs
- Progressive story development

#### Error Simulation
Use the Dev Tools to set error rates:
- 0% - No errors (default)
- 10% - Occasional errors
- 50% - Frequent errors for stress testing

#### Network Delay Simulation
All API calls include realistic delays (200-800ms) to simulate network latency.

## API Service Integration

The mock mode is seamlessly integrated into the API service layer:

```typescript
import { apiWithMock } from './services/api-with-mock.service';

// This automatically uses mock data when in test mode
const campaigns = await apiWithMock.getCampaigns();
```

## Development Workflow

1. **Start the dev server**:
   ```bash
   npm run dev
   ```

2. **Enable mock mode** using one of the methods above

3. **Use the Dev Tools** to:
   - Switch between users to test different permission levels
   - Enable error simulation to test error handling
   - Reset data when needed

4. **Test all features** without backend dependencies:
   - User authentication flows
   - Campaign creation and management
   - Game interactions and AI responses
   - Error states and edge cases

## Testing Patterns

### Browser Testing
```javascript
// Navigate with test mode
page.goto("http://localhost:3002?test_mode=true&test_user_id=test-123");

// All API calls will use mock data
await page.click('button'); // Works without backend
```

### Component Testing
```typescript
// Enable mock mode programmatically
apiWithMock.setMockMode(true, 'test-user-pro');

// Test components with mock data
render(<CampaignList />);
// Will show mock campaigns
```

## Debugging

### Check Mock Mode Status
Open browser console and look for:
```
🎭 Mock mode enabled for user: test-user-basic
```

### View Mock State
```javascript
// In browser console
apiWithMock.getMockService().getMockState()
```

### Monitor API Calls
All API calls log to console with timing information:
```
✅ API call completed in 0.35s: /campaigns
```

## Important Notes

1. **Production Safety**: Mock mode is automatically disabled in production builds
2. **Data Persistence**: Mock data resets on page reload unless using Dev Tools reset
3. **Feature Parity**: Mock mode implements all current API endpoints
4. **Type Safety**: All mock data follows TypeScript interfaces from `api.types.ts`

## Troubleshooting

### Mock mode not working?
1. Check URL has `?test_mode=true`
2. Verify you're in development mode
3. Check browser console for errors
4. Try using Dev Tools toggle

### API calls failing?
1. Ensure mock service is initialized
2. Check if error simulation is enabled
3. Verify the endpoint is implemented in mock service

### Data not updating?
1. Mock data changes are in-memory only
2. Use Dev Tools reset to restore defaults
3. Check if the store is properly connected to the API service
