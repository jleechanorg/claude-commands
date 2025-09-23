# Command Frequency Research Methodology

## CRITICAL FINDING: Original Analysis Methodology Error

**Date**: 2025-09-22
**Issue**: Systematic undercount of `/reviewdeep` and `/cons` commands despite extensive usage
**Impact**: Invalidated 87%+ accuracy claims and command hierarchy

### Original Methodology Failure

**What Went Wrong**:
- Individual agent processing captured `/reviewdeep` (1,241 mentions) and `/cons` (971 mentions)
- Statistical aggregation phase failed to weight these commands properly
- Final hierarchy excluded two major command patterns
- Claims of 87%+ accuracy were based on incomplete command modeling

**Evidence of Usage**:
```bash
grep -r "reviewdeep" docs/genesis/processing/ | wc -l  # Result: 1,241
grep -r "/cons" docs/genesis/processing/ | wc -l      # Result: 971
```

## Corrected Research Instructions

### PHASE 1: Complete Command Extraction

**Objective**: Extract ALL slash commands from 9,936 authentic prompts with accurate frequency counts

**Method**: Deploy 10 parallel subagents to systematically analyze raw conversation data

**Subagent Task Distribution**:
- **Agent 1-10**: Each processes ~994 prompts (chunks 1-10)
- **Focus**: Count ALL slash command occurrences, not just statistical patterns
- **Output**: Raw frequency counts for each command type

### PHASE 2: Command Classification

**Primary Commands** (>5% usage):
- Commands that appear in >500 conversations
- Direct user-initiated workflow triggers
- Independent decision points

**Secondary Commands** (1-5% usage):
- Moderate frequency usage patterns
- Context-dependent triggers
- Workflow continuation commands

**Support Commands** (<1% usage):
- Rare or specialized usage
- Fallback mechanisms
- Experimental commands

### PHASE 3: Statistical Validation

**Requirements**:
- Cross-validate counts across multiple agents
- Verify statistical significance of command distributions
- Calculate confidence intervals for usage percentages
- Identify command co-occurrence patterns

### PHASE 4: Behavioral Pattern Analysis

**For Each Command**:
- Extract authentic usage examples (minimum 20 per command)
- Identify contextual triggers and decision patterns
- Map command flow sequences and dependencies
- Document temporal and situational usage patterns

## Expected Command Categories

Based on preliminary findings, expected major commands:

### Confirmed High-Usage Commands
- **`/execute`**: Direct implementation (high frequency expected)
- **`/reviewdeep`**: Comprehensive analysis (1,241 mentions = ~12.5%)
- **`/cons`**: Multi-consultant analysis (971 mentions = ~9.8%)
- **`/tdd`**: Test-driven development (significant usage expected)
- **`/redgreen`**: Debugging workflows (moderate usage expected)
- **`/copilot`**: Single-agent analysis (support role expected)

### Other Commands to Investigate
- **`/arch`**: Architecture review
- **`/pr`**: Pull request operations
- **`/orch`**: Orchestration (previously excluded)
- **`/think`**: Strategic thinking
- **`/debug`**: Debugging analysis

## Quality Control Requirements

### Data Integrity Checks
1. **Total Count Validation**: Sum of all command frequencies should align with total prompt count
2. **Command Format Validation**: Ensure proper slash command syntax recognition
3. **Context Validation**: Verify commands appear in authentic user prompts (not system responses)
4. **Duplicate Detection**: Prevent double-counting of commands in multi-command prompts

### Statistical Rigor
1. **Sample Size Adequacy**: Minimum 100 examples per major command for statistical significance
2. **Distribution Analysis**: Chi-square tests for command frequency distributions
3. **Confidence Intervals**: 95% confidence intervals for all usage percentages
4. **Temporal Stability**: Verify command usage patterns are consistent across conversation timeline

## Success Criteria

### Quantitative Targets
- **Command Coverage**: Identify and model 95%+ of all slash command usage
- **Frequency Accuracy**: ±2% accuracy for major command frequency percentages
- **Pattern Completeness**: Minimum 20 authentic examples per command type
- **Statistical Significance**: p<0.05 for all claimed command preferences

### Qualitative Requirements
- **Authentic Examples**: All command patterns based on real user prompts
- **Contextual Understanding**: Clear triggers and decision patterns for each command
- **Workflow Integration**: Understanding of command sequences and dependencies
- **Behavioral Modeling**: Accurate representation of user decision-making patterns

## Implementation Plan

### Step 1: Data Preparation
- Verify access to all 482 processing files in `docs/genesis/processing/`
- Create standardized extraction templates for subagents
- Establish data validation protocols and quality checks

### Step 2: Parallel Processing Execution
- Deploy 10 subagents with identical methodology
- Process all conversation data systematically
- Implement progress tracking and intermediate validation

### Step 3: Results Aggregation
- Combine results from all 10 subagents
- Cross-validate counts and resolve discrepancies
- Generate comprehensive command frequency report

### Step 4: System Prompt Update
- Update command hierarchy based on corrected frequencies
- Integrate authentic behavioral patterns for all commands
- Validate 87%+ accuracy claims with complete command modeling

## Risk Mitigation

### Technical Risks
- **Processing Errors**: Implement checkpointing and error recovery
- **Data Quality**: Multiple validation passes and cross-agent verification
- **Scalability**: Parallel processing to handle large dataset efficiently

### Methodology Risks
- **Bias Prevention**: Systematic sampling and standardized extraction protocols
- **Completeness**: Multiple passes to ensure no commands are missed
- **Accuracy**: Statistical validation and confidence interval calculation

This methodology ensures comprehensive, accurate command frequency analysis that captures the authentic behavioral patterns needed for reliable autonomous user mimicry.
