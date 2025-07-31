/**
 * Mock Data for Frontend v2
 *
 * Comprehensive test data based on patterns from testing_ui folder
 * and realistic game scenarios.
 */

import type {
  Campaign,
  User,
  UserSettings,
  InteractionResponse,
  StoryEntry,
  GameState
} from './api.types';

// Mock Users with different subscription tiers
export const mockUsers: Record<string, User> = {
  'test-user-basic': {
    uid: 'test-user-basic',
    email: 'adventurer@worldarchitect.ai',
    displayName: 'Test Adventurer',
    photoURL: undefined
  },
  'test-user-pro': {
    uid: 'test-user-pro',
    email: 'hero@worldarchitect.ai',
    displayName: 'Test Hero',
    photoURL: 'https://api.dicebear.com/7.x/avataaars/svg?seed=hero'
  },
  'test-user-gm': {
    uid: 'test-user-gm',
    email: 'gamemaster@worldarchitect.ai',
    displayName: 'Test Game Master',
    photoURL: 'https://api.dicebear.com/7.x/avataaars/svg?seed=gm'
  }
};

// Mock Campaigns with various states and genres
export const mockCampaigns: Campaign[] = [
  {
    id: 'camp-001',
    title: "The Dragon's Hoard",
    prompt: "A classic fantasy adventure where brave heroes seek an ancient dragon's treasure",
    created_at: '2024-01-15T10:30:00Z',
    last_played: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    user_id: 'test-user-basic',
    use_default_world: true,
  },
  {
    id: 'camp-002',
    title: 'Neon Shadows: Tokyo 2087',
    prompt: 'A cyberpunk thriller in the neon-lit streets of future Tokyo',
    created_at: '2024-01-20T14:00:00Z',
    last_played: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    user_id: 'test-user-pro',
    selected_prompts: ['cyberpunk_world', 'tech_noir'],
  },
  {
    id: 'camp-003',
    title: 'Murder at Ashwood Manor',
    prompt: 'A classic murder mystery set in a Victorian mansion',
    created_at: '2024-01-10T09:15:00Z',
    last_played: '2024-01-22T20:30:00Z',
    user_id: 'test-user-basic',
  },
  {
    id: 'camp-004',
    title: 'Whispers in Darkwater',
    prompt: 'A horror story in a town where nightmares become real',
    created_at: '2024-01-25T22:00:00Z',
    last_played: '2024-01-25T23:45:00Z',
    user_id: 'test-user-gm',
    selected_prompts: ['horror_atmosphere', 'psychological'],
  },
  {
    id: 'camp-005',
    title: 'Hidden Chicago',
    prompt: 'Modern urban fantasy where magic hides in plain sight',
    created_at: '2023-12-20T16:30:00Z',
    last_played: '2024-01-05T18:00:00Z',
    user_id: 'test-user-pro',
  }
];

// Mock game state
export const mockGameStates: Record<string, GameState> = {
  'camp-001': {
    debug_mode: false,
    player_character_data: {
      name: 'Thorin Ironforge',
      level: 5,
      hp: 45,
      max_hp: 52,
      mbti: 'ISTJ'
    },
    npc_data: {
      'Ancient Dragon': {
        name: 'Ancient Dragon',
        hp: 200,
        max_hp: 200
      }
    }
  },
  'camp-002': {
    debug_mode: false,
    player_character_data: {
      name: 'Kai "Ghost" Nakamura',
      level: 8,
      hp: 32,
      max_hp: 40,
      mbti: 'INTP'
    },
    combat_state: {
      active: true,
      combatants: {
        'player': { initiative: 18 },
        'corp-sec-1': { initiative: 12 }
      }
    }
  }
};

// Mock story entries
export const mockStoryEntries: Record<string, StoryEntry[]> = {
  'camp-001': [
    {
      actor: 'gemini',
      text: 'The ancient door creaks open, revealing a vast chamber filled with glittering treasures...',
      narrative: 'The ancient door creaks open, revealing a vast chamber filled with glittering treasures and the sound of deep, rhythmic breathing...',
      timestamp: new Date(Date.now() - 300000).toISOString()
    },
    {
      actor: 'user',
      text: 'I carefully step into the chamber',
      mode: 'character',
      timestamp: new Date(Date.now() - 240000).toISOString()
    },
    {
      actor: 'gemini',
      text: 'You carefully step into the chamber, your torch casting dancing shadows on the walls.',
      narrative: 'As you step forward, your torch illuminates ancient runes along the walls. The breathing grows louder.',
      dice_rolls: [
        { type: 'Perception', result: 15, modifier: 3, total: 18, reason: 'Noticing details' }
      ],
      timestamp: new Date(Date.now() - 180000).toISOString()
    }
  ],
  'camp-002': [
    {
      actor: 'gemini',
      text: '"The corps won\'t stop hunting you, Ghost. You know too much."',
      narrative: '"The corps won\'t stop hunting you, Ghost. You know too much." The fixer\'s augmented eyes gleam in the neon light.',
      entities_mentioned: ['The Fixer', 'Corporate Security'],
      timestamp: new Date(Date.now() - 120000).toISOString()
    },
    {
      actor: 'user',
      text: 'I reach for my weapon',
      mode: 'character',
      timestamp: new Date(Date.now() - 60000).toISOString()
    },
    {
      actor: 'gemini',
      text: 'Corporate security bursts through the door! Roll for initiative.',
      narrative: 'Before you can draw, the door explodes inward. Three corporate security officers storm in, weapons raised.',
      session_header: 'COMBAT INITIATED',
      dice_rolls: [
        { type: 'Initiative', result: 12, modifier: 2, total: 14, reason: 'Combat order' }
      ],
      timestamp: new Date().toISOString()
    }
  ]
};

// Mock user settings
export const mockUserSettings: Record<string, UserSettings> = {
  'test-user-basic': {
    debug_mode: false,
    gemini_model: 'gemini-1.5-flash'
  },
  'test-user-pro': {
    debug_mode: true,
    gemini_model: 'gemini-1.5-pro'
  },
  'test-user-gm': {
    debug_mode: true,
    gemini_model: 'gemini-1.5-pro'
  }
};

// Error scenarios for testing
export const mockErrors = {
  network: new Error('Network request failed'),
  timeout: new Error('Request timeout'),
  unauthorized: new Error('Unauthorized: Invalid authentication'),
  validation: new Error('Validation error: Title is required'),
  serverError: new Error('Internal server error'),
  notFound: new Error('Resource not found'),
  rateLimit: new Error('Rate limit exceeded. Try again later.')
};

// Delay simulation for realistic UX
export const mockDelay = (ms: number = 300) =>
  new Promise(resolve => setTimeout(resolve, ms + Math.random() * 200));
