#!/bin/bash
# Setup aliases for Claude commands in Cursor
# Usage: source setup-aliases.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up Claude command aliases..."

# Git workflow aliases
alias claude-header="$SCRIPT_DIR/header.sh"
alias claude-nb="$SCRIPT_DIR/nb.sh"
alias claude-newbranch="$SCRIPT_DIR/newbranch.sh"
alias claude-push="$SCRIPT_DIR/push.sh"
alias claude-pr="$SCRIPT_DIR/pr.sh"
alias claude-integrate="$SCRIPT_DIR/integrate.sh"

# Testing aliases
alias claude-test="$SCRIPT_DIR/test.sh"
alias claude-testui="$SCRIPT_DIR/testui.sh"
alias claude-testuif="$SCRIPT_DIR/testuif.sh"
alias claude-testhttp="$SCRIPT_DIR/testhttp.sh"
alias claude-testi="$SCRIPT_DIR/testi.sh"
alias claude-coverage="$SCRIPT_DIR/coverage.sh"

# Development aliases
alias claude-tdd="$SCRIPT_DIR/tdd.sh"
alias claude-rg="$SCRIPT_DIR/rg.sh"
alias claude-context="$SCRIPT_DIR/context.sh"
alias claude-learn="$SCRIPT_DIR/learn.sh"

# AI-assisted aliases
alias claude-think="$SCRIPT_DIR/think.sh"
alias claude-execute="$SCRIPT_DIR/execute.sh"
alias claude-e="$SCRIPT_DIR/e.sh"
alias claude-plan="$SCRIPT_DIR/plan.sh"

echo "✅ Aliases set up successfully!"
echo ""
echo "You can now use commands like:"
echo "  claude-test      # Run tests"
echo "  claude-push      # Push changes"
echo "  claude-pr        # Create PR"
echo ""
echo "To make these permanent, add this line to your ~/.bashrc or ~/.zshrc:"
echo "  source $SCRIPT_DIR/setup-aliases.sh"