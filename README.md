# WorldArchitect.AI

An AI-powered tabletop RPG platform that serves as a digital Game Master for D&D 5e experiences. Create dynamic, interactive storytelling adventures with Google's Gemini AI.

## 🎲 Features

- **AI Game Master**: Intelligent storytelling that adapts to player choices
- **D&D 5e Integration**: Complete rule implementation with automated combat
- **Persistent Campaigns**: Save and resume long-form adventures
- **Multiple AI Personas**: Choose from Narrative Flair, Mechanical Precision, or Calibration Rigor
- **Rich Character Development**: MBTI personality system for deep character interactions
- **Export & Share**: Download campaigns in PDF, DOCX, or TXT formats

## 📋 Product Specification

For a detailed overview of the application's vision, user journey, and core features from a product perspective, please see our comprehensive product specification document.

**[📖 View the Full Product Specification](product_spec.md)**

## 🚀 Quick Start

```bash
# Run the development server
cd mvp_site && vpython main.py

# Run tests
./run_tests.sh

# Deploy to production
./deploy.sh
```

## 🛠️ Technology Stack

- **Backend**: Python 3.11 + Flask + Gunicorn
- **AI Service**: Google Gemini API (2.5-flash, 2.5-pro models)
- **Database**: Firebase Firestore
- **Frontend**: Vanilla JavaScript + Bootstrap 5.3.2
- **Deployment**: Docker + Google Cloud Run

## 📚 Documentation

- [Product Specification](product_spec.md) - Complete product overview and features.
- [Development Guide](mvp_site/CLAUDE.md) - Development setup and patterns for contributors.

---

*An intelligent RPG companion for limitless adventures.*
