#!/usr/bin/env python3
"""
Confusion matrix generator for validation prototype.
Creates detailed error analysis for each validator.
"""

import json
import os
from datetime import datetime
from tests.ground_truth import ground_truth_labels


def generate_confusion_matrix(
    validator_name: str, predictions: dict, ground_truth: dict
) -> dict:
    """Generate confusion matrix for a validator."""

    # Initialize matrix
    # Rows: Actual (Present/Absent)
    # Cols: Predicted (Present/Absent)
    matrix = {
        "validator": validator_name,
        "matrix": {
            "entity_present": {
                "predicted_present": 0,  # True Positive
                "predicted_absent": 0,  # False Negative
            },
            "entity_absent": {
                "predicted_present": 0,  # False Positive
                "predicted_absent": 0,  # True Negative
            },
        },
        "per_entity_analysis": {},
        "error_patterns": [],
    }

    # Analyze each test case
    for test_id, truth in ground_truth.items():
        if test_id not in predictions:
            continue

        pred = predictions[test_id]

        # Analyze each entity
        all_entities = set(
            truth.get("entities_found", []) + truth.get("entities_missing", [])
        )

        for entity in all_entities:
            if entity not in matrix["per_entity_analysis"]:
                matrix["per_entity_analysis"][entity] = {
                    "tp": 0,
                    "fp": 0,
                    "tn": 0,
                    "fn": 0,
                    "error_cases": [],
                }

            entity_stats = matrix["per_entity_analysis"][entity]

            # Determine actual and predicted states
            actual_present = entity in truth.get("entities_found", [])
            predicted_present = entity in pred.get("entities_found", [])

            # Update confusion matrix
            if actual_present and predicted_present:
                matrix["matrix"]["entity_present"]["predicted_present"] += 1
                entity_stats["tp"] += 1
            elif actual_present and not predicted_present:
                matrix["matrix"]["entity_present"]["predicted_absent"] += 1
                entity_stats["fn"] += 1
                entity_stats["error_cases"].append(
                    {
                        "test_id": test_id,
                        "type": "false_negative",
                        "entity": entity,
                        "narrative_snippet": f"Test {test_id} - entity was present but not detected",
                    }
                )
            elif not actual_present and predicted_present:
                matrix["matrix"]["entity_absent"]["predicted_present"] += 1
                entity_stats["fp"] += 1
                entity_stats["error_cases"].append(
                    {
                        "test_id": test_id,
                        "type": "false_positive",
                        "entity": entity,
                        "narrative_snippet": f"Test {test_id} - entity was absent but detected",
                    }
                )
            else:  # not actual_present and not predicted_present
                matrix["matrix"]["entity_absent"]["predicted_absent"] += 1
                entity_stats["tn"] += 1

    # Identify error patterns
    matrix["error_patterns"] = analyze_error_patterns(matrix["per_entity_analysis"])

    # Calculate summary statistics
    tp = matrix["matrix"]["entity_present"]["predicted_present"]
    fn = matrix["matrix"]["entity_present"]["predicted_absent"]
    fp = matrix["matrix"]["entity_absent"]["predicted_present"]
    tn = matrix["matrix"]["entity_absent"]["predicted_absent"]

    total = tp + fn + fp + tn
    accuracy = (tp + tn) / total if total > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

    matrix["statistics"] = {
        "accuracy": round(accuracy, 3),
        "sensitivity": round(sensitivity, 3),
        "specificity": round(specificity, 3),
        "total_predictions": total,
    }

    return matrix


def analyze_error_patterns(per_entity_analysis: dict) -> list[dict]:
    """Analyze patterns in prediction errors."""
    patterns = []

    # Check for entities that are consistently missed
    for entity, stats in per_entity_analysis.items():
        if stats["fn"] > 0 and stats["tp"] == 0:
            patterns.append(
                {
                    "pattern": "always_missed",
                    "entity": entity,
                    "description": f"{entity} is never detected when present",
                    "occurrences": stats["fn"],
                }
            )
        elif stats["fp"] > stats["tp"]:
            patterns.append(
                {
                    "pattern": "over_detected",
                    "entity": entity,
                    "description": f"{entity} is detected more often when absent than present",
                    "false_positives": stats["fp"],
                    "true_positives": stats["tp"],
                }
            )

    return patterns


def create_visual_matrix(matrix_data: dict) -> str:
    """Create a text-based visual representation of the confusion matrix."""
    m = matrix_data["matrix"]

    visual = f"""
Confusion Matrix for {matrix_data["validator"]}
===============================================

                 Predicted
                 Present    Absent
Actual  Present    {m["entity_present"]["predicted_present"]:4d}      {m["entity_present"]["predicted_absent"]:4d}
        Absent     {m["entity_absent"]["predicted_present"]:4d}      {m["entity_absent"]["predicted_absent"]:4d}

Accuracy: {matrix_data["statistics"]["accuracy"]:.1%}
Sensitivity: {matrix_data["statistics"]["sensitivity"]:.1%}
Specificity: {matrix_data["statistics"]["specificity"]:.1%}
"""
    return visual


def generate_all_confusion_matrices():
    """Generate confusion matrices for all validators."""

    # Sample data - would normally come from actual test runs

    # Sample predictions for different validators
    validator_predictions = {
        "SimpleTokenValidator": {
            "test_001": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
            "test_002": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
            "test_003": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
            "test_004": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
            "test_005": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
        },
        "TokenValidator": {
            "test_001": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
            "test_002": {"entities_found": ["Gideon"], "entities_missing": ["Rowan"]},
            "test_003": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
            "test_004": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
            "test_005": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
        },
        "FuzzyTokenValidator": {
            "test_001": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
            "test_002": {"entities_found": ["Gideon"], "entities_missing": ["Rowan"]},
            "test_003": {"entities_found": [], "entities_missing": ["Gideon", "Rowan"]},
            "test_004": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
            "test_005": {"entities_found": ["Gideon", "Rowan"], "entities_missing": []},
        },
    }

    report = {
        "confusion_matrix_report": {
            "timestamp": datetime.now().isoformat(),
            "validators": {},
            "summary": {
                "most_accurate": None,
                "common_error_patterns": [],
                "recommendations": [],
            },
        }
    }

    # Generate matrix for each validator
    for validator_name, predictions in validator_predictions.items():
        matrix = generate_confusion_matrix(
            validator_name, predictions, ground_truth_labels
        )
        report["confusion_matrix_report"]["validators"][validator_name] = matrix

        # Print visual matrix
        print(create_visual_matrix(matrix))

    # Analyze overall patterns
    accuracies = {
        name: data["statistics"]["accuracy"]
        for name, data in report["confusion_matrix_report"]["validators"].items()
    }

    report["confusion_matrix_report"]["summary"]["most_accurate"] = max(
        accuracies.items(), key=lambda x: x[1]
    )[0]

    # Common error patterns
    all_patterns = []
    for validator_data in report["confusion_matrix_report"]["validators"].values():
        all_patterns.extend(validator_data["error_patterns"])

    # Find most common pattern types
    pattern_types = {}
    for pattern in all_patterns:
        ptype = pattern["pattern"]
        if ptype not in pattern_types:
            pattern_types[ptype] = 0
        pattern_types[ptype] += 1

    report["confusion_matrix_report"]["summary"]["common_error_patterns"] = [
        {"pattern": ptype, "frequency": count} for ptype, count in pattern_types.items()
    ]

    # Recommendations
    if "always_missed" in pattern_types:
        report["confusion_matrix_report"]["summary"]["recommendations"].append(
            "Some entities are consistently missed - consider enhancing descriptor matching"
        )
    if "over_detected" in pattern_types:
        report["confusion_matrix_report"]["summary"]["recommendations"].append(
            "False positive rate is high - consider stricter matching criteria"
        )

    return report


if __name__ == "__main__":
    # Generate confusion matrices
    report = generate_all_confusion_matrices()

    # Save report
    os.makedirs("benchmarks", exist_ok=True)

    with open("benchmarks/confusion_matrix_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nReport saved to benchmarks/confusion_matrix_report.json")
