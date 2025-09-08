#!/usr/bin/env python3
"""
Demo: Intelligent Conversation Parsing
Shows how the system extracts valuable content while filtering contamination
"""

from claude_code_context_filter import ClaudeCodeContextFilter, ContextQualityScorer

def demo_intelligent_parsing():
    contaminated_conversation = """Assistant: I'll help you implement the authentication system.

[Used mcp__serena__read_file tool]

Looking at the current implementation in auth.py:

```python
def authenticate(user_id, password):
    # Current implementation is basic
    return validate_credentials(user_id, password)
```

This code has several issues:
1. No error handling for invalid inputs
2. No logging for security events
3. Missing input validation

User: Can you add proper error handling?

[Used Bash tool]

I'll add comprehensive error handling with proper validation:

```python
def authenticate(user_id, password):
    try:
        if not user_id or not password:
            raise ValueError("Missing credentials")

        # Log security event
        logger.info(f"Authentication attempt for user: {user_id}")

        return validate_credentials(user_id, password)
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return False
```

This improved version handles edge cases properly."""

    filter = ClaudeCodeContextFilter()
    scorer = ContextQualityScorer()

    print("🧠 INTELLIGENT CONVERSATION PARSING DEMO")
    print("=" * 60)
    print()

    # Show original contaminated conversation
    print("📝 ORIGINAL (Contaminated):")
    print(f"Length: {len(contaminated_conversation)} chars")
    print("Contains protocol refs:", "[Used" in contaminated_conversation)
    print()

    # Extract clean messages
    clean_messages = filter.extract_clean_messages(contaminated_conversation)

    print(f"🎯 EXTRACTED MESSAGES: {len(clean_messages)}")
    print("-" * 40)

    for i, msg in enumerate(clean_messages, 1):
        print(f"\n📧 Message {i} ({msg.role.upper()}):")
        print(f"   Quality Score: {msg.quality_score:.2f}")
        print(f"   Length: {len(msg.content)} chars")
        print(f"   Has Code: {'✅' if '```' in msg.content else '❌'}")
        print(f"   Has Technical Terms: {'✅' if any(term in msg.content.lower() for term in ['implementation', 'error', 'validation']) else '❌'}")
        print(f"   Protocol Refs Removed: {'✅' if '[Used' not in msg.content else '❌'}")
        print(f"   Tool Metadata: {msg.metadata}")
        print(f"   Content Preview: {msg.content[:100]}...")

    # Show final clean context
    clean_context = filter._rebuild_conversation_context(clean_messages)
    overall_quality = scorer.score_content_quality(clean_context)

    print()
    print("🎯 FINAL CLEAN CONTEXT:")
    print("-" * 40)
    print(f"Overall Quality Score: {overall_quality:.2f}")
    print(f"Length Reduction: {len(contaminated_conversation)} → {len(clean_context)} chars ({((len(contaminated_conversation) - len(clean_context)) / len(contaminated_conversation) * 100):.1f}% reduction)")
    print()
    print("CLEAN CONTEXT OUTPUT:")
    print(clean_context)

if __name__ == "__main__":
    demo_intelligent_parsing()
