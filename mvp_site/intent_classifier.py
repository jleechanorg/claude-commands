"""
Local Intent Classifier using FastEmbed.

This module provides a lightweight, local, in-memory classification system
to determine the appropriate agent mode based on user input.

It uses the `fastembed` library (ONNX Runtime) with `BAAI/bge-small-en-v1.5`
to generate embeddings for user input and compare them against pre-computed
anchor phrases for each agent mode.

## How It Works

### Classification Process

1. **Initialization** (async, background thread):
   - Loads FastEmbed model (`BAAI/bge-small-en-v1.5`, ~133MB)
   - Pre-computes anchor embeddings for each mode from ANCHOR_PHRASES
   - L2 normalizes all embeddings
   - Stores in `anchor_embeddings` dict

2. **Classification** (per request):
   - Embeds user input → 384-dim vector
   - L2 normalizes user embedding
   - Computes cosine similarity vs each anchor group
   - Takes max similarity per mode
   - Returns mode with highest similarity if ≥ SIMILARITY_THRESHOLD (0.65)
   - Otherwise defaults to MODE_CHARACTER (story mode)

### Integration with Agent Routing

The classifier is integrated into `get_agent_for_input()` routing logic with the
following priority order:

**Priority 5: Semantic Intent Classification** (this classifier runs here)

The classifier runs ONLY if:
- No "GOD MODE:" prefix detected (Priority 1)
- No character creation completion detected (Priority 2)
- Character creation not active (Priority 3)
- No "THINK:" prefix detected (Priority 4)

### Interaction with String Prefixes

**String prefixes take precedence over semantic classification:**

- `"GOD MODE:"` prefix (Priority 1): Returns immediately, classifier never runs
- `"THINK:"` prefix (Priority 4): Returns immediately, classifier never runs

**Example:**
- Input: `"THINK: What should I do?"` → PlanningAgent (prefix detected, classifier skipped)
- Input: `"What should I do?"` → Classifier runs → may return MODE_THINK → PlanningAgent

### Interaction with Mode Toggle (API Parameter)

**Mode toggle (`mode` parameter) is checked at different priorities:**

1. **Early check** (before classifier):
   - `mode="god"` → checked in Priority 1 (before classifier)
   - `mode="think"` → checked in Priority 4 (before classifier)

2. **Fallback check** (after classifier):
   - `mode="combat"` → checked in Priority 6 (after classifier)
   - `mode="rewards"` → checked in Priority 6 (after classifier)
   - `mode="info"` → checked in Priority 6 (after classifier)

**Example:**
- Input: `"attack"`, `mode="combat"`
- Flow: Classifier runs first → returns MODE_CHARACTER → Priority 6 checks mode="combat" → CombatAgent

### Interaction with State Validation

**State validation behavior varies by agent type:**

1. **CombatAgent** - Routes on semantic intent alone:
   - Can handle both active combat and initiating new combat
   - Example: User says "I attack the goblin" when not in combat → CombatAgent initiates combat

2. **RewardsAgent** - Routes on semantic intent alone:
   - Can handle both pending rewards and checking for missed rewards
   - Example: User says "claim my rewards" but LLM forgot to set rewards_pending → RewardsAgent checks for missed rewards

3. **CharacterCreationAgent** - Routes on semantic intent alone:
   - Can handle both active character creation and initiating level-up/recreation
   - Example: User says "level up" when not in character creation → CharacterCreationAgent handles level-up
   - Example: User wants to recreate character → CharacterCreationAgent handles recreation

**Example Scenarios:**

**Scenario 1: Combat Intent + Combat Active**
- Input: `"I attack the goblin!"`
- Classifier: Returns MODE_COMBAT (0.85 confidence)
- State: `game_state.is_in_combat() == True`
- Result: ✅ CombatAgent (handles active combat)

**Scenario 2: Combat Intent + Combat NOT Active (Valid Case)**
- Input: `"I attack the goblin!"`
- Classifier: Returns MODE_COMBAT (0.85 confidence)
- State: `game_state.is_in_combat() == False`
- Result: ✅ CombatAgent (can initiate combat - e.g., attacking non-hostile NPC starts combat)

**Scenario 3: Rewards Intent + Rewards Pending**
- Input: `"claim my rewards"`
- Classifier: Returns MODE_REWARDS (0.80 confidence)
- State: `RewardsAgent.matches_game_state() == True` (rewards pending)
- Result: ✅ RewardsAgent (processes pending rewards)

**Scenario 4: Rewards Intent + No Rewards Pending (Valid Case)**
- Input: `"claim my rewards"`
- Classifier: Returns MODE_REWARDS (0.80 confidence)
- State: `RewardsAgent.matches_game_state() == False` (no rewards pending)
- Result: ✅ RewardsAgent (can check for missed rewards - e.g., LLM forgot to set rewards_pending)

**Scenario 5: Character Creation Intent + Character Creation Active**
- Input: `"level up"`
- Classifier: Returns MODE_CHARACTER_CREATION (0.75 confidence)
- State: `CharacterCreationAgent.matches_game_state() == True` (character creation active)
- Result: ✅ CharacterCreationAgent (handles active character creation)

**Scenario 6: Character Creation Intent + Character Creation NOT Active (Valid Case)**
- Input: `"level up"`
- Classifier: Returns MODE_CHARACTER_CREATION (0.75 confidence)
- State: `CharacterCreationAgent.matches_game_state() == False` (character creation not active)
- Result: ✅ CharacterCreationAgent (can initiate level-up - e.g., user wants to level up outside character creation)

**Scenario 7: Character Creation Intent + Character Recreation (Valid Case)**
- Input: `"I want to recreate my character"`
- Classifier: Returns MODE_CHARACTER_CREATION (0.70 confidence)
- State: `CharacterCreationAgent.matches_game_state() == False` (character creation not active)
- Result: ✅ CharacterCreationAgent (can handle character recreation)

### Supported Modes

The classifier supports the following modes:
- `MODE_THINK` → PlanningAgent (no state check)
- `MODE_INFO` → InfoAgent (no state check)
- `MODE_COMBAT` → CombatAgent (routes on intent, can initiate combat)
- `MODE_REWARDS` → RewardsAgent (routes on intent, can check for missed rewards)
- `MODE_CHARACTER_CREATION` → CharacterCreationAgent (routes on intent, can initiate level-up/recreation)
- `MODE_CAMPAIGN_UPGRADE` → CampaignUpgradeAgent (routes on intent, can guide toward divine ascension)
- `MODE_CHARACTER` → StoryModeAgent (default fallback)

**Security Note:** The classifier is explicitly blocked from returning `MODE_GOD`
(security safeguard - god mode must be explicitly requested via prefix or mode parameter).

### Confidence Threshold

`SIMILARITY_THRESHOLD = 0.65`

If the highest similarity score is below this threshold, the classifier defaults
to `MODE_CHARACTER` (story mode). This prevents false positives from low-confidence
classifications.

## Usage

    from mvp_site.intent_classifier import classify_intent

    mode, confidence = classify_intent("Check my inventory")
    if mode == constants.MODE_INFO:
        # Route to InfoAgent
        ...

## Thread Safety

The classifier uses thread-safe initialization with locks to prevent race conditions
during model loading and inference. Multiple threads can safely call `classify_intent()`
concurrently.

## Error Handling

If classification fails (model not ready, error during inference), the classifier
defaults to `MODE_CHARACTER` with 0.0 confidence, ensuring the system always has a
fallback agent.
"""

import atexit
import os
import threading
import time
import traceback

import numpy as np

from mvp_site import constants, logging_util

# Check for fastembed availability
try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    logging_util.warning("🧠 CLASSIFIER: fastembed not available - semantic routing disabled")

# Check for ONNX Runtime (required by fastembed)
try:
    import onnxruntime  # noqa: F401
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False
    logging_util.warning("🧠 CLASSIFIER: onnxruntime not available - semantic routing disabled")

# Model Configuration
# BAAI/bge-small-en-v1.5 is small (~133MB), fast, and effective for this task.
MODEL_NAME = "BAAI/bge-small-en-v1.5"  # slightly better than MiniLM, still small

# Classification Confidence Threshold
# If the highest similarity score is below this, default to MODE_CHARACTER (story mode).
SIMILARITY_THRESHOLD = 0.65

# Anchor Phrases for each Mode
# These define the "centers of gravity" for each intent.
ANCHOR_PHRASES = {
    constants.MODE_THINK: [
        "what should i do?",
        "i need a plan",
        "let me think about this",
        "assess the situation",
        "what are my options?",
        "strategize",
        "analyze the threat",
        "consider the consequences",
        "review my objectives",
        "planning phase",
        "wait a minute",
        "hold on",
        "let's pause and think",
    ],
    constants.MODE_INFO: [
        "check my inventory",
        "what do i have?",
        "show my equipment",
        "list my items",
        "what am i wearing?",
        "check stats",
        "show character sheet",
        "view abilities",
        "inspect my gear",
        "open backpack",
        "how much gold do i have?",
        "check my spells",
        "what is my ac?",
        "do i have any potions?",
        "list my skills",
    ],
    constants.MODE_COMBAT: [
        "roll initiative",
        "start combat",
        "i attack",
        "attack the goblin",
        "draw weapon",
        "prepare for battle",
        "execute the prisoner",
        "coup de grace",
        "fight",
        "engage enemy",
        "cast offensive spell",
    ],
    constants.MODE_CHARACTER_CREATION: [
        "level up",
        "i want to level up",
        "start level up",
        "apply level up",
        "increase level",
        "choose feat",
        "select subclass",
        "add ability score",
    ],
    constants.MODE_REWARDS: [
        "claim my rewards",
        "what did i get?",
        "show me the loot",
        "distribute rewards",
        "process rewards",
        "claim xp",
        "what are my rewards?",
        "loot distribution",
        "collect rewards",
        "reward me",
    ],
    constants.MODE_CAMPAIGN_UPGRADE: [
        "i wanna be a god",
        "i want to be a god",
        "accelerate my god",
        "let me be multiverse god",
        "become a deity",
        "ascend to godhood",
        "divine ascension",
        "become divine",
        "multiverse upgrade",
        "sovereign protocol",
        "transcend mortality",
        "tier upgrade",
        "upgrade my campaign",
        "go to next tier",
        "become more powerful",
        "reach godhood",
        "i want divine power",
        "skip to god tier",
        "multiverse god",
        "cosmic ascension",
    ],
    constants.MODE_CHARACTER: [
        "i look around",
        "go north",
        "talk to the innkeeper",
        "open the door",
        "cast fireball",
        "sneak past the guard",
        "investigate the room",
        "i say hello",
        "draw my sword",
        "continue",
        "what happens next?",
    ],
}


class LocalIntentClassifier:
    _instance = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()  # Separate lock for initialization

    def __init__(self):
        self.model = None
        self.anchor_embeddings: dict[str, np.ndarray] = {}
        self.ready = False
        self._load_error = None
        self._initializing = False  # Flag to track initialization state
        self._cleaned_up = False  # Flag to prevent double cleanup
        self._retry_count = 0
        self._max_retries = 3  # Maximum retry attempts
        
        # Register cleanup handler for graceful shutdown
        atexit.register(self._cleanup)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize_async(self):
        """Start initialization in a background thread."""
        # Check dependencies first
        if not FASTEMBED_AVAILABLE or not ONNXRUNTIME_AVAILABLE:
            logging_util.warning(
                "🧠 CLASSIFIER: Dependencies not available (fastembed={}, onnxruntime={}). "
                "Semantic routing disabled.".format(FASTEMBED_AVAILABLE, ONNXRUNTIME_AVAILABLE)
            )
            self._load_error = "Dependencies not available"
            return
        
        with self._init_lock:
            if self.ready or self._initializing:
                return
            self._initializing = True
        threading.Thread(target=self._initialize_model, daemon=True).start()

    def _initialize_model(self):
        """Load model and compute anchor embeddings (heavy operation) with retry logic."""
        max_retries = self._max_retries
        retry_delay = 2.0  # Start with 2 seconds
        
        try:
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        logging_util.info(
                            f"🧠 CLASSIFIER: Retry attempt {attempt}/{max_retries - 1} "
                            f"after {retry_delay:.1f}s delay..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    
                    logging_util.info(f"🧠 CLASSIFIER: Loading embedding model {MODEL_NAME}...")
                    # threads=1 to avoid hogging CPU during startup
                    model = TextEmbedding(model_name=MODEL_NAME, threads=1)
                    
                    # Only assign to self.model after successful creation
                    # This prevents partial initialization state
                    self.model = model

                    logging_util.info("🧠 CLASSIFIER: Computing anchor embeddings...")
                    for mode, phrases in ANCHOR_PHRASES.items():
                        # fastembed returns a generator, convert to list then array
                        embeddings_list = list(self.model.embed(phrases))
                        # Stack to create (N, D) matrix
                        matrix = np.array(embeddings_list)
                        
                        # L2 Normalization (required because BGE-Small returns unnormalized vectors)
                        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                        # Avoid division by zero
                        norms[norms == 0] = 1.0
                        self.anchor_embeddings[mode] = matrix / norms

                    self.ready = True
                    self._retry_count = attempt
                    logging_util.info(
                        f"🧠 CLASSIFIER: Ready for inference (succeeded on attempt {attempt + 1})."
                    )
                    return  # Success - exit retry loop
                    
                except Exception as e:
                    # Reset model to None on failure to allow retry
                    self.model = None
                    self._load_error = str(e)
                    
                    if attempt < max_retries - 1:
                        logging_util.warning(
                            f"🧠 CLASSIFIER: Initialization attempt {attempt + 1} failed: {e}. "
                            f"Will retry in {retry_delay:.1f}s..."
                        )
                    else:
                        # Final attempt failed
                        logging_util.error(
                            f"🧠 CLASSIFIER: Initialization failed after {max_retries} attempts: {e}. "
                            f"Semantic routing disabled - all requests will default to MODE_CHARACTER."
                        )
                        self._retry_count = attempt
        finally:
            with self._init_lock:
                self._initializing = False

    def predict(self, text: str) -> tuple[str, float]:
        """
        Predict the agent mode for the given text.

        Returns:
            Tuple[str, float]: (Selected Mode, Confidence Score)

        If model is not ready or confidence is low, returns (MODE_CHARACTER, 0.0).
        """
        # Input validation: handle edge cases
        if not text or not text.strip():
            logging_util.debug("🧠 CLASSIFIER: Empty or whitespace-only input. Defaulting.")
            return constants.MODE_CHARACTER, 0.0
        
        if len(text.strip()) < 2:
            logging_util.debug("🧠 CLASSIFIER: Input too short (< 2 chars). Defaulting.")
            return constants.MODE_CHARACTER, 0.0

        # Use lock to ensure atomic read of ready/model/anchor_embeddings state
        # This prevents race conditions where initialization is in progress
        retry_needed = False
        with self._lock:
            if not self.ready:
                if self._load_error:
                    # If initialization failed, try to recover by retrying initialization
                    if self.model is None:
                        logging_util.warning(
                            f"🧠 CLASSIFIER: Model not ready (failed: {self._load_error}). Retrying initialization..."
                        )
                        retry_needed = True
                    else:
                        logging_util.warning(
                            f"🧠 CLASSIFIER: Model not ready (failed: {self._load_error}). Defaulting."
                        )
                else:
                    logging_util.debug("🧠 CLASSIFIER: Model still loading. Defaulting.")
                
        # Retry initialization if needed (outside lock to avoid deadlock)
        # initialize_async uses _init_lock, not _lock, so this is safe
        if retry_needed:
            self.initialize_async()
            return constants.MODE_CHARACTER, 0.0
        
        # Re-check ready state after potential retry (without lock for quick check)
        if not self.ready:
            return constants.MODE_CHARACTER, 0.0

        # Re-acquire lock to read model state atomically
        with self._lock:
            # Defensive check: ensure model exists even if ready flag is set
            if self.model is None:
                logging_util.warning("🧠 CLASSIFIER: Model is None despite ready=True. Defaulting.")
                return constants.MODE_CHARACTER, 0.0

            # Copy references to local variables while holding lock
            # This ensures we use a consistent snapshot of the model state
            model = self.model
            anchor_embeddings = self.anchor_embeddings.copy()  # Shallow copy for safety

        # Now we can use model and anchor_embeddings without holding the lock
        # This prevents blocking other threads during the potentially slow embedding computation
        try:
            start_time = time.time()
            
            # Embed user text
            # fastembed returns generator
            user_embedding = list(model.embed([text]))[0]  # Shape (D,)

            # L2 Normalization (required because BGE-Small returns unnormalized vectors)
            norm = np.linalg.norm(user_embedding)
            if norm > 0:
                user_embedding = user_embedding / norm

            best_mode = constants.MODE_CHARACTER
            best_score = -1.0

            # Compare against all anchor groups
            for mode, anchors in anchor_embeddings.items():
                # anchors is (N, D), user_embedding is (D,)
                # fastembed vectors are normalized, so dot product is cosine similarity
                scores = np.dot(anchors, user_embedding)
                max_score = np.max(scores)

                if max_score > best_score:
                    best_score = max_score
                    best_mode = mode

            elapsed_time = time.time() - start_time
            truncated_text = text[:30] + ("..." if len(text) > 30 else "")
            logging_util.info(
                f"🧠 CLASSIFIER: Input='{truncated_text}' -> {best_mode} (score={best_score:.3f}) | ⏱️ Latency: {elapsed_time*1000:.2f}ms"
            )

            if best_score >= SIMILARITY_THRESHOLD:
                return best_mode, float(best_score)

            return constants.MODE_CHARACTER, float(best_score)

        except Exception as e:
            logging_util.error(f"🧠 CLASSIFIER: Prediction error: {e}")
            return constants.MODE_CHARACTER, 0.0

    def _cleanup(self):
        """Clean up resources to prevent native library crashes during shutdown."""
        if self._cleaned_up:
            return
        
        self._cleaned_up = True
        
        # Clear model reference before Python exits to prevent FastEmbed/ONNX Runtime
        # native library cleanup crashes. The model will be garbage collected, but
        # clearing the reference explicitly helps avoid termination issues.
        if self.model is not None:
            try:
                # FastEmbed doesn't have explicit cleanup, but clearing the reference
                # helps prevent crashes during Python exit
                self.model = None
                self.anchor_embeddings.clear()
                self.ready = False
            except Exception:
                # Ignore errors during cleanup - we're shutting down anyway
                pass


# Global helper
def classify_intent(text: str) -> tuple[str, float]:
    """Public API to classify intent."""
    return LocalIntentClassifier.get_instance().predict(text)


def initialize():
    """Public API to trigger initialization."""
    # Skip initialization in test mode unless explicitly requested
    skip_classifier = os.environ.get("TESTING", "").lower() == "true"
    force_classifier = os.environ.get("ENABLE_SEMANTIC_ROUTING", "").lower() == "true"
    
    if force_classifier or not skip_classifier:
        LocalIntentClassifier.get_instance().initialize_async()
    else:
        logging_util.info("🧪 TESTING_MODE: Skipping semantic classifier initialization (use ENABLE_SEMANTIC_ROUTING=true to override)")
