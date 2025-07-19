"""
Test harness for consistent evaluation of validators.
Provides a framework for running validators against test narratives
and comparing results with ground truth.
"""

import json
import os
import sys
import time
from collections.abc import Callable
from datetime import datetime

# Add prototype to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ground_truth import calculate_accuracy, ground_truth_labels
from tests.test_narratives import test_narratives


class TestHarness:
    """Test harness for validator evaluation."""

    def __init__(self):
        self.results = {}
        self.validators = {}
        self.timing_data = {}

    def register_validator(self, name: str, validator_func: Callable):
        """Register a validator function for testing."""
        self.validators[name] = validator_func

    def run_single_test(self, validator_name: str, test_narrative: dict) -> dict:
        """Run a single validator on a single test narrative."""
        validator = self.validators[validator_name]

        # Extract test data
        narrative_text = test_narrative["narrative"]
        expected_entities = test_narrative["expected_entities"]
        location = test_narrative["location"]

        # Time the validation
        start_time = time.time()

        try:
            # Run validator
            validation_result = validator(
                narrative_text=narrative_text,
                expected_entities=expected_entities,
                location=location,
            )

            elapsed_time = time.time() - start_time

            # Add timing data
            validation_result["elapsed_time"] = elapsed_time
            validation_result["test_id"] = test_narrative["id"]

            return validation_result

        except Exception as e:
            # Handle validator errors
            elapsed_time = time.time() - start_time
            return {
                "error": str(e),
                "elapsed_time": elapsed_time,
                "test_id": test_narrative["id"],
                "all_entities_present": False,
                "entities_found": [],
                "entities_missing": expected_entities,
            }

    def run_all_tests(self, validator_name: str) -> dict:
        """Run a validator against all test narratives."""
        results = []
        total_time = 0

        for narrative in test_narratives:
            result = self.run_single_test(validator_name, narrative)
            results.append(result)
            total_time += result.get("elapsed_time", 0)

        # Calculate metrics
        predictions = {r["test_id"]: r for r in results}
        accuracy = calculate_accuracy(predictions)

        # Calculate precision/recall
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        for test_id, pred in predictions.items():
            truth = ground_truth_labels[test_id]

            # Compare entity detection
            for entity in pred.get("entities_found", []):
                if entity in truth["entities_found"]:
                    true_positives += 1
                else:
                    false_positives += 1

            for entity in pred.get("entities_missing", []):
                if entity in truth["entities_missing"]:
                    true_negatives += 1
                else:
                    false_negatives += 1

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "validator_name": validator_name,
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(test_narratives),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "total_time": total_time,
            "avg_time_per_test": total_time / len(test_narratives),
            "detailed_results": results,
            "metrics": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "true_negatives": true_negatives,
                "false_negatives": false_negatives,
            },
        }

    def compare_validators(self) -> dict:
        """Run all registered validators and compare results."""
        comparison = {"timestamp": datetime.now().isoformat(), "validators": {}}

        for validator_name in self.validators:
            print(f"Testing {validator_name}...")
            results = self.run_all_tests(validator_name)
            comparison["validators"][validator_name] = {
                "accuracy": results["accuracy"],
                "precision": results["precision"],
                "recall": results["recall"],
                "f1_score": results["f1_score"],
                "avg_time": results["avg_time_per_test"],
            }
            self.results[validator_name] = results

        # Rank validators
        ranked = sorted(
            comparison["validators"].items(),
            key=lambda x: (x[1]["f1_score"], -x[1]["avg_time"]),
            reverse=True,
        )
        comparison["rankings"] = [
            {"rank": i + 1, "validator": name, **metrics}
            for i, (name, metrics) in enumerate(ranked)
        ]

        return comparison

    def generate_report(self, output_file: str = None):
        """Generate a comprehensive test report."""
        report = {
            "test_harness_report": {
                "generated_at": datetime.now().isoformat(),
                "test_narratives_count": len(test_narratives),
                "validators_tested": list(self.validators.keys()),
                "comparison": self.compare_validators(),
                "detailed_results": self.results,
            }
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {output_file}")

        return report

    def run_edge_cases_only(self, validator_name: str) -> dict:
        """Run validator only on identified edge cases."""
        edge_case_ids = [
            "test_005",
            "test_009",
            "test_010",
            "test_011",
            "test_017",
            "test_020",
        ]
        edge_narratives = [n for n in test_narratives if n["id"] in edge_case_ids]

        results = []
        for narrative in edge_narratives:
            result = self.run_single_test(validator_name, narrative)
            results.append(result)

        return {
            "validator_name": validator_name,
            "edge_cases_tested": len(edge_narratives),
            "results": results,
        }


# Example usage
if __name__ == "__main__":
    # Create test harness
    harness = TestHarness()

    # Example dummy validator for testing
    def dummy_validator(narrative_text, expected_entities, location):
        """Dummy validator that always returns empty results."""
        return {
            "all_entities_present": False,
            "entities_found": [],
            "entities_missing": expected_entities,
            "confidence": 0.0,
        }

    # Register and test
    harness.register_validator("dummy", dummy_validator)
    results = harness.run_all_tests("dummy")

    print(f"Dummy validator accuracy: {results['accuracy']:.2%}")
    print(f"Average time per test: {results['avg_time_per_test']:.4f}s")
