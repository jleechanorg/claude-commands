#!/usr/bin/env python3
"""
Automatic Correction Detection Engine
Detects and classifies user corrections in real-time during conversations
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class CorrectionDetector:
    """Detects and classifies correction patterns in user messages"""
    
    def __init__(self):
        self.patterns = {
            'dont_do_instead': [
                r"don't\s+(.*?),\s*(.*?)(?:\.|$)",
                r"don't\s+(.*?)\.\s*(.*?)(?:\.|$)",
                r"avoid\s+(.*?),\s*(.*?)(?:\.|$)",
                r"stop\s+(.*?),\s*(.*?)(?:\.|$)"
            ],
            'use_instead': [
                r"use\s+(.*?)\s+instead\s+of\s+(.*?)(?:\.|$)",
                r"prefer\s+(.*?)\s+over\s+(.*?)(?:\.|$)",
                r"choose\s+(.*?)\s+not\s+(.*?)(?:\.|$)"
            ],
            'preference': [
                r"i\s+prefer\s+(.*?)(?:\.|$)",
                r"i\s+like\s+(.*?)(?:\.|$)",
                r"my\s+preference\s+is\s+(.*?)(?:\.|$)",
                r"please\s+use\s+(.*?)(?:\.|$)"
            ],
            'context_behavior': [
                r"when\s+(.*?),\s*(.*?)(?:\.|$)",
                r"if\s+(.*?),\s*(.*?)(?:\.|$)",
                r"during\s+(.*?),\s*(.*?)(?:\.|$)",
                r"for\s+(.*?),\s*(.*?)(?:\.|$)"
            ],
            'always_rule': [
                r"always\s+(.*?)(?:\.|$)",
                r"make\s+sure\s+to\s+(.*?)(?:\.|$)",
                r"remember\s+to\s+(.*?)(?:\.|$)"
            ],
            'never_rule': [
                r"never\s+(.*?)(?:\.|$)",
                r"don't\s+ever\s+(.*?)(?:\.|$)",
                r"avoid\s+(.*?)(?:\.|$)"
            ],
            'correction': [
                r"actually,?\s+(.*?)(?:\.|$)",
                r"no,?\s+(.*?)(?:\.|$)",
                r"wrong,?\s+(.*?)(?:\.|$)",
                r"incorrect,?\s+(.*?)(?:\.|$)"
            ],
            'mistake_fix': [
                r"(?:that's\s+)?(?:wrong|incorrect|mistake).*?should\s+be\s+(.*?)(?:\.|$)",
                r"fix.*?(?:by|to)\s+(.*?)(?:\.|$)",
                r"change.*?(?:to|into)\s+(.*?)(?:\.|$)"
            ]
        }
        
        self.context_keywords = {
            'urgent': ['quick', 'urgent', 'asap', 'immediately', 'fast', 'rush', 'hurry'],
            'quality': ['careful', 'thorough', 'comprehensive', 'detailed', 'precise'],
            'coding': ['function', 'class', 'variable', 'import', 'test', 'code', 'script'],
            'review': ['pr', 'review', 'check', 'verify', 'approve', 'merge'],
            'workflow': ['command', 'process', 'step', 'procedure', 'protocol'],
            'testing': ['test', 'testing', 'spec', 'coverage', 'validate'],
            'documentation': ['docs', 'readme', 'documentation', 'comment'],
            'git': ['commit', 'branch', 'merge', 'push', 'pull', 'git']
        }
    
    def detect_corrections(self, message: str) -> List[Dict]:
        """Detect all correction patterns in a message"""
        corrections = []
        message_lower = message.lower().strip()
        
        for correction_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    correction = {
                        'type': correction_type,
                        'raw_match': match,
                        'pattern': match if isinstance(match, tuple) else (match,),
                        'original_text': message,
                        'confidence': self._calculate_confidence(correction_type, message_lower),
                        'context': self._detect_context(message_lower),
                        'timestamp': datetime.now().isoformat(),
                        'processed': False
                    }
                    corrections.append(correction)
        
        return self._deduplicate_corrections(corrections)
    
    def _calculate_confidence(self, correction_type: str, message: str) -> float:
        """Calculate confidence score for detected correction"""
        base_confidence = 0.7
        
        # Boost confidence for certain patterns
        confidence_boosts = {
            'dont_do_instead': 0.2,
            'use_instead': 0.2,
            'always_rule': 0.1,
            'never_rule': 0.1,
            'correction': 0.15
        }
        
        confidence = base_confidence + confidence_boosts.get(correction_type, 0.0)
        
        # Boost for explicit language
        if any(word in message for word in ['always', 'never', 'must', 'should']):
            confidence += 0.1
        
        # Boost for clear structure
        if ',' in message or '.' in message:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _detect_context(self, message: str) -> List[str]:
        """Detect context keywords in message"""
        detected_contexts = []
        
        for context, keywords in self.context_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_contexts.append(context)
        
        return detected_contexts if detected_contexts else ['general']
    
    def _deduplicate_corrections(self, corrections: List[Dict]) -> List[Dict]:
        """Remove duplicate or overlapping corrections"""
        if not corrections:
            return corrections
        
        # Sort by confidence (highest first)
        corrections.sort(key=lambda x: x['confidence'], reverse=True)
        
        unique_corrections = []
        seen_patterns = set()
        
        for correction in corrections:
            pattern_key = str(correction['pattern'])
            if pattern_key not in seen_patterns:
                unique_corrections.append(correction)
                seen_patterns.add(pattern_key)
        
        return unique_corrections
    
    def format_correction_summary(self, corrections: List[Dict]) -> str:
        """Format corrections for user confirmation"""
        if not corrections:
            return "No corrections detected."
        
        summary_lines = [f"🧠 Detected {len(corrections)} correction(s):"]
        
        for i, correction in enumerate(corrections, 1):
            pattern_text = " → ".join(correction['pattern']) if len(correction['pattern']) > 1 else correction['pattern'][0]
            context_text = ", ".join(correction['context'])
            confidence = correction['confidence']
            
            summary_lines.append(
                f"  {i}. [{correction['type']}] {pattern_text} "
                f"(confidence: {confidence:.2f}, context: {context_text})"
            )
        
        return "\n".join(summary_lines)

class AutoCorrectionPipeline:
    """Pipeline for processing corrections automatically"""
    
    def __init__(self):
        self.detector = CorrectionDetector()
        self.memory_file = Path.home() / ".cache" / "claude-learning" / "auto_corrections.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    
    def process_user_message(self, message: str, conversation_context: Optional[Dict] = None) -> Dict:
        """Process a user message for corrections and return results"""
        result = {
            'corrections_detected': [],
            'storage_success': False,
            'user_confirmation_needed': False,
            'summary': ""
        }
        
        # Detect corrections
        corrections = self.detector.detect_corrections(message)
        result['corrections_detected'] = corrections
        
        if corrections:
            # Store corrections
            stored = self._store_corrections(corrections, conversation_context)
            result['storage_success'] = stored
            
            # Generate summary
            result['summary'] = self.detector.format_correction_summary(corrections)
            result['user_confirmation_needed'] = True
        
        return result
    
    def _store_corrections(self, corrections: List[Dict], conversation_context: Optional[Dict] = None) -> bool:
        """Store corrections in local memory"""
        try:
            # Load existing corrections
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'corrections': [], 'metadata': {'created': datetime.now().isoformat()}}
            
            # Add new corrections
            for correction in corrections:
                correction_entry = {
                    'id': f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(data['corrections'])}",
                    'correction': correction,
                    'conversation_context': conversation_context or {},
                    'stored_at': datetime.now().isoformat(),
                    'processed': False
                }
                data['corrections'].append(correction_entry)
            
            # Save updated data
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error storing corrections: {e}")
            return False
    
    def get_unprocessed_corrections(self) -> List[Dict]:
        """Get corrections that haven't been processed to Memory MCP yet"""
        if not self.memory_file.exists():
            return []
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            return [c for c in data.get('corrections', []) if not c.get('processed', False)]
        
        except:
            return []
    
    def mark_corrections_processed(self, correction_ids: List[str]) -> bool:
        """Mark corrections as processed after successful Memory MCP storage"""
        if not self.memory_file.exists():
            return False
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            for correction in data.get('corrections', []):
                if correction['id'] in correction_ids:
                    correction['processed'] = True
                    correction['processed_at'] = datetime.now().isoformat()
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except:
            return False

def test_correction_detection():
    """Test the correction detection system"""
    detector = CorrectionDetector()
    pipeline = AutoCorrectionPipeline()
    
    test_messages = [
        "Don't use inline imports, use module-level imports instead.",
        "I prefer structured commit messages with clear prefixes.",
        "When urgent, focus on surgical fixes not comprehensive refactoring.",
        "Always run tests before marking tasks complete.",
        "Actually, that approach won't work.",
        "Never hardcode values in the main code.",
        "Use enhanced_learn.py instead of manual learning."
    ]
    
    print("🧪 Testing Correction Detection Engine")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        result = pipeline.process_user_message(message)
        print(f"   Detected: {len(result['corrections_detected'])} correction(s)")
        if result['summary']:
            print(f"   Summary: {result['summary']}")
    
    # Show unprocessed corrections
    unprocessed = pipeline.get_unprocessed_corrections()
    print(f"\n📊 Total unprocessed corrections: {len(unprocessed)}")

if __name__ == "__main__":
    test_correction_detection()