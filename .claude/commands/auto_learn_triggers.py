#!/usr/bin/env python3
"""
Auto-Learning Trigger Detection for Enhanced /learn Command
Detects patterns that should automatically trigger learning capture
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

class AutoLearnTrigger:
    def __init__(self):
        self.failure_patterns = [
            r'\b(?:error|failed|exception|❌|FAILED|ERROR)\b',
            r'doesn\'?t work',
            r'not working',
            r'try again',
            r'attempt \d+',
            r'still failing'
        ]
        
        self.success_patterns = [
            r'\b(?:success|passed|✅|SUCCESS|PASSED|works now)\b',
            r'\b(?:fixed|resolved|solved|working)\b',
            r'tests? (?:pass|passed)',
            r'finally working'
        ]
        
        self.merge_intentions = [
            r'\b(?:merge|ready|looks good|ship it|deploy this)\b',
            r'ready to merge',
            r'this is done',
            r'completed',
            r'finished',
            r'good to go'
        ]
        
        # Track failure sequences
        self.failure_count = 0
        self.last_failure_context = None
        
    def detect_merge_intention(self, text: str) -> bool:
        """Detect if user is indicating readiness to merge"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) 
                  for pattern in self.merge_intentions)
    
    def detect_failure_pattern(self, text: str) -> bool:
        """Detect failure patterns in text"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) 
                  for pattern in self.failure_patterns)
    
    def detect_success_pattern(self, text: str) -> bool:
        """Detect success patterns in text"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) 
                  for pattern in self.success_patterns)
    
    def track_failure_recovery(self, text: str) -> Optional[str]:
        """Track failure sequences and detect recovery patterns"""
        if self.detect_failure_pattern(text):
            self.failure_count += 1
            self.last_failure_context = text
            return None
        
        elif self.detect_success_pattern(text) and self.failure_count >= 3:
            # Success after 3+ failures - trigger learning
            trigger_reason = f"Success after {self.failure_count} failures"
            self.failure_count = 0  # Reset counter
            self.last_failure_context = None
            return trigger_reason
        
        elif self.detect_success_pattern(text):
            # Reset failure count on success
            self.failure_count = 0
            self.last_failure_context = None
            
        return None
    
    def should_trigger_learning(self, text: str, context: Dict = None) -> Dict:
        """Main function to determine if learning should be triggered"""
        triggers = {
            'merge_intention': False,
            'failure_recovery': False,
            'reason': None,
            'context': None
        }
        
        # Check merge intention
        if self.detect_merge_intention(text):
            triggers['merge_intention'] = True
            triggers['reason'] = "User indicated readiness to merge"
            triggers['context'] = text
        
        # Check failure recovery
        recovery_reason = self.track_failure_recovery(text)
        if recovery_reason:
            triggers['failure_recovery'] = True
            triggers['reason'] = recovery_reason
            triggers['context'] = {
                'last_failure': self.last_failure_context,
                'success_text': text,
                'failure_count': self.failure_count
            }
        
        return triggers

# Global trigger instance for session tracking
auto_trigger = AutoLearnTrigger()

def check_auto_learning_triggers(user_input: str) -> Dict:
    """Check if user input should trigger automatic learning"""
    return auto_trigger.should_trigger_learning(user_input)

def create_learning_proposal(trigger_info: Dict, conversation_context: str = None) -> Dict:
    """Generate learning proposal based on trigger information"""
    proposal = {
        'classification': '✅',  # Default to best practice
        'section': 'Core Principles & Interaction',
        'content': '',
        'rationale': '',
        'evidence': trigger_info.get('context', '')
    }
    
    if trigger_info.get('merge_intention'):
        proposal.update({
            'classification': '⚠️',
            'section': 'Git Workflow',
            'content': 'Before merging, automatically capture learnings with /learn to preserve knowledge',
            'rationale': 'Prevents loss of valuable problem-solving patterns when switching contexts'
        })
    
    elif trigger_info.get('failure_recovery'):
        proposal.update({
            'classification': '🚨',
            'section': 'Critical Lessons (Compressed)',
            'content': f"Pattern recognition: When encountering repeated failures, document successful resolution approach",
            'rationale': f"Multiple failure attempts followed by success indicates valuable learning opportunity"
        })
    
    return proposal

def generate_claude_md_update(proposal: Dict) -> str:
    """Generate CLAUDE.md update text with proper formatting"""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    update_text = f"""
## Learning Update - {timestamp}

**Section**: {proposal['section']}
**Classification**: {proposal['classification']}

**New Rule**:
{proposal['classification']} **Auto-Learning**: {proposal['content']}

**Rationale**: {proposal['rationale']}

**Evidence**: {proposal['evidence']}
"""
    
    return update_text

def create_learning_branch_and_pr(proposal: Dict, original_branch: str) -> Dict:
    """Create learning branch and PR for CLAUDE.md updates"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    learning_branch = f"learning-{timestamp}-auto-trigger"
    
    try:
        # Create new branch
        subprocess.run(['git', 'checkout', '-b', learning_branch], check=True)
        
        # Generate CLAUDE.md update
        update_content = generate_claude_md_update(proposal)
        
        # This would append to CLAUDE.md in real implementation
        # For now, create a proposal file
        proposal_file = Path(f"roadmap/learning_proposal_{timestamp}.md")
        proposal_file.write_text(update_content)
        
        # Stage and commit
        subprocess.run(['git', 'add', str(proposal_file)], check=True)
        subprocess.run(['git', 'commit', '-m', f'learn: Auto-captured learning from {proposal["classification"]} pattern'], check=True)
        
        # Push and create PR
        subprocess.run(['git', 'push', 'origin', f'HEAD:{learning_branch}'], check=True)
        
        # Create PR using gh CLI
        pr_result = subprocess.run([
            'gh', 'pr', 'create', 
            '--title', f'learn: Auto-captured learning - {proposal["classification"]} pattern',
            '--body', f'Auto-generated learning from trigger detection\n\n{update_content}'
        ], capture_output=True, text=True)
        
        # Switch back to original branch
        subprocess.run(['git', 'checkout', original_branch], check=True)
        
        return {
            'success': True,
            'branch': learning_branch,
            'pr_url': pr_result.stdout.strip() if pr_result.returncode == 0 else None,
            'proposal_file': str(proposal_file)
        }
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': str(e),
            'branch': learning_branch
        }

if __name__ == "__main__":
    # Test the auto-trigger system
    test_inputs = [
        "This looks good, ready to merge",
        "ERROR: Test failed again",
        "Still not working, attempt 3",
        "Finally! Tests are passing now",
        "Ship it!"
    ]
    
    for input_text in test_inputs:
        triggers = check_auto_learning_triggers(input_text)
        if triggers['merge_intention'] or triggers['failure_recovery']:
            print(f"TRIGGER: {input_text}")
            print(f"Reason: {triggers['reason']}")
            proposal = create_learning_proposal(triggers)
            print(f"Proposal: {proposal['content']}")
            print("---")