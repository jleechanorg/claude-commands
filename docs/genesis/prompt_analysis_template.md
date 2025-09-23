# Comprehensive Prompt Analysis Template for Context Engineering (2025)

## Research-Based Framework

This template incorporates 2025 best practices from:
- **Hierarchical Prompting Taxonomy (HPT)**: Cognitive demand assessment
- **Context Engineering Principles**: Dynamic context assembly and pruning
- **Behavioral Classification Schema**: Multi-dimensional user modeling
- **Conversational Data Annotation**: Intent-based taxonomies

## Template Structure

### Prompt Entry Schema

```json
{
  "prompt_id": "unique_identifier",
  "raw_prompt": "exact_user_input",
  "timestamp": "ISO_timestamp",
  "project_context": "project_name",

  "context_analysis": {
    "conversation_state": {
      "previous_actions": ["list_of_recent_actions"],
      "current_branch": "git_branch_name",
      "session_duration": "time_in_session",
      "recent_errors": ["any_error_contexts"],
      "work_focus": "current_development_area"
    },

    "technical_context": {
      "file_references": ["mentioned_files"],
      "technology_stack": ["relevant_technologies"],
      "command_history": ["recent_slash_commands"],
      "complexity_indicators": ["multi-file", "integration", "security"],
      "urgency_signals": ["urgent", "critical", "blocking"]
    },

    "environmental_context": {
      "time_of_day": "work_hour_classification",
      "project_phase": "development_stage",
      "team_context": "solo_or_collaborative",
      "deployment_state": "dev_staging_prod"
    }
  },

  "cognitive_analysis": {
    "intent_classification": {
      "primary_intent": "main_goal_category",
      "secondary_intents": ["supporting_goals"],
      "implicit_expectations": ["unstated_requirements"]
    },

    "cognitive_load": {
      "hp_score": "hierarchical_prompting_score_0_to_5",
      "complexity_factors": {
        "information_density": "low_medium_high",
        "decision_complexity": "simple_moderate_complex",
        "technical_depth": "surface_intermediate_deep"
      }
    },

    "reasoning_analysis": {
      "why_said": "psychological_motivation",
      "trigger_event": "what_prompted_this_request",
      "expected_outcome": "user_expectation",
      "workflow_position": "where_in_development_cycle"
    }
  },

  "behavioral_classification": {
    "communication_style": {
      "directness_level": "ultra_direct_moderate_verbose",
      "technical_precision": "low_medium_high",
      "emotional_tone": "neutral_frustrated_excited_focused",
      "command_preference": "cli_gui_mixed"
    },

    "user_persona_indicators": {
      "expertise_level": "novice_intermediate_expert",
      "workflow_preference": "manual_semi_automated_fully_automated",
      "quality_standards": "permissive_standard_strict",
      "risk_tolerance": "conservative_balanced_aggressive"
    }
  },

  "taxonomic_classification": {
    "core_tenet": {
      "category": "selected_from_taxonomy",
      "description": "why_this_tenet_applies",
      "evidence": ["supporting_indicators"]
    },

    "theme_classification": {
      "primary_theme": "main_thematic_category",
      "sub_themes": ["related_themes"],
      "pattern_family": "recurring_behavioral_pattern"
    },

    "goal_hierarchy": {
      "immediate_goal": "specific_task_objective",
      "session_goal": "broader_session_objective",
      "project_goal": "overarching_project_aim",
      "meta_goal": "development_philosophy_goal"
    }
  },

  "predictive_modeling": {
    "next_likely_actions": ["predicted_follow_up_prompts"],
    "command_probability": {
      "/tdd": "probability_score",
      "/redgreen": "probability_score",
      "/orch": "probability_score",
      "/execute": "probability_score"
    },
    "workflow_trajectory": "predicted_workflow_path",
    "completion_indicators": ["signals_task_is_done"]
  },

  "quality_metrics": {
    "authenticity_score": "0_to_1_behavioral_match",
    "information_density": "chars_per_semantic_unit",
    "technical_specificity": "concrete_vs_abstract_ratio",
    "action_orientation": "imperative_vs_descriptive_ratio"
  }
}
```

## Core Tenets Taxonomy (Research-Based)

### Primary Tenets
1. **Ultra-Directness**: Maximum information density, minimal words
2. **Command-First**: Prefer automation over manual processes
3. **Technical Precision**: Specific files, errors, metrics, technologies
4. **Quality-by-Default**: Built-in testing, security, performance expectations
5. **Automation-Preferred**: Orchestration over step-by-step instructions
6. **Evidence-Based**: Verify before acting, measure outcomes
7. **Efficiency-Optimized**: Shortest path to reliable solution

### Theme Categories (HPT-Inspired)
1. **Feature Development**: New capability creation
2. **System Maintenance**: Bug fixes, optimization, refactoring
3. **Quality Assurance**: Testing, validation, security
4. **Workflow Automation**: Process improvement, CI/CD
5. **Investigation**: Debugging, analysis, research
6. **Knowledge Management**: Documentation, learning, memory
7. **Infrastructure**: Setup, configuration, deployment

### Goal Hierarchy Framework
1. **Immediate** (0-15 min): Specific task completion
2. **Session** (15-120 min): Feature/fix completion with validation
3. **Sprint** (1-7 days): Complete feature delivery with testing
4. **Project** (weeks-months): Major capability or system evolution
5. **Meta** (ongoing): Development philosophy and practice evolution

## Example Analysis

### Sample Prompt: "fix auth timeout in mvp_site/core/auth.py"

```json
{
  "prompt_id": "auth_timeout_fix_001",
  "raw_prompt": "fix auth timeout in mvp_site/core/auth.py",
  "timestamp": "2025-09-22T10:15:00Z",
  "project_context": "worldarchitect.ai",

  "context_analysis": {
    "conversation_state": {
      "previous_actions": ["user reported 500 errors", "identified auth module"],
      "current_branch": "hotfix-auth-timeout",
      "session_duration": "15_minutes",
      "recent_errors": ["Authentication timeout after 30s"],
      "work_focus": "production_bug_resolution"
    },

    "technical_context": {
      "file_references": ["mvp_site/core/auth.py"],
      "technology_stack": ["Python", "Flask", "Authentication"],
      "command_history": ["/debug", "/logs"],
      "complexity_indicators": ["security_critical"],
      "urgency_signals": ["production_issue"]
    }
  },

  "cognitive_analysis": {
    "intent_classification": {
      "primary_intent": "bug_resolution",
      "secondary_intents": ["system_stability", "user_experience"],
      "implicit_expectations": ["include_testing", "verify_fix"]
    },

    "cognitive_load": {
      "hp_score": 3,
      "complexity_factors": {
        "information_density": "high",
        "decision_complexity": "moderate",
        "technical_depth": "intermediate"
      }
    },

    "reasoning_analysis": {
      "why_said": "Production issue causing user authentication failures",
      "trigger_event": "User complaints about login timeouts",
      "expected_outcome": "Authentication works reliably within timeout limits",
      "workflow_position": "urgent_production_fix"
    }
  },

  "behavioral_classification": {
    "communication_style": {
      "directness_level": "ultra_direct",
      "technical_precision": "high",
      "emotional_tone": "focused",
      "command_preference": "cli"
    },

    "user_persona_indicators": {
      "expertise_level": "expert",
      "workflow_preference": "fully_automated",
      "quality_standards": "strict",
      "risk_tolerance": "conservative"
    }
  },

  "taxonomic_classification": {
    "core_tenet": {
      "category": "Technical Precision",
      "description": "Provides exact file path and specific issue",
      "evidence": ["mvp_site/core/auth.py", "timeout", "auth"]
    },

    "theme_classification": {
      "primary_theme": "System Maintenance",
      "sub_themes": ["Security", "Performance"],
      "pattern_family": "production_hotfix"
    },

    "goal_hierarchy": {
      "immediate_goal": "Fix authentication timeout bug",
      "session_goal": "Restore stable authentication system",
      "project_goal": "Maintain reliable user experience",
      "meta_goal": "Production system reliability"
    }
  },

  "predictive_modeling": {
    "next_likely_actions": ["/redgreen fix timeout handling", "test auth flow", "deploy hotfix"],
    "command_probability": {
      "/redgreen": 0.85,
      "/tdd": 0.1,
      "/execute": 0.05
    },
    "workflow_trajectory": "fix -> test -> deploy -> monitor",
    "completion_indicators": ["auth tests pass", "timeout eliminated", "user login success"]
  },

  "quality_metrics": {
    "authenticity_score": 0.95,
    "information_density": 0.9,
    "technical_specificity": 0.95,
    "action_orientation": 0.9
  }
}
```

## Usage Guidelines

### For Each Prompt Analysis:
1. **Context First**: Understand the complete situational context
2. **Cognitive Modeling**: Analyze the mental state and reasoning
3. **Multi-Dimensional Classification**: Apply taxonomies systematically
4. **Predictive Elements**: Model likely next actions and outcomes
5. **Quality Validation**: Ensure analysis meets research standards

### Quality Criteria:
- **Completeness**: All schema fields populated with relevant data
- **Consistency**: Classifications align with established taxonomies
- **Predictive Value**: Analysis enables accurate next-prompt generation
- **Behavioral Fidelity**: Captures authentic user patterns and preferences

This template incorporates 2025 research in context engineering, hierarchical prompting taxonomy, and behavioral classification to provide comprehensive analysis suitable for training AI systems to authentically continue user workflows.
