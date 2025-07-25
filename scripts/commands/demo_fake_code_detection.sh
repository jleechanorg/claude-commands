#!/bin/bash
# Demo script showing how code authenticity detection works

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Code Authenticity Detection Demo ===${NC}"
echo ""
echo "This demo shows what the analyze_code_authenticity.sh script does:"
echo ""

# Show example of fake code
echo -e "${YELLOW}Example 1: Fake Code Pattern${NC}"
cat << 'EOF'
def handle_user_input(input_text):
    """AI-powered response generator"""
    input_lower = input_text.lower()
    
    if 'error' in input_lower:
        return "Thank you for reporting this error!"
    elif 'help' in input_lower:
        return "I'm here to help! What do you need?"
    elif 'bug' in input_lower:
        return "Excellent bug report! We'll investigate."
    else:
        return "I understand. Let me process that."
EOF

echo -e "\n${RED}Why this is FAKE:${NC}"
echo "- Claims to be 'AI-powered' but uses simple keyword matching"
echo "- Hardcoded responses based on keywords"
echo "- No actual processing or intelligence"
echo ""

echo -e "${YELLOW}Example 2: Real Code Pattern${NC}"
cat << 'EOF'
def validate_user_input(input_text):
    """Validate and sanitize user input"""
    if not input_text:
        raise ValueError("Input cannot be empty")
    
    # Remove leading/trailing whitespace
    cleaned = input_text.strip()
    
    # Check length constraints
    if len(cleaned) < 3:
        raise ValueError("Input too short (min 3 chars)")
    if len(cleaned) > 500:
        raise ValueError("Input too long (max 500 chars)")
    
    # Check for SQL injection patterns
    dangerous_patterns = ['DROP TABLE', 'DELETE FROM', '; --']
    for pattern in dangerous_patterns:
        if pattern in cleaned.upper():
            raise SecurityError(f"Dangerous pattern detected: {pattern}")
    
    return cleaned
EOF

echo -e "\n${GREEN}Why this is REAL:${NC}"
echo "- Performs actual validation with specific rules"
echo "- Has real logic based on security requirements"
echo "- Returns processed data, not hardcoded responses"
echo ""

echo -e "${BLUE}How the Script Works:${NC}"
echo "1. Collects all changed code files (Python, JS, TS, Go, etc.)"
echo "2. Creates a markdown file with the code content"
echo "3. Sends to Claude LLM for analysis"
echo "4. Claude identifies fake patterns like:"
echo "   - Hardcoded responses"
echo "   - Keyword-based logic claiming to be AI"
echo "   - Mock implementations"
echo "   - Demo/placeholder code"
echo "5. Returns warning if fake code detected"
echo ""

echo -e "${GREEN}Benefits:${NC}"
echo "✅ Maintains code quality standards"
echo "✅ Catches misleading implementations early"
echo "✅ Non-blocking (developer decides)"
echo "✅ Integrates with learning system"
echo "✅ Uses AI for nuanced understanding"
echo ""

echo -e "${YELLOW}Note:${NC} The script does NOT use keyword matching itself!"
echo "It uses Claude's LLM to understand code semantically."