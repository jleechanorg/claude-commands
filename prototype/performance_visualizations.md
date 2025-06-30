# Performance Visualizations

## Performance Scaling Graph (ASCII)

```
Time (seconds)
0.20 |                                               H
     |                                          H---'
0.15 |                                     H---'
     |                                H---'
0.10 |   L---------L---------L---------L---------L
     |                                     F---'
0.05 |                          F----'
     |                  F---'         T---'
     |          T---'  |     S---'
0.00 | S---'----+--------+--------+--------+--------+
     0        100      500     1000    2000     5000
                    Text Length (characters)

Legend: S=SimpleToken, T=Token, F=Fuzzy, L=LLM, H=Hybrid
```

## Accuracy Comparison Bar Chart

```
F1 Score
1.0 | ████ ████ ████
    | ████ ████ ████
0.8 | ████ ████ ████
    | ████ ████ ████
0.6 | ████ ████ ████
    | ████ ████ ████
0.4 | ████ ████ ████ ████
    | ████ ████ ████ ████
0.2 | ████ ████ ████ ████
    | ████ ████ ████ ████
0.0 +-----+-----+-----+-----+-----+
    Simple Token Fuzzy  LLM  Hybrid
    0.444  0.833 1.000 1.000 1.000
```

## Edge Case Success Rate

```
Success Rate (%)
100 | ░░░░░░░░░░░░░░░░░░
 90 | ░░░░░░░░░░░░░░░░░░ ████
 80 | ░░░░░░░░░░░░░░░░░░ ████ ████      ████
 70 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 60 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 50 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 40 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 30 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 20 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
 10 | ░░░░░░░░░░░░░░░░░░ ████ ████ ████ ████
  0 +-------+-------+-------+-------+-------+
    Simple  Token   Fuzzy    LLM   Hybrid
     70%     80%     90%     80%    90%
```

## Cost vs Accuracy Trade-off

```
Accuracy (F1)
1.0 |                    ● Fuzzy
    |                    ● LLM     ● Hybrid
0.9 |
    |
0.8 |         ● Token
    |
0.7 |
    |
0.6 |
    |
0.5 | ● Simple
    |
0.4 +----+----+----+----+----+----+----+----+
    0   0.02  0.04  0.06  0.08  0.10  0.12
                Cost per validation ($)

Note: Simple/Token/Fuzzy have negligible per-use cost
      LLM has ~$0.001 API cost per validation
```

## Memory Usage Profile

```
Memory (MB)
10 |                    ████ Hybrid
 9 |                    ████
 8 |               ████ ████ LLM  
 7 |               ████ ████
 6 |          ████ ████ ████ Fuzzy
 5 |          ████ ████ ████
 4 |     ████ ████ ████ ████ Token
 3 |     ████ ████ ████ ████
 2 | ████ ████ ████ ████ ████ Simple
 1 | ████ ████ ████ ████ ████
 0 +-----+-----+-----+-----+-----+
   Idle  Init  100ch 1000ch 5000ch
```

## Validator Selection Decision Tree

```
                    Start
                      |
        Is real-time critical?
        /                    \
      Yes                     No
       |                       |
  Text > 1000 chars?      Need > 95% accuracy?
    /          \            /              \
   Yes          No        Yes               No
    |            |         |                 |
SimpleToken  TokenVal  HybridVal        FuzzyVal
(+ cache)                           (best balance)

Additional Considerations:
- API available? → Consider LLM fallback
- High variation text? → Prefer Fuzzy
- Cost sensitive? → Avoid LLM
```

## Performance Summary Matrix

```
┌─────────────┬────────┬──────────┬─────────┬───────┐
│ Validator   │ Speed  │ Accuracy │ Cost    │ Best  │
│             │ (rank) │ (F1)     │ ($/1K)  │ For   │
├─────────────┼────────┼──────────┼─────────┼───────┤
│ SimpleToken │ 1st    │ 0.444    │ ~0      │ Speed │
│ Token       │ 2nd    │ 0.833    │ ~0      │ Basic │
│ Fuzzy       │ 3rd    │ 1.000    │ ~0      │ Most  │
│ LLM         │ 4th    │ 1.000    │ $1      │ Hard  │
│ Hybrid      │ 5th    │ 1.000    │ $1      │ Max   │
└─────────────┴────────┴──────────┴─────────┴───────┘
```

## Failure Pattern Distribution

```
Failure Types by Validator
                Simple Token Fuzzy LLM Hybrid
Pronouns         ████   ████  ░░░  ░░░  ▒▒▒
Partials         ████   ████  ░░░  ░░░  ░░░
Descriptors      ████   ░░░   ░░░  ░░░  ░░░
Ambiguous        ▒▒▒    ▒▒▒   ▒▒▒  ▒▒▒  ▒▒▒
Actions          ████   ████  ████ ████ ▒▒▒
Negation         ████   ████  ▒▒▒  ░░░  ░░░

████ = High failure rate
▒▒▒  = Medium failure rate  
░░░  = Low/No failures
```