#!/usr/bin/env python3
"""
Quick comparison of Pydantic vs Simple validation focusing on Cassian problem.
Runs fewer iterations for faster results.
"""

import json
import os
import sys
import time
import unittest
from datetime import datetime

import logging_util

import tempfile

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from integration_test_lib import IntegrationTestSetup
from main import create_app

# Configure logging
logging_util.basicConfig(
    level=logging_util.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging_util.getLogger(__name__)


class TestQuickValidationComparison(unittest.TestCase):
    """Quick comparison focusing on the Cassian problem"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        # Load Sariel campaign prompts
        prompts_path = os.path.join(
            os.path.dirname(__file__), "data", "sariel_campaign_prompts.json"
        )
        with open(prompts_path) as f:
            cls.sariel_data = json.load(f)

    def test_cassian_problem_comparison(self):
        """Test just the Cassian problem with both validation approaches"""
        logger.info("=== Testing Cassian Problem Resolution ===")

        results = {
            "test_date": datetime.now().isoformat(),
            "simple_cassian_tests": [],
            "pydantic_cassian_tests": [],
        }

        # Test 5 times with Simple validation
        logger.info("\n=== Testing with Simple Validation (5 runs) ===")
        for i in range(5):
            logger.info(f"\nSimple Run {i + 1}/5")
            os.environ["USE_PYDANTIC"] = "false"
            cassian_mentioned = self._test_cassian_problem(f"simple_{i}")
            results["simple_cassian_tests"].append(
                {"run": i + 1, "cassian_mentioned": cassian_mentioned}
            )
            logger.info(
                f"Result: Cassian {'✓ mentioned' if cassian_mentioned else '✗ missing'}"
            )
            time.sleep(1)

        # Test 5 times with Pydantic validation
        logger.info("\n=== Testing with Pydantic Validation (5 runs) ===")
        for i in range(5):
            logger.info(f"\nPydantic Run {i + 1}/5")
            os.environ["USE_PYDANTIC"] = "true"
            cassian_mentioned = self._test_cassian_problem(f"pydantic_{i}")
            results["pydantic_cassian_tests"].append(
                {"run": i + 1, "cassian_mentioned": cassian_mentioned}
            )
            logger.info(
                f"Result: Cassian {'✓ mentioned' if cassian_mentioned else '✗ missing'}"
            )
            time.sleep(1)

        # Save and display results
        self._save_results(results)
        self._display_summary(results)

    def _test_cassian_problem(self, run_id: str) -> bool:
        """Test just the Cassian problem interaction"""
        try:
            # Create campaign
            user_id = f"test-cassian-{run_id}"
            initial_prompt = self.sariel_data["prompts"][0]

            campaign_data = {
                "prompt": initial_prompt["input"],
                "title": f"Cassian Test {run_id}",
                "selected_prompts": ["narrative", "mechanics"],
            }

            response = self.client.post(
                "/api/campaigns",
                headers=IntegrationTestSetup.create_test_headers(user_id),
                data=json.dumps(campaign_data),
                content_type="application/json",
            )

            if response.status_code != 201:
                logger.error(f"Campaign creation failed: {response.status_code}")
                return False

            campaign_id = response.get_json()["campaign_id"]

            # Skip first interaction, go straight to Cassian problem
            cassian_prompt = self.sariel_data["prompts"][
                2
            ]  # "ask for forgiveness. tell cassian..."

            interaction_data = {"input": cassian_prompt["input"], "mode": "character"}

            response = self.client.post(
                f"/api/campaigns/{campaign_id}/interaction",
                headers=IntegrationTestSetup.create_test_headers(user_id),
                data=json.dumps(interaction_data),
                content_type="application/json",
            )

            if response.status_code == 200:
                narrative = response.get_json().get("narrative", "").lower()
                return "cassian" in narrative
            logger.error(f"Interaction failed: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error in test: {e}")
            return False

    def _save_results(self, results: dict):
        """Save results to file"""
        # Use temporary directory for test outputs


        temp_dir = tempfile.mkdtemp(prefix="cassian_test_")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(temp_dir, f"cassian_test_{timestamp}.json")

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nResults saved to: {filepath}")

    def _display_summary(self, results: dict):
        """Display summary of Cassian problem results"""
        logger.info("\n" + "=" * 60)
        logger.info("CASSIAN PROBLEM TEST RESULTS")
        logger.info("=" * 60)

        # Simple validation
        simple_success = sum(
            1 for r in results["simple_cassian_tests"] if r["cassian_mentioned"]
        )
        logger.info(f"\nSimple Validation: {simple_success}/5 ({simple_success * 20}%)")

        # Pydantic validation
        pydantic_success = sum(
            1 for r in results["pydantic_cassian_tests"] if r["cassian_mentioned"]
        )
        logger.info(
            f"Pydantic Validation: {pydantic_success}/5 ({pydantic_success * 20}%)"
        )

        # Analysis
        logger.info("\nAnalysis:")
        if simple_success == 0 and pydantic_success == 0:
            logger.info(
                "❌ The Cassian Problem remains unsolved with current implementation"
            )
            logger.info("   Entity tracking modules are not fully integrated")
        elif simple_success > pydantic_success:
            logger.info(
                f"✓ Simple validation performed better ({simple_success * 20}% vs {pydantic_success * 20}%)"
            )
        elif pydantic_success > simple_success:
            logger.info(
                f"✓ Pydantic validation performed better ({pydantic_success * 20}% vs {simple_success * 20}%)"
            )
        else:
            logger.info(f"= Both approaches performed equally ({simple_success * 20}%)")

        logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    unittest.main()
