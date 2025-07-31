# Zustand State Management for WorldArchitect.AI

This directory contains the Zustand state stores for managing application state in the frontend_v2 React application.

## Installation

First, install Zustand if not already installed:

```bash
npm install zustand
```

## Store Overview

### 1. Auth Store (`authStore.ts`)
Manages user authentication state, login/logout actions, and session persistence.

**Key Features:**
- User authentication state
- Login methods (email/password and Google OAuth)
- Session persistence using localStorage
- Error handling and loading states

**Usage Example:**
```tsx
import { useAuthStore } from '@/stores';

function LoginComponent() {
  const { user, isLoading, error, login, logout } = useAuthStore();

  const handleLogin = async () => {
    try {
      await login('user@example.com', 'password');
      // User is now logged in
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div>
      {user ? (
        <div>
          <p>Welcome, {user.displayName}!</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={handleLogin} disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

### 2. Campaign Store (`campaignStore.ts`)
Manages campaign list, selected campaign, and CRUD operations for campaigns.

**Key Features:**
- Campaign list management
- Create, read, update, delete operations
- Selected campaign tracking
- Loading and error states for each operation

**Usage Example:**
```tsx
import { useCampaignStore } from '@/stores';
import { useEffect } from 'react';

function CampaignList() {
  const {
    campaigns,
    isLoading,
    error,
    fetchCampaigns,
    createCampaign,
    selectCampaign
  } = useCampaignStore();

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreateCampaign = async () => {
    try {
      const campaignId = await createCampaign({
        title: 'New Adventure',
        character: 'Brave Knight',
        setting: 'Medieval Kingdom',
        description: 'A quest to save the realm'
      });
      console.log('Created campaign:', campaignId);
    } catch (error) {
      console.error('Failed to create campaign:', error);
    }
  };

  return (
    <div>
      <button onClick={handleCreateCampaign}>Create Campaign</button>
      {isLoading ? (
        <p>Loading campaigns...</p>
      ) : (
        <ul>
          {campaigns.map(campaign => (
            <li key={campaign.id}>
              <button onClick={() => selectCampaign(campaign)}>
                {campaign.title}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### 3. Game Store (`gameStore.ts`)
Manages real-time game state, story entries, and user interactions during gameplay.

**Key Features:**
- Game state management (HP, NPCs, combat, etc.)
- Story entry tracking
- Real-time interaction handling
- Mode switching (character/god mode)
- Typing indicators

**Usage Example:**
```tsx
import { useGameStore } from '@/stores';
import { useEffect } from 'react';

function GamePlayView({ campaignId }: { campaignId: string }) {
  const {
    gameState,
    storyEntries,
    currentMode,
    isSending,
    sendInteraction,
    setMode,
    initializeGame
  } = useGameStore();

  useEffect(() => {
    initializeGame(campaignId);
  }, [campaignId]);

  const handleSendMessage = async (message: string) => {
    await sendInteraction(message, currentMode);
  };

  // Subscribe to HP changes
  useEffect(() => {
    const unsubscribe = useGameStore.subscribe(
      (state) => state.gameState.player_character_data?.hp,
      (hp) => {
        console.log('Player HP changed:', hp);
      }
    );
    return unsubscribe;
  }, []);

  return (
    <div>
      <div className="story-log">
        {storyEntries.map((entry, index) => (
          <div key={index} className={`story-entry ${entry.actor}`}>
            <p>{entry.text}</p>
            {entry.dice_rolls?.map((roll, i) => (
              <span key={i}>🎲 {roll.type}: {roll.total}</span>
            ))}
          </div>
        ))}
      </div>

      <div className="game-stats">
        <p>HP: {gameState.player_character_data?.hp} / {gameState.player_character_data?.max_hp}</p>
        <button onClick={() => setMode(currentMode === 'character' ? 'god' : 'character')}>
          Mode: {currentMode}
        </button>
      </div>
    </div>
  );
}
```

### 4. Theme Store (`themeStore.ts`)
Manages application themes and applies them to the DOM.

**Key Features:**
- Theme switching between light, dark, fantasy, cyberpunk, and spooky
- Automatic theme application on load
- CSS variable updates
- Theme persistence

**Usage Example:**
```tsx
import { useThemeStore } from '@/stores';

function ThemeSwitcher() {
  const { currentTheme, availableThemes, setTheme } = useThemeStore();

  return (
    <select
      value={currentTheme}
      onChange={(e) => setTheme(e.target.value as Theme)}
    >
      {availableThemes.map(theme => (
        <option key={theme} value={theme}>
          {theme.charAt(0).toUpperCase() + theme.slice(1)}
        </option>
      ))}
    </select>
  );
}
```

## Advanced Usage

### Subscribing to Specific State Changes
```tsx
// Subscribe to specific state changes
useEffect(() => {
  const unsubscribe = useGameStore.subscribe(
    (state) => state.gameState.combat_state?.active,
    (isInCombat) => {
      if (isInCombat) {
        console.log('Combat started!');
        // Play combat music, show combat UI, etc.
      }
    }
  );
  return unsubscribe;
}, []);
```

### Using Multiple Stores Together
```tsx
function GameScreen() {
  const { user } = useAuthStore();
  const { selectedCampaign } = useCampaignStore();
  const { gameState, sendInteraction } = useGameStore();
  const { currentTheme } = useThemeStore();

  if (!user) return <LoginScreen />;
  if (!selectedCampaign) return <CampaignList />;

  return (
    <div className={`game-screen theme-${currentTheme}`}>
      <h1>{selectedCampaign.title}</h1>
      <p>Playing as: {gameState.player_character_data?.name}</p>
      {/* Game UI */}
    </div>
  );
}
```

### Accessing Store Outside React Components
```tsx
// Get current state
const currentUser = useAuthStore.getState().user;

// Subscribe to changes
const unsubscribe = useAuthStore.subscribe(
  (state) => state.user,
  (user) => console.log('User changed:', user)
);

// Perform actions
useAuthStore.getState().logout();
```

## Integration with API Service

Currently, the stores use mock data. To integrate with the actual API service:

1. Import the API service:
```tsx
import { apiService } from '../../../../frontend_v2/src/services/api.service';
```

2. Replace mock implementations with actual API calls:
```tsx
// In authStore.ts
login: async (email: string, password: string) => {
  set({ isLoading: true, error: null });
  try {
    const response = await apiService.login(email, password);
    set({
      user: response.user,
      isAuthenticated: true,
      isLoading: false
    });
  } catch (error) {
    set({
      error: error instanceof Error ? error.message : 'Login failed',
      isLoading: false
    });
    throw error;
  }
},
```

## Testing

To test the stores, you can use Zustand's testing utilities:

```tsx
import { renderHook, act } from '@testing-library/react-hooks';
import { useAuthStore } from './authStore';

test('login updates user state', async () => {
  const { result } = renderHook(() => useAuthStore());

  await act(async () => {
    await result.current.login('test@example.com', 'password');
  });

  expect(result.current.user).toBeDefined();
  expect(result.current.user?.email).toBe('test@example.com');
  expect(result.current.isAuthenticated).toBe(true);
});
```

## Best Practices

1. **Use selectors for performance**:
```tsx
// Instead of this (re-renders on any store change)
const store = useAuthStore();

// Do this (re-renders only when user changes)
const user = useAuthStore(state => state.user);
```

2. **Keep stores focused**: Each store should handle a specific domain of the application.

3. **Handle errors gracefully**: Always include error states and clear them appropriately.

4. **Use TypeScript**: All stores are fully typed for better developer experience.

5. **Persist only necessary data**: Use the `partialize` option to persist only essential data.

## Migration from Existing Code

To migrate existing component state to Zustand:

1. Identify component state that should be global
2. Move state definition to appropriate store
3. Replace `useState` with store hooks
4. Update event handlers to use store actions
5. Remove prop drilling

Example migration:
```tsx
// Before (component state)
const [campaigns, setCampaigns] = useState([]);
const [loading, setLoading] = useState(false);

// After (Zustand store)
const { campaigns, isLoading, fetchCampaigns } = useCampaignStore();
```
