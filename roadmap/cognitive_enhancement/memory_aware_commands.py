#!/usr/bin/env python3
"""
Memory-Aware Command Processing System
======================================

This module provides a unified system for integrating memory pattern queries
into all slash commands, creating a consistent experience where commands
automatically consult learned patterns before execution.

Features:
- Universal command wrapper system
- Command-specific pattern querying
- Memory-informed decision making
- Consistent pattern application across all commands
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import re

# Import the cognitive enhancement framework
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from query_patterns import PatternQueryEngine, QueryResult, MemoryConsciousResponseGenerator
from enhanced_learn import EnhancedLearner
from enhanced_execute_wrapper import EnhancedExecuteWrapper


@dataclass
class CommandContext:
    """Context information for command execution."""
    command_name: str
    raw_args: str
    parsed_args: Dict[str, Any]
    user_intent: str
    complexity_level: str
    requires_memory: bool


@dataclass
class MemoryGuidance:
    """Memory guidance for command execution."""
    patterns_found: List[Any]
    recommendations: List[str]
    critical_warnings: List[str]
    preferred_approaches: List[str]
    avoid_patterns: List[str]


class MemoryAwareCommandProcessor:
    """Unified command processor with memory pattern integration."""
    
    def __init__(self):
        self.learner = EnhancedLearner()
        self.query_engine = PatternQueryEngine(self.learner)
        self.memory_generator = MemoryConsciousResponseGenerator(self.learner)
        self.execute_wrapper = EnhancedExecuteWrapper()
        
        # Command-specific pattern queries
        self.command_patterns = {
            'execute': self._query_execute_patterns,
            'e': self._query_execute_patterns,
            'plan': self._query_execute_patterns,
            'testui': self._query_test_patterns,
            'testuif': self._query_test_patterns,
            'testhttp': self._query_test_patterns,
            'testhttpf': self._query_test_patterns,
            'testi': self._query_test_patterns,
            'learn': self._query_learn_patterns,
            'push': self._query_git_patterns,
            'pr': self._query_git_patterns,
            'integrate': self._query_git_patterns,
            'newbranch': self._query_git_patterns,
            'review': self._query_review_patterns,
            'coverage': self._query_test_patterns,
            'think': self._query_think_patterns
        }
    
    def _query_execute_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for execute/plan commands."""
        query = f"execute implementation {context.raw_args} approach workflow subagent"
        return self.query_engine.query_patterns(query, limit=5)
    
    def _query_test_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for test commands."""
        test_type = "ui" if "ui" in context.command_name else "http" if "http" in context.command_name else "integration"
        query = f"test {test_type} testing {context.raw_args} browser automation"
        return self.query_engine.query_patterns(query, limit=5)
    
    def _query_learn_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for learn command."""
        query = f"learning documentation rules {context.raw_args} mistake correction"
        return self.query_engine.query_patterns(query, limit=5)
    
    def _query_git_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for git-related commands."""
        query = f"git {context.command_name} {context.raw_args} branch workflow"
        return self.query_engine.query_patterns(query, limit=5)
    
    def _query_review_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for review command."""
        query = f"code review {context.raw_args} analysis quality"
        return self.query_engine.query_patterns(query, limit=5)
    
    def _query_think_patterns(self, context: CommandContext) -> QueryResult:
        """Query patterns for think command."""
        query = f"thinking analysis {context.raw_args} problem solving approach"
        return self.query_engine.query_patterns(query, limit=5)
    
    def analyze_command_context(self, command: str, args: str) -> CommandContext:
        """Analyze command context to determine memory consultation needs."""
        
        # Parse command and arguments
        parsed_args = self._parse_command_args(command, args)
        
        # Determine user intent
        intent = self._determine_user_intent(command, args)
        
        # Assess complexity
        complexity = self._assess_command_complexity(command, args)
        
        # Determine if memory consultation is needed
        requires_memory = self._should_consult_memory(command, args, complexity)
        
        return CommandContext(
            command_name=command,
            raw_args=args,
            parsed_args=parsed_args,
            user_intent=intent,
            complexity_level=complexity,
            requires_memory=requires_memory
        )
    
    def _parse_command_args(self, command: str, args: str) -> Dict[str, Any]:
        """Parse command arguments into structured data."""
        parsed = {
            'raw_text': args,
            'word_count': len(args.split()),
            'has_flags': '-' in args,
            'has_paths': '/' in args or '\\' in args,
            'keywords': []
        }
        
        # Extract common keywords based on command type
        if command in ['execute', 'e', 'plan']:
            implementation_keywords = ['implement', 'create', 'build', 'fix', 'update', 'modify']
            parsed['keywords'] = [kw for kw in implementation_keywords if kw in args.lower()]
        
        elif command in ['testui', 'testuif', 'testhttp', 'testhttpf', 'testi']:
            test_keywords = ['test', 'browser', 'api', 'ui', 'functionality']
            parsed['keywords'] = [kw for kw in test_keywords if kw in args.lower()]
        
        return parsed
    
    def _determine_user_intent(self, command: str, args: str) -> str:
        """Determine the user's intent behind the command."""
        args_lower = args.lower()
        
        intent_patterns = {
            'fix_problem': ['fix', 'debug', 'solve', 'issue', 'problem', 'error', 'bug'],
            'implement_feature': ['implement', 'create', 'build', 'add', 'new'],
            'improve_existing': ['improve', 'enhance', 'optimize', 'refactor', 'update'],
            'test_functionality': ['test', 'verify', 'check', 'validate'],
            'analyze_code': ['analyze', 'review', 'examine', 'investigate'],
            'manage_workflow': ['merge', 'push', 'branch', 'integrate']
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in args_lower for keyword in keywords):
                return intent
        
        # Default based on command
        command_intents = {
            'execute': 'implement_feature',
            'e': 'implement_feature', 
            'plan': 'implement_feature',
            'testui': 'test_functionality',
            'testuif': 'test_functionality',
            'testhttp': 'test_functionality',
            'review': 'analyze_code',
            'push': 'manage_workflow',
            'pr': 'manage_workflow'
        }
        
        return command_intents.get(command, 'general_task')
    
    def _assess_command_complexity(self, command: str, args: str) -> str:
        """Assess the complexity level of the command."""
        
        # High complexity indicators
        high_indicators = [
            'architecture', 'system', 'comprehensive', 'entire', 'full',
            'complex', 'advanced', 'integration', 'migration'
        ]
        
        # Medium complexity indicators
        medium_indicators = [
            'implement', 'create', 'build', 'multiple', 'several',
            'api', 'database', 'feature', 'enhancement'
        ]
        
        # Low complexity indicators
        low_indicators = [
            'fix', 'simple', 'small', 'quick', 'minor', 'single'
        ]
        
        args_lower = args.lower()
        
        # Count matches
        high_score = sum(1 for indicator in high_indicators if indicator in args_lower)
        medium_score = sum(1 for indicator in medium_indicators if indicator in args_lower)
        low_score = sum(1 for indicator in low_indicators if indicator in args_lower)
        
        # Word count factor
        word_count = len(args.split())
        
        if high_score >= 1 or word_count > 15:
            return "High"
        elif medium_score >= 1 or word_count > 8:
            return "Medium"
        elif low_score >= 1 or word_count <= 5:
            return "Low"
        else:
            return "Medium"
    
    def _should_consult_memory(self, command: str, args: str, complexity: str) -> bool:
        """Determine if memory consultation is beneficial for this command."""
        
        # Always consult for high complexity
        if complexity == "High":
            return True
        
        # Always consult for execution commands
        if command in ['execute', 'e', 'plan']:
            return True
        
        # Consult for testing commands if they mention specific functionality
        if command.startswith('test') and len(args.split()) > 3:
            return True
        
        # Consult for git operations
        if command in ['push', 'pr', 'integrate', 'newbranch']:
            return True
        
        # Consult for learning commands
        if command == 'learn':
            return True
        
        return False
    
    def consult_memory(self, context: CommandContext) -> Optional[MemoryGuidance]:
        """Consult memory patterns for the given command context."""
        
        if not context.requires_memory:
            return None
        
        # Get command-specific pattern query function
        query_func = self.command_patterns.get(context.command_name, self._query_generic_patterns)
        
        # Query patterns
        result = query_func(context)
        
        if not result or not result.matches:
            return None
        
        # Extract guidance
        guidance = MemoryGuidance(
            patterns_found=result.matches,
            recommendations=[],
            critical_warnings=[],
            preferred_approaches=[],
            avoid_patterns=[]
        )
        
        # Categorize patterns
        for match in result.matches:
            pattern = match.pattern
            
            if pattern.pattern_type == "correction" and pattern.confidence >= 0.8:
                guidance.critical_warnings.append(pattern.content)
            
            elif pattern.pattern_type == "preference":
                guidance.preferred_approaches.append(pattern.content)
            
            elif pattern.pattern_type == "workflow":
                guidance.recommendations.append(f"Follow workflow: {pattern.content}")
            
            elif "avoid" in pattern.content.lower() or "don't" in pattern.content.lower():
                guidance.avoid_patterns.append(pattern.content)
            
            else:
                guidance.recommendations.append(pattern.content)
        
        return guidance
    
    def _query_generic_patterns(self, context: CommandContext) -> QueryResult:
        """Generic pattern query for commands without specific handlers."""
        query = f"{context.command_name} {context.raw_args} command usage"
        return self.query_engine.query_patterns(query, limit=3)
    
    def format_memory_guidance(self, guidance: Optional[MemoryGuidance]) -> str:
        """Format memory guidance for display."""
        
        if not guidance or not guidance.patterns_found:
            return "🧠 **Memory Consultation**: No relevant patterns found."
        
        output = []
        output.append("🧠 **MEMORY CONSULTATION RESULTS**:")
        output.append(f"Found {len(guidance.patterns_found)} relevant patterns")
        
        if guidance.critical_warnings:
            output.append("\n🚨 **CRITICAL WARNINGS** (High-confidence corrections):")
            for warning in guidance.critical_warnings:
                output.append(f"  ⚠️ {warning[:100]}...")
        
        if guidance.preferred_approaches:
            output.append("\n🎯 **PREFERRED APPROACHES** (User preferences):")
            for approach in guidance.preferred_approaches:
                output.append(f"  • {approach[:100]}...")
        
        if guidance.recommendations:
            output.append("\n💡 **RECOMMENDATIONS** (Learned patterns):")
            for rec in guidance.recommendations[:3]:  # Limit to top 3
                output.append(f"  • {rec[:100]}...")
        
        if guidance.avoid_patterns:
            output.append("\n❌ **AVOID PATTERNS** (Known issues):")
            for avoid in guidance.avoid_patterns:
                output.append(f"  • {avoid[:100]}...")
        
        return "\n".join(output)
    
    def process_command(self, command: str, args: str) -> str:
        """Process a command with memory awareness."""
        
        # Analyze command context
        context = self.analyze_command_context(command, args)
        
        # Consult memory patterns
        guidance = self.consult_memory(context)
        
        # Format memory guidance
        memory_section = self.format_memory_guidance(guidance)
        
        # Generate command-specific response
        if command in ['execute', 'e']:
            return self.execute_wrapper.enhanced_execute(args, "execute") + f"\n\n{memory_section}"
        
        elif command == 'plan':
            return self.execute_wrapper.enhanced_execute(args, "plan") + f"\n\n{memory_section}"
        
        else:
            # Generic memory-aware response
            response_parts = []
            response_parts.append(f"Processing `/{command}` command with memory awareness...")
            response_parts.append(f"**Task**: {args}")
            response_parts.append(f"**Complexity**: {context.complexity_level}")
            response_parts.append(f"**Intent**: {context.user_intent}")
            response_parts.append("")
            response_parts.append(memory_section)
            
            if guidance and (guidance.critical_warnings or guidance.preferred_approaches):
                response_parts.append("\n✅ **Memory patterns will be applied during execution.**")
            
            return "\n".join(response_parts)


def main():
    """Example usage of memory-aware command processing."""
    processor = MemoryAwareCommandProcessor()
    
    # Test different command types
    test_commands = [
        ("execute", "implement user authentication with OAuth"),
        ("testui", "test the login form functionality"),
        ("push", "push changes to feature branch"),
        ("learn", "always use headless=True for browser tests"),
        ("review", "analyze the code quality of the API module")
    ]
    
    for command, args in test_commands:
        print(f"\n{'='*80}")
        print(f"Command: /{command} {args}")
        print('='*80)
        result = processor.process_command(command, args)
        print(result)


if __name__ == "__main__":
    main()