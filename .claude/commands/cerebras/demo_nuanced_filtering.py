#!/usr/bin/env python3
"""
Demo: Nuanced Context Filtering
Shows how the system handles different types of content intelligently
"""

from claude_code_context_filter import ClaudeCodeContextFilter, ContextQualityScorer

def test_different_content_types():
    """Test the system with various content types to show nuanced handling"""

    filter = ClaudeCodeContextFilter()
    scorer = ContextQualityScorer()

    test_cases = [
        {
            "name": "High Value Technical",
            "content": """Assistant: Here's the implementation:

```python
def secure_auth(user, pwd):
    if not user or len(pwd) < 8:
        raise ValueError("Invalid credentials")
    return hash_password(pwd) == stored_hash
```

This adds proper validation and security."""
        },

        {
            "name": "Mixed Contamination",
            "content": """Assistant: I'll check the file.

[Used mcp__serena__read_file tool]

The authentication code looks good:

```python
def auth():
    return True
```

[Used another tool]

This should work for your needs."""
        },

        {
            "name": "Heavy Contamination",
            "content": """[Used tool1] [Used tool2] [Used mcp__tool] Basic response."""
        },

        {
            "name": "Pure Discussion",
            "content": """User: What's the best approach for authentication?
