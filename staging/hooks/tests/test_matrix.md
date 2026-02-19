# Test Matrix for compose-commands.sh

## Current Test Coverage (✅ = Implemented)

### Basic Command Processing
✅ Single command passes through unchanged
✅ Multiple commands detected (2 commands)
✅ Composition instruction added
✅ No commands passes through unchanged
✅ Complex text preserved
✅ Three+ commands composed (4 commands)

### Input Formats
✅ Empty prompt handled
✅ Missing prompt field
✅ Text before commands detected
✅ Mixed text and commands preserved

### JSON Handling
✅ Escaped quotes in prompt
✅ Special characters (newlines, tabs, brackets)
✅ Unicode characters
✅ Malformed JSON gracefully handled

### Edge Cases
✅ PR text with file paths (test_pr_text.sh)

## Missing Test Cases to Add (Red-Green TDD)

### 🔴 Command Variations
- [ ] Commands with numbers: `/test123 /debug456`
- [ ] Commands with underscores: `/test_command /debug_mode`
- [ ] Commands with hyphens: `/test-feature /debug-mode`
- [ ] Mixed case commands: `/TEST /Debug /MiXeD`
- [ ] Very long command names: `/verylongcommandnamethatexceedsreasonablelength`

### 🔴 Text Positioning
- [ ] Commands in middle of text: `text before /command1 middle text /command2 text after`
- [ ] Commands at very end: `some text /command1 /command2`
- [ ] Commands with punctuation: `/think, /debug. /analyze!`
- [ ] Commands with parentheses: `(/think /debug) analyze this`
- [ ] Commands in quotes: `"use /think and /debug commands"`

### 🔴 JSON Edge Cases
- [ ] Nested JSON in prompt: `{"prompt": "{\"nested\": \"value\"} /think"}`
- [ ] Array in prompt field: `{"prompt": ["text", "/command"]}`
- [ ] Null prompt: `{"prompt": null}`
- [ ] Numeric prompt: `{"prompt": 123}`
- [ ] Boolean prompt: `{"prompt": true}`

### 🔴 Performance & Scale
- [ ] Very large input (1MB of text)
- [ ] Many commands (20+ slash commands)
- [ ] Deeply nested JSON structure
- [ ] Input with many slashes but few commands: `http://example.com/path/to/file /think`

### 🔴 Security Tests
- [ ] Command injection attempts: `/think && rm -rf /`
- [ ] Path traversal in commands: `/../../etc/passwd`
- [ ] SQL injection patterns: `/think'; DROP TABLE--`
- [ ] Script tags in text: `<script>/alert /xss</script>`

### 🔴 Whitespace Handling
- [ ] Commands with extra spaces: `/think  /debug   /analyze`
- [ ] Tabs between commands: `/think\t/debug`
- [ ] Newlines between commands: `/think\n/debug`
- [ ] Commands with trailing spaces: `/think /debug `

### 🔴 Error Recovery
- [ ] Partial JSON: `{"prompt": "test /comm`
- [ ] Invalid UTF-8 sequences
- [ ] Binary data in input
- [ ] Circular reference attempts

### 🔴 Boundary Conditions
- [ ] Empty commands: `// //`
- [ ] Single slash: `/`
- [ ] Command without text: `/`
- [ ] Maximum command length (test limits)

## Test Implementation Priority

### High Priority (Core Functionality)
1. Commands with numbers/underscores/hyphens
2. Commands in middle of text
3. Null/numeric/boolean prompt values
4. Whitespace handling

### Medium Priority (Robustness)
1. Very large inputs
2. Many commands
3. Security injection tests
4. Nested JSON

### Low Priority (Edge Cases)
1. Binary data
2. Invalid UTF-8
3. Circular references
4. Performance stress tests

## Red-Green-Refactor Process

For each new test:
1. **RED**: Write failing test first
2. **GREEN**: Minimal code to pass
3. **REFACTOR**: Improve implementation

Example workflow:
```bash
# 1. Add test case to test_compose_commands.sh
# 2. Run test - expect failure
bash .claude/hooks/tests/test_compose_commands.sh
# 3. Update compose-commands.sh to handle case
# 4. Run test - expect success
# 5. Refactor if needed
```

## Coverage Goal
- Current: 14 tests
- Target: 40+ tests
- Focus: Real-world edge cases and security