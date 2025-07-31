import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { apiWithMock } from '../services/api-with-mock.service';
import type {
  GameState,
  StoryEntry,
  InteractionRequest,
  InteractionResponse,
  PlayerCharacterData,
  NPCData,
  CombatState,
  DiceRoll
} from '../services/api.types';

interface GameStoreState {
  // State
  campaignId: string | null;
  gameState: GameState;
  storyEntries: StoryEntry[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;

  // UI State
  currentMode: 'character' | 'god';
  isTyping: boolean;
  typingUser: string | null;

  // Actions
  initializeGame: (campaignId: string) => Promise<void>;
  sendInteraction: (input: string, mode?: 'character' | 'god') => Promise<void>;
  updateGameState: (updates: Partial<GameState>) => void;
  updatePlayerCharacter: (updates: Partial<PlayerCharacterData>) => void;
  updateNPC: (npcId: string, updates: Partial<NPCData>) => void;
  updateCombatState: (updates: Partial<CombatState>) => void;
  addStoryEntry: (entry: StoryEntry) => void;
  setMode: (mode: 'character' | 'god') => void;
  setTyping: (isTyping: boolean, user?: string) => void;
  clearError: () => void;
  reset: () => void;
}

const initialGameState: GameState = {
  debug_mode: false,
  player_character_data: {},
  npc_data: {},
  combat_state: {
    active: false,
    combatants: {}
  },
  custom_campaign_state: {}
};

export const useGameStore = create<GameStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    campaignId: null,
    gameState: initialGameState,
    storyEntries: [],
    isLoading: false,
    isSending: false,
    error: null,
    currentMode: 'character',
    isTyping: false,
    typingUser: null,

    // Initialize game for a campaign
    initializeGame: async (campaignId: string) => {
      set({ isLoading: true, error: null, campaignId });
      try {
        const response = await apiWithMock.getCampaign(campaignId);

        set({
          gameState: response.game_state || initialGameState,
          storyEntries: response.story || [],
          isLoading: false
        });
      } catch (error) {
        set({
          error: error instanceof Error ? error.message : 'Failed to initialize game',
          isLoading: false
        });
        throw error;
      }
    },

    // Send user interaction
    sendInteraction: async (input: string, mode = 'character') => {
      const { campaignId, storyEntries } = get();
      if (!campaignId) {
        set({ error: 'No campaign selected' });
        return;
      }

      set({ isSending: true, error: null });

      // Add user's message immediately
      const userEntry: StoryEntry = {
        actor: 'user',
        text: input,
        mode,
        timestamp: new Date().toISOString(),
        user_scene_number: storyEntries.filter(e => e.actor === 'user').length + 1
      };

      set(state => ({
        storyEntries: [...state.storyEntries, userEntry]
      }));

      try {
        const response = await apiWithMock.sendInteraction(campaignId, { input, mode });

        // Create AI response entry
        const aiEntry: StoryEntry = {
          actor: 'gemini',
          text: response.response || '',
          mode,
          timestamp: new Date().toISOString(),
          narrative: response.narrative,
          entities_mentioned: response.entities_mentioned,
          location_confirmed: response.location_confirmed,
          state_updates: response.state_updates,
          debug_info: response.debug_mode ? { sequence_id: response.sequence_id } : undefined,
          planning_block: response.planning_block,
          dice_rolls: response.dice_rolls,
          god_mode_response: response.god_mode_response
        };

        // Update state with response
        set(state => ({
          storyEntries: [...state.storyEntries, aiEntry],
          gameState: response.state_updates
            ? { ...state.gameState, ...response.state_updates }
            : state.gameState,
          isSending: false
        }));
      } catch (error) {
        set({
          error: error instanceof Error ? error.message : 'Failed to send interaction',
          isSending: false
        });
        throw error;
      }
    },

    // Update game state
    updateGameState: (updates: Partial<GameState>) => {
      set(state => ({
        gameState: { ...state.gameState, ...updates }
      }));
    },

    // Update player character
    updatePlayerCharacter: (updates: Partial<PlayerCharacterData>) => {
      set(state => ({
        gameState: {
          ...state.gameState,
          player_character_data: {
            ...state.gameState.player_character_data,
            ...updates
          }
        }
      }));
    },

    // Update NPC
    updateNPC: (npcId: string, updates: Partial<NPCData>) => {
      set(state => ({
        gameState: {
          ...state.gameState,
          npc_data: {
            ...state.gameState.npc_data,
            [npcId]: {
              ...state.gameState.npc_data?.[npcId],
              ...updates
            }
          }
        }
      }));
    },

    // Update combat state
    updateCombatState: (updates: Partial<CombatState>) => {
      set(state => ({
        gameState: {
          ...state.gameState,
          combat_state: {
            ...state.gameState.combat_state,
            ...updates
          }
        }
      }));
    },

    // Add story entry
    addStoryEntry: (entry: StoryEntry) => {
      set(state => ({
        storyEntries: [...state.storyEntries, entry]
      }));
    },

    // Set interaction mode
    setMode: (mode: 'character' | 'god') => {
      set({ currentMode: mode });
    },

    // Set typing indicator
    setTyping: (isTyping: boolean, user?: string) => {
      set({
        isTyping,
        typingUser: isTyping ? (user || 'Someone') : null
      });
    },

    // Clear error
    clearError: () => {
      set({ error: null });
    },

    // Reset game state
    reset: () => {
      set({
        campaignId: null,
        gameState: initialGameState,
        storyEntries: [],
        isLoading: false,
        isSending: false,
        error: null,
        currentMode: 'character',
        isTyping: false,
        typingUser: null
      });
    }
  }))
);
