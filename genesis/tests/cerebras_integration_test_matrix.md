# Cerebras Genesis Integration Test Matrix

## Complete Test Matrix Coverage - All Integration Scenarios

### **Matrix 1: Prompt Generation Testing (use_cerebras × simulation_prompt)**
| Function | use_cerebras | simulation_prompt | Expected Prompt Size | Expected Content |
|----------|-------------|-------------------|-------------------|------------------|
| generate_execution_strategy | True | Skipped | < 3000 chars | No user mimicry |
| generate_execution_strategy | False | Loaded | > 30000 chars | Full user mimicry |
| generate_tdd_implementation | True | N/A | < 5000 chars | TDD-focused |

### **Matrix 2: Function Parameter Testing (Cerebras × Codex × Parameters)**
| Function | use_cerebras | use_codex | Expected Tool | Expected Timeout |
|----------|-------------|-----------|---------------|------------------|
| execute_claude_command | True | False | cerebras_direct.sh | 1200s |
| execute_claude_command | False | False | claude CLI | 600s |
| execute_claude_command | False | True | codex CLI | 600s |
| execute_claude_command | True | True | cerebras_direct.sh | 1200s |

### **Matrix 3: Genesis Workflow Stage Testing (4-Stage Enhanced)**
| Iteration | Stage 1 | Stage 2 | Stage 3 | Stage 4 | Expected Flow |
|-----------|---------|---------|---------|---------|---------------|
| 1 | Planning (Cerebras) | TDD Gen (Cerebras) | Test/Fix (Claude) | Validation | Full enhanced flow |
| 1 | Planning (Fallback) | TDD Gen (Failed) | Execution (Claude) | Validation | Fallback to 3-stage |

### **Matrix 4: Error Handling & Fallback Testing**
| Scenario | Cerebras Script | Expected Behavior | Fallback Action |
|----------|----------------|------------------|-----------------|
| Script Missing | Not Found | Log warning | Use Claude CLI |
| API Key Missing | Auth Failure | API Error | Use Claude CLI |
| Large Prompt | > 50KB | Timeout/Error | Chunk or fallback |
| Network Failure | Connection Error | Retry/Fail | Use Claude CLI |

### **Matrix 5: Prompt Size Validation Testing**
| Function | Input Size | Cerebras Mode | Expected Output Size | Performance Target |
|----------|------------|---------------|-------------------|-------------------|
| generate_execution_strategy | Small goal | True | < 3KB | < 1s |
| generate_execution_strategy | Large goal | True | < 5KB | < 2s |
| generate_tdd_implementation | Complex task | True | < 10KB | < 3s |

**Total Matrix Tests**: 45 systematic test cases covering all Cerebras integration scenarios
