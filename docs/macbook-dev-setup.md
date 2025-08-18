# MacBook Dev Environment Setup Guide

This guide provides a comprehensive setup script for replicating the complete development environment used for WorldArchitect.AI on a new MacBook. Based on the current development environment analysis.

## Prerequisites

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (for Apple Silicon Macs)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"

# For Intel Macs, use:
# echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
```

## Core Development Tools

### System Package Managers & Tools
```bash
# Essential development tools
brew install git
brew install gh  # GitHub CLI
brew install pup  # HTML/XML parser

# Python development
brew install python@3.12

# Node.js via NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc
nvm install 20.19.4
nvm use 20.19.4
nvm alias default 20.19.4

# Rust development
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

## Claude Code & AI Development Tools

### Claude Code CLI Setup
```bash
# Install Claude Code CLI locally
mkdir -p ~/.claude/local
cd ~/.claude/local

# Note: Replace with actual installation method for Claude Code CLI
# This may require downloading from Anthropic or installing via npm
npm install -g claude-code

# Claude Code Router
npm install -g @musistudio/claude-code-router@1.0.38

# Claude Usage Monitor
pip3 install claude-usage-monitor
```

### AI/LLM Development Tools
```bash
# Gemini CLI
npm install -g @google/gemini-cli@0.1.18

# Qwen Code (Cerebras integration)
npm install -g @qwen-code/qwen-code@0.0.7

# Claude Code Enhanced
npm install -g claude-code-enhanced

# Usage monitoring
npm install -g ccusage@15.6.0
```

## Development Utilities

### Search & Productivity Tools
```bash
# DuckDuckGo Search CLI
npm install -g @oevortex/ddg_search@1.1.1

# Git workflow enhancement
npm install -g @withgraphite/graphite-cli@1.6.7

# Code scheduling (Rust tool)
cargo install claude-code-schedule
```

### Additional Python Tools
```bash
# UV (Fast Python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Pytest for testing
pip3 install pytest

# RunPod CLI (for cloud GPU instances)
pip3 install runpod

# VastAI CLI (for cloud GPU instances)
pip3 install vastai
```

## Environment Configuration

### Shell Configuration (~/.zshrc)
```bash
# Add this to your ~/.zshrc file

# SSH Agent Management
if ! pgrep -u "$USER" ssh-agent > /dev/null; then
    ssh-agent -s > ~/.ssh/agent_env
fi
if [ -f ~/.ssh/agent_env ]; then
    . ~/.ssh/agent_env > /dev/null
fi

# Project-specific aliases
alias wa='cd ~/projects/worldarchitect.ai'
alias push="git add . ; git commit -a -m \"a\" ; git push"
alias commit='git commit -a -m "a" && git push'
alias status='git status'
alias add='git add .'
alias integrate='./integrate.sh'

# Claude Code aliases
alias claudedanger='claude --dangerously-skip-permissions --model sonnet'
alias claudep='source ./claude_start.sh'
alias claudepw='source ./claude_start.sh --worker'
alias claudeps='source ./claude_start.sh --supervisor'
alias claudepd='source ./claude_start.sh --default'
alias claudepq='source ./claude_start.sh --qwen'
alias claudepc="./claude_start.sh --cerebras"

# Development tool aliases
alias cm='claude-monitor --plan max20 --timezone PST'
alias qwend="qwen --yolo"
alias code="cursor"  # If using Cursor editor
alias h='history | grep'

# Auto-navigate to project
if [ "$PWD" = "$HOME" ]; then
    cd ~/projects/worldarchitect.ai
fi

# Path additions
export PATH="$HOME/.cargo/bin:$HOME/.claude/local:$HOME/.local/bin:$PATH"

# NVM setup
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

### Python Virtual Environment Function
```bash
# Add this function to ~/.zshrc for project-specific Python environment
vpython() {
    PROJECT_ROOT_PATH="$HOME/projects/worldarchitect.ai"
    VENV_ACTIVATE_SCRIPT="$PROJECT_ROOT_PATH/venv/bin/activate"
    if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
        echo "Error: Virtual environment activate script not found at $VENV_ACTIVATE_SCRIPT"
        echo "Please create the virtual environment first: cd $PROJECT_ROOT_PATH && python3 -m venv venv"
        return 1
    fi
    if [[ "$VIRTUAL_ENV" != "$PROJECT_ROOT_PATH/venv" ]]; then
        echo "Activating virtual environment: $PROJECT_ROOT_PATH/venv"
        source "$VENV_ACTIVATE_SCRIPT"
    else
        echo "Virtual environment already active."
    fi
    echo "Running python $*"
    python "$@"
}
```

## Environment Variables Setup

### Create ~/.env_secrets file (DO NOT COMMIT TO GIT)
```bash
# Create a secure file for API keys and secrets
touch ~/.env_secrets
chmod 600 ~/.env_secrets

# Add to ~/.env_secrets (replace with your actual keys):
export CLAUDE_API_KEY="your-claude-api-key-here"
export NOTION_KEY="your-notion-key-here"
export GEMINI_API_KEY="your-gemini-api-key-here"
export CEREBRAS_API_KEY="your-cerebras-api-key-here"
export OPENAI_API_KEY="your-openai-compatible-key-here"
export OPENAI_BASE_URL="https://api.cerebras.ai/v1"
export OPENAI_MODEL="qwen-3-coder-480b"
export RUNPOD_API_KEY="your-runpod-key-here"
export EMAIL_USER="your-email-here"
export EMAIL_PASS="your-app-password-here"

# Firebase Configuration (replace with your project)
export FIREBASE_API_KEY="your-firebase-api-key"
export FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
export FIREBASE_PROJECT_ID="your-project-id"
export FIREBASE_STORAGE_BUCKET="your-project.firebasestorage.app"
export FIREBASE_MESSAGING_SENDER_ID="your-sender-id"
export FIREBASE_APP_ID="your-app-id"
export FIREBASE_MEASUREMENT_ID="your-measurement-id"
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

### Load secrets in shell configuration
```bash
# Add to ~/.zshrc
if [ -f ~/.env_secrets ]; then
    source ~/.env_secrets
fi

# Claude Code configuration
export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=20000

# Test credentials
export TEST_EMAIL="test@example.com"
export TEST_PASSWORD="testpassword"
```

## SSH Setup

### Generate SSH Key
```bash
# Generate Ed25519 SSH key (recommended)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard (macOS)
pbcopy < ~/.ssh/id_ed25519.pub

# Add to GitHub/GitLab/etc.
# Paste the copied key in your Git provider's SSH settings
```

## Project Setup

### Clone and Setup WorldArchitect.AI
```bash
# Create projects directory
mkdir -p ~/projects
cd ~/projects

# Clone the repository (replace with your fork)
git clone git@github.com:your-username/worldarchitect.ai.git
cd worldarchitect.ai

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install project-specific tools
npm install  # If package.json exists

# Set up pre-commit hooks (if configured)
# pre-commit install
```

## Verification Script

### Test Installation
```bash
#!/bin/bash
# Save as verify_setup.sh and run: chmod +x verify_setup.sh && ./verify_setup.sh

echo "🔍 Verifying MacBook Dev Setup..."

# Check core tools
echo "📝 Core Tools:"
which git && git --version
which gh && gh --version
which python3 && python3 --version
which node && node --version
which npm && npm --version
which cargo && cargo --version
which brew && brew --version

echo ""
echo "🤖 AI Development Tools:"
which claude 2>/dev/null && echo "✅ Claude CLI installed" || echo "❌ Claude CLI missing"
which qwen 2>/dev/null && echo "✅ Qwen CLI installed" || echo "❌ Qwen CLI missing"
pip3 show claude-usage-monitor > /dev/null && echo "✅ Claude Usage Monitor installed" || echo "❌ Claude Usage Monitor missing"

echo ""
echo "🔧 Development Utilities:"
which uv 2>/dev/null && echo "✅ UV installed" || echo "❌ UV missing"
which pytest 2>/dev/null && echo "✅ Pytest installed" || echo "❌ Pytest missing"
which runpod 2>/dev/null && echo "✅ RunPod CLI installed" || echo "❌ RunPod CLI missing"

echo ""
echo "🔑 Environment Variables:"
[ -n "$CLAUDE_API_KEY" ] && echo "✅ CLAUDE_API_KEY set" || echo "❌ CLAUDE_API_KEY missing"
[ -n "$GEMINI_API_KEY" ] && echo "✅ GEMINI_API_KEY set" || echo "❌ GEMINI_API_KEY missing"
[ -n "$FIREBASE_PROJECT_ID" ] && echo "✅ Firebase config set" || echo "❌ Firebase config missing"

echo ""
echo "📁 Project Structure:"
[ -d "~/projects/worldarchitect.ai" ] && echo "✅ Project directory exists" || echo "❌ Project directory missing"
[ -f "~/.ssh/id_ed25519" ] && echo "✅ SSH key exists" || echo "❌ SSH key missing"

echo ""
echo "🎉 Setup verification complete!"
```

## Next Steps

1. **Run the verification script** to ensure all tools are properly installed
2. **Configure your IDE/Editor** with appropriate extensions for Python, JavaScript, and AI development
3. **Set up Claude Code workspace** in your project directory
4. **Configure Firebase credentials** for your specific project
5. **Test the development workflow** by running the project's test suite

## Security Notes

- Never commit API keys or secrets to version control
- Use environment variables for all sensitive configuration
- Regularly rotate API keys and access tokens
- Keep your SSH keys secure and use passphrases
- Use `chmod 600` for files containing secrets

## Troubleshooting

### Common Issues

1. **Permission denied for SSH**: Ensure SSH key is added to ssh-agent and GitHub
2. **Command not found**: Check PATH configuration and reload shell
3. **Python import errors**: Verify virtual environment is activated
4. **API rate limits**: Ensure proper API key configuration and usage monitoring

### Getting Help

- Check the project's README for specific setup instructions
- Review the `.claude/` directory for project-specific configurations
- Consult the development team's documentation in `docs/`
- Use Claude Code CLI help: `claude --help`

---

*This setup guide is based on the development environment analysis performed on 2025-08-18. Tools and versions may need updates over time.*