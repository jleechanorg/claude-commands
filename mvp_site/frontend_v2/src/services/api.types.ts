/**
 * Type definitions for API requests and responses
 */

// User types
export interface User {
  uid: string;
  email?: string;
  displayName?: string;
  photoURL?: string;
}

// Campaign types
export interface Campaign {
  id: string;
  title: string;
  prompt: string;
  created_at: string;
  last_played: string;
  user_id: string;
  selected_prompts?: string[];
  use_default_world?: boolean;
  theme?: string;
  difficulty?: string;
  status?: string;
}

export interface CampaignCreateRequest {
  title: string;
  character?: string;
  setting?: string;
  description?: string;
  prompt?: string; // Legacy support
  selected_prompts?: string[];
  custom_options?: string[];
}

export interface CampaignUpdateRequest {
  title: string;
}

// Game state types
export interface GameState {
  debug_mode?: boolean;
  player_character_data?: PlayerCharacterData;
  npc_data?: Record<string, NPCData>;
  combat_state?: CombatState;
  custom_campaign_state?: Record<string, any>;
  [key: string]: any;
}

export interface PlayerCharacterData {
  name?: string;
  level?: number;
  hp?: number;
  max_hp?: number;
  mbti?: string;
  [key: string]: any;
}

export interface NPCData {
  name: string;
  mbti?: string;
  hp?: number;
  max_hp?: number;
  [key: string]: any;
}

export interface CombatState {
  combatants?: Record<string, any>;
  active?: boolean;
  [key: string]: any;
}

// Story/Interaction types
export interface StoryEntry {
  actor: 'user' | 'gemini';
  text: string;
  mode?: 'character' | 'god';
  timestamp?: string;
  // Structured fields for AI responses
  narrative?: string;
  entities_mentioned?: string[];
  location_confirmed?: string;
  state_updates?: Record<string, any>;
  debug_info?: Record<string, any>;
  session_header?: string;
  planning_block?: string;
  dice_rolls?: DiceRoll[];
  resources?: string;
  rewards_box?: RewardsBox;
  god_mode_response?: string;
  system_warnings?: string[];
  user_scene_number?: number;
}

export interface DiceRoll {
  type: string;
  result: number;
  modifier?: number;
  total?: number;
  reason?: string;
}

export interface RewardsBox {
  source?: string;
  xp_gained?: number;
  current_xp?: number;
  next_level_xp?: number;
  progress_percent?: number;
  level_up_available?: boolean;
  loot?: string[];
  gold?: number;
}

export interface InteractionRequest {
  input: string;
  mode?: 'character' | 'god';
}

export interface InteractionResponse {
  success: boolean;
  response?: string;
  narrative?: string;
  debug_mode?: boolean;
  sequence_id?: number;
  state_updates?: Record<string, any>;
  entities_mentioned?: string[];
  location_confirmed?: string;
  session_header?: string;
  planning_block?: string;
  dice_rolls?: DiceRoll[];
  resources?: string;
  rewards_box?: RewardsBox;
  god_mode_response?: string;
  system_warnings?: string[];
  user_scene_number?: number;
  error?: string;
}

// Settings types
export interface UserSettings {
  debug_mode?: boolean;
  gemini_model?: string;
}

// Export types
export type ExportFormat = 'pdf' | 'docx' | 'txt';

// API Response types
export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  message?: string;
  traceback?: string;
}

export interface CampaignListResponse {
  campaigns: Campaign[];
}

export interface CampaignDetailResponse {
  campaign: Campaign;
  story: StoryEntry[];
  game_state: GameState;
  planning_block?: string; // Character choice interface data
  title: string; // Direct access to campaign title
}

export interface CampaignCreateResponse {
  success: boolean;
  campaign_id: string;
}

// Error types
export interface ApiError extends Error {
  traceback?: string;
  status?: number;
}
