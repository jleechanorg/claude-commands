#!/usr/bin/env python3
"""
Demo: Nuanced Context Filtering - NOT Black & White
Shows intelligent extraction of valuable content from contaminated conversations
"""

from claude_code_context_filter import ClaudeCodeContextFilter, ContextQualityScorer

def demo_nuanced_filtering():
    """Show how the system intelligently handles different content types"""

    filter = ClaudeCodeContextFilter()
    scorer = ContextQualityScorer()

    test_cases = [
        {
            "name": "🟢 High Value Technical",
            "content": """Assistant: Here's a secure authentication implementation:

```python
def secure_auth(user, password):
    if not user or len(password) < 8:
        raise ValueError("Invalid credentials")
    return hash_password(password) == stored_hash
```

This adds proper validation and security checks.""",
            "expected": "KEEP - has code + technical explanation"
        },

        {
            "name": "🟡 Mixed Quality (Contaminated but Valuable)",
            "content": """Assistant: I'll check the authentication file.

[Used mcp__serena__read_file tool]

The current code has security issues:

```python
def authenticate(user, pwd):
    return user == "admin"  # BAD: hardcoded check
```

[Used Bash tool]

Here's the improved version with proper security.""",
            "expected": "FILTER & KEEP - remove protocol refs, keep valuable analysis"
        },

        {
            "name": "🔴 Heavy Contamination",
            "content": """[Used tool1] [Used tool2] [Used mcp__cerebras tool] Basic response with no value.""",
            "expected": "REJECT - mostly protocol with minimal value"
        },

        {
            "name": "🟢 Pure Technical Discussion",
            "content": """User: What authentication method should we use for the API?
Assistant: For API authentication, I recommend JWT tokens with:
1. Short expiration times (15-30 minutes)
2. Refresh token rotation
3. Rate limiting per user
4. HTTPS enforcement

This provides good security without being overly complex.""",
            "expected": "KEEP - pure technical discussion, high value"
        }
    ]

    print("🧠 NUANCED CONTEXT FILTERING DEMO")
    print("=" * 80)
    print("This shows the system is NOT black & white - it intelligently extracts value")
    print()

    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Expected: {case['expected']}")
        print()

        # Show original
        print(f"   📝 ORIGINAL ({len(case['content'])} chars):")
        print(f"   {repr(case['content'][:100])}...")
        print()

        # Process with our intelligent filter
        clean_messages = filter.extract_clean_messages(case['content'])

        if clean_messages:
            clean_context = filter._rebuild_conversation_context(clean_messages)
            quality = scorer.score_content_quality(clean_context)

            print(f"   🎯 FILTERED RESULT:")
            print(f"   Quality Score: {quality:.2f}")
            print(f"   Length: {len(clean_context)} chars")
            print(f"   Protocol Refs Removed: {'[Used' not in clean_context}")
            print(f"   Valuable Content Preserved: {len(clean_context) > 50}")
            print(f"   Preview: {repr(clean_context[:100])}...")
        else:
            print(f"   🎯 RESULT: Rejected (no valuable content found)")

        print()
        print("-" * 60)
        print()

if __name__ == "__main__":
    demo_nuanced_filtering()
