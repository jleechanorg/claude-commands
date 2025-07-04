#!/usr/bin/env python3
"""
Configuration for real Gemini API testing
"""
import os
import logging

# Model configuration
DEFAULT_MODEL = 'gemini-2.5-flash'  # Fast and cheap for all operations
TEST_MODEL = 'gemini-2.5-flash'  # Explicitly use for all tests

# API Configuration
MAX_TOKENS = 2000  # Limit output for cost control
TEMPERATURE = 0.7  # Slightly lower for more consistent results
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Cost Management
MAX_BUDGET_USD = 1.00  # Hard limit
COST_PER_1K_INPUT_TOKENS = 0.00035  # gemini-1.5-flash pricing
COST_PER_1K_OUTPUT_TOKENS = 0.00105
WARNING_THRESHOLD_USD = 0.50  # Warn at 50% budget

# Safety Settings (matching mvp_site)
try:
    from google.genai import types
    
    SAFETY_SETTINGS = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, 
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, 
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, 
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, 
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
    ]
except ImportError:
    # Fallback for environments without the SDK
    SAFETY_SETTINGS = []

# API Key Management
def get_api_key():
    """Get Gemini API key from environment or file"""
    # Check environment first
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # Check home directory
    home_key_path = os.path.expanduser("~/.gemini_api_key.txt")
    if os.path.exists(home_key_path):
        with open(home_key_path, "r") as f:
            return f.read().strip()
    
    # Check project root
    project_key_path = os.path.join(os.path.dirname(__file__), "../../../gemini_api_key.txt")
    if os.path.exists(project_key_path):
        with open(project_key_path, "r") as f:
            return f.read().strip()
    
    raise ValueError("No Gemini API key found. Set GEMINI_API_KEY or create ~/.gemini_api_key.txt")

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test Configuration
TEST_CAMPAIGNS = ["sariel_v2_001", "thornwood_001"]  # Limited set
TEST_SCENARIOS = ["multi_character", "combat_injured", "npc_heavy"]  # 3 key scenarios
RUNS_PER_TEST = 1  # Single run to minimize costs

# File paths
OUTPUT_DIR = "analysis/real_llm_results"
CACHE_DIR = "analysis/real_llm_cache"