# /experiment (or /abtest) - A/B Testing with Multiple Claude Terminals

Run controlled experiments to test different configurations, rules, or approaches across multiple Claude instances.

## Usage

```
/experiment [experiment-name]
/abtest [experiment-name]
```

## Protocol

### 1. Experiment Setup Phase

#### 1.1 Define Hypothesis
- **Question**: What are we testing? (e.g., "Do stricter rules reduce hallucinations?")
- **Control**: Current/baseline configuration
- **Treatment(s)**: Modified configuration(s) to test
- **Success Metrics**: How will we measure effectiveness?

#### 1.2 Create Experiment Branch
```bash
git checkout -b experiment-[name]
```

#### 1.3 Document Experiment Design
Create `EXPERIMENT_DESIGN.md` with:
- Hypothesis
- Control configuration
- Treatment configuration(s)
- Test tasks/scenarios
- Evaluation criteria
- Expected outcomes

### 2. Configuration Phase

#### 2.1 Create Test Branches
```bash
# Control branch
git checkout -b testing-control-[name]
git push -u origin testing-control-[name]

# Treatment branch(es)
git checkout -b testing-treatment-[name]
git push -u origin testing-treatment-[name]
```

#### 2.2 Set Up Configurations
- **Control**: Copy current CLAUDE.md or relevant config
- **Treatment**: Apply modifications to test
- **Both**: Add identical `TESTING_TASKS.md` with blind instructions

#### 2.3 Create Evaluation Framework
- Scoring rubric
- Measurement criteria
- Output file requirements (e.g., `test_results.md`)

### 3. Execution Phase

#### 3.1 Prepare Test Prompts
Create neutral prompts that don't reveal the experiment:
```
I need help with some development tasks on the worldarchitect.ai project. 
Please checkout the branch `testing-[control/treatment]-[name]` and complete 
the tasks listed in TESTING_TASKS.md. Follow all instructions carefully.
```

#### 3.2 Document Test Sessions
Track:
- Session IDs/timestamps
- Which configuration each Claude uses
- Any deviations from protocol

### 4. Analysis Phase

#### 4.1 Collect Results
```bash
# Check for output files
gh api repos/owner/repo/pulls/[PR#]/files --jq '.[].filename'

# Review actual changes
gh pr view [PR#] --json files,additions,deletions
```

#### 4.2 Objective Evaluation
Create evaluation matrix:
- Task completion rates
- Instruction compliance
- Specific behavior measurements
- Hallucination detection
- Error rates

#### 4.3 Statistical Analysis
- Calculate improvement percentages
- Identify significant differences
- Note unexpected behaviors

### 5. Documentation Phase

#### 5.1 Write Up Results
Create `EXPERIMENT_RESULTS.md`:
- Executive summary
- Detailed findings
- Specific examples
- Recommendations

#### 5.2 Meta-Analysis
Document:
- What worked/didn't work
- Surprising findings
- Limitations of the experiment
- Future experiment ideas

### 6. Implementation Phase

Based on results:
- Keep successful changes
- Discard harmful changes
- Plan follow-up experiments
- Update main configuration

## Example Experiment Structure

```
experiment-[name]/
├── EXPERIMENT_DESIGN.md          # Hypothesis and methodology
├── TESTING_TASKS.md             # Blind task list for Claudes
├── EVALUATION_RUBRIC.md         # Scoring criteria
├── control/
│   └── CLAUDE.md               # Control configuration
├── treatment/
│   └── CLAUDE.md               # Treatment configuration
├── results/
│   ├── control_output.md       # Control group results
│   ├── treatment_output.md     # Treatment group results
│   └── ANALYSIS.md            # Comparative analysis
└── EXPERIMENT_RESULTS.md       # Final conclusions
```

## Best Practices

### 1. Blind Testing
- Don't reveal experiment nature in prompts
- Use neutral task descriptions
- Avoid leading questions

### 2. Clear Metrics
- Define success before starting
- Use objective measurements
- Avoid post-hoc interpretations

### 3. Control Variables
- Keep tasks identical between groups
- Use same prompts (except branch names)
- Test at similar times/conditions

### 4. Honest Analysis
- Report all findings, not just positive
- Note your own biases
- Consider alternative explanations

### 5. Reproducibility
- Document everything
- Save all outputs
- Make it easy to replicate

## Common Experiments

### 1. Rule Effectiveness
Test if specific rules change behavior:
- Hallucination prevention
- Instruction compliance
- Error handling

### 2. Configuration Optimization
Test different organizations:
- Rule ordering
- Section grouping
- Verbosity levels

### 3. Prompt Engineering
Test instruction variations:
- Command structures
- Explanation depth
- Example inclusion

### 4. Capability Testing
Test understanding of abilities:
- Tool usage patterns
- Problem-solving approaches
- Self-limitation recognition

## Evaluation Helpers

### Behavior Checklist
```markdown
- [ ] Followed primary instruction
- [ ] Created required outputs
- [ ] Showed evidence for claims
- [ ] Admitted limitations when appropriate
- [ ] Avoided prohibited behaviors
- [ ] Completed all tasks
```

### Scoring Template
```markdown
| Metric | Control | Treatment | Difference |
|--------|---------|-----------|------------|
| Task Completion | X/Y | X/Y | +/-% |
| Hallucinations | Count | Count | +/-% |
| Instructions Followed | X/Y | X/Y | +/-% |
| Evidence Shown | X/Y | X/Y | +/-% |
```

## Anti-Patterns to Avoid

1. **Confirmation Bias**: Don't design experiments to prove what you want
2. **Moving Goalposts**: Don't change success criteria after seeing results
3. **Cherry-Picking**: Report all results, not just favorable ones
4. **Over-Interpretation**: Don't claim causation from correlation
5. **Fake Metrics**: Don't invent scores without clear criteria

## Meta-Learning

After each experiment:
1. What did we learn about testing AI behavior?
2. How can we improve the experiment process?
3. What biases affected our analysis?
4. What would we do differently?

Remember: The goal is learning, not proving preconceptions right!