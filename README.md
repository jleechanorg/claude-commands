# WorldArchitect.AI - AI-Powered Tabletop RPG Platform

> **🏆 Innovation Highlights**: See our [Innovation Summary](README_SUMMARY.md) showcasing breakthrough advances in AI-first development, including industry-first universal command composition and autonomous multi-agent orchestration.

## 🎲 Overview

WorldArchitect.AI is a revolutionary AI-powered platform that serves as your digital Game Master for Dungeons & Dragons 5th Edition experiences. Using advanced language models and sophisticated state management, it delivers dynamic, interactive storytelling that adapts to your choices in real-time - no human DM required.

## ✨ Key Benefits

- **Always Available GM**: Play D&D anytime without coordinating schedules
- **Consistent Rule Enforcement**: AI ensures fair and accurate gameplay
- **Dynamic Storytelling**: Narratives that adapt to your decisions with perfect state synchronization
- **Multiple Play Styles**: Choose from different AI personas for varied experiences
- **Persistent Campaigns**: Your adventures are saved and continue where you left off
- **Export Your Adventures**: Download your campaigns as PDF, DOCX, or TXT files

## 🛠️ Technologies

### Backend
- **Python 3.11** with Flask framework
- **Google Gemini AI** (2.5-flash model)
- **Firebase** (Authentication & Firestore)
- **Docker** containerization
- **Google Cloud Run** deployment

### Frontend
- **Vanilla JavaScript** (ES6+)
- **Bootstrap 5.3.2** responsive UI
- **Multiple theme support** (Light, Dark, Fantasy, Cyberpunk)

### AI & Game Logic
- **Pydantic** structured generation for improved consistency
- **MBTI personality system** for deep character interactions
- **Entity tracking** for narrative consistency
- **Dual-pass generation** for accuracy

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Firebase project with Firestore
- Google Cloud project with Gemini API access

### Installation

```bash
# Clone the repository
git clone https://github.com/jleechan2015/worldarchitect.ai.git
cd worldarchitect-ai

# Set up virtual environment (see VENV_SETUP.md for detailed instructions)
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r mvp_site/requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally using vpython script
./vpython mvp_site/main.py serve
```

### Docker Deployment

```bash
# Build the container
docker build -t worldarchitect-ai .

# Run with environment variables
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your-key \
  -e FIREBASE_PROJECT_ID=your-project \
  worldarchitect-ai
```

## 📚 Documentation

For a comprehensive understanding of the platform, including detailed architecture, game mechanics, and development guidelines, see our [Product Specification](product_spec.md).

## 🎮 Features

- **Campaign Management**: Create and manage multiple campaigns
- **AI Game Master**: Three specialized personas for different play styles
- **Full D&D 5e Support**: Complete rule implementation
- **Character & God Modes**: Standard play or administrative control
- **State Persistence**: Never lose your progress
- **Export Functionality**: Save your adventures in multiple formats
- **Debug Mode**: Full transparency into AI decisions

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Run with coverage
./run_tests.sh --coverage

# Run integration tests
./run_tests.sh --integration

# Run specific test with vpython
TESTING=true ./vpython mvp_site/test_file.py
```

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) and refer to the [product specification](product_spec.md) for architectural details.

### 🤖 Claude Code Integration

This repository includes Claude Code GitHub Action for AI-assisted development. You can interact with Claude directly in pull requests by mentioning `@claude`. See [Claude Code Setup Guide](.github/CLAUDE_CODE_SETUP.md) for configuration instructions.

## 🔬 Command Composition System Validation

### Overview
We've validated a **True Universal Command Composition System** that enables natural language control of AI behavior through semantic composition. This system allows commands like `/think /analyze /arch` to reliably modify how Claude approaches problems.

### Key Findings from A/B Testing

**✅ Proven Capabilities:**
- **Behavioral Modification**: Reliably changes thinking patterns across 15+ headless Claude instances
- **Tool Integration**: Commands consistently trigger appropriate MCP tools (99% vs 20% for natural language)
- **Emergent Structure**: Complex 8-step analytical frameworks emerge naturally from command combinations
- **Cross-Context Consistency**: Patterns hold across debugging, strategic analysis, and meta-cognitive tasks

**📊 Test Results:**
- **Test Set A** (Debugging): Command composition → systematic 6-8 thought analysis; Natural language → direct problem-solving
- **Test Set B** (Strategic Analysis): Command composition → comprehensive risk-reward frameworks; Natural language → focused recommendations
- **Sample Evidence**: `tmp/ab_test_results_analysis.md` contains full behavioral pattern documentation

**🎯 Honest Positioning:**
- **Accurate Claim**: "Behavioral modification technology that reliably changes how Claude approaches problems"
- **What It Provides**: Consistent systematic analysis, tool integration, behavioral predictability
- **What Needs Validation**: Outcome quality improvements, user preference, cost-benefit analysis

### Architecture & Implementation
- **Meta-prompt Approach**: Leverages Claude's natural language processing vs rigid parsing
- **Universal Composition**: Any command combination works through semantic understanding
- **Tool Ecosystem Integration**: Reliable bridge between user intent and MCP capabilities

### Next Steps
1. **Outcome Validation**: Measure solution effectiveness, not just process sophistication
2. **User Studies**: Blind evaluation of output quality and user preferences  
3. **Mechanism Research**: Test alternative explanations vs architectural uniqueness
4. **Real-world Application**: Identify specific use cases where behavioral consistency adds value

*See `roadmap/scratchpad_dev1752948734.md` for complete validation methodology and balanced critical assessment.*

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Dungeons & Dragons 5th Edition by Wizards of the Coast
- Google Gemini AI for powering our Game Master
- The tabletop RPG community for inspiration

---

**Ready to embark on your AI-powered adventure?** Visit [worldarchitect.ai](https://worldarchitect.ai) to start playing!