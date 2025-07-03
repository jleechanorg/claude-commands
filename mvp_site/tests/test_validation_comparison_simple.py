#!/usr/bin/env python3
"""
Simple comparison of Pydantic vs Simple validation using existing integration.
Tests what's actually implemented in the codebase.
"""
import unittest
import os
import json
import sys
import logging
import subprocess
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestValidationComparisonSimple(unittest.TestCase):
    """Compare Pydantic vs Simple validation with what's actually integrated"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Load Sariel campaign prompts
        prompts_path = os.path.join(os.path.dirname(__file__), 'data', 'sariel_campaign_prompts.json')
        with open(prompts_path, 'r') as f:
            cls.sariel_data = json.load(f)
    
    def test_run_both_validations(self):
        """Run tests with both Pydantic and Simple validation"""
        results = {
            'test_date': datetime.now().isoformat(),
            'pydantic_results': [],
            'simple_results': []
        }
        
        # Test with Simple validation (default)
        logger.info("=== Testing with Simple Validation ===")
        for i in range(3):  # Run 3 times for initial test
            logger.info(f"Simple validation run {i+1}/3")
            result = self._run_single_test("simple", i)
            results['simple_results'].append(result)
        
        # Test with Pydantic validation
        logger.info("\n=== Testing with Pydantic Validation ===")
        for i in range(3):  # Run 3 times for initial test
            logger.info(f"Pydantic validation run {i+1}/3")
            result = self._run_single_test("pydantic", i)
            results['pydantic_results'].append(result)
        
        # Save results
        self._save_results(results)
        
        # Print summary
        self._print_summary(results)
    
    def _run_single_test(self, validation_type: str, run_number: int) -> dict:
        """Run a single test with specified validation type"""
        # Set environment variable
        env = os.environ.copy()
        env['USE_PYDANTIC'] = 'true' if validation_type == 'pydantic' else 'false'
        env['TESTING'] = 'true'
        
        result = {
            'run_number': run_number,
            'validation_type': validation_type,
            'cassian_problem_tested': False,
            'cassian_mentioned': False,
            'errors': []
        }
        
        try:
            # Run the integration test for interaction #2 (Cassian problem)
            python_path = '/home/jleechan/projects/worldarchitect.ai/vpython'
            test_script = os.path.join(os.path.dirname(__file__), 'run_cassian_test.py')
            
            # Create a simple test runner script
            test_runner_content = '''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
import json
from test_integration.integration_test_lib import IntegrationTestSetup

# Load test data
with open('data/sariel_campaign_prompts.json', 'r') as f:
    sariel_data = json.load(f)

app = create_app()
app.config['TESTING'] = True
client = app.test_client()
user_id = 'test-cassian-' + sys.argv[1]

# Create campaign
initial_prompt = sariel_data['prompts'][0]
campaign_data = {
    'prompt': initial_prompt['input'],
    'title': 'Cassian Test ' + sys.argv[1],
    'selected_prompts': ['narrative', 'mechanics']
}

response = client.post(
    '/api/campaigns',
    headers=IntegrationTestSetup.create_test_headers(user_id),
    data=json.dumps(campaign_data)
)

if response.status_code == 201:
    campaign_id = response.get_json()['campaign_id']
    
    # Run Cassian interaction
    cassian_prompt = sariel_data['prompts'][2]  # The Cassian problem prompt
    interaction_data = {'input': cassian_prompt['input']}
    
    response = client.post(
        f'/api/campaigns/{campaign_id}/interaction',
        headers=IntegrationTestSetup.create_test_headers(user_id),
        data=json.dumps(interaction_data)
    )
    
    if response.status_code == 200:
        result = response.get_json()
        narrative = result.get('narrative', '')
        print(json.dumps({
            'success': True,
            'cassian_mentioned': 'cassian' in narrative.lower(),
            'narrative_length': len(narrative)
        }))
    else:
        print(json.dumps({'success': False, 'error': f'Interaction failed: {response.status_code}'}))
else:
    print(json.dumps({'success': False, 'error': f'Campaign creation failed: {response.status_code}'}))
'''
            
            # Write the test runner
            with open(test_script, 'w') as f:
                f.write(test_runner_content)
            
            # Run the test
            cmd = [python_path, test_script, f"{validation_type}_{run_number}"]
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=os.path.dirname(__file__))
            
            if proc.returncode == 0:
                try:
                    output = json.loads(proc.stdout.strip())
                    result['cassian_problem_tested'] = output.get('success', False)
                    result['cassian_mentioned'] = output.get('cassian_mentioned', False)
                except:
                    result['errors'].append(f"Failed to parse output: {proc.stdout}")
            else:
                result['errors'].append(f"Test failed: {proc.stderr}")
                
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def _save_results(self, results: dict):
        """Save results to file"""
        # Use temporary directory for test outputs
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='validation_results_')
        
        filepath = os.path.join(temp_dir, f'comparison_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {filepath}")
    
    def _print_summary(self, results: dict):
        """Print summary of results"""
        logger.info("\n=== VALIDATION COMPARISON SUMMARY ===")
        
        # Simple validation summary
        simple_cassian_success = sum(1 for r in results['simple_results'] if r['cassian_mentioned'])
        simple_test_success = sum(1 for r in results['simple_results'] if r['cassian_problem_tested'])
        logger.info(f"\nSimple Validation:")
        logger.info(f"  Tests run successfully: {simple_test_success}/3")
        logger.info(f"  Cassian mentioned: {simple_cassian_success}/3")
        
        # Pydantic validation summary
        pydantic_cassian_success = sum(1 for r in results['pydantic_results'] if r['cassian_mentioned'])
        pydantic_test_success = sum(1 for r in results['pydantic_results'] if r['cassian_problem_tested'])
        logger.info(f"\nPydantic Validation:")
        logger.info(f"  Tests run successfully: {pydantic_test_success}/3")
        logger.info(f"  Cassian mentioned: {pydantic_cassian_success}/3")
        
        logger.info("\n" + "="*50)


if __name__ == '__main__':
    unittest.main()