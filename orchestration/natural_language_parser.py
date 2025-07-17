#!/usr/bin/env python3
"""
Natural Language Command Parser for Opus Terminal
Converts natural language commands to agent system API calls
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    """Parsed command structure."""
    action: str
    target: Optional[str]
    parameters: Dict[str, str]
    confidence: float
    raw_command: str


class NaturalLanguageParser:
    """Parser for natural language commands in Opus terminal."""
    
    def __init__(self):
        self.command_patterns = {
            # Task delegation patterns
            'delegate_task': [
                r'(?:build|create|make|develop|implement|enhance|improve|fix|update|modify)\s+(?:a\s+)?(.+)',
                r'(?:please\s+)?(?:can\s+you\s+)?(?:build|create|make|develop|implement|enhance|improve|fix|update|modify)\s+(.+)',
                r'(?:i\s+need\s+)?(?:you\s+to\s+)?(?:build|create|make|develop|implement|enhance|improve|fix|update|modify)\s+(.+)',
                r'(?:task|job|work):\s*(.+)',
                r'(?:delegate|assign|give)\s+(?:task|job|work)\s*:?\s*(.+)',
            ],
            
            # Status check patterns
            'check_status': [
                r'(?:what\'s\s+the\s+)?status\??',
                r'(?:show\s+)?(?:system\s+)?status',
                r'(?:how\s+are\s+)?(?:things\s+)?(?:going|doing)\??',
                r'(?:what\'s\s+)?(?:happening|going\s+on)\??',
                r'(?:check\s+)?(?:agent\s+)?status',
                r'(?:list\s+)?(?:active\s+)?agents',
            ],
            
            # Help patterns
            'show_help': [
                r'help\??',
                r'(?:what\s+can\s+)?(?:you\s+)?(?:do|commands?)\??',
                r'(?:how\s+do\s+i|how\s+to)\s+(.+)',
                r'(?:available\s+)?(?:commands?|options?)',
                r'(?:help\s+me\s+(?:with\s+)?(?:understand\s+)?)?(?:connection|connecting|collaboration)',
                r'(?:show\s+me\s+)?(?:connection\s+)?(?:options|methods)',
                r'(?:what\s+are\s+my\s+)?(?:monitoring\s+)?(?:options|choices)',
                r'(?:how\s+does\s+this\s+work)\??',
            ],
            
            # Agent management
            'spawn_agent': [
                r'(?:spawn|start|create|launch)\s+(?:a\s+)?(?:new\s+)?(?:sonnet\s+)?agent',
                r'(?:add|get)\s+(?:another|more)\s+(?:sonnet\s+)?agent',
                r'(?:need\s+)?(?:more\s+)?(?:help|agents?|workers?)',
            ],
            
            # Agent monitoring
            'monitor_agents': [
                r'(?:monitor|watch|observe)\s+(?:the\s+)?(?:sonnet\s+)?agents?',
                r'(?:what\s+are\s+the\s+)?(?:sonnet\s+)?agents?\s+(?:doing|working\s+on)',
                r'(?:show\s+me\s+)?(?:agent\s+)?(?:activity|monitoring|details)',
                r'(?:how\s+do\s+i\s+)?(?:monitor|watch|see)\s+(?:what\s+)?(?:agents?\s+are\s+doing|activity)',
                r'(?:visibility\s+into\s+)?(?:agent\s+)?(?:work|progress|activity)',
            ],
            
            # Agent connection
            'connect_agent': [
                r'(?:connect\s+to\s+)?(?:sonnet\s+)?(?:agent\s+)?(\d+|sonnet-\d+)',
                r'(?:connect\s+to\s+)?(?:the\s+)?(?:sonnet\s+)?agent(?:\s+(.+))?',
                r'(?:join|attach\s+to)\s+(?:sonnet\s+)?(?:agent\s+)?(.+)',
                r'(?:use\s+claude\s+code\s+cli\s+)?(?:with|in)\s+(?:sonnet\s+)?(?:agent\s+)?(.+)',
                r'(?:collaborate\s+with)\s+(?:sonnet\s+)?(?:agent\s+)?(.+)',
            ],
            
            # Task monitoring
            'check_progress': [
                r'(?:how\'s\s+)?(?:the\s+)?(?:progress|task)\s+(?:going|doing)\??',
                r'(?:check\s+)?(?:task\s+)?progress',
                r'(?:what\'s\s+the\s+)?(?:status\s+of\s+)?(?:my\s+)?task\??',
                r'(?:any\s+)?(?:updates|progress)\??',
            ],
            
            # System commands
            'stop_system': [
                r'(?:stop|shutdown|quit|exit)\s+(?:system|everything)',
                r'(?:shutdown|stop)\s+(?:all\s+)?agents?',
            ],
            
            # Conversational responses
            'greeting': [
                r'(?:hi|hello|hey)(?:\s+there)?\??',
                r'(?:good\s+)?(?:morning|afternoon|evening)',
            ],
            
            'thanks': [
                r'(?:thank\s+you|thanks?)(?:\s+(?:very\s+)?much)?\??',
                r'(?:i\s+)?appreciate\s+(?:it|that)',
            ]
        }
        
        self.priority_keywords = {
            'high': ['urgent', 'asap', 'immediately', 'high priority', 'critical'],
            'medium': ['soon', 'medium priority', 'when possible'],
            'low': ['later', 'low priority', 'whenever', 'no rush']
        }
    
    def parse_command(self, user_input: str) -> ParsedCommand:
        """Parse natural language input into structured command."""
        user_input = user_input.strip().lower()
        
        # Try to match against known patterns
        for action, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, user_input)
                if match:
                    # Extract parameters based on action type
                    parameters = self._extract_parameters(action, match, user_input)
                    confidence = self._calculate_confidence(pattern, user_input)
                    
                    return ParsedCommand(
                        action=action,
                        target=match.group(1) if match.groups() else None,
                        parameters=parameters,
                        confidence=confidence,
                        raw_command=user_input
                    )
        
        # If no pattern matches, try to infer intent
        return self._infer_intent(user_input)
    
    def _extract_parameters(self, action: str, match: re.Match, raw_input: str) -> Dict[str, str]:
        """Extract parameters based on action type."""
        params = {}
        
        if action == 'delegate_task':
            # Extract priority
            priority = self._extract_priority(raw_input)
            params['priority'] = priority
            
            # Extract deadline hints
            deadline_patterns = [
                r'(?:by|before|within)\s+(\d+)\s+(hours?|days?|weeks?)',
                r'(?:in\s+)?(\d+)\s+(hours?|days?|weeks?)',
                r'(?:deadline|due):\s*(.+)',
            ]
            
            for pattern in deadline_patterns:
                deadline_match = re.search(pattern, raw_input)
                if deadline_match:
                    params['deadline'] = deadline_match.group(0)
                    break
        
        return params
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority level from text."""
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return priority
        return 'medium'  # default
    
    def _calculate_confidence(self, pattern: str, user_input: str) -> float:
        """Calculate confidence score for pattern match."""
        # Basic confidence calculation based on pattern specificity
        base_confidence = 0.8
        
        # Boost confidence for exact matches
        if pattern.count('\\s+') < 2:  # Simple patterns
            base_confidence += 0.1
        
        # Boost for specific keywords
        specific_keywords = ['build', 'create', 'implement', 'develop', 'status', 'help']
        for keyword in specific_keywords:
            if keyword in user_input:
                base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _infer_intent(self, user_input: str) -> ParsedCommand:
        """Infer intent when no pattern matches."""
        # Check for question words
        if any(word in user_input for word in ['what', 'how', 'when', 'where', 'why']):
            return ParsedCommand(
                action='show_help',
                target=user_input,
                parameters={'type': 'question'},
                confidence=0.3,
                raw_command=user_input
            )
        
        # Check for task-like language
        task_indicators = ['need', 'want', 'should', 'must', 'have to', 'require']
        if any(indicator in user_input for indicator in task_indicators):
            return ParsedCommand(
                action='delegate_task',
                target=user_input,
                parameters={'priority': 'medium', 'inferred': 'true'},
                confidence=0.4,
                raw_command=user_input
            )
        
        # Default to unknown command
        return ParsedCommand(
            action='unknown',
            target=user_input,
            parameters={},
            confidence=0.1,
            raw_command=user_input
        )
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on partial input."""
        suggestions = []
        
        # Common task suggestions
        task_suggestions = [
            "Build a user authentication system",
            "Create a REST API for user management",
            "Implement a database schema for products",
            "Develop a responsive web interface",
            "Build automated tests for the system",
            "Create documentation for the API",
            "Implement error handling and logging",
            "Build a caching layer for performance"
        ]
        
        # Status and help suggestions
        system_suggestions = [
            "What's the status?",
            "Show me the agents",
            "How's the progress?",
            "Help me with commands",
            "Spawn a new agent",
            "Check system status"
        ]
        
        if len(partial_input) < 3:
            return task_suggestions[:4] + system_suggestions[:4]
        
        # Filter suggestions based on partial input
        all_suggestions = task_suggestions + system_suggestions
        filtered = [s for s in all_suggestions if partial_input.lower() in s.lower()]
        
        return filtered[:8]  # Return top 8 suggestions


def format_response(command: ParsedCommand, result: str) -> str:
    """Format response in natural language."""
    if command.action == 'greeting':
        return "Hello! I'm Opus, your AI agent coordinator. I can help you build systems, manage tasks, and coordinate development work. What would you like me to work on?"
    
    elif command.action == 'thanks':
        return "You're welcome! I'm here to help with any development tasks you need. What's next?"
    
    elif command.action == 'delegate_task':
        if command.target:
            return f"Got it! I'll work on: {command.target}\n\n{result}"
        else:
            return f"I'll handle that task for you.\n\n{result}"
    
    elif command.action == 'check_status':
        return f"Here's the current system status:\n\n{result}"
    
    elif command.action == 'show_help':
        return f"I can help you with:\n\n{result}"
    
    elif command.action == 'unknown':
        return f"I'm not sure how to handle that. {result}\n\nTry asking me to 'build', 'create', or 'implement' something, or ask for 'status' or 'help'."
    
    else:
        return result


if __name__ == "__main__":
    # Test the parser
    parser = NaturalLanguageParser()
    
    test_commands = [
        "Build a user authentication system",
        "What's the status?",
        "Help me with commands",
        "Create a REST API urgently",
        "I need you to implement a database schema",
        "How's the progress going?",
        "Hello there!",
        "Thanks for your help"
    ]
    
    print("🧠 Natural Language Parser Test")
    print("=" * 50)
    
    for cmd in test_commands:
        result = parser.parse_command(cmd)
        print(f"\nInput: '{cmd}'")
        print(f"Action: {result.action}")
        print(f"Target: {result.target}")
        print(f"Parameters: {result.parameters}")
        print(f"Confidence: {result.confidence:.2f}")