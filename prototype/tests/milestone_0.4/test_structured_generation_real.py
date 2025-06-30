#!/usr/bin/env python3
"""
Enhanced Test Framework with Real Gemini API Integration
Extends the base test framework to support real LLM calls
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import os
import sys

# Add imports from base test framework
from test_structured_generation import (
    TestHarness, TestApproach, TestResult,
    get_scenario
)

# Import real API client
from gemini_client import get_client, GeminiClient
from scripts.prompt_templates import get_prompt_template
from schemas.entities_simple import SceneManifest, create_from_game_state
from prototype.validators.narrative_sync_validator import NarrativeSyncValidator

logger = logging.getLogger(__name__)


class RealLLMTestHarness(TestHarness):
    """Test harness with real Gemini API integration"""
    
    def __init__(self, use_real_api: bool = True, dry_run: bool = False):
        """Initialize with API configuration"""
        super().__init__()
        self.use_real_api = use_real_api
        self.dry_run = dry_run
        self.gemini_client: Optional[GeminiClient] = None
        
        if use_real_api and not dry_run:
            self.gemini_client = get_client(use_mock=False)
            logger.info("Initialized real Gemini API client")
        else:
            logger.info(f"Running in {'dry run' if dry_run else 'mock'} mode")
    
    def _extract_expected_entities(self, game_state: Dict[str, Any]) -> List[str]:
        """Extract entity names that should appear in the narrative"""
        entities = []
        
        # Add player character
        if "player_character_data" in game_state:
            pc = game_state["player_character_data"]
            if isinstance(pc, dict) and "name" in pc:
                entities.append(pc["name"])
        
        # Add NPCs
        if "npc_data" in game_state:
            npcs = game_state["npc_data"]
            if isinstance(npcs, dict):
                # NPCs are stored as a dictionary with names as keys
                for npc_name, npc_data in npcs.items():
                    if isinstance(npc_data, dict):
                        # Only include present, conscious NPCs
                        if (npc_data.get("present", True) and 
                            npc_data.get("conscious", True) and
                            npc_data.get("hp", 1) > 0 and
                            not npc_data.get("hidden", False)):
                            entities.append(npc_name)
            elif isinstance(npcs, list):
                # Handle list format too
                for npc in npcs:
                    if isinstance(npc, dict) and "name" in npc:
                        # Only include conscious, visible NPCs
                        if npc.get("hp_current", 1) > 0 and not npc.get("hidden", False):
                            entities.append(npc["name"])
        
        return entities
    
    def _generate_real_narrative(self, prompt: str, approach: TestApproach) -> Tuple[str, Dict[str, Any]]:
        """Generate narrative using real Gemini API"""
        if self.dry_run:
            logger.info(f"DRY RUN: Would call API with {len(prompt)} chars")
            return "Dry run narrative", {"duration": 0, "tokens": 0}
        
        if not self.use_real_api or not self.gemini_client:
            # Fall back to mock
            return self._generate_mock_narrative(prompt, approach)
        
        # Add system instruction based on approach
        system_instruction = self._get_system_instruction(approach)
        
        # Call real API
        response = self.gemini_client.generate_narrative(prompt, system_instruction)
        
        if not response["success"]:
            logger.error(f"API call failed: {response.get('error')}")
            # Fall back to mock on failure
            return self._generate_mock_narrative(prompt, approach)
        
        # Extract narrative and metrics
        narrative = response["text"]
        metrics = {
            "duration": response["duration"],
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
            "cost_usd": response.get("cost_usd", 0)
        }
        
        return narrative, metrics
    
    def _get_system_instruction(self, approach: TestApproach) -> str:
        """Get system instruction based on approach"""
        if approach == TestApproach.VALIDATION_ONLY:
            return "Generate a narrative continuation for this D&D campaign scene."
        elif approach == TestApproach.PYDANTIC_ONLY:
            return """Generate a narrative continuation that mentions ALL entities from the provided manifest.
Format your response as:
1. A narrative paragraph
2. A JSON block with entity tracking"""
        else:  # COMBINED
            return """Generate a narrative in JSON format with entity tracking.
You MUST include ALL entities from the manifest and return valid JSON with these fields:
- narrative: the story text mentioning all characters
- entities_mentioned: array of all character names mentioned
- location_confirmed: the current location name"""
    
    def _run_validation_only(self, campaign_id: str, scenario: Dict[str, Any]) -> TestResult:
        """Test approach 1: Current validation-only method with real API"""
        start_time = time.time()
        
        # Get prompt from template
        prompt = get_prompt_template("baseline", scenario)
        
        # Generate with real API
        narrative, api_metrics = self._generate_real_narrative(prompt, TestApproach.VALIDATION_ONLY)
        generation_time = api_metrics["duration"] * 1000  # Convert to ms
        
        # Debug output
        logger.info(f"Generated narrative: {narrative[:100]}...")
        logger.info(f"Expected entities: {self._extract_expected_entities(scenario['game_state'])}")
        
        # Validate
        validation_start = time.time()
        # Extract expected entities from game state
        expected_entities = self._extract_expected_entities(scenario["game_state"])
        
        validation_result = self.validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location=scenario["game_state"].get("location", "Unknown")
        )
        validation_time = (time.time() - validation_start) * 1000
        
        # Results from validation
        entities_expected = self._extract_expected_entities(scenario["game_state"])
        entities_found = validation_result.entities_found
        entities_missing = validation_result.entities_missing
        
        return TestResult(
            approach=TestApproach.VALIDATION_ONLY,
            campaign_id=campaign_id,
            scenario_id=scenario.get("scenario_id", "unknown"),
            session=scenario.get("session", 0),
            turn=scenario.get("turn", 0),
            generation_time_ms=generation_time,
            validation_time_ms=validation_time,
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=api_metrics.get("input_tokens", 0) + api_metrics.get("output_tokens", 0),
            estimated_cost=api_metrics.get("cost_usd", 0),
            entities_expected=entities_expected,
            entities_found=entities_found,
            entities_missing=entities_missing,
            desync_detected=not validation_result.all_entities_present,
            desync_pattern="missing_entities" if validation_result.entities_missing else None,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..." if len(narrative) > 200 else narrative
        )
    
    def _run_pydantic_only(self, campaign_id: str, scenario: Dict[str, Any]) -> TestResult:
        """Test approach 2: Pydantic-structured generation with real API"""
        start_time = time.time()
        
        # Create manifest
        manifest = create_from_game_state(
            scenario["game_state"], 
            scenario.get("session", 1),
            scenario.get("turn", 1)
        )
        
        # Get structured prompt
        prompt = get_prompt_template("pydantic", scenario, manifest)
        
        # Generate with real API
        narrative, api_metrics = self._generate_real_narrative(prompt, TestApproach.PYDANTIC_ONLY)
        generation_time = api_metrics["duration"] * 1000
        
        # Simple validation (check if entities mentioned)
        entities_expected = self._extract_expected_entities(scenario["game_state"])
        entities_found = []
        entities_missing = []
        
        # Parse structured response if present
        structured_data = self.gemini_client.parse_structured_response(narrative, "json") if self.gemini_client else None
        
        if structured_data and "entities_mentioned" in structured_data:
            entities_found = structured_data["entities_mentioned"]
        else:
            # Fall back to simple text matching
            for entity in entities_expected:
                if entity.lower() in narrative.lower():
                    entities_found.append(entity)
                else:
                    entities_missing.append(entity)
        
        return TestResult(
            approach=TestApproach.PYDANTIC_ONLY,
            campaign_id=campaign_id,
            scenario_id=scenario.get("scenario_id", "unknown"),
            session=scenario.get("session", 0),
            turn=scenario.get("turn", 0),
            generation_time_ms=generation_time,
            validation_time_ms=0,  # No validation step
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=api_metrics.get("input_tokens", 0) + api_metrics.get("output_tokens", 0),
            estimated_cost=api_metrics.get("cost_usd", 0),
            entities_expected=entities_expected,
            entities_found=entities_found,
            entities_missing=entities_missing,
            desync_detected=len(entities_missing) > 0,
            desync_pattern="structured_generation" if entities_missing else None,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..." if len(narrative) > 200 else narrative
        )
    
    def _run_combined(self, campaign_id: str, scenario: Dict[str, Any]) -> TestResult:
        """Test approach 3: Combined Pydantic + validation with real API"""
        start_time = time.time()
        
        # Create manifest
        manifest = create_from_game_state(
            scenario["game_state"], 
            scenario.get("session", 1),
            scenario.get("turn", 1)
        )
        
        # Get combined prompt
        prompt = get_prompt_template("combined", scenario, manifest)
        
        # Generate with real API
        response_text, api_metrics = self._generate_real_narrative(prompt, TestApproach.COMBINED)
        generation_time = api_metrics["duration"] * 1000
        
        # Parse structured response if present
        structured_data = self.gemini_client.parse_structured_response(response_text, "json") if self.gemini_client else None
        
        # Extract narrative from structured response or use full response
        if structured_data and "narrative" in structured_data:
            narrative = structured_data["narrative"]
            entities_from_json = structured_data.get("entities_mentioned", [])
        else:
            narrative = response_text
            entities_from_json = []
        
        # Full validation
        validation_start = time.time()
        # Extract expected entities from game state
        expected_entities = self._extract_expected_entities(scenario["game_state"])
        
        validation_result = self.validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location=scenario["game_state"].get("location", "Unknown")
        )
        validation_time = (time.time() - validation_start) * 1000
        
        # Results - use JSON entities if available, otherwise validation results
        entities_expected = self._extract_expected_entities(scenario["game_state"])
        entities_found = entities_from_json if entities_from_json else validation_result.entities_found
        entities_missing = [e for e in entities_expected if e not in entities_found]
        
        return TestResult(
            approach=TestApproach.COMBINED,
            campaign_id=campaign_id,
            scenario_id=scenario.get("scenario_id", "unknown"),
            session=scenario.get("session", 0),
            turn=scenario.get("turn", 0),
            generation_time_ms=generation_time,
            validation_time_ms=validation_time,
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=api_metrics.get("input_tokens", 0) + api_metrics.get("output_tokens", 0),
            estimated_cost=api_metrics.get("cost_usd", 0),
            entities_expected=entities_expected,
            entities_found=entities_found,
            entities_missing=entities_missing,
            desync_detected=not validation_result.all_entities_present,
            desync_pattern="missing_entities" if validation_result.entities_missing else None,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..." if len(narrative) > 200 else narrative
        )
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary from API client"""
        if self.gemini_client:
            return self.gemini_client.get_cost_summary()
        return {"total_calls": 0, "total_cost_usd": 0}
    
    def run_limited_tests(self, campaigns: List[str], scenarios: List[str], approach: TestApproach) -> List[TestResult]:
        """Run limited set of tests for cost control"""
        results = []
        
        for campaign_id in campaigns:
            for scenario_id in scenarios:
                logger.info(f"Testing {campaign_id} - {scenario_id} with {approach.value}")
                
                # Get scenario (note: get_scenario takes scenario_id first, then campaign_id)
                scenario = get_scenario(scenario_id, campaign_id)
                if not scenario:
                    logger.warning(f"Scenario not found: {campaign_id}/{scenario_id}")
                    continue
                
                # Check budget before each test
                if self.gemini_client:
                    cost_summary = self.gemini_client.get_cost_summary()
                    if cost_summary["total_cost_usd"] >= 0.90:  # Stop at 90% budget
                        logger.warning("Approaching budget limit, stopping tests")
                        break
                
                # Run test
                result = self._run_single_test(campaign_id, scenario_id, approach)
                results.append(result)
        
        return results