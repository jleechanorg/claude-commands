#!/bin/bash
# Self-Reflection Pipeline - Pipes detection results back to Claude for self-correction
# Based on Google's 17% improvement research from AI self-questioning

# Parse detection results and create reflection prompt
DETECTION_OUTPUT="$1"
ORIGINAL_INPUT="$2"

if [[ "$DETECTION_OUTPUT" == *"SPECULATION DETECTED"* ]] || [[ "$DETECTION_OUTPUT" == *"FAKE CODE DETECTED"* ]]; then
    cat << EOF
## Self-Reflection Prompt

I notice my previous response contained quality issues detected by the pattern analysis:

$DETECTION_OUTPUT

Based on this feedback, let me revise my response to:
1. Remove speculative language about system states
2. Replace placeholder/template code with real implementations  
3. Focus on observable facts rather than assumptions
4. Provide functional code that actually works

Here's my improved response:
EOF
else
    # No issues detected - pass through original
    echo "$ORIGINAL_INPUT"
fi