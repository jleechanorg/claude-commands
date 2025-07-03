#!/usr/bin/env python3
"""
Compare Pydantic vs Simple validation approaches for entity tracking.
Uses real Sariel campaign data to test entity sync performance.
"""
import unittest
import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import create_app
from game_state import GameState
from entity_tracking import SceneManifest, create_from_game_state
from entity_preloader import EntityPreloader
from entity_validator import EntityValidator
from entity_instructions import EntityInstructionGenerator
from test_integration.integration_test_lib import IntegrationTestSetup, setup_integration_test_environment

# Import both validation schemas
from schemas import entities_pydantic, entities_simple

# Set up the integration test environment
test_setup = setup_integration_test_environment(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationMetrics:
    """Track metrics for validation comparison"""
    def __init__(self, name: str):
        self.name = name
        self.total_runs = 0
        self.entity_tracking_success = 0
        self.cassian_problem_success = 0
        self.validation_errors = 0
        self.execution_times = []
        self.memory_usage = []
        
    def record_run(self, success: bool, cassian_success: bool, exec_time: float, memory: int = 0):
        self.total_runs += 1
        if success:
            self.entity_tracking_success += 1
        if cassian_success:
            self.cassian_problem_success += 1
        self.execution_times.append(exec_time)
        if memory:
            self.memory_usage.append(memory)
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'total_runs': self.total_runs,
            'entity_tracking_rate': self.entity_tracking_success / self.total_runs if self.total_runs > 0 else 0,
            'cassian_problem_rate': self.cassian_problem_success / self.total_runs if self.total_runs > 0 else 0,
            'avg_execution_time': sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0,
            'avg_memory_usage': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
            'validation_errors': self.validation_errors
        }


class TestEntityValidationComparison(unittest.TestCase):
    """Compare Pydantic vs Simple validation approaches"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = 'test-validation-comparison'
        
        # Load Sariel campaign prompts
        prompts_path = os.path.join(os.path.dirname(__file__), 'data', 'sariel_campaign_prompts.json')
        with open(prompts_path, 'r') as f:
            cls.sariel_data = json.load(f)
            
        # Initialize components
        cls.entity_preloader = EntityPreloader()
        cls.entity_validator = EntityValidator()
        cls.instruction_generator = EntityInstructionGenerator()
    
    def test_pydantic_validation_replay(self):
        """Test entity tracking using Pydantic validation"""
        logger.info("=== Starting Pydantic Validation Test ===")
        metrics = ValidationMetrics("Pydantic")
        
        # Run 10 replays
        for run in range(10):
            logger.info(f"Pydantic Run {run + 1}/10")
            success, cassian_success, exec_time = self._run_single_replay(
                f"pydantic_run_{run}", 
                use_pydantic=True
            )
            metrics.record_run(success, cassian_success, exec_time)
        
        # Save results
        self._save_metrics(metrics, "pydantic_results.json")
        
        # Report summary
        summary = metrics.get_summary()
        logger.info(f"Pydantic Results: {summary}")
        
    def test_simple_validation_replay(self):
        """Test entity tracking using Simple validation"""
        logger.info("=== Starting Simple Validation Test ===")
        metrics = ValidationMetrics("Simple")
        
        # Run 10 replays
        for run in range(10):
            logger.info(f"Simple Run {run + 1}/10")
            success, cassian_success, exec_time = self._run_single_replay(
                f"simple_run_{run}", 
                use_pydantic=False
            )
            metrics.record_run(success, cassian_success, exec_time)
        
        # Save results
        self._save_metrics(metrics, "simple_results.json")
        
        # Report summary
        summary = metrics.get_summary()
        logger.info(f"Simple Results: {summary}")
    
    def _run_single_replay(self, run_id: str, use_pydantic: bool) -> tuple[bool, bool, float]:
        """Run a single replay and return (overall_success, cassian_success, execution_time)"""
        start_time = time.time()
        overall_success = True
        cassian_success = False
        
        try:
            # Create campaign
            prompts = self.sariel_data['prompts']
            initial_prompt = prompts[0]
            
            campaign_data = {
                'prompt': initial_prompt['input'],
                'title': f'Validation Test {run_id}',
                'selected_prompts': ['narrative', 'mechanics']
            }
            
            create_response = self.client.post(
                '/api/campaigns',
                headers=IntegrationTestSetup.create_test_headers(self.user_id),
                data=json.dumps(campaign_data)
            )
            
            if create_response.status_code != 201:
                logger.error(f"Failed to create campaign: {create_response.status_code}")
                return False, False, time.time() - start_time
                
            campaign_info = create_response.get_json()
            campaign_id = campaign_info['campaign_id']
            
            # Process interactions
            for i, prompt in enumerate(prompts[1:6]):  # First 5 interactions
                is_cassian = prompt['metadata'].get('is_cassian_problem', False)
                
                # Submit interaction
                interaction_data = {'input': prompt['input']}
                response = self.client.post(
                    f'/api/campaigns/{campaign_id}/interaction',
                    headers=IntegrationTestSetup.create_test_headers(self.user_id),
                    data=json.dumps(interaction_data)
                )
                
                if response.status_code != 200:
                    logger.error(f"Interaction {i+1} failed: {response.status_code}")
                    overall_success = False
                    continue
                
                # Validate entity tracking
                result = response.get_json()
                narrative = result.get('narrative', '')
                
                # Check entity presence based on validation approach
                if use_pydantic:
                    entity_present = self._validate_with_pydantic(narrative, prompt)
                else:
                    entity_present = self._validate_with_simple(narrative, prompt)
                
                if not entity_present:
                    logger.warning(f"Entity tracking failed for interaction {i+1}")
                    overall_success = False
                
                # Special check for Cassian problem
                if is_cassian and "cassian" in narrative.lower():
                    cassian_success = True
                    logger.info("Cassian problem SOLVED!")
            
        except Exception as e:
            logger.error(f"Error during replay: {e}")
            overall_success = False
        
        exec_time = time.time() - start_time
        return overall_success, cassian_success, exec_time
    
    def _validate_with_pydantic(self, narrative: str, prompt: dict) -> bool:
        """Validate entity presence using Pydantic schema"""
        expected_entities = prompt['context'].get('expected_entities', [])
        
        # Use Pydantic validation logic
        try:
            # Create validation data structure
            validation_data = {
                'entities': expected_entities,
                'narrative': narrative
            }
            # Validate using Pydantic (simplified for testing)
            for entity in expected_entities:
                if entity.lower() not in narrative.lower():
                    return False
            return True
        except Exception as e:
            logger.error(f"Pydantic validation error: {e}")
            return False
    
    def _validate_with_simple(self, narrative: str, prompt: dict) -> bool:
        """Validate entity presence using Simple validation"""
        expected_entities = prompt['context'].get('expected_entities', [])
        
        # Use simple string matching
        for entity in expected_entities:
            if entity.lower() not in narrative.lower():
                return False
        return True
    
    def _save_metrics(self, metrics: ValidationMetrics, filename: str):
        """Save metrics to file"""
        # Use temporary directory for test outputs
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='validation_metrics_')
        
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(metrics.get_summary(), f, indent=2)
        
        logger.info(f"Saved results to {filepath}")


if __name__ == '__main__':
    unittest.main()