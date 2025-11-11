#!/usr/bin/env python3
"""
Apply the comprehensive analysis template to the last 10 user prompts
"""

import glob
import json
import os
import re
from datetime import datetime, timedelta


def get_last_10_prompts():
    """Extract last 10 unique user prompts"""
    search_pattern = os.path.expanduser('~/.claude/projects/*/*.jsonl')
    files = glob.glob(search_pattern)

    user_prompts = []
    two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()

    for file_path in files:
        try:
            with open(file_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'user' and data.get('timestamp', '') > two_weeks_ago:
                            message = data.get('message', {})
                            content = ''

                            if isinstance(message.get('content'), str):
                                content = message['content']
                            elif isinstance(message.get('content'), list):
                                for item in message['content']:
                                    if isinstance(item, dict) and item.get('type') == 'text':
                                        content += item.get('text', '')
                                    elif isinstance(item, str):
                                        content += item

                            if (len(content.strip()) > 10 and
                                not content.strip().startswith(('Caveat:', '<command-name>', '<local-command-stdout>', '**CRITICAL FILE', '🚨 CRITICAL FILE'))):

                                user_prompts.append({
                                    'prompt_text': content.strip(),
                                    'timestamp': data.get('timestamp', ''),
                                    'project': file_path.split('/')[-2] if '/' in file_path else 'unknown',
                                    'branch': data.get('gitBranch', 'unknown'),
                                    'conversation_id': os.path.basename(file_path).replace('.jsonl', ''),
                                    'file_path': file_path
                                })
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue

    # Deduplicate and get last 10
    unique_prompts = []
    seen = set()
    for prompt in sorted(user_prompts, key=lambda x: x['timestamp']):
        content_key = prompt['prompt_text'][:100].strip().lower()
        if content_key not in seen:
            seen.add(content_key)
            unique_prompts.append(prompt)

    return unique_prompts[-10:]


def analyze_prompt(prompt_data, index):
    """Apply comprehensive analysis template to a single prompt"""

    prompt_text = prompt_data['prompt_text']

    # Context Analysis
    has_commands = '/' in prompt_text
    commands_found = re.findall(r'/(\w+)', prompt_text)
    file_references = re.findall(r'[\w./]+\.\w+', prompt_text)
    urgency_signals = any(word in prompt_text.lower() for word in ['urgent', 'critical', 'asap', 'immediately', 'blocking'])

    # Communication Style Analysis
    word_count = len(prompt_text.split())
    is_direct = word_count <= 15 and not any(phrase in prompt_text.lower() for phrase in ['please', 'could you', 'would you'])
    action_verbs = ['fix', 'implement', 'add', 'create', 'update', 'deploy', 'test', 'run', 'make', 'setup']
    has_action_verb = any(verb in prompt_text.lower() for verb in action_verbs)

    # Intent Classification
    intent_indicators = {
        'bug_fix': ['fix', 'error', 'bug', 'issue', 'problem', 'broken'],
        'feature_development': ['implement', 'add', 'create', 'new', 'feature', 'build'],
        'testing': ['test', 'tdd', 'coverage', 'pytest', 'validation'],
        'investigation': ['debug', 'analyze', 'check', 'investigate', 'print', 'show'],
        'workflow': ['run', 'execute', 'process', 'workflow'],
        'information': ['what', 'how', 'why', 'explain', 'show', 'print']
    }

    primary_intent = 'general'
    for intent, keywords in intent_indicators.items():
        if any(keyword in prompt_text.lower() for keyword in keywords):
            primary_intent = intent
            break

    # Cognitive Load Assessment (0-5 scale)
    complexity_score = 0
    if word_count > 20: complexity_score += 1
    if len(commands_found) > 1: complexity_score += 1
    if len(file_references) > 0: complexity_score += 1
    if any(tech in prompt_text.lower() for tech in ['database', 'api', 'security', 'deploy']): complexity_score += 1
    if urgency_signals: complexity_score += 1

    # Generate reasoning analysis
    reasoning_triggers = {
        'test the codex mode': 'Verification of new functionality or mode',
        'generate the 6k entries': 'Data processing and analysis task',
        'print me the last 10': 'Information retrieval and debugging',
        'restore/keep the goals': 'Project state management and continuation'
    }

    why_said = "Task execution or information request"
    for pattern, reason in reasoning_triggers.items():
        if any(word in prompt_text.lower() for word in pattern.split()):
            why_said = reason
            break

    # Command prediction
    command_probabilities = {'/execute': 0.4, '/debug': 0.2, '/analyze': 0.2, '/tdd': 0.1, '/orch': 0.1}

    if primary_intent == 'bug_fix':
        command_probabilities = {'/redgreen': 0.7, '/debug': 0.2, '/execute': 0.1}
    elif primary_intent == 'feature_development':
        command_probabilities = {'/tdd': 0.6, '/execute': 0.3, '/orch': 0.1}
    elif primary_intent == 'testing':
        command_probabilities = {'/test': 0.5, '/tdd': 0.3, '/execute': 0.2}
    elif primary_intent == 'investigation':
        command_probabilities = {'/debug': 0.5, '/analyze': 0.3, '/execute': 0.2}

    # Quality metrics
    authenticity_score = 0.0
    if word_count <= 15: authenticity_score += 0.3
    elif word_count <= 25: authenticity_score += 0.2
    else: authenticity_score += 0.1

    if has_commands: authenticity_score += 0.25
    if file_references: authenticity_score += 0.15
    if has_action_verb: authenticity_score += 0.2
    if is_direct: authenticity_score += 0.1

    analysis = {
        'prompt_id': f'prompt_{index+1:02d}',
        'raw_prompt': prompt_text,
        'timestamp': prompt_data['timestamp'],
        'project_context': prompt_data['project'],

        'context_analysis': {
            'conversation_state': {
                'current_branch': prompt_data['branch'],
                'work_focus': primary_intent,
                'session_context': 'active_development'
            },
            'technical_context': {
                'file_references': file_references,
                'command_history': commands_found,
                'complexity_indicators': ['multi_step'] if complexity_score > 2 else ['simple'],
                'urgency_signals': ['urgent'] if urgency_signals else []
            }
        },

        'cognitive_analysis': {
            'intent_classification': {
                'primary_intent': primary_intent,
                'implicit_expectations': ['efficient_execution', 'accurate_results']
            },
            'cognitive_load': {
                'hp_score': min(complexity_score, 5),
                'complexity_factors': {
                    'information_density': 'high' if word_count > 15 else 'medium',
                    'decision_complexity': 'moderate' if commands_found else 'simple',
                    'technical_depth': 'intermediate' if file_references else 'surface'
                }
            },
            'reasoning_analysis': {
                'why_said': why_said,
                'trigger_event': 'User workflow continuation or information need',
                'expected_outcome': 'Immediate task completion with technical precision',
                'workflow_position': 'mid_development_cycle'
            }
        },

        'behavioral_classification': {
            'communication_style': {
                'directness_level': 'ultra_direct' if is_direct else 'moderate',
                'technical_precision': 'high' if file_references or commands_found else 'medium',
                'emotional_tone': 'focused',
                'command_preference': 'cli' if has_commands else 'mixed'
            },
            'user_persona_indicators': {
                'expertise_level': 'expert',
                'workflow_preference': 'fully_automated' if has_commands else 'semi_automated',
                'quality_standards': 'strict',
                'risk_tolerance': 'conservative'
            }
        },

        'taxonomic_classification': {
            'core_tenet': {
                'category': 'Ultra-Directness' if is_direct else 'Technical Precision',
                'description': f'Demonstrates {word_count}-word directness with specific technical context',
                'evidence': commands_found + file_references
            },
            'theme_classification': {
                'primary_theme': primary_intent.replace('_', ' ').title(),
                'pattern_family': 'workflow_continuation'
            },
            'goal_hierarchy': {
                'immediate_goal': f'Execute {primary_intent} task',
                'session_goal': 'Complete development workflow step',
                'project_goal': 'Maintain development momentum',
                'meta_goal': 'Efficient technical workflow execution'
            }
        },

        'predictive_modeling': {
            'command_probability': command_probabilities,
            'workflow_trajectory': f'{primary_intent} -> validation -> next_task',
            'completion_indicators': ['task_executed', 'results_validated']
        },

        'quality_metrics': {
            'authenticity_score': round(min(authenticity_score, 1.0), 3),
            'information_density': round(len(prompt_text) / word_count, 2),
            'technical_specificity': 0.8 if file_references or commands_found else 0.4,
            'action_orientation': 0.9 if has_action_verb else 0.3
        }
    }

    return analysis


def main():
    """Run template analysis on last 10 prompts"""
    print("Analyzing last 10 user prompts with comprehensive template...")

    prompts = get_last_10_prompts()
    analyses = []

    for i, prompt in enumerate(prompts):
        analysis = analyze_prompt(prompt, i)
        analyses.append(analysis)

    # Save full analysis
    output_file = '/Users/jleechan/projects/worktree_genesis/docs/genesis/last_10_prompt_analyses.json'
    with open(output_file, 'w') as f:
        json.dump(analyses, f, indent=2)

    # Print summary
    print("\n=== COMPREHENSIVE ANALYSIS OF LAST 10 PROMPTS ===\n")

    for i, analysis in enumerate(analyses, 1):
        print(f"**PROMPT {i}**: \"{analysis['raw_prompt'][:60]}...\"")
        print(f"  • **Intent**: {analysis['cognitive_analysis']['intent_classification']['primary_intent']}")
        print(f"  • **Tenet**: {analysis['taxonomic_classification']['core_tenet']['category']}")
        print(f"  • **Cognitive Load**: {analysis['cognitive_analysis']['cognitive_load']['hp_score']}/5")
        print(f"  • **Authenticity**: {analysis['quality_metrics']['authenticity_score']}")
        print(f"  • **Why Said**: {analysis['cognitive_analysis']['reasoning_analysis']['why_said']}")

        # Top predicted command
        top_command = max(analysis['predictive_modeling']['command_probability'].items(), key=lambda x: x[1])
        print(f"  • **Predicted Next**: {top_command[0]} ({top_command[1]:.1%} confidence)")
        print(f"  • **Project**: {analysis['project_context']}")
        print()

    print(f"Full detailed analysis saved to: {output_file}")

    # Summary statistics
    avg_authenticity = sum(a['quality_metrics']['authenticity_score'] for a in analyses) / len(analyses)
    avg_cognitive_load = sum(a['cognitive_analysis']['cognitive_load']['hp_score'] for a in analyses) / len(analyses)

    intents = [a['cognitive_analysis']['intent_classification']['primary_intent'] for a in analyses]
    intent_counts = {intent: intents.count(intent) for intent in set(intents)}

    print("\n=== SUMMARY STATISTICS ===")
    print(f"Average Authenticity Score: {avg_authenticity:.3f}")
    print(f"Average Cognitive Load: {avg_cognitive_load:.1f}/5")
    print(f"Intent Distribution: {intent_counts}")

    return analyses


if __name__ == "__main__":
    analyses = main()
