#!/usr/bin/env python3
"""
Extract recent conversation context for Cerebras API calls.
Reads from ~/.claude/projects and returns the most recent 20K tokens of conversation.
"""

import os
import json
import glob
import hashlib
from pathlib import Path
from datetime import datetime
import sys
import re

# Module-level constant to avoid duplication
DEFAULT_MAX_TOKENS = 20000

_SECRET_PATTERNS = [
    re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'),           # common API key prefix
    re.compile(r'\b[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{27,}\b'),  # JWT-like
    re.compile(r'(?i)\b(api[_\- ]?key|token|secret)\s*[:=]\s*[^\s]+'),
]

def _redact(s):
    """Redact potential secrets from conversation content"""
    redacted = s
    for pat in _SECRET_PATTERNS:
        redacted = pat.sub('[REDACTED]', redacted)
    return redacted

def _sanitize_path(path):
    """Convert path to unique, hash-based format to prevent collisions"""
    # Use a short hash of the absolute path to avoid collisions
    cwd_hash = hashlib.sha256(path.encode('utf-8')).hexdigest()[:12]
    return f"{Path(path).name}-{cwd_hash}"

def estimate_tokens(text):
    """Rough token estimation: ~4 characters per token"""
    return len(text) // 4

def _extract_content_text(content):
    """Extract text content from various message formats"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from Claude's message structure
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown_tool')
                    text_parts.append(f"[Used {tool_name} tool]")
            else:
                text_parts.append(str(item))
        return '\n'.join(text_parts)
    else:
        return str(content)

def _format_message_text(message):
    """Format a message with role, timestamp, and content"""
    timestamp = message.get('timestamp', '')
    timestamp_str = f" ({timestamp})" if timestamp else ""
    return f"\n## {message['role'].title()}{timestamp_str}\n{message['content']}\n"

def extract_conversation_context(max_tokens=DEFAULT_MAX_TOKENS):
    """
    Extract recent conversation context from Claude Code CLI history.
    Returns formatted context string limited to max_tokens.
    """
    
    # Find current project directory in ~/.claude/projects
    projects_dir = Path.home() / '.claude' / 'projects'
    current_cwd = os.getcwd()
    
    # Convert current working directory to unique sanitized format
    # e.g., /Users/$USER/projects/your-project.com/worktree_cereb -> worktree_cereb-a1b2c3d4e5f6  
    sanitized_cwd = _sanitize_path(current_cwd)
    project_dir = projects_dir / sanitized_cwd
    
    if not project_dir.exists():
        # Fallback: try multiple patterns to find matching directory across platforms
        current_name = Path(current_cwd).name
        
        # Cross-platform fallback patterns
        # Claude Code CLI converts path separators to hyphens, so we need to handle:
        # /path/to/worktree_cereb -> -path-to-worktree-cereb (but also worktree_cereb -> worktree-cereb)
        hyphenated_name = current_name.replace('_', '-')
        patterns = [
            f"*{current_name}*",                    # Original pattern: *worktree_cereb*  
            f"*{hyphenated_name}*",                 # Hyphenated pattern: *worktree-cereb*
            f"*-{hyphenated_name}",                 # End pattern: *-worktree-cereb
            f"*-{hyphenated_name}-*",               # Middle pattern: *-worktree-cereb-*
        ]
        
        matches = []
        for pattern in patterns:
            pattern_matches = list(projects_dir.glob(pattern))
            if pattern_matches:
                matches.extend(pattern_matches)
                break  # Use first successful pattern
        
        if matches:
            # Sort by modification time, use most recent
            project_dir = max(matches, key=lambda d: d.stat().st_mtime)
        else:
            print("No conversation history found for current project", file=sys.stderr)
            return ""
    
    # Find most recent conversation file
    jsonl_files = list(project_dir.glob('*.jsonl'))
    if not jsonl_files:
        print("No conversation files found", file=sys.stderr)
        return ""
    
    # Use most recently modified file
    latest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)
    
    try:
        messages = []
        
        # Read JSONL file line by line
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    # Extract message content based on record type
                    if record.get('type') == 'user' and 'message' in record:
                        content = _extract_content_text(record['message'].get('content', ''))
                        
                        if content and content.strip():
                            messages.append({
                                'role': 'user',
                                'content': _redact(content),
                                'timestamp': record.get('timestamp', '')
                            })
                    
                    elif record.get('type') == 'assistant' and 'message' in record:
                        content = _extract_content_text(record['message'].get('content', ''))
                        
                        if content and content.strip():
                            messages.append({
                                'role': 'assistant', 
                                'content': _redact(content),
                                'timestamp': record.get('timestamp', '')
                            })
                            
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
        
        # Build context string, working backwards from most recent
        context_lines = [
            "# Recent Conversation Context",
            "",
            "This is the recent conversation history that led to the current task:",
            ""
        ]
        
        total_tokens = estimate_tokens('\n'.join(context_lines))
        
        # Collect messages that fit within token limit (working backwards from most recent)
        selected_messages = []
        for message in reversed(messages):
            message_text = _format_message_text(message)
            message_tokens = estimate_tokens(message_text)
            
            if total_tokens + message_tokens > max_tokens:
                break
                
            selected_messages.append(message)
            total_tokens += message_tokens
        
        # Sort selected messages chronologically (oldest first) based on timestamp
        selected_messages.sort(key=lambda m: m.get('timestamp', ''))
        
        # Add sorted messages to context in chronological order
        for message in selected_messages:
            message_text = _format_message_text(message)
            context_lines.append(message_text)
        
        # If we have context, format it nicely
        if len(context_lines) > 4:  # More than just headers
            context_lines.append(f"\n---\n*Context extracted from: {latest_file.name}*")
            context_lines.append(f"*Estimated tokens: {total_tokens:,}*")
            return '\n'.join(context_lines)
        else:
            return ""
            
    except Exception as e:
        print(f"Error extracting conversation context: {e}", file=sys.stderr)
        return ""

if __name__ == '__main__':
    max_tokens = DEFAULT_MAX_TOKENS
    if len(sys.argv) > 1:
        try:
            max_tokens = int(sys.argv[1])
        except ValueError:
            pass
    
    context = extract_conversation_context(max_tokens)
    print(context)