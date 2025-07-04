# WorldArchitect.AI - AI-Powered Tabletop RPG Platform

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
git clone https://github.com/your-repo/worldarchitect-ai.git
cd worldarchitect-ai/mvp_site

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally
python main.py
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
TESTING=true vpython -m pytest

# Run with coverage
TESTING=true vpython -m pytest --cov=. --cov-report=html
```

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) and refer to the [product specification](product_spec.md) for architectural details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Dungeons & Dragons 5th Edition by Wizards of the Coast
- Google Gemini AI for powering our Game Master
- The tabletop RPG community for inspiration

---

**Ready to embark on your AI-powered adventure?** Visit [worldarchitect.ai](https://worldarchitect.ai) to start playing!