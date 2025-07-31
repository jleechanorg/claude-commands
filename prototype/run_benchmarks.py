#!/usr/bin/env python3
"""
Simple benchmark runner that tests validators with varying narrative lengths.
Run from the prototype directory.
"""

import json
import os
import time
from datetime import datetime

from validators.fuzzy_token_validator import FuzzyTokenValidator
from validators.llm_validator import LLMValidator
from validators.token_validator import SimpleTokenValidator, TokenValidator


# Test with different narrative lengths
def test_length_performance():
    """Test validator performance with different narrative lengths."""

    # Import validators




    lengths = [100, 500, 1000, 2000, 5000]
    validators = {
        "SimpleToken": SimpleTokenValidator(),
        "Token": TokenValidator(),
        "Fuzzy": FuzzyTokenValidator(),
        "LLM": LLMValidator(),  # Uses mock
    }

    results = {
        "test": "narrative_length_performance",
        "timestamp": datetime.now().isoformat(),
        "results": {},
    }

    print("Testing validator performance with varying narrative lengths...")
    print(f"Lengths: {lengths}")
    print(f"Validators: {list(validators.keys())}")
    print("-" * 60)

    for length in lengths:
        print(f"\nTesting with {length} character narratives:")
        length_results = {}

        # Generate test narrative
        narrative = "Gideon walked through the chamber. " * (length // 35)
        narrative = narrative[:length]

        for name, validator in validators.items():
            try:
                # Time the validation
                start = time.time()
                result = validator.validate(
                    narrative_text=narrative, expected_entities=["Gideon", "Rowan"]
                )
                duration = time.time() - start

                length_results[name] = {
                    "duration": duration,
                    "found": result["entities_found"],
                    "confidence": result["confidence"],
                }

                print(f"  {name}: {duration:.4f}s (found: {result['entities_found']})")

            except Exception as e:
                print(f"  {name}: ERROR - {e}")
                length_results[name] = {"error": str(e)}

        results["results"][str(length)] = length_results

    # Save results
    with open("benchmarks/length_performance.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/length_performance.json")
    return results


if __name__ == "__main__":


    os.makedirs("benchmarks", exist_ok=True)
    test_length_performance()
