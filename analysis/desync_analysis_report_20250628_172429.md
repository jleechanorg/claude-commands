# Narrative Desynchronization Analysis Report

Generated: 2025-06-28 17:24:29

## Executive Summary

- **Total Samples Analyzed**: 100
- **Desync Occurrences**: 68
- **Overall Desync Rate**: 68.00%

## Scenario-Specific Analysis

| Scenario | Total | Desync | Rate |
|----------|-------|--------|------|
| Combat Scene | 20 | 16 | 80.0% |
| Hidden Party Member | 20 | 10 | 50.0% |
| Location Transition | 20 | 16 | 80.0% |
| Split Party | 20 | 11 | 55.0% |
| Unconscious Party Member | 20 | 15 | 75.0% |

## Missing Entity Analysis

### Most Frequently Omitted Entities

- **Kira**: 68 times (100.0% of desyncs)
- **Rowan**: 41 times (60.3% of desyncs)
- **Gideon**: 24 times (35.3% of desyncs)
- **Bandit Leader**: 16 times (23.5% of desyncs)
- **Bandit Archer**: 16 times (23.5% of desyncs)

### Character Status Correlation

| Status | Total Occurrences | Times Missing | Missing Rate |
|--------|------------------|---------------|-------------|
| unconscious | 15 | 15 | 100.0% |
| scouting | 53 | 53 | 100.0% |
| conscious | 121 | 94 | 77.7% |
| healing | 68 | 41 | 60.3% |
| hidden | 10 | 6 | 60.0% |
| shopping | 11 | 0 | 0.0% |

## Narrative Pattern Analysis

### Common Missing Combinations

- Kira + Rowan: 16 occurrences
- Gideon + Kira + Rowan: 10 occurrences
- Bandit Archer + Bandit Leader + Kira + Rowan: 9 occurrences
- Gideon + Kira: 8 occurrences
- Bandit Archer + Bandit Leader + Gideon + Kira + Rowan: 6 occurrences

### Example Failed Narratives

**Example 1** (Scenario: Unconscious Party Member)
- Narrative: "In the Forest Clearing, Gideon surveys the area."
- Missing: Rowan, Kira

**Example 2** (Scenario: Combat Scene)
- Narrative: "Gideon and Rowan move through the Forest Clearing."
- Missing: Kira, Bandit Leader, Bandit Archer

**Example 3** (Scenario: Location Transition)
- Narrative: "The party gathers in the Forest Path."
- Missing: Gideon, Rowan, Kira

**Example 4** (Scenario: Split Party)
- Narrative: "The party gathers in the Forest Clearing."
- Missing: Gideon, Kira

**Example 5** (Scenario: Hidden Party Member)
- Narrative: "In the Forest Clearing, Gideon surveys the area."
- Missing: Rowan, Kira


### Example Successful Narratives

**Example 1** (Scenario: Hidden Party Member)
- Narrative: "In the Forest Clearing, Gideon stands ready while Rowan stands ready while Kira prepare for what's ahead."
- Mentioned: Gideon, Rowan, Kira

**Example 2** (Scenario: Location Transition)
- Narrative: "In the Forest Path, Gideon stands ready while Rowan stands ready while Kira prepare for what's ahead."
- Mentioned: Gideon, Rowan, Kira

**Example 3** (Scenario: Split Party)
- Narrative: "In the Forest Clearing, Gideon stands ready while Kira prepare for what's ahead."
- Mentioned: Gideon, Kira


## Recommendations

1. CRITICAL: High overall desync rate (68.0%). Immediate implementation of state synchronization protocol recommended.
2. Scenario 'Hidden Party Member' has 50.0% failure rate. Consider specific handling for this scenario type.
3. Scenario 'Unconscious Party Member' has 75.0% failure rate. Consider specific handling for this scenario type.
4. Scenario 'Combat Scene' has 80.0% failure rate. Consider specific handling for this scenario type.
5. Scenario 'Location Transition' has 80.0% failure rate. Consider specific handling for this scenario type.
6. Scenario 'Split Party' has 55.0% failure rate. Consider specific handling for this scenario type.
7. High-risk statuses for entity omission: conscious (77.7%), healing (60.3%), unconscious (100.0%), scouting (100.0%), hidden (60.0%). Implement explicit status handling in prompts.
8. Frequently omitted entities: Rowan, Kira, Bandit Leader, Bandit Archer, Gideon. Consider explicit entity manifest in prompt.
9. Successful narrative patterns identified. Consider using these as templates for consistent entity inclusion.

## Technical Details for Implementation

Based on this analysis, the following technical implementations are recommended:

1. **Entity Manifest Generation**: Create explicit entity lists before narrative generation
2. **Status-Aware Prompting**: Include character status in prompt context
3. **Validation Layer**: Implement post-generation validation to catch omissions
4. **Fallback Mechanism**: Retry generation when entities are missing
