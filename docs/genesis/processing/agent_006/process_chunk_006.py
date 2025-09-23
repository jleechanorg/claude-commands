#!/usr/bin/env python3
"""
Behavioral Analysis Processing for Chunk 006
Processes 994 prompts (4971-5964) with parallel behavioral analysis
Maintains 0.87+ authenticity threshold with automatic saves every 20 prompts
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re
from typing import Dict, List, Any, Tuple

class BehavioralAnalyzer:
    def __init__(self, template_path: str, output_dir: str):
        self.template_path = template_path
        self.output_dir = output_dir
        self.processed_count = 0
        self.results = []
        self.target_authenticity = 0.87

        # Load template
        with open(template_path, 'r') as f:
            self.template = json.load(f)

    def analyze_conversation_state(self, prompt: dict) -> dict:
        """Analyze conversation state from prompt content"""
        content = prompt.get('content', '').lower()

        # Extract previous actions indicators
        previous_actions = []
        if 'git' in content:
            previous_actions.append('git_operations')
        if 'test' in content or 'pytest' in content:
            previous_actions.append('testing')
        if 'file' in content or 'edit' in content:
            previous_actions.append('file_editing')
        if 'curl' in content or 'http' in content:
            previous_actions.append('api_testing')

        # Detect branch context
        current_branch = "unknown"
        if 'main' in content:
            current_branch = "main"
        elif 'dev' in content or 'development' in content:
            current_branch = "development"
        elif 'feature' in content:
            current_branch = "feature_branch"

        # Session duration indicators
        session_duration = "0_minutes"
        if 'again' in content or 'retry' in content:
            session_duration = "5-15_minutes"
        elif 'continue' in content or 'keep' in content:
            session_duration = "15-30_minutes"

        # Recent errors
        recent_errors = []
        if 'error' in content or 'fail' in content:
            recent_errors.append('execution_error')
        if 'timeout' in content or 'tieout' in content:  # Note: typo in original
            recent_errors.append('timeout_error')
        if 'not work' in content or 'broken' in content:
            recent_errors.append('functionality_error')

        # Work focus
        work_focus = "unknown"
        if 'test' in content:
            work_focus = "testing"
        elif 'deploy' in content or 'production' in content:
            work_focus = "deployment"
        elif 'debug' in content or 'fix' in content:
            work_focus = "debugging"
        elif 'implement' in content or 'create' in content:
            work_focus = "development"

        return {
            "previous_actions": previous_actions,
            "current_branch": current_branch,
            "session_duration": session_duration,
            "recent_errors": recent_errors,
            "work_focus": work_focus
        }

    def analyze_technical_context(self, prompt: dict) -> dict:
        """Analyze technical context from prompt content"""
        content = prompt.get('content', '').lower()

        # File references
        file_references = []
        file_patterns = [r'\.py\b', r'\.js\b', r'\.json\b', r'\.md\b', r'\.sh\b', r'\.yml\b', r'\.yaml\b']
        for pattern in file_patterns:
            if re.search(pattern, content):
                file_references.append(pattern.strip('.\\b'))

        # Technology stack
        technology_stack = []
        tech_indicators = {
            'python': ['python', 'pytest', 'pip', 'django', 'flask'],
            'javascript': ['javascript', 'node', 'npm', 'react', 'vue'],
            'web': ['http', 'curl', 'api', 'rest', 'json'],
            'git': ['git', 'github', 'commit', 'push', 'pull'],
            'docker': ['docker', 'container', 'dockerfile'],
            'cloud': ['aws', 'gcp', 'azure', 'cloud', 'deploy']
        }

        for tech, keywords in tech_indicators.items():
            if any(keyword in content for keyword in keywords):
                technology_stack.append(tech)

        # Command history indicators
        command_history = []
        if 'curl' in content:
            command_history.append('curl_request')
        if 'git' in content:
            command_history.append('git_command')
        if 'python' in content or 'py' in content:
            command_history.append('python_execution')
        if 'test' in content:
            command_history.append('test_command')

        # Complexity indicators
        complexity_indicators = []
        if len(content) > 200:
            complexity_indicators.append('long_request')
        if content.count('{') > 2:
            complexity_indicators.append('json_structure')
        if content.count('\n') > 5:
            complexity_indicators.append('multi_line')
        if 'localhost' in content and 'port' in content:
            complexity_indicators.append('local_service')

        # Urgency signals
        urgency_signals = []
        urgent_words = ['urgent', 'asap', 'quick', 'fast', 'immediately', 'now', 'timeout']
        if any(word in content for word in urgent_words):
            urgency_signals.append('time_pressure')
        if 'error' in content or 'fail' in content:
            urgency_signals.append('error_resolution')
        if 'again' in content or 'retry' in content:
            urgency_signals.append('repeated_attempt')

        return {
            "file_references": file_references,
            "technology_stack": technology_stack,
            "command_history": command_history,
            "complexity_indicators": complexity_indicators,
            "urgency_signals": urgency_signals
        }

    def analyze_behavioral_patterns(self, prompt: dict) -> dict:
        """Analyze behavioral patterns from prompt content"""
        content = prompt.get('content', '').lower()

        # Interaction style
        interaction_style = "unknown"
        if len(content) < 20:
            interaction_style = "terse"
        elif len(content) < 100:
            interaction_style = "concise"
        elif len(content) > 200:
            interaction_style = "detailed"
        else:
            interaction_style = "standard"

        # Communication patterns
        communication_patterns = []
        if '?' in content:
            communication_patterns.append('questioning')
        if 'please' in content or 'could you' in content:
            communication_patterns.append('polite_request')
        if content.startswith('test') or content.startswith('try'):
            communication_patterns.append('directive')
        if 'help' in content or 'how' in content:
            communication_patterns.append('seeking_guidance')

        # Problem solving approach
        problem_solving_approach = "unknown"
        if 'test' in content and 'curl' in content:
            problem_solving_approach = "systematic_testing"
        elif 'try' in content and 'again' in content:
            problem_solving_approach = "iterative_refinement"
        elif 'debug' in content or 'fix' in content:
            problem_solving_approach = "diagnostic"
        elif 'implement' in content or 'create' in content:
            problem_solving_approach = "constructive"

        # Learning indicators
        learning_indicators = []
        if 'how' in content or 'what' in content:
            learning_indicators.append('information_seeking')
        if 'example' in content or 'show' in content:
            learning_indicators.append('example_driven')
        if 'why' in content or 'because' in content:
            learning_indicators.append('understanding_oriented')

        # Feedback preferences
        feedback_preferences = []
        if 'verbose' in content or 'detailed' in content:
            feedback_preferences.append('detailed_response')
        elif 'quick' in content or 'simple' in content:
            feedback_preferences.append('concise_response')

        return {
            "interaction_style": interaction_style,
            "communication_patterns": communication_patterns,
            "problem_solving_approach": problem_solving_approach,
            "learning_indicators": learning_indicators,
            "feedback_preferences": feedback_preferences
        }

    def analyze_intent_classification(self, prompt: dict) -> dict:
        """Analyze intent classification from prompt content"""
        content = prompt.get('content', '').lower()

        # Primary goal
        primary_goal = "unknown"
        if 'test' in content:
            primary_goal = "testing"
        elif 'debug' in content or 'fix' in content:
            primary_goal = "debugging"
        elif 'implement' in content or 'create' in content:
            primary_goal = "development"
        elif 'deploy' in content or 'production' in content:
            primary_goal = "deployment"
        elif 'learn' in content or 'understand' in content:
            primary_goal = "learning"

        # Secondary objectives
        secondary_objectives = []
        if 'performance' in content or 'optimize' in content:
            secondary_objectives.append('optimization')
        if 'security' in content or 'auth' in content:
            secondary_objectives.append('security')
        if 'monitor' in content or 'log' in content:
            secondary_objectives.append('monitoring')

        # Task complexity
        task_complexity = "low"
        complexity_score = 0
        if len(content) > 100:
            complexity_score += 1
        if content.count('\n') > 3:
            complexity_score += 1
        if any(tech in content for tech in ['api', 'json', 'curl', 'http']):
            complexity_score += 1
        if any(term in content for term in ['localhost', 'port', 'endpoint']):
            complexity_score += 1

        if complexity_score >= 3:
            task_complexity = "high"
        elif complexity_score >= 2:
            task_complexity = "medium"

        # Domain expertise
        domain_expertise = "unknown"
        if 'curl' in content and 'json' in content:
            domain_expertise = "api_testing"
        elif 'git' in content:
            domain_expertise = "version_control"
        elif 'python' in content or 'pytest' in content:
            domain_expertise = "python_development"
        elif 'web' in content or 'http' in content:
            domain_expertise = "web_development"

        # Success criteria
        success_criteria = []
        if 'work' in content or 'success' in content:
            success_criteria.append('functional_success')
        if 'fast' in content or 'quick' in content:
            success_criteria.append('performance')
        if 'test' in content and 'pass' in content:
            success_criteria.append('test_passing')

        return {
            "primary_goal": primary_goal,
            "secondary_objectives": secondary_objectives,
            "task_complexity": task_complexity,
            "domain_expertise": domain_expertise,
            "success_criteria": success_criteria
        }

    def analyze_cognitive_state(self, prompt: dict) -> dict:
        """Analyze cognitive state from prompt content"""
        content = prompt.get('content', '').lower()

        # Attention level
        attention_level = "normal"
        if len(content) < 10:
            attention_level = "low"
        elif len(content) > 200:
            attention_level = "high"
        elif 'focus' in content or 'attention' in content:
            attention_level = "focused"

        # Frustration indicators
        frustration_indicators = []
        if 'again' in content or 'still' in content:
            frustration_indicators.append('repetitive_attempts')
        if 'not work' in content or 'fail' in content:
            frustration_indicators.append('failure_experience')
        if 'timeout' in content or 'slow' in content:
            frustration_indicators.append('performance_issues')

        # Confidence markers
        confidence_markers = []
        if 'should work' in content or 'will work' in content:
            confidence_markers.append('outcome_certainty')
        if content.startswith('test') or content.startswith('try'):
            confidence_markers.append('initiative_taking')
        if 'implement' in content or 'create' in content:
            confidence_markers.append('construction_confidence')

        # Multitasking signs
        multitasking_signs = []
        if 'also' in content or 'and' in content:
            multitasking_signs.append('parallel_objectives')
        if content.count('then') > 0:
            multitasking_signs.append('sequential_planning')

        # Flow state indicators
        flow_state_indicators = []
        if len(content) > 150 and content.count('\n') > 3:
            flow_state_indicators.append('detailed_specification')
        if 'continue' in content or 'next' in content:
            flow_state_indicators.append('progression_momentum')

        return {
            "attention_level": attention_level,
            "frustration_indicators": frustration_indicators,
            "confidence_markers": confidence_markers,
            "multitasking_signs": multitasking_signs,
            "flow_state_indicators": flow_state_indicators
        }

    def calculate_authenticity_score(self, analysis: dict) -> dict:
        """Calculate authenticity scores based on analysis"""

        # Natural language flow (0.0-1.0)
        natural_flow = 0.6  # Base score
        comm_patterns = analysis['behavioral_patterns']['communication_patterns']
        if 'polite_request' in comm_patterns:
            natural_flow += 0.1
        if 'questioning' in comm_patterns:
            natural_flow += 0.1
        if len(comm_patterns) > 2:
            natural_flow += 0.1
        natural_flow = min(1.0, natural_flow)

        # Context coherence (0.0-1.0)
        context_coherence = 0.5  # Base score
        tech_stack = analysis['technical_context']['technology_stack']
        if len(tech_stack) > 0:
            context_coherence += 0.2
        if analysis['conversation_state']['work_focus'] != "unknown":
            context_coherence += 0.2
        if len(analysis['technical_context']['command_history']) > 0:
            context_coherence += 0.1
        context_coherence = min(1.0, context_coherence)

        # Behavioral consistency (0.0-1.0)
        behavioral_consistency = 0.7  # Base score
        if analysis['behavioral_patterns']['interaction_style'] != "unknown":
            behavioral_consistency += 0.1
        if analysis['behavioral_patterns']['problem_solving_approach'] != "unknown":
            behavioral_consistency += 0.1
        if len(analysis['cognitive_state']['confidence_markers']) > 0:
            behavioral_consistency += 0.1
        behavioral_consistency = min(1.0, behavioral_consistency)

        # Technical accuracy (0.0-1.0)
        technical_accuracy = 0.6  # Base score
        if analysis['intent_classification']['domain_expertise'] != "unknown":
            technical_accuracy += 0.2
        if analysis['intent_classification']['task_complexity'] != "low":
            technical_accuracy += 0.1
        if len(analysis['technical_context']['complexity_indicators']) > 1:
            technical_accuracy += 0.1
        technical_accuracy = min(1.0, technical_accuracy)

        # Human-like variance (0.0-1.0)
        human_variance = 0.8  # Base score
        if len(analysis['cognitive_state']['frustration_indicators']) > 0:
            human_variance += 0.1
        if 'terse' in analysis['behavioral_patterns']['interaction_style']:
            human_variance += 0.1
        human_variance = min(1.0, human_variance)

        # Overall score (weighted average)
        overall_score = (
            natural_flow * 0.25 +
            context_coherence * 0.25 +
            behavioral_consistency * 0.20 +
            technical_accuracy * 0.15 +
            human_variance * 0.15
        )

        return {
            "natural_language_flow": round(natural_flow, 3),
            "context_coherence": round(context_coherence, 3),
            "behavioral_consistency": round(behavioral_consistency, 3),
            "technical_accuracy": round(technical_accuracy, 3),
            "human_like_variance": round(human_variance, 3),
            "overall_score": round(overall_score, 3)
        }

    def analyze_prompt(self, prompt: dict) -> dict:
        """Perform complete behavioral analysis on a single prompt"""
        analysis = {
            "prompt_id": prompt.get('extraction_order'),
            "timestamp": prompt.get('timestamp'),
            "content_preview": prompt.get('content', '')[:100] + "..." if len(prompt.get('content', '')) > 100 else prompt.get('content', ''),
            "analysis": {
                "conversation_state": self.analyze_conversation_state(prompt),
                "technical_context": self.analyze_technical_context(prompt),
                "behavioral_patterns": self.analyze_behavioral_patterns(prompt),
                "intent_classification": self.analyze_intent_classification(prompt),
                "cognitive_state": self.analyze_cognitive_state(prompt)
            }
        }

        # Calculate authenticity score
        analysis["analysis"]["authenticity_score"] = self.calculate_authenticity_score(analysis["analysis"])

        return analysis

    def save_checkpoint(self, batch_num: int):
        """Save checkpoint every 20 prompts"""
        checkpoint_file = os.path.join(
            self.output_dir,
            f"checkpoint_batch_{batch_num:03d}.json"
        )

        checkpoint_data = {
            "batch_number": batch_num,
            "processed_count": self.processed_count,
            "total_target": 994,
            "progress_percentage": round((self.processed_count / 994) * 100, 2),
            "timestamp": datetime.now().isoformat(),
            "average_authenticity": self.calculate_average_authenticity(),
            "results": self.results[-20:]  # Last 20 results
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        print(f"✅ Checkpoint saved: batch {batch_num}, processed {self.processed_count}/994 prompts")

    def calculate_average_authenticity(self) -> float:
        """Calculate average authenticity score"""
        if not self.results:
            return 0.0

        scores = [r["analysis"]["authenticity_score"]["overall_score"] for r in self.results]
        return round(sum(scores) / len(scores), 3)

    def process_chunk(self, chunk_data: dict) -> dict:
        """Process entire chunk with parallel processing"""
        prompts = chunk_data['prompts']
        total_prompts = len(prompts)

        print(f"🚀 Starting behavioral analysis of {total_prompts} prompts")
        print(f"📊 Target authenticity: {self.target_authenticity}")
        print(f"💾 Saving checkpoints every 20 prompts to: {self.output_dir}")

        # Process in batches of 20 for checkpoint saving
        batch_size = 20
        batch_num = 1

        for i in range(0, total_prompts, batch_size):
            batch_prompts = prompts[i:i + batch_size]

            # Process batch with threading for parallel analysis
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self.analyze_prompt, prompt) for prompt in batch_prompts]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        self.results.append(result)
                        self.processed_count += 1

                        # Print progress every 5 prompts
                        if self.processed_count % 5 == 0:
                            avg_auth = self.calculate_average_authenticity()
                            print(f"⚡ Processed {self.processed_count}/{total_prompts} | Avg Auth: {avg_auth}")

                    except Exception as e:
                        print(f"❌ Error processing prompt: {e}")

            # Save checkpoint after each batch
            self.save_checkpoint(batch_num)
            batch_num += 1

            # Check if we're maintaining quality threshold
            avg_authenticity = self.calculate_average_authenticity()
            if avg_authenticity < self.target_authenticity:
                print(f"⚠️ WARNING: Average authenticity {avg_authenticity} below target {self.target_authenticity}")

        # Final summary
        final_avg = self.calculate_average_authenticity()
        print(f"\n🎯 PROCESSING COMPLETE")
        print(f"📈 Total processed: {self.processed_count}/{total_prompts}")
        print(f"🎖️ Final average authenticity: {final_avg}")
        print(f"✅ Target met: {'YES' if final_avg >= self.target_authenticity else 'NO'}")

        return {
            "total_processed": self.processed_count,
            "average_authenticity": final_avg,
            "target_met": final_avg >= self.target_authenticity,
            "results": self.results
        }

def main():
    """Main execution function"""

    # Paths
    chunk_file = "/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/chunks/chunk_006.json"
    template_file = "/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/agent_006/behavioral_analysis_template.json"
    output_dir = "/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/agent_006/"

    # Load chunk data
    print("📂 Loading chunk 006 data...")
    with open(chunk_file, 'r') as f:
        chunk_data = json.load(f)

    # Initialize analyzer
    analyzer = BehavioralAnalyzer(template_file, output_dir)

    # Process chunk
    start_time = time.time()
    results = analyzer.process_chunk(chunk_data)
    end_time = time.time()

    # Save final results
    final_results_file = os.path.join(output_dir, "final_analysis_results.json")
    results["processing_time_seconds"] = round(end_time - start_time, 2)
    results["timestamp"] = datetime.now().isoformat()

    with open(final_results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n🏁 Analysis complete! Processing time: {results['processing_time_seconds']} seconds")
    print(f"💾 Final results saved to: {final_results_file}")

if __name__ == "__main__":
    main()