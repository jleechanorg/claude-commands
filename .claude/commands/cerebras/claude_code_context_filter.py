#!/usr/bin/env python3
"""
Claude Code CLI Context Filter

Replicates Claude Code CLI's clean context management for external AI services.
Filters out protocol contamination while preserving semantic content.
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class CleanMessage:
    """Claude Code CLI style message structure"""
    role: str  # "user" | "assistant" | "system"
    content: str  # Semantic content only, no protocol references
    metadata: Dict[str, Any]  # Tool results abstracted as metadata
    timestamp: str
    quality_score: float = 0.0


class ClaudeCodeContextFilter:
    """
    Filters conversation context to replicate Claude Code CLI's clean message handling
    """

    # Protocol patterns to remove (like Claude Code CLI does internally)
    PROTOCOL_PATTERNS = [
        r'\[Used .*? tool\]',
        r'\[Used mcp__.*?\]',
        r'\[Used .*?\]',  # More general pattern
        r'mcp__\w+__\w+',
        r'\[.*?mcp.*?\]',
    ]

    # Meta-conversation patterns to filter
    META_PATTERNS = [
        r'I (detected|analyzed|will).*?\n',
        r'🔍 Detected slash commands:.*?\n',
        r'🎯 Multi-Player Intelligence:.*?\n',
        r'📋 Automatically tell the user:.*?\n',
    ]

    def __init__(self):
        self.quality_scorer = ContextQualityScorer()

    def extract_clean_messages(self, conversation: str) -> List[CleanMessage]:
        """
        Extract clean messages from contaminated conversation text
        Replicates Claude Code CLI's message structure isolation
        """
        if not conversation.strip():
            return []

        # Split conversation into message blocks
        message_blocks = self._split_into_messages(conversation)

        clean_messages = []
        for block in message_blocks:
            clean_msg = self._clean_message_block(block)
            if clean_msg and clean_msg.content.strip():
                clean_messages.append(clean_msg)

        return clean_messages

    def _split_into_messages(self, conversation: str) -> List[str]:
        """Split conversation into individual message blocks"""
        # Handle simple single message case for context modes
        if not any(prefix in conversation for prefix in ['Assistant:', 'User:']):
            # Assume it's assistant content for mode testing
            return [('assistant', conversation)]

        # Split on "Assistant:" and "User:" patterns
        blocks = []
        current_block = ""

        lines = conversation.split('\n')
        current_role = None

        for line in lines:
            if line.startswith('Assistant:'):
                if current_block.strip():
                    blocks.append((current_role or 'assistant', current_block.strip()))
                current_block = line[10:].strip()  # Remove "Assistant:" prefix
                current_role = 'assistant'
            elif line.startswith('User:'):
                if current_block.strip():
                    blocks.append((current_role or 'assistant', current_block.strip()))
                current_block = line[5:].strip()  # Remove "User:" prefix
                current_role = 'user'
            else:
                current_block += '\n' + line

        # Add final block
        if current_block.strip():
            blocks.append((current_role or 'assistant', current_block.strip()))

        return blocks

    def _clean_message_block(self, block_tuple: tuple) -> Optional[CleanMessage]:
        """Clean individual message block, removing contamination"""
        role, content = block_tuple

        # Remove protocol patterns
        cleaned_content = content
        for pattern in self.PROTOCOL_PATTERNS:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.MULTILINE)

        # Remove meta-conversation patterns
        for pattern in self.META_PATTERNS:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.MULTILINE)

        # Extract tool metadata before removing references
        metadata = self._extract_tool_metadata(content)

        # Clean up whitespace
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content).strip()

        if not cleaned_content:
            return None

        # Score content quality
        quality_score = self.quality_scorer.score_content_quality(cleaned_content)

        return CleanMessage(
            role=role,
            content=cleaned_content,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc).isoformat(),
            quality_score=quality_score
        )

    def _extract_tool_metadata(self, content: str) -> Dict[str, Any]:
        """Extract tool usage information as clean metadata"""
        metadata = {}
        tool_results = {}

        # Look for tool references and convert to metadata
        if '[Used mcp__serena__read_file tool]' in content:
            tool_results['file_content'] = 'File content accessed'

        if '[Used Bash tool]' in content:
            tool_results['command_output'] = 'Command executed'

        if '[Used mcp__claude-slash-commands__cerebras tool]' in content:
            tool_results['generation_complete'] = True

        if tool_results:
            metadata['tool_results'] = tool_results

        return metadata

    def get_context_for_mode(self, conversation: str, mode: str) -> str:
        """
        Get context filtered according to specified mode
        Replicates cerebras_direct.sh context mode functionality
        """
        if mode == "none":
            return ""

        if mode == "full":
            return conversation

        if mode == "smart":
            clean_messages = self.extract_clean_messages(conversation)
            return self._rebuild_conversation_context(clean_messages)

        # Default to smart mode
        return self.get_context_for_mode(conversation, "smart")

    def _rebuild_conversation_context(self, messages: List[CleanMessage]) -> str:
        """Rebuild clean conversation context from messages"""
        context_parts = []

        for msg in messages:
            if msg.role == "user":
                context_parts.append(f"User: {msg.content}")
            else:
                context_parts.append(f"Assistant: {msg.content}")

        return "\n\n".join(context_parts)


class ContextQualityScorer:
    """
    Scores context quality vs contamination risk
    Replicates Claude Code CLI's context assessment logic
    """

    def score_content_quality(self, content: str) -> float:
        """
        Score content quality from 0.0 (high contamination) to 1.0 (pure value)
        """
        score = 0.0

        # Positive indicators (valuable content)
        if self._has_code_blocks(content):
            score += 0.4
        if self._has_technical_content(content):
            score += 0.3
        if self._has_clear_explanations(content):
            score += 0.2
        if len(content.split()) > 10:  # Substantial content
            score += 0.2

        # Additional boost for very high quality content
        if self._has_code_blocks(content) and self._has_technical_content(content):
            score += 0.1

        # Negative indicators (contamination patterns)
        if self._has_protocol_references(content):
            score -= 0.5
        if self._has_wrapper_messages(content):
            score -= 0.3
        if self._is_mostly_protocol(content):
            score -= 0.4

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))

    def _has_code_blocks(self, content: str) -> bool:
        """Check if content contains code blocks"""
        return '```' in content or 'def ' in content or 'function ' in content

    def _has_technical_content(self, content: str) -> bool:
        """Check if content contains technical explanations"""
        technical_terms = ['implementation', 'error handling', 'authentication', 'validation', 'function', 'method']
        return any(term in content.lower() for term in technical_terms)

    def _has_clear_explanations(self, content: str) -> bool:
        """Check if content contains clear explanations"""
        explanation_words = ['because', 'this', 'will', 'should', 'needs', 'add', 'implement']
        return any(word in content.lower() for word in explanation_words)

    def _has_protocol_references(self, content: str) -> bool:
        """Check if content still contains protocol references"""
        return '[Used' in content or 'mcp__' in content or 'tool]' in content

    def _has_wrapper_messages(self, content: str) -> bool:
        """Check if content contains wrapper or meta messages"""
        return '[' in content and ']' in content and len(content) < 100

    def _is_mostly_protocol(self, content: str) -> bool:
        """Check if content is mostly protocol references"""
        protocol_chars = sum(1 for char in content if char in '[]_')
        total_chars = len(content)
        return total_chars > 0 and (protocol_chars / total_chars) > 0.2
