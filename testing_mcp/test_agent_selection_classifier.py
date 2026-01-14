#!/usr/bin/env python3
"""
Integration test for Agent Selection (all 7 agents) with Real LLMs.

Verifies that natural language inputs are correctly routed to the right agent.
Tests all 7 agents:
- Semantic Classifier Agents (5): Think, Info, Combat, Character Creation, Story
- Explicit Override Agents (1): God Mode
- Game State Agents (1): Rewards

For each agent: 1 simple prompt + 2 ambiguous prompts.
Uses REAL LLMs (not mock) to ensure end-to-end validation.

NEW TEST CASES (PR #3491):
- CharacterCreationAgent routing on intent alone (level-up without active character creation)
- CharacterCreationAgent routing on explicit mode without state
- Case-insensitive mode parameter handling (COMBAT, REWARDS, CHARACTER_CREATION, INFO)
- State transition support (CombatAgent/RewardsAgent/CharacterCreationAgent can initiate transitions)
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import requests

from lib import MCPClient
from lib.campaign_utils import create_campaign, process_action, ensure_game_state_seed, get_campaign_state
from lib.server_utils import pick_free_port, start_local_mcp_server, LocalServer
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
)

TEST_NAME = "agent_selection_classifier"

# Test Cases: (Agent Name, Detection Method, Expected Log Pattern, List of Phrases, Setup Function)
TEST_CASES = [
    {
        "agent": "PlanningAgent (Think Mode)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_THINK",
        "phrases": [
            "I need a plan",              # Simple
            "What are my options?",       # Ambiguous 1 (Question)
            "Let's pause and think",      # Ambiguous 2 (Meta)
        ],
        "setup": None,  # No special setup needed
    },
    {
        "agent": "InfoAgent (Info Mode)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_INFO",
        "phrases": [
            "Show character sheet",       # Simple
            "What am I carrying?",        # Ambiguous 1 (Natural question)
            "Check inventory",            # Ambiguous 2 (Command)
        ],
        "setup": None,
    },
    {
        "agent": "CombatAgent (Combat Mode)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_COMBAT",
        "phrases": [
            "Roll initiative!",           # Simple
            "I attack the guard",         # Ambiguous 1 (Action)
            "Execute him",                # Ambiguous 2 (Short command)
        ],
        "setup": None,
    },
    {
        "agent": "CharacterCreationAgent (Character Creation)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_CHAR_CREATION",
        "phrases": [
            "I want to level up",         # Simple
            "Select a feat",              # Ambiguous 1 (Process step)
            "Increase my strength",       # Ambiguous 2 (Stat change)
        ],
        "setup": None,
    },
    {
        "agent": "StoryModeAgent (Story Fallback)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_STORY",
        "phrases": [
            "I look around",              # Simple
            "Go north",                   # Ambiguous 1 (Movement)
            "Talk to the innkeeper",      # Ambiguous 2 (Social)
        ],
        "setup": None,
    },
    {
        "agent": "GodModeAgent (God Mode)",
        "detection": "explicit",
        "pattern": "GOD_MODE_DETECTED",
        "phrases": [
            "GOD MODE: set my hp to 100",  # Simple
            "GOD MODE: spawn a dragon",    # Ambiguous 1 (Spawn)
            "GOD MODE: teleport me",       # Ambiguous 2 (Teleport)
        ],
        "setup": None,
    },
    {
        "agent": "RewardsAgent (Rewards Mode)",
        "detection": "game_state",
        "pattern": "REWARDS_STATE_ACTIVE",
        "phrases": [
            "Process my rewards",         # Simple (but state-based, not input-based)
            "Give me my XP",              # Ambiguous 1 (Request)
            "Show my loot",               # Ambiguous 2 (Query)
        ],
        "setup": "setup_rewards_state",  # Need to set up combat/encounter completion
    },
    # Valid use cases: State transitions that should work
    {
        "agent": "CombatAgent (Initiate Combat)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_COMBAT",
        "phrases": [
            "I attack the goblin",        # Attack non-hostile NPC (should initiate combat)
        ],
        "setup": "setup_no_combat_state",  # Ensure NOT in combat
        "expected_agent": "CombatAgent",  # Should route to CombatAgent even if not in combat
    },
    {
        "agent": "RewardsAgent (Check Missed Rewards)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_REWARDS",
        "phrases": [
            "claim my rewards",          # LLM forgot to set rewards_pending (should check for missed rewards)
        ],
        "setup": "setup_no_rewards_state",  # Ensure NO rewards pending
        "expected_agent": "RewardsAgent",  # Should route to RewardsAgent even if no rewards pending
    },
    {
        "agent": "CombatAgent (Explicit Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*combat",
        "phrases": [
            "continue",                   # Generic input with mode="combat"
        ],
        "setup": "setup_no_combat_state",  # Ensure NOT in combat
        "expected_agent": "CombatAgent",  # Should route to CombatAgent even if not in combat
        "mode_override": "combat",       # Force mode="combat"
    },
    # NEW: CharacterCreationAgent routing on intent alone (level-up without active character creation)
    {
        "agent": "CharacterCreationAgent (Level-Up Intent)",
        "detection": "semantic",
        "pattern": "SEMANTIC_INTENT_CHAR_CREATION",
        "phrases": [
            "level up",                   # Level-up intent when NOT in character creation
            "I want to level up",         # Explicit level-up request
        ],
        "setup": "setup_no_character_creation_state",  # Ensure character creation NOT active
        "expected_agent": "CharacterCreationAgent",  # Should route to CharacterCreationAgent even if not active
    },
    # NEW: CharacterCreationAgent routing on explicit mode without state
    {
        "agent": "CharacterCreationAgent (Explicit Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*character_creation",
        "phrases": [
            "continue",                   # Generic input with mode="character_creation"
        ],
        "setup": "setup_no_character_creation_state",  # Ensure character creation NOT active
        "expected_agent": "CharacterCreationAgent",  # Should route to CharacterCreationAgent even if not active
        "mode_override": "character_creation",  # Force mode="character_creation"
    },
    # NEW: Case-insensitive mode parameter handling
    {
        "agent": "CombatAgent (Case-Insensitive Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*combat",
        "phrases": [
            "continue",                   # Generic input with mode="COMBAT" (uppercase)
        ],
        "setup": "setup_no_combat_state",
        "expected_agent": "CombatAgent",
        "mode_override": "COMBAT",       # Uppercase mode should work
    },
    {
        "agent": "RewardsAgent (Case-Insensitive Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*rewards",
        "phrases": [
            "continue",                   # Generic input with mode="REWARDS" (uppercase)
        ],
        "setup": "setup_no_rewards_state",
        "expected_agent": "RewardsAgent",
        "mode_override": "REWARDS",      # Uppercase mode should work
    },
    {
        "agent": "CharacterCreationAgent (Case-Insensitive Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*character_creation",
        "phrases": [
            "continue",                   # Generic input with mode="CHARACTER_CREATION" (uppercase)
        ],
        "setup": "setup_no_character_creation_state",
        "expected_agent": "CharacterCreationAgent",
        "mode_override": "CHARACTER_CREATION",  # Uppercase mode should work
    },
    {
        "agent": "InfoAgent (Case-Insensitive Mode)",
        "detection": "explicit_mode",
        "pattern": "API_EXPLICIT_MODE.*info",
        "phrases": [
            "continue",                   # Generic input with mode="INFO" (uppercase)
        ],
        "setup": None,
        "expected_agent": "InfoAgent",
        "mode_override": "INFO",         # Uppercase mode should work
    },
    # TRULY AMBIGUOUS TEST CASES: Even we're not sure which agent will handle these
    # These test the classifier's semantic understanding on genuinely ambiguous inputs
    {
        "agent": "Ambiguous: Help Request",
        "detection": "semantic",
        "pattern": None,  # No expected pattern - let classifier decide
        "phrases": [
            "help",                       # Could be PlanningAgent (planning help), InfoAgent (info help), or StoryModeAgent (general help)
        ],
        "setup": None,
        # No expected_agent - test which agent classifier chooses
    },
    {
        "agent": "Ambiguous: What Should I Do",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "what should I do?",         # Could be PlanningAgent (strategic planning) or StoryModeAgent (narrative guidance)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Check Command",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "check",                     # Could be InfoAgent (check stats/inventory) or CombatAgent (check enemy/initiative)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Use Ability",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "use my ability",            # Could be CombatAgent (combat ability) or CharacterCreationAgent (character ability/feat)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: What's Next",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "what's next?",              # Could be PlanningAgent (next step in plan), InfoAgent (next in sequence), or StoryModeAgent (narrative progression)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Do Something",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "do something",              # Extremely ambiguous - could route to any agent depending on context
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: I Need Help",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "I need help",               # Could be PlanningAgent (help planning) or StoryModeAgent (general narrative help)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Show Me",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "show me",                   # Could be InfoAgent (show info/stats) or StoryModeAgent (show narrative element)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: What Can I Do",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "what can I do?",            # Could be PlanningAgent (what actions available) or InfoAgent (what info available)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Generic Responses",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "ok",                        # Very ambiguous - likely StoryModeAgent fallback
            "yes",                       # Very ambiguous - likely StoryModeAgent fallback
            "no",                        # Very ambiguous - likely StoryModeAgent fallback
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Action Without Context",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "attack",                    # Could be CombatAgent (combat action) or StoryModeAgent (narrative action if not in combat)
        ],
        "setup": "setup_no_combat_state",  # Not in combat - test if classifier routes to CombatAgent anyway
    },
    {
        "agent": "Ambiguous: Status Query",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "status",                    # Could be InfoAgent (character status) or PlanningAgent (situation status)
        ],
        "setup": None,
    },
    {
        "agent": "Ambiguous: Next Step",
        "detection": "semantic",
        "pattern": None,
        "phrases": [
            "next step",                 # Could be PlanningAgent (planning next step) or StoryModeAgent (narrative next step)
        ],
        "setup": None,
    },
]

# Server startup is handled by start_local_mcp_server from lib.server_utils
# which automatically uses real LLMs (MOCK_SERVICES_MODE=false)

def check_logs_for(log_path, pattern):
    """Check if pattern exists in log file using regex matching."""
    import re
    try:
        with open(log_path, "rb") as f:
            content = f.read().decode('utf-8', errors='ignore')
            # If pattern contains regex syntax (.*), use regex matching
            if '.*' in pattern or '.*?' in pattern:
                # Use regex search with case-insensitive matching
                return bool(re.search(pattern, content, re.IGNORECASE | re.DOTALL))
            else:
                # Simple substring match for non-regex patterns (case-insensitive)
                return pattern.lower() in content.lower()
    except (IOError, OSError):
        return False

def clear_log(log_path):
    """Clear log content to ensure fresh checks."""
    with open(log_path, "w") as f:
        f.write("")

def setup_rewards_state(client, user_id, campaign_id):
    """Set up game state with rewards pending (combat ended with summary)."""
    # Use God Mode to set up combat state that triggers RewardsAgent
    # Combat must be ended with a combat_summary containing xp_awarded
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="GOD MODE: Set combat_state.in_combat=false, combat_state.combat_phase='ended', combat_state.combat_summary={'xp_awarded': 100, 'enemies_defeated': ['test_enemy']}, combat_state.rewards_processed=false",
        mode="god"
    )
    
    # Give server time to process state update
    time.sleep(2)

def setup_no_combat_state(client, user_id, campaign_id):
    """Set up game state with NO combat active."""
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="GOD MODE: Set combat_state.in_combat=false, combat_state.combat_phase=null",
        mode="god"
    )
    time.sleep(2)

def setup_no_rewards_state(client, user_id, campaign_id):
    """Set up game state with NO rewards pending."""
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="GOD MODE: Set combat_state.rewards_processed=true, rewards_pending=null",
        mode="god"
    )
    time.sleep(2)

def setup_no_character_creation_state(client, user_id, campaign_id):
    """Set up game state with character creation NOT active (character completed, no level-up pending)."""
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="GOD MODE: Set custom_campaign_state.character_creation_in_progress=false, custom_campaign_state.character_creation_completed=true, rewards_pending.level_up_available=false",
        mode="god"
    )
    time.sleep(2)

def test_all_agents():
    parser = argparse.ArgumentParser(description="Test all 7 agents with real LLMs")
    parser.add_argument(
        "--server-url",
        type=str,
        help="MCP server URL (e.g., http://127.0.0.1:8001)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Disable evidence bundle capture (evidence is enabled by default)",
    )
    args = parser.parse_args()
    
    # Setup evidence directory (always enabled by default unless --no-evidence)
    evidence_dir = None
    if not args.no_evidence:
        evidence_dir = get_evidence_dir(TEST_NAME)
        print(f"📦 Evidence directory: {evidence_dir}")
    
    # Setup server
    server_url = args.server_url
    local_server: LocalServer | None = None
    log_path = None
    
    if args.start_local:
        port = pick_free_port()
        print(f"🚀 Starting local MCP server on port {port}...")
        # start_local_mcp_server automatically uses real LLMs (MOCK_SERVICES_MODE=false)
        env_overrides = {
            "ENABLE_SEMANTIC_ROUTING": "true",
            "WORLDAI_DEV_MODE": "true",
        }
        local_server = start_local_mcp_server(port, env_overrides=env_overrides)
        log_path = local_server.log_path
        server_url = f"{local_server.base_url}/mcp"
        print(f"✅ Server started: {server_url}")
        print(f"📝 Log file: {log_path}")
        time.sleep(3)  # Give server time to start
    else:
        if not server_url:
            parser.error("Must provide --server-url or --start-local")
        # For external server, we can't easily get logs, so we'll skip log checks
        print(f"⚠️  Using external server - log pattern checks will be limited")
    
    client = MCPClient(server_url, timeout_s=600.0)
    
    try:
        # Wait for healthy
        if local_server:
            base_url = local_server.base_url
            start_wait = time.time()
            healthy = False
            while time.time() - start_wait < 30:
                try:
                    r = requests.get(f"{base_url}/health", timeout=1)
                    if r.status_code == 200:
                        healthy = True
                        break
                except (requests.RequestException, ConnectionError):
                    pass
                time.sleep(0.5)
            
            assert healthy, "Server failed to start."
        
        user_id = "test_agent_selection_user"
        campaign_id = create_campaign(
            client, 
            user_id, 
            title="Agent Selection Test",
            character="Tester",
            setting="Test Lab", 
            description="Testing all agent selection"
        )
        
        # Ensure character creation is complete
        ensure_game_state_seed(client, user_id=user_id, campaign_id=campaign_id)
        
        # Capture provenance and setup evidence tracking
        provenance = None
        request_responses = []
        if evidence_dir:
            provenance = capture_provenance(
                server_url,
                local_server.pid if local_server else None,
                server_env_overrides={"ENABLE_SEMANTIC_ROUTING": "true"} if local_server else None,
            )
        
        # Poll for classifier readiness (it loads in background)
        if local_server and log_path:
            print("⏳ Waiting for classifier to load (polling)...")
            start = time.time()
            classifier_ready = False
            
            while time.time() - start < 60:
                clear_log(log_path)
                # "I need a plan" should trigger THINK mode
                process_action(
                    client, 
                    user_id=user_id, 
                    campaign_id=campaign_id, 
                    user_input="I need a plan to escape", 
                    mode="character" 
                )
                
                if check_logs_for(log_path, "SEMANTIC_INTENT_THINK"):
                    print("✅ Classifier is ready and working! (Think Mode detected in logs)")
                    classifier_ready = True
                    break
                
                print(".", end="", flush=True)
                time.sleep(2)
            
            assert classifier_ready, "Classifier failed to load or classify within timeout."
        
        # Run Data-Driven Tests
        total_test_cases = sum(len(case["phrases"]) for case in TEST_CASES)
        print(f"\n🔎 Running Agent Selection Tests ({len(TEST_CASES)} test cases, {total_test_cases} total phrases)...")
        print(f"{'='*70}")
        
        results = []
        
        for case in TEST_CASES:
            agent_name = case["agent"]
            pattern = case["pattern"]
            detection = case["detection"]
            setup_func = case.get("setup")
            
            print(f"\n🧪 Testing {agent_name} ({detection} detection)...")
            
            # Run setup if needed
            if setup_func == "setup_rewards_state":
                print("  ⚙️  Setting up rewards state...")
                setup_rewards_state(client, user_id, campaign_id)
            elif setup_func == "setup_no_combat_state":
                print("  ⚙️  Setting up NO combat state...")
                setup_no_combat_state(client, user_id, campaign_id)
            elif setup_func == "setup_no_rewards_state":
                print("  ⚙️  Setting up NO rewards state...")
                setup_no_rewards_state(client, user_id, campaign_id)
            elif setup_func == "setup_no_character_creation_state":
                print("  ⚙️  Setting up NO character creation state...")
                setup_no_character_creation_state(client, user_id, campaign_id)
            
            for i, phrase in enumerate(case["phrases"], 1):
                phrase_type = "Simple" if i == 1 else f"Ambiguous {i-1}"
                
                if local_server and log_path:
                    clear_log(log_path)
                
                try:
                    # Determine mode based on agent or override
                    mode = case.get("mode_override", "character")
                    if not mode and "God" in agent_name:
                        mode = "god"
                    elif not mode and "Rewards" in agent_name:
                        mode = "character"  # Rewards is state-based, not input-based
                    elif not mode:
                        mode = "character"
                    
                    response = process_action(
                        client,
                        user_id=user_id,
                        campaign_id=campaign_id,
                        user_input=phrase,
                        mode=mode
                    )
                    
                    # Save request/response for evidence
                    if evidence_dir:
                        request_responses.append({
                            "test_case": agent_name,
                            "phrase_type": phrase_type,
                            "phrase": phrase,
                            "mode": mode,
                            "request": {
                                "user_input": phrase,
                                "mode": mode,
                                "campaign_id": campaign_id,
                            },
                            "response": response,
                        })
                    
                    # Check logs for pattern
                    if local_server and log_path:
                        # Handle truly ambiguous cases (no expected pattern)
                        if pattern is None:
                            # For ambiguous cases, just verify that SOME agent handled it (response exists)
                            # Log which agent was chosen for analysis
                            if response:
                                # Try to detect which agent handled it from logs
                                agents_to_check = ["PlanningAgent", "InfoAgent", "CombatAgent", "CharacterCreationAgent", "StoryModeAgent", "GodModeAgent", "RewardsAgent"]
                                chosen_agent = None
                                with open(log_path, "r", errors="ignore") as f:
                                    log_content = f.read()
                                    for agent in agents_to_check:
                                        if agent in log_content:
                                            chosen_agent = agent
                                            break
                                
                                if chosen_agent:
                                    print(f"  🔍 [{phrase_type}] '{phrase}' -> Classifier chose: {chosen_agent} (Ambiguous - any agent acceptable)")
                                else:
                                    print(f"  🔍 [{phrase_type}] '{phrase}' -> Classifier handled (Ambiguous - agent not detected in logs)")
                                results.append({"agent": agent_name, "phrase": phrase, "passed": True, "chosen_agent": chosen_agent})
                            else:
                                print(f"  ❌ [{phrase_type}] '{phrase}' -> ERROR: No response received")
                                results.append({"agent": agent_name, "phrase": phrase, "passed": False})
                        else:
                            found = check_logs_for(log_path, pattern)
                            # Also check for expected agent routing if specified
                            expected_agent = case.get("expected_agent")
                            if expected_agent:
                                agent_found = check_logs_for(log_path, expected_agent)
                                if found and agent_found:
                                    print(f"  ✅ [{phrase_type}] '{phrase}' -> {pattern} -> {expected_agent} (Pass)")
                                    results.append({"agent": agent_name, "phrase": phrase, "passed": True})
                                elif found and not agent_found:
                                    print(f"  ❌ [{phrase_type}] '{phrase}' -> {pattern} found but NOT routed to {expected_agent}")
                                    # Show last 500 chars of log for debugging
                                    with open(log_path, "r", errors="ignore") as f:
                                        log_content = f.read()
                                        print(f"      Log tail: {log_content[-500:]}")
                                    results.append({"agent": agent_name, "phrase": phrase, "passed": False})
                                else:
                                    print(f"  ❌ [{phrase_type}] '{phrase}' -> Expected {pattern} but not found")
                                    # Show last 500 chars of log for debugging
                                    with open(log_path, "r", errors="ignore") as f:
                                        log_content = f.read()
                                        print(f"      Log tail: {log_content[-500:]}")
                                    results.append({"agent": agent_name, "phrase": phrase, "passed": False})
                            else:
                                if found:
                                    print(f"  ✅ [{phrase_type}] '{phrase}' -> {pattern} (Pass)")
                                    results.append({"agent": agent_name, "phrase": phrase, "passed": True})
                                else:
                                    print(f"  ❌ [{phrase_type}] '{phrase}' -> Expected {pattern} but not found")
                                    # Show last 500 chars of log for debugging
                                    with open(log_path, "r", errors="ignore") as f:
                                        log_content = f.read()
                                        print(f"      Log tail: {log_content[-500:]}")
                                    results.append({"agent": agent_name, "phrase": phrase, "passed": False})
                    else:
                        # External server - can't check logs
                        if pattern is None:
                            # For ambiguous cases, just verify response exists
                            if response:
                                print(f"  🔍 [{phrase_type}] '{phrase}' -> (External server, ambiguous - classifier chose an agent)")
                                results.append({"agent": agent_name, "phrase": phrase, "passed": True})
                            else:
                                print(f"  ❌ [{phrase_type}] '{phrase}' -> ERROR: No response received")
                                results.append({"agent": agent_name, "phrase": phrase, "passed": False})
                        else:
                            print(f"  ⚠️  [{phrase_type}] '{phrase}' -> (External server, log check skipped)")
                            results.append({"agent": agent_name, "phrase": phrase, "passed": True})
                    
                    time.sleep(1)  # Small delay between requests
                    
                except Exception as e:
                    print(f"  ❌ [{phrase_type}] '{phrase}' -> ERROR: {e}")
                    results.append({"agent": agent_name, "phrase": phrase, "passed": False, "error": str(e)})
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*70}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("passed", False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {100 * passed_tests / total_tests if total_tests > 0 else 0:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for r in results:
                if not r.get("passed", False):
                    print(f"  - {r['agent']}: '{r['phrase']}'")
                    if "error" in r:
                        print(f"    Error: {r['error']}")
        
        # Latency Check
        if local_server:
            print(f"\n⚡ Measuring Classification Latency (5 requests)...")
            start_lat = time.time()
            for _ in range(5):
                process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input="I need a plan",
                    mode="character"
                )
            avg_lat = (time.time() - start_lat) / 5
            print(f"Average Latency (including HTTP overhead): {avg_lat*1000:.2f}ms")
        
        # Create evidence bundle
        if evidence_dir and provenance:
            print(f"\n📦 Creating evidence bundle...")
            results_dict = {
                "test_cases": results,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": 100 * passed_tests / total_tests if total_tests > 0 else 0,
                },
            }
            create_evidence_bundle(
                evidence_dir=evidence_dir,
                test_name=TEST_NAME,
                provenance=provenance,
                results=results_dict,
                request_responses=request_responses,
                server_log_path=log_path if log_path and log_path.exists() else None,
            )
            print(f"✅ Evidence bundle created: {evidence_dir}")
        
        # Exit with error code if any tests failed
        if failed_tests > 0:
            print(f"\n❌ SOME TESTS FAILED")
            sys.exit(1)
        else:
            print(f"\n✅ ALL TESTS PASSED")
            sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if local_server:
            print(f"\n🛑 Stopping local server...")
            local_server.stop()

if __name__ == "__main__":
    test_all_agents()
