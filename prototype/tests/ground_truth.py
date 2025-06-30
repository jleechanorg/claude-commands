"""
Ground truth labels for test narrative validation.
Defines expected validation results for each test narrative.
"""

from typing import Dict, List, Any

ground_truth_labels = {
    "test_001": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 1.0,
        "notes": "Both entities explicitly named"
    },
    
    "test_002": {
        "all_entities_present": False,
        "entities_found": ["Gideon"],  # "knight" should map to Gideon
        "entities_missing": ["Rowan"],
        "confidence": 0.5,
        "notes": "Only knight/Gideon present, Rowan missing"
    },
    
    "test_003": {
        "all_entities_present": False,
        "entities_found": [],
        "entities_missing": ["Gideon", "Rowan"],
        "confidence": 0.0,
        "notes": "Empty chamber, no entities present"
    },
    
    "test_004": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],  # Via "Ser Vance" and "healer"
        "entities_missing": [],
        "confidence": 0.9,
        "notes": "Entities referenced by title/role"
    },
    
    "test_005": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],  # Via pronouns + context
        "entities_missing": [],
        "confidence": 0.7,
        "notes": "Pronoun references require context"
    },
    
    "test_006": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "entity_states": {"Rowan": ["hidden"]},
        "confidence": 1.0,
        "notes": "Both present, Rowan hidden"
    },
    
    "test_007": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "entity_states": {"Rowan": ["unconscious"]},
        "confidence": 1.0,
        "notes": "Both present, Rowan unconscious"
    },
    
    "test_008": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 1.0,
        "combat_active": True,
        "notes": "Combat scenario with both entities"
    },
    
    "test_009": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 0.8,
        "notes": "Partial names but recognizable"
    },
    
    "test_010": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 0.8,
        "notes": "Descriptive references mapping needed"
    },
    
    "test_011": {
        "all_entities_present": False,
        "entities_found": [],
        "entities_missing": ["Gideon", "Rowan"],
        "confidence": 0.3,
        "notes": "Generic party reference insufficient"
    },
    
    "test_012": {
        "all_entities_present": False,
        "entities_found": [],
        "entities_missing": ["Gideon", "Rowan"],
        "confidence": 1.0,
        "notes": "Wrong character names (Marcus, Elena)"
    },
    
    "test_013": {
        "all_entities_present": False,
        "entities_found": ["Gideon"],
        "entities_missing": ["Rowan"],
        "confidence": 0.9,
        "notes": "Past tense with only Gideon present"
    },
    
    "test_014": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 1.0,
        "notes": "Clear dialogue attributions"
    },
    
    "test_015": {
        "all_entities_present": False,
        "entities_found": ["Gideon"],
        "entities_missing": ["Rowan"],
        "confidence": 0.9,
        "notes": "Rowan only in thoughts, not present"
    },
    
    "test_016": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 1.0,
        "notes": "Explicit names with plural reference"
    },
    
    "test_017": {
        "all_entities_present": False,
        "entities_found": [],
        "entities_missing": ["Gideon", "Rowan"],
        "confidence": 0.4,
        "notes": "Actions imply presence but no identification"
    },
    
    "test_018": {
        "all_entities_present": False,
        "entities_found": ["Rowan"],
        "entities_missing": ["Gideon"],
        "confidence": 1.0,
        "notes": "Only Rowan explicitly present"
    },
    
    "test_019": {
        "all_entities_present": True,
        "entities_found": ["Gideon", "Rowan"],
        "entities_missing": [],
        "confidence": 1.0,
        "notes": "Time skip with both named"
    },
    
    "test_020": {
        "all_entities_present": False,
        "entities_found": [],
        "entities_missing": ["Gideon", "Rowan"],
        "confidence": 0.2,
        "notes": "Too ambiguous to confirm presence"
    }
}

# Validation metrics for expected results
validation_metrics = {
    "true_positives": 10,  # Correctly identified present entities
    "true_negatives": 10,  # Correctly identified missing entities  
    "expected_accuracy": 1.0,  # Perfect validator should achieve this
    "acceptable_accuracy": 0.85,  # Minimum acceptable accuracy
    "edge_case_ids": ["test_005", "test_009", "test_010", "test_011", "test_017", "test_020"]
}

def get_ground_truth(test_id: str) -> Dict[str, Any]:
    """Get ground truth for a specific test narrative."""
    return ground_truth_labels.get(test_id, {})

def calculate_accuracy(predictions: Dict[str, Dict]) -> float:
    """Calculate accuracy based on predictions vs ground truth."""
    correct = 0
    total = len(ground_truth_labels)
    
    for test_id, truth in ground_truth_labels.items():
        pred = predictions.get(test_id, {})
        
        # Check if all_entities_present matches
        if pred.get("all_entities_present") == truth["all_entities_present"]:
            # Also check if found/missing entities match
            pred_found = set(pred.get("entities_found", []))
            truth_found = set(truth["entities_found"])
            
            pred_missing = set(pred.get("entities_missing", []))
            truth_missing = set(truth["entities_missing"])
            
            if pred_found == truth_found and pred_missing == truth_missing:
                correct += 1
    
    return correct / total if total > 0 else 0.0