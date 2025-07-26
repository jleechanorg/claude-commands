# Experiment Branch Mapping - COORDINATOR EYES ONLY

## Experiment: Specification vs Behavioral Anti-Hallucination

**Hypothesis**: Specification-based output constraints reduce test execution hallucination rates compared to behavioral warnings.

## Branch Mapping (Randomized)

### Subject A = CONTROL GROUP
- **Branch**: `experiment-config-alpha`
- **Configuration**: Original CLAUDE.md from main branch (behavioral warnings)
- **Features**: "NEVER SIMULATE", "NEVER create fake files", generic anti-hallucination warnings

### Subject B = TREATMENT GROUP
- **Branch**: `experiment-config-beta`
- **Configuration**: New CLAUDE.md with specification-based constraints
- **Features**: Mandatory output formats, structured evidence templates, guided generation

### Evaluator Branch
- **Branch**: `experiment-config-eval`
- **Purpose**: Blind evaluation with standardized rubric

## Random Assignment Proof
```json
{
  "randomization_seed": "0",
  "mapping": {
    "subject_a": "control",
    "subject_b": "treatment"
  }
}
```

## Expected Outcomes
If hypothesis is correct:
- **Subject B** (treatment) should have lower hallucination scores
- **Subject B** should show better evidence quality
- **Subject A** (control) may show overcorrection (false inability claims)

## Test Execution Order
1. Launch Subject A: `experiment-config-alpha`
2. Launch Subject B: `experiment-config-beta`
3. Collect results and anonymize for evaluator
4. Launch evaluator on: `experiment-config-eval`
5. Reveal mapping and analyze results

**IMPORTANT**: Keep this mapping hidden from test subjects and evaluator to maintain blind conditions.
