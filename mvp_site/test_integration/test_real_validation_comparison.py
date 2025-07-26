#!/usr/bin/env python3
"""
Real comparison of Pydantic vs Simple validation using Sariel campaign data.
Tests entity tracking performance with what's actually integrated.
"""

import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime
from typing import Any

import logging_util

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


class TestRealValidationComparison(unittest.TestCase):
    """Compare Pydantic vs Simple validation with real campaign interactions"""

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

    def test_complete_validation_comparison(self):
        """Run full comparison between Pydantic and Simple validation"""
        logger.info("=== Starting Complete Validation Comparison ===")

        results = {
            "test_date": datetime.now().isoformat(),
            "simple_runs": [],
            "pydantic_runs": [],
        }

        # Run 10 tests with Simple validation
        logger.info("\n=== Running 10 tests with Simple Validation ===")
        for i in range(10):
            logger.info(f"\nSimple Run {i + 1}/10")
            os.environ["USE_PYDANTIC"] = "false"
            run_result = self._run_single_campaign_test(f"simple_run_{i}")
            results["simple_runs"].append(run_result)
            time.sleep(1)  # Brief pause between runs

        # Run 10 tests with Pydantic validation
        logger.info("\n=== Running 10 tests with Pydantic Validation ===")
        for i in range(10):
            logger.info(f"\nPydantic Run {i + 1}/10")
            os.environ["USE_PYDANTIC"] = "true"
            run_result = self._run_single_campaign_test(f"pydantic_run_{i}")
            results["pydantic_runs"].append(run_result)
            time.sleep(1)  # Brief pause between runs

        # Save and display results
        self._save_results(results)
        self._display_summary(results)

    def _run_single_campaign_test(self, run_id: str) -> dict[str, Any]:
        """Run a single campaign test focusing on the Cassian problem"""
        result = {
            "run_id": run_id,
            "validation_type": "pydantic"
            if os.environ.get("USE_PYDANTIC") == "true"
            else "simple",
            "campaign_created": False,
            "interactions": [],
            "cassian_problem_tested": False,
            "cassian_mentioned": False,
            "total_entities_tracked": 0,
            "errors": [],
        }

        try:
            # Create campaign
            user_id = f"test-validation-{run_id}"
            initial_prompt = self.sariel_data["prompts"][0]

            campaign_data = {
                "prompt": initial_prompt["input"],
                "title": f"Validation Test {run_id}",
                "selected_prompts": ["narrative", "mechanics"],
            }

            response = self.client.post(
                "/api/campaigns",
                headers=IntegrationTestSetup.create_test_headers(user_id),
                data=json.dumps(campaign_data),
                content_type="application/json",
            )

            if response.status_code != 201:
                result["errors"].append(
                    f"Campaign creation failed: {response.status_code}"
                )
                return result

            campaign_info = response.get_json()
            campaign_id = campaign_info["campaign_id"]
            result["campaign_created"] = True
            logger.info(f"Created campaign: {campaign_id}")

            # Run first 5 interactions, focusing on the Cassian problem
            for i, prompt_data in enumerate(self.sariel_data["prompts"][1:6]):
                interaction_result = {
                    "prompt_id": prompt_data["prompt_id"],
                    "is_cassian_problem": prompt_data["metadata"].get(
                        "is_cassian_problem", False
                    ),
                    "expected_entities": prompt_data["context"].get(
                        "expected_entities", []
                    ),
                    "entities_found": [],
                    "success": False,
                }

                # Submit interaction using correct parameter name
                interaction_data = {
                    "input": prompt_data["input"],  # Using 'input' not 'prompt'
                    "mode": "character",
                }

                response = self.client.post(
                    f"/api/campaigns/{campaign_id}/interaction",
                    headers=IntegrationTestSetup.create_test_headers(user_id),
                    data=json.dumps(interaction_data),
                    content_type="application/json",
                )

                if response.status_code == 200:
                    interaction_result["success"] = True
                    response_data = response.get_json()
                    narrative = response_data.get("narrative", "").lower()

                    # Check for expected entities
                    for entity in interaction_result["expected_entities"]:
                        if entity.lower() in narrative:
                            interaction_result["entities_found"].append(entity)

                    # Special check for Cassian problem
                    if interaction_result["is_cassian_problem"]:
                        result["cassian_problem_tested"] = True
                        if "cassian" in narrative:
                            result["cassian_mentioned"] = True
                            logger.info("✓ Cassian appeared in response!")
                        else:
                            logger.warning("✗ Cassian missing from response")

                    # Log entity tracking
                    found_count = len(interaction_result["entities_found"])
                    expected_count = len(interaction_result["expected_entities"])
                    logger.info(
                        f"Interaction {i + 1}: {found_count}/{expected_count} entities tracked"
                    )

                else:
                    interaction_result["error"] = (
                        f"Request failed: {response.status_code}"
                    )
                    logger.error(f"Interaction {i + 1} failed: {response.status_code}")

                result["interactions"].append(interaction_result)
                result["total_entities_tracked"] += len(
                    interaction_result["entities_found"]
                )

        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Error in run {run_id}: {e}")

        return result

    def _save_results(self, results: dict[str, Any]):
        """Save results to file"""
        # Use temporary directory for test outputs

        temp_dir = tempfile.mkdtemp(prefix="real_comparison_")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(temp_dir, f"real_comparison_{timestamp}.json")

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nResults saved to: {filepath}")

    def _display_summary(self, results: dict[str, Any]):
        """Display summary of results"""
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION COMPARISON SUMMARY")
        logger.info("=" * 60)

        # Simple validation summary
        simple_runs = results["simple_runs"]
        simple_cassian_solved = sum(1 for r in simple_runs if r["cassian_mentioned"])
        simple_total_entities = sum(r["total_entities_tracked"] for r in simple_runs)
        simple_successful_runs = sum(1 for r in simple_runs if r["campaign_created"])

        logger.info("\nSimple Validation Results:")
        logger.info(f"  Successful runs: {simple_successful_runs}/10")
        logger.info(
            f"  Cassian Problem solved: {simple_cassian_solved}/10 ({simple_cassian_solved * 10}%)"
        )
        logger.info(f"  Total entities tracked: {simple_total_entities}")
        logger.info(f"  Avg entities per run: {simple_total_entities / 10:.1f}")

        # Pydantic validation summary
        pydantic_runs = results["pydantic_runs"]
        pydantic_cassian_solved = sum(
            1 for r in pydantic_runs if r["cassian_mentioned"]
        )
        pydantic_total_entities = sum(
            r["total_entities_tracked"] for r in pydantic_runs
        )
        pydantic_successful_runs = sum(
            1 for r in pydantic_runs if r["campaign_created"]
        )

        logger.info("\nPydantic Validation Results:")
        logger.info(f"  Successful runs: {pydantic_successful_runs}/10")
        logger.info(
            f"  Cassian Problem solved: {pydantic_cassian_solved}/10 ({pydantic_cassian_solved * 10}%)"
        )
        logger.info(f"  Total entities tracked: {pydantic_total_entities}")
        logger.info(f"  Avg entities per run: {pydantic_total_entities / 10:.1f}")

        # Comparison
        logger.info("\nComparison:")
        logger.info(
            f"  Cassian Problem: Simple {simple_cassian_solved * 10}% vs Pydantic {pydantic_cassian_solved * 10}%"
        )
        logger.info(
            f"  Entity Tracking: Simple {simple_total_entities} vs Pydantic {pydantic_total_entities}"
        )

        # Winner
        if simple_cassian_solved > pydantic_cassian_solved:
            logger.info("\n🏆 Winner: Simple Validation")
        elif pydantic_cassian_solved > simple_cassian_solved:
            logger.info("\n🏆 Winner: Pydantic Validation")
        else:
            logger.info("\n🤝 Tie - Both performed equally")

        logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    unittest.main()
