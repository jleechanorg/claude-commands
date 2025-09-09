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

Assistant: For security, I recommend using established libraries like bcrypt for password hashing, implementing proper session management, and adding two-factor authentication when possible. Always validate inputs and use HTTPS."""
        }
    ]

    print("🎯 NUANCED FILTERING DEMO")
    print("=" * 50)
    print()

    for case in test_cases:
        print(f"📝 {case['name']}:")
        print(f"   Original Length: {len(case['content'])} chars")

        # Get quality score
        quality = scorer.score_content_quality(case['content'])
        print(f"   Quality Score: {quality:.2f}")

        # Apply filtering
        clean_messages = filter.extract_clean_messages(case['content'])
        clean_context = filter._rebuild_conversation_context(clean_messages)

        print(f"   Filtered Length: {len(clean_context)} chars")
        print(f"   Size Change: {((len(clean_context) - len(case['content'])) / len(case['content']) * 100):+.1f}%")
        print(f"   Has Code: {'✅' if '```' in clean_context else '❌'}")
        print(f"   Protocol Refs: {'❌' if '[Used' in clean_context else '✅ Clean'}")
        print(f"   Preview: {clean_context[:100]}...")
        print()

if __name__ == "__main__":
    test_different_content_types()
