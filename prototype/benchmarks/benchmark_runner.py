"""
Benchmark runner for validation prototype.
Tests validators with configurable parameters and narrative lengths.
"""

import json
import os
import random
import sys
import time
from datetime import datetime
from typing import Any

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now we can import from the prototype package
from prototype.logging_config import metrics_collector, setup_logging
from prototype.tests.test_narratives import test_narratives
from prototype.validators.fuzzy_token_validator import FuzzyTokenValidator
from prototype.validators.hybrid_validator import HybridValidator
from prototype.validators.llm_validator import LLMValidator
from prototype.validators.token_validator import SimpleTokenValidator, TokenValidator


class BenchmarkRunner:
    """Runs performance benchmarks on validators."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.logger = setup_logging("BenchmarkRunner")

    def generate_narrative(self, length: int, entities: list[str]) -> str:
        """Generate a synthetic narrative of specified length."""
        templates = [
            "{entity} walked through the {place}.",
            "The {place} was quiet when {entity} arrived.",
            "{entity} looked around the {place} carefully.",
            "In the {place}, {entity} found what they were looking for.",
            "The sound echoed as {entity} moved through the {place}.",
        ]

        places = ["chamber", "corridor", "hall", "room", "passage", "courtyard"]

        narrative_parts = []
        current_length = 0

        while current_length < length:
            template = random.choice(templates)
            entity = random.choice(entities + ["someone", "a figure", "they"])
            place = random.choice(places)

            sentence = template.format(entity=entity, place=place)
            narrative_parts.append(sentence)
            current_length += len(sentence)

        narrative = " ".join(narrative_parts)

        # Trim to exact length
        if len(narrative) > length:
            narrative = narrative[:length].rsplit(" ", 1)[0] + "."

        return narrative

    def benchmark_validator(
        self, validator, test_cases: list[dict], name: str
    ) -> dict[str, Any]:
        """Benchmark a single validator."""
        self.logger.info(f"Benchmarking {name}...")

        results = {
            "validator": name,
            "timestamp": datetime.now().isoformat(),
            "test_count": len(test_cases),
            "timings": [],
            "errors": 0,
            "narrative_lengths": [],
        }

        for i, test_case in enumerate(test_cases):
            narrative = test_case.get("narrative", "")
            expected = test_case.get("expected_entities", ["Gideon", "Rowan"])

            try:
                start_time = time.time()
                result = validator.validate(narrative, expected)
                duration = time.time() - start_time

                results["timings"].append(duration)
                results["narrative_lengths"].append(len(narrative))

            except Exception as e:
                self.logger.error(f"Error in test {i}: {e}")
                results["errors"] += 1
                results["timings"].append(0)
                results["narrative_lengths"].append(len(narrative))

        # Calculate statistics
        valid_timings = [t for t in results["timings"] if t > 0]
        if valid_timings:
            results["stats"] = {
                "min_time": min(valid_timings),
                "max_time": max(valid_timings),
                "avg_time": sum(valid_timings) / len(valid_timings),
                "total_time": sum(valid_timings),
                "success_rate": len(valid_timings) / len(test_cases),
            }
        else:
            results["stats"] = {
                "min_time": 0,
                "max_time": 0,
                "avg_time": 0,
                "total_time": 0,
                "success_rate": 0,
            }

        return results

    def run_length_benchmarks(self, lengths: list[int] = None) -> dict[str, Any]:
        """Benchmark validators with different narrative lengths."""
        if lengths is None:
            lengths = [100, 500, 1000, 2000, 5000]

        validators = {
            "SimpleTokenValidator": SimpleTokenValidator(),
            "TokenValidator": TokenValidator(),
            "FuzzyTokenValidator": FuzzyTokenValidator(),
            "LLMValidator": LLMValidator(),  # Will use mock
            "HybridValidator": HybridValidator(),
        }

        results = {
            "benchmark_type": "narrative_length",
            "timestamp": datetime.now().isoformat(),
            "lengths": lengths,
            "results": {},
        }

        for length in lengths:
            self.logger.info(f"\nBenchmarking with {length} character narratives...")

            # Generate test cases
            test_cases = []
            for i in range(10):  # 10 tests per length
                narrative = self.generate_narrative(
                    length, ["Gideon", "Rowan", "Marcus", "Elena"]
                )
                test_cases.append(
                    {
                        "narrative": narrative,
                        "expected_entities": ["Gideon", "Rowan"],
                        "id": f"synthetic_{length}_{i}",
                    }
                )

            # Benchmark each validator
            length_results = {}
            for name, validator in validators.items():
                bench_result = self.benchmark_validator(validator, test_cases, name)
                length_results[name] = bench_result["stats"]["avg_time"]

            results["results"][str(length)] = length_results

        return results

    def run_comprehensive_benchmark(self) -> dict[str, Any]:
        """Run comprehensive benchmarks on all validators."""
        validators = {
            "SimpleTokenValidator": SimpleTokenValidator(),
            "TokenValidator": TokenValidator(),
            "FuzzyTokenValidator": FuzzyTokenValidator(fuzzy_threshold=0.8),
            "LLMValidator": LLMValidator(),  # Will use mock
            "HybridValidator_weighted": HybridValidator(
                combination_strategy="weighted_vote"
            ),
            "HybridValidator_majority": HybridValidator(
                combination_strategy="majority"
            ),
            "HybridValidator_unanimous": HybridValidator(
                combination_strategy="unanimous"
            ),
        }

        results = {
            "benchmark_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
            "validators": list(validators.keys()),
            "test_narratives_used": len(test_narratives),
            "individual_results": {},
        }

        # Use test narratives
        for name, validator in validators.items():
            bench_result = self.benchmark_validator(validator, test_narratives, name)
            results["individual_results"][name] = bench_result

        # Generate comparison
        results["comparison"] = self._generate_comparison(results["individual_results"])

        return results

    def _generate_comparison(self, individual_results: dict) -> dict[str, Any]:
        """Generate performance comparison."""
        comparison = {
            "fastest": None,
            "slowest": None,
            "most_reliable": None,
            "rankings": [],
        }

        # Extract average times and success rates
        validator_stats = []
        for name, result in individual_results.items():
            stats = result.get("stats", {})
            validator_stats.append(
                {
                    "name": name,
                    "avg_time": stats.get("avg_time", float("inf")),
                    "success_rate": stats.get("success_rate", 0),
                }
            )

        # Sort by average time
        validator_stats.sort(key=lambda x: x["avg_time"])

        if validator_stats:
            comparison["fastest"] = validator_stats[0]["name"]
            comparison["slowest"] = validator_stats[-1]["name"]

            # Find most reliable
            validator_stats.sort(key=lambda x: x["success_rate"], reverse=True)
            comparison["most_reliable"] = validator_stats[0]["name"]

            # Overall rankings (balance of speed and reliability)
            for v in validator_stats:
                # Simple scoring: lower time is better, higher success rate is better
                # Normalize to 0-1 range
                time_score = 1 - (v["avg_time"] / validator_stats[-1]["avg_time"])
                reliability_score = v["success_rate"]
                overall_score = (time_score + reliability_score) / 2

                v["overall_score"] = overall_score

            validator_stats.sort(key=lambda x: x["overall_score"], reverse=True)
            comparison["rankings"] = validator_stats

        return comparison

    def save_results(self, results: dict[str, Any], filename: str):
        """Save benchmark results to file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        self.logger.info(f"Results saved to {filepath}")

    def run_all_benchmarks(self):
        """Run all benchmark suites."""
        self.logger.info("Starting comprehensive benchmark suite...")

        # Run different benchmark types
        comprehensive = self.run_comprehensive_benchmark()
        self.save_results(comprehensive, "comprehensive_benchmark.json")

        length_bench = self.run_length_benchmarks()
        self.save_results(length_bench, "length_benchmark.json")

        # Save metrics
        metrics = metrics_collector.get_metrics()
        self.save_results(metrics, "metrics_summary.json")

        self.logger.info("All benchmarks completed!")

        return {
            "comprehensive": comprehensive,
            "length_based": length_bench,
            "metrics": metrics,
        }


if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_all_benchmarks()
