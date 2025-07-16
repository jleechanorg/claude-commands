#!/usr/bin/env python3
"""
Response Enhancement System for Week 2 Conscious Memory Integration
Shows memory insights in responses when relevant patterns are found
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from context_aware_memory import MemoryQueryEngine

class ResponseEnhancer:
    """Enhances responses with memory insights and learned patterns"""
    
    def __init__(self):
        self.memory_engine = MemoryQueryEngine()
        self.response_templates = {
            'memory_consultation_header': "💭 **Checking memory for relevant patterns...**",
            'memory_insights_found': "🧠 **Memory Insights Applied**",
            'memory_insights_none': "💭 *No specific patterns found for this context*",
            'pattern_application': "📋 **Applying learned patterns:**",
            'confidence_notice': "⚡ *Based on previous corrections and preferences*"
        }
    
    def enhance_response_with_memory(self, user_message: str, base_response: str = "", show_process: bool = True) -> Dict:
        """Enhance a response with memory consultation and insights"""
        
        # Query memory for relevant patterns
        memory_result = self.memory_engine.query_relevant_patterns(user_message)
        
        enhancement_data = {
            'enhanced_response': base_response,
            'memory_consultation_performed': memory_result['consultation_needed'],
            'patterns_applied': [],
            'insights_shown': [],
            'behavioral_modifications': [],
            'response_metadata': {
                'context_analysis': memory_result['context_analysis'],
                'patterns_found': len(memory_result['patterns_found']),
                'consultation_priority': memory_result['context_analysis'].get('consultation_priority', 'low')
            }
        }
        
        if memory_result['consultation_needed']:
            if show_process:
                # Add memory consultation header
                enhancement_data['enhanced_response'] = self._add_memory_consultation_header(
                    enhancement_data['enhanced_response']
                )
            
            # Apply found patterns
            if memory_result['patterns_found']:
                pattern_applications = self._apply_patterns_to_response(
                    memory_result['patterns_found'], 
                    memory_result['context_analysis']
                )
                enhancement_data['patterns_applied'] = pattern_applications
                
                if show_process:
                    # Add insights section
                    insights_section = self._generate_insights_section(memory_result)
                    enhancement_data['enhanced_response'] += "\n\n" + insights_section
                
                # Apply behavioral modifications
                behavioral_mods = self._generate_behavioral_modifications(
                    memory_result['confidence_weighted_suggestions']
                )
                enhancement_data['behavioral_modifications'] = behavioral_mods
            
            else:
                if show_process:
                    # Add "no patterns found" notice
                    enhancement_data['enhanced_response'] += f"\n\n{self.response_templates['memory_insights_none']}"
        
        # Add response metadata if requested
        if show_process and enhancement_data['patterns_applied']:
            metadata_section = self._generate_metadata_section(enhancement_data)
            enhancement_data['enhanced_response'] += "\n\n" + metadata_section
        
        return enhancement_data
    
    def _add_memory_consultation_header(self, response: str) -> str:
        """Add memory consultation header to response"""
        if response:
            return f"{self.response_templates['memory_consultation_header']}\n\n{response}"
        else:
            return self.response_templates['memory_consultation_header']
    
    def _generate_insights_section(self, memory_result: Dict) -> str:
        """Generate the insights section showing what was found"""
        lines = [self.response_templates['memory_insights_found']]
        
        if memory_result['memory_insights']:
            lines.extend(memory_result['memory_insights'])
        
        return "\n".join(lines)
    
    def _apply_patterns_to_response(self, patterns: List[Dict], context: Dict) -> List[Dict]:
        """Apply found patterns to generate response modifications"""
        pattern_applications = []
        
        for pattern in patterns:
            application = {
                'pattern_id': pattern.get('id', 'unknown'),
                'pattern_type': pattern.get('correction_type', 'unknown'),
                'pattern_text': pattern.get('pattern', ''),
                'confidence': pattern.get('confidence', 0),
                'relevance': pattern.get('relevance_score', 0),
                'application_rule': self._determine_application_rule(pattern, context),
                'behavioral_change': self._suggest_behavioral_change(pattern)
            }
            pattern_applications.append(application)
        
        return pattern_applications
    
    def _determine_application_rule(self, pattern: Dict, context: Dict) -> str:
        """Determine how to apply this pattern in current context"""
        correction_type = pattern.get('correction_type', 'unknown')
        pattern_text = pattern.get('pattern', '')
        
        if isinstance(pattern_text, list):
            pattern_text = " → ".join(pattern_text)
        
        application_rules = {
            'dont_do_instead': f"Avoid: {pattern_text.split(' → ')[0] if ' → ' in pattern_text else pattern_text}",
            'use_instead': f"Use: {pattern_text.split(' → ')[1] if ' → ' in pattern_text else pattern_text}",
            'preference': f"Apply preference: {pattern_text}",
            'context_behavior': f"Context-specific: {pattern_text}",
            'always_rule': f"Always: {pattern_text}",
            'never_rule': f"Never: {pattern_text}"
        }
        
        return application_rules.get(correction_type, f"Apply: {pattern_text}")
    
    def _suggest_behavioral_change(self, pattern: Dict) -> str:
        """Suggest behavioral change based on pattern"""
        correction_type = pattern.get('correction_type', 'unknown')
        confidence = pattern.get('confidence', 0)
        
        if confidence > 0.8:
            strength = "strongly"
        elif confidence > 0.6:
            strength = "moderately"
        else:
            strength = "lightly"
        
        behavior_suggestions = {
            'dont_do_instead': f"Avoid this approach ({strength} learned)",
            'use_instead': f"Prefer this alternative ({strength} learned)",
            'preference': f"Apply user preference ({strength} learned)",
            'context_behavior': f"Context-specific behavior ({strength} learned)",
            'always_rule': f"Mandatory behavior ({strength} learned)",
            'never_rule': f"Prohibited behavior ({strength} learned)"
        }
        
        return behavior_suggestions.get(correction_type, f"Apply pattern ({strength} learned)")
    
    def _generate_behavioral_modifications(self, suggestions: List[Dict]) -> List[Dict]:
        """Generate behavioral modifications based on confidence-weighted suggestions"""
        modifications = []
        
        for suggestion in suggestions:
            if suggestion['combined_score'] > 0.6:  # Only high-confidence suggestions
                modification = {
                    'modification_type': suggestion['type'],
                    'description': suggestion['recommendation'],
                    'confidence_score': suggestion['confidence'],
                    'application_priority': 'high' if suggestion['combined_score'] > 0.8 else 'medium',
                    'behavioral_instruction': self._generate_behavioral_instruction(suggestion)
                }
                modifications.append(modification)
        
        return modifications
    
    def _generate_behavioral_instruction(self, suggestion: Dict) -> str:
        """Generate specific behavioral instruction"""
        pattern_type = suggestion['type']
        confidence = suggestion['confidence']
        
        if confidence > 0.8:
            instructions = {
                'dont_do_instead': "Immediately check for this anti-pattern before responding",
                'use_instead': "Actively apply this alternative approach",
                'preference': "Default to this user preference",
                'always_rule': "Mandatory: Always follow this rule",
                'never_rule': "Mandatory: Never violate this rule"
            }
        else:
            instructions = {
                'dont_do_instead': "Consider avoiding this pattern",
                'use_instead': "Consider this alternative approach",
                'preference': "Take this user preference into account",
                'always_rule': "Try to follow this rule",
                'never_rule': "Try to avoid this pattern"
            }
        
        return instructions.get(pattern_type, "Apply this learned pattern")
    
    def _generate_metadata_section(self, enhancement_data: Dict) -> str:
        """Generate metadata section for transparency"""
        metadata = enhancement_data['response_metadata']
        
        lines = [
            "---",
            "**🔧 Response Enhancement Metadata:**",
            f"- Context Priority: {metadata['consultation_priority']}",
            f"- Patterns Applied: {len(enhancement_data['patterns_applied'])}",
            f"- Behavioral Modifications: {len(enhancement_data['behavioral_modifications'])}",
        ]
        
        if enhancement_data['patterns_applied']:
            lines.append("- Applied Patterns:")
            for pattern in enhancement_data['patterns_applied'][:3]:  # Show top 3
                lines.append(f"  - {pattern['application_rule']} (confidence: {pattern['confidence']:.1f})")
        
        lines.append(f"- {self.response_templates['confidence_notice']}")
        
        return "\n".join(lines)

class ConversationMemoryIntegrator:
    """Integrates memory consultation into conversation flow"""
    
    def __init__(self):
        self.response_enhancer = ResponseEnhancer()
        self.session_file = Path.home() / ".cache" / "claude-learning" / "memory_integration_session.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_data = self._load_session()
    
    def _load_session(self) -> Dict:
        """Load current session data"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'session_start': datetime.now().isoformat(),
            'memory_consultations': 0,
            'patterns_applied': 0,
            'behavioral_modifications': 0,
            'consultation_log': []
        }
    
    def _save_session(self):
        """Save session data"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except:
            pass
    
    def process_conversation_turn(self, user_message: str, ai_response: str = "", show_memory_process: bool = True) -> Dict:
        """Process a conversation turn with memory integration"""
        
        # Enhance response with memory
        enhancement_result = self.response_enhancer.enhance_response_with_memory(
            user_message, ai_response, show_memory_process
        )
        
        # Update session tracking
        if enhancement_result['memory_consultation_performed']:
            self.session_data['memory_consultations'] += 1
        
        self.session_data['patterns_applied'] += len(enhancement_result['patterns_applied'])
        self.session_data['behavioral_modifications'] += len(enhancement_result['behavioral_modifications'])
        
        # Log consultation
        self.session_data['consultation_log'].append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message[:100] + "..." if len(user_message) > 100 else user_message,
            'consultation_performed': enhancement_result['memory_consultation_performed'],
            'patterns_found': enhancement_result['response_metadata']['patterns_found'],
            'priority': enhancement_result['response_metadata']['consultation_priority']
        })
        
        # Keep only last 10 consultations
        if len(self.session_data['consultation_log']) > 10:
            self.session_data['consultation_log'] = self.session_data['consultation_log'][-10:]
        
        self._save_session()
        
        return {
            'enhanced_response': enhancement_result['enhanced_response'],
            'memory_applied': enhancement_result['memory_consultation_performed'],
            'session_stats': self.get_session_stats(),
            'behavioral_guidance': enhancement_result['behavioral_modifications']
        }
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        return {
            'memory_consultations': self.session_data['memory_consultations'],
            'patterns_applied': self.session_data['patterns_applied'],
            'behavioral_modifications': self.session_data['behavioral_modifications'],
            'session_duration': self._calculate_session_duration()
        }
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration"""
        try:
            start = datetime.fromisoformat(self.session_data['session_start'])
            duration = datetime.now() - start
            return f"{duration.seconds // 60} minutes"
        except:
            return "unknown"
    
    def generate_memory_consultation_report(self) -> str:
        """Generate report on memory consultations"""
        stats = self.get_session_stats()
        
        lines = [
            "📊 **Memory Integration Session Report**",
            "",
            f"**Session Duration**: {stats['session_duration']}",
            f"**Memory Consultations**: {stats['memory_consultations']}",
            f"**Patterns Applied**: {stats['patterns_applied']}",
            f"**Behavioral Modifications**: {stats['behavioral_modifications']}",
            ""
        ]
        
        if self.session_data['consultation_log']:
            lines.extend([
                "**Recent Consultations**:",
                ""
            ])
            
            for log_entry in self.session_data['consultation_log'][-5:]:
                timestamp = log_entry['timestamp'][:19].replace('T', ' ')
                consultation = "✅" if log_entry['consultation_performed'] else "❌"
                priority = log_entry['priority']
                patterns = log_entry['patterns_found']
                
                lines.append(f"- {timestamp}: {consultation} Priority: {priority}, Patterns: {patterns}")
                lines.append(f"  Message: {log_entry['user_message']}")
        
        return "\n".join(lines)

def demo_response_enhancement():
    """Demonstrate the response enhancement system"""
    
    integrator = ConversationMemoryIntegrator()
    
    conversation_examples = [
        {
            'user': "Write a function to validate email addresses",
            'ai': "I'll create a comprehensive email validation function using regex patterns."
        },
        {
            'user': "Review this code for any issues",
            'ai': "Let me analyze the code for potential problems and best practices."
        },
        {
            'user': "Quick fix for the broken import statement",
            'ai': "I'll provide a fast solution for the import issue."
        },
        {
            'user': "How should I structure my test files?",
            'ai': "Here's the recommended test file organization structure."
        }
    ]
    
    print("🧠 Response Enhancement System Demo")
    print("=" * 60)
    
    for i, example in enumerate(conversation_examples, 1):
        print(f"\n--- Conversation Turn {i} ---")
        print(f"User: {example['user']}")
        print(f"Base AI Response: {example['ai']}")
        print("\n" + "-" * 40)
        
        result = integrator.process_conversation_turn(
            example['user'], 
            example['ai'], 
            show_memory_process=True
        )
        
        print("Enhanced Response:")
        print(result['enhanced_response'])
        
        if result['behavioral_guidance']:
            print(f"\nBehavioral Guidance:")
            for guidance in result['behavioral_guidance']:
                print(f"  - {guidance['behavioral_instruction']}")
    
    print("\n" + "=" * 60)
    report = integrator.generate_memory_consultation_report()
    print(report)

if __name__ == "__main__":
    demo_response_enhancement()