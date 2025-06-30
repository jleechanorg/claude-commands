#!/usr/bin/env python3
"""
Analyze narrative desynchronization patterns in collected samples.

This script processes collected narrative samples to identify:
- Common desync patterns
- Entity types most prone to being missed
- Correlation between game state and desync occurrence
- Statistical analysis of error frequencies
"""

import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple
import re

def load_samples(filepath: str) -> Dict[str, Any]:
    """Load narrative samples from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_desync_patterns(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in narrative desynchronization."""
    patterns = {
        "total_samples": len(samples),
        "desync_count": 0,
        "missing_entity_types": defaultdict(int),
        "scenario_desync_rates": defaultdict(lambda: {"total": 0, "desync": 0}),
        "entity_mention_patterns": defaultdict(int),
        "common_missing_combinations": Counter(),
        "status_correlation": defaultdict(lambda: {"total": 0, "missing": 0})
    }
    
    for sample in samples:
        scenario_name = sample["scenario_name"]
        patterns["scenario_desync_rates"][scenario_name]["total"] += 1
        
        if sample["desync_detected"]:
            patterns["desync_count"] += 1
            patterns["scenario_desync_rates"][scenario_name]["desync"] += 1
            
            # Track missing entities
            for entity in sample["missing_entities"]:
                patterns["missing_entity_types"][entity] += 1
            
            # Track missing entity combinations
            if len(sample["missing_entities"]) > 1:
                combo = tuple(sorted(sample["missing_entities"]))
                patterns["common_missing_combinations"][combo] += 1
            
            # Analyze entity status correlation
            if "scenario_data" in sample:
                game_state = sample["scenario_data"]["game_state"]
                
                # Check party member statuses
                if "party_members" in game_state:
                    for member in game_state["party_members"]:
                        for status in member.get("status", []):
                            patterns["status_correlation"][status]["total"] += 1
                            if member["name"] in sample["missing_entities"]:
                                patterns["status_correlation"][status]["missing"] += 1
    
    # Calculate rates
    patterns["overall_desync_rate"] = (patterns["desync_count"] / patterns["total_samples"]) * 100
    
    for scenario, data in patterns["scenario_desync_rates"].items():
        data["rate"] = (data["desync"] / data["total"]) * 100 if data["total"] > 0 else 0
    
    for status, data in patterns["status_correlation"].items():
        data["missing_rate"] = (data["missing"] / data["total"]) * 100 if data["total"] > 0 else 0
    
    return patterns

def identify_narrative_patterns(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Identify common patterns in narrative text."""
    narrative_patterns = {
        "phrase_patterns": Counter(),
        "entity_reference_styles": defaultdict(list),
        "successful_patterns": [],
        "failed_patterns": []
    }
    
    for sample in samples:
        narrative = sample["narrative"]
        
        # Extract common phrases
        phrases = re.findall(r'\b\w+\s+\w+\s+\w+\b', narrative.lower())
        for phrase in phrases:
            narrative_patterns["phrase_patterns"][phrase] += 1
        
        # Categorize by success/failure
        if sample["desync_detected"]:
            narrative_patterns["failed_patterns"].append({
                "narrative": narrative,
                "missing": sample["missing_entities"],
                "scenario": sample["scenario_name"]
            })
        else:
            narrative_patterns["successful_patterns"].append({
                "narrative": narrative,
                "mentioned": sample["mentioned_entities"],
                "scenario": sample["scenario_name"]
            })
        
        # Track how entities are referenced
        for entity in sample["mentioned_entities"]:
            # Find how the entity was referenced in the narrative
            entity_lower = entity.lower()
            if entity_lower in narrative.lower():
                # Extract context around entity mention
                pattern = rf'(\w+\s+)?{re.escape(entity_lower)}(\s+\w+)?'
                matches = re.findall(pattern, narrative.lower())
                for match in matches:
                    context = ''.join(match).strip()
                    narrative_patterns["entity_reference_styles"][entity].append(context)
    
    return narrative_patterns

def generate_recommendations(patterns: Dict[str, Any], narrative_patterns: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []
    
    # High-level desync rate recommendation
    if patterns["overall_desync_rate"] > 20:
        recommendations.append(
            f"CRITICAL: High overall desync rate ({patterns['overall_desync_rate']:.1f}%). "
            "Immediate implementation of state synchronization protocol recommended."
        )
    
    # Scenario-specific recommendations
    for scenario, data in patterns["scenario_desync_rates"].items():
        if data["rate"] > 30:
            recommendations.append(
                f"Scenario '{scenario}' has {data['rate']:.1f}% failure rate. "
                "Consider specific handling for this scenario type."
            )
    
    # Status-based recommendations
    high_risk_statuses = []
    for status, data in patterns["status_correlation"].items():
        if data["missing_rate"] > 50:
            high_risk_statuses.append(f"{status} ({data['missing_rate']:.1f}%)")
    
    if high_risk_statuses:
        recommendations.append(
            f"High-risk statuses for entity omission: {', '.join(high_risk_statuses)}. "
            "Implement explicit status handling in prompts."
        )
    
    # Entity-specific recommendations
    frequently_missing = [
        entity for entity, count in patterns["missing_entity_types"].items()
        if count > patterns["total_samples"] * 0.1
    ]
    if frequently_missing:
        recommendations.append(
            f"Frequently omitted entities: {', '.join(frequently_missing)}. "
            "Consider explicit entity manifest in prompt."
        )
    
    # Pattern-based recommendations
    if len(narrative_patterns["successful_patterns"]) > 10:
        recommendations.append(
            "Successful narrative patterns identified. "
            "Consider using these as templates for consistent entity inclusion."
        )
    
    return recommendations

def save_analysis_report(patterns: Dict[str, Any], narrative_patterns: Dict[str, Any], 
                        recommendations: List[str], output_dir: str = "analysis"):
    """Save analysis report to file."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"desync_analysis_report_{timestamp}.md")
    
    with open(report_file, 'w') as f:
        f.write("# Narrative Desynchronization Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Samples Analyzed**: {patterns['total_samples']}\n")
        f.write(f"- **Desync Occurrences**: {patterns['desync_count']}\n")
        f.write(f"- **Overall Desync Rate**: {patterns['overall_desync_rate']:.2f}%\n\n")
        
        # Scenario Analysis
        f.write("## Scenario-Specific Analysis\n\n")
        f.write("| Scenario | Total | Desync | Rate |\n")
        f.write("|----------|-------|--------|------|\n")
        for scenario, data in sorted(patterns["scenario_desync_rates"].items()):
            f.write(f"| {scenario} | {data['total']} | {data['desync']} | {data['rate']:.1f}% |\n")
        
        # Entity Analysis
        f.write("\n## Missing Entity Analysis\n\n")
        f.write("### Most Frequently Omitted Entities\n\n")
        for entity, count in sorted(patterns["missing_entity_types"].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / patterns["desync_count"]) * 100 if patterns["desync_count"] > 0 else 0
            f.write(f"- **{entity}**: {count} times ({percentage:.1f}% of desyncs)\n")
        
        # Status Correlation
        f.write("\n### Character Status Correlation\n\n")
        f.write("| Status | Total Occurrences | Times Missing | Missing Rate |\n")
        f.write("|--------|------------------|---------------|-------------|\n")
        for status, data in sorted(patterns["status_correlation"].items(), 
                                  key=lambda x: x[1]["missing_rate"], reverse=True):
            f.write(f"| {status} | {data['total']} | {data['missing']} | {data['missing_rate']:.1f}% |\n")
        
        # Common Patterns
        f.write("\n## Narrative Pattern Analysis\n\n")
        f.write("### Common Missing Combinations\n\n")
        for combo, count in patterns["common_missing_combinations"].most_common(5):
            f.write(f"- {' + '.join(combo)}: {count} occurrences\n")
        
        # Sample Failed Narratives
        f.write("\n### Example Failed Narratives\n\n")
        for i, pattern in enumerate(narrative_patterns["failed_patterns"][:5], 1):
            f.write(f"**Example {i}** (Scenario: {pattern['scenario']})\n")
            f.write(f"- Narrative: \"{pattern['narrative']}\"\n")
            f.write(f"- Missing: {', '.join(pattern['missing'])}\n\n")
        
        # Sample Successful Narratives
        f.write("\n### Example Successful Narratives\n\n")
        for i, pattern in enumerate(narrative_patterns["successful_patterns"][:3], 1):
            f.write(f"**Example {i}** (Scenario: {pattern['scenario']})\n")
            f.write(f"- Narrative: \"{pattern['narrative']}\"\n")
            f.write(f"- Mentioned: {', '.join(pattern['mentioned'])}\n\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        for i, rec in enumerate(recommendations, 1):
            f.write(f"{i}. {rec}\n")
        
        # Technical Details
        f.write("\n## Technical Details for Implementation\n\n")
        f.write("Based on this analysis, the following technical implementations are recommended:\n\n")
        f.write("1. **Entity Manifest Generation**: Create explicit entity lists before narrative generation\n")
        f.write("2. **Status-Aware Prompting**: Include character status in prompt context\n")
        f.write("3. **Validation Layer**: Implement post-generation validation to catch omissions\n")
        f.write("4. **Fallback Mechanism**: Retry generation when entities are missing\n")
    
    print(f"Analysis report saved to: {report_file}")
    
    # Also save raw data for further analysis
    data_file = os.path.join(output_dir, f"desync_analysis_data_{timestamp}.json")
    with open(data_file, 'w') as f:
        json.dump({
            "patterns": patterns,
            "narrative_patterns": {
                "phrase_frequency": dict(narrative_patterns["phrase_patterns"].most_common(20)),
                "successful_count": len(narrative_patterns["successful_patterns"]),
                "failed_count": len(narrative_patterns["failed_patterns"])
            },
            "recommendations": recommendations
        }, f, indent=2, default=str)
    
    print(f"Raw analysis data saved to: {data_file}")

def main():
    """Main execution function."""
    print("Narrative Desynchronization Pattern Analyzer")
    print("=" * 50)
    
    # Find the most recent sample file
    data_dir = "data"
    sample_files = [f for f in os.listdir(data_dir) if f.startswith("narrative_samples_") and f.endswith(".json")]
    
    if not sample_files:
        print("No sample files found. Please run collect_narrative_samples.py first.")
        return
    
    latest_file = sorted(sample_files)[-1]
    filepath = os.path.join(data_dir, latest_file)
    print(f"Analyzing: {filepath}")
    
    # Load samples
    data = load_samples(filepath)
    samples = data["samples"]
    
    print(f"Loaded {len(samples)} samples from {data['metadata']['collection_date']}")
    
    # Analyze patterns
    patterns = analyze_desync_patterns(samples)
    narrative_patterns = identify_narrative_patterns(samples)
    
    # Generate recommendations
    recommendations = generate_recommendations(patterns, narrative_patterns)
    
    # Save report
    save_analysis_report(patterns, narrative_patterns, recommendations)
    
    # Print summary
    print("\nAnalysis Summary:")
    print("-" * 30)
    print(f"Overall desync rate: {patterns['overall_desync_rate']:.2f}%")
    print(f"Scenarios analyzed: {len(patterns['scenario_desync_rates'])}")
    print(f"Unique entities tracked: {len(patterns['missing_entity_types'])}")
    print(f"Recommendations generated: {len(recommendations)}")

if __name__ == "__main__":
    main()