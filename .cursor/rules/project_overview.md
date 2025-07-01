# WorldArchitect.AI Project Overview

## Project Description

WorldArchitect.AI is an AI-powered tabletop RPG platform that serves as a digital Game Master for D&D 5e experiences. The application uses Google's Gemini AI to generate dynamic narratives, manage game mechanics, and create interactive storytelling.

## Technology Stack

- **Backend**: Python 3.11 + Flask + Gunicorn
- **AI Service**: Google Gemini API (2.5-flash, 2.5-pro models) via `google-genai` SDK
- **Database**: Firebase Firestore for persistence and real-time sync
- **Frontend**: Vanilla JavaScript (ES6+) + Bootstrap 5.3.2
- **Deployment**: Docker + Google Cloud Run

## Architecture

### Core Components

- **`main.py`**: Flask application entry point with API routes
- **`game_state.py`**: Campaign state management, combat system, data migrations
- **`gemini_service.py`**: AI integration with context management and personality-driven responses
- **`firestore_service.py`**: Database operations and real-time synchronization
- **`document_generator.py`**: Export campaigns to PDF/DOCX/TXT formats

### AI System

The platform uses three specialized AI personas:
- **Narrative Flair**: Storytelling and character development
- **Mechanical Precision**: Rules and game mechanics  
- **Calibration Rigor**: Game balance and design

System instructions are stored in `prompts/` directory with MBTI personality definitions in `prompts/personalities/`.

### Data Architecture

- **Firestore Collections**: Campaigns, game states, user data
- **State Management**: Deep recursive merging for nested updates
- **Schema Evolution**: Defensive data access patterns for backward compatibility
- **Append-Only Patterns**: Game history preserved through append operations

## File Structure

```
worldarchitect.ai/
├── mvp_site/                    # Main application
│   ├── main.py                  # Flask routes and application factory
│   ├── game_state.py           # Core state management
│   ├── gemini_service.py       # AI service integration  
│   ├── firestore_service.py    # Database layer
│   ├── document_generator.py   # Export functionality
│   ├── constants.py            # Shared constants
│   ├── static/                 # Frontend assets
│   │   ├── app.js             # Main application logic
│   │   ├── auth.js            # Authentication handling
│   │   ├── style.css          # Application styling
│   │   └── themes/            # Theme CSS files
│   ├── templates/              # HTML templates
│   │   └── index.html         # Single page application
│   ├── prompts/                # AI system instructions
│   │   ├── *.md               # Persona instructions
│   │   └── personalities/      # MBTI definitions
│   ├── tests/                  # Test directory
│   │   └── test_*.py          # Comprehensive test suite
│   └── requirements.txt        # Python dependencies
├── prototype/                  # Experimental code
│   └── tests/                 # Prototype test organization
├── roadmap/                    # Project planning
│   └── scratchpad_*.md        # Active work tracking
├── .cursor/                    # AI collaboration rules
│   └── rules/                 # Documentation
└── deploy.sh                   # Deployment script
```

## Development Commands

### Testing

**IMPORTANT**: Always run `vpython` tests and commands from the PROJECT ROOT directory, not from subdirectories. This ensures proper virtual environment context and prevents "command not found" errors.

```bash
# Run all tests (from project root)
./run_tests.sh

# Run specific test file (from project root - NOT from mvp_site/)
TESTING=true vpython mvp_site/test_integration.py

# Run data integrity tests (catches corruption bugs)
TESTING=true vpython mvp_site/test_data_integrity.py

# Run combat integration tests (end-to-end combat flow)
TESTING=true vpython mvp_site/test_combat_integration.py

# Run specific test method
TESTING=true vpython -m unittest mvp_site.test_module.TestClass.test_method
```

### Running the Application
```bash
# Development (from project root)
vpython mvp_site/main.py

# Production (Docker)
./deploy.sh                 # Deploy to dev environment
./deploy.sh stable          # Deploy to stable environment
```

### Environment Setup
- Always use the project virtual environment (`venv`)
- Set `TESTING=true` environment variable when running tests (uses faster AI models)
- Firebase service account configured via environment variables

## Important Development Patterns

### Gemini API Usage
```python
# Use modern google-genai SDK patterns
from google import genai
from google.genai import types
client = genai.Client(api_key=api_key)
response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
```

### Data Handling
```python
# Defensive data access for schema evolution
campaign_data.get('last_played', 'N/A')  # Backend
campaign?.last_played || 'N/A'           # Frontend

# Type validation for dynamic data
if isinstance(item, dict):
    name = item.get('name', str(item))
```

### Testing Patterns
- Use `TESTING=true` environment variable for faster AI models
- Always use temporary directories for test file operations
- Case-insensitive field detection for AI-generated data
- Flexible assertions for AI content validation

### Prototype Test Organization
- All prototype test files go in `prototype/tests/`
- Milestone-specific tests in `prototype/tests/milestone_X.Y/`
- Never place prototype test files in root directory

## Key Constraints

- **AI Models**: 
  - DEFAULT_MODEL = 'gemini-2.5-flash'
  - LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'
  - TEST_MODEL = 'gemini-1.5-flash'
- **SDK**: Must use modern `google-genai` SDK (not legacy `google-generativeai`)
- **Virtual Environment**: Always activate `venv` before running Python commands
- **Test Isolation**: Use temporary directories to avoid overwriting application files
- **Data Integrity**: Implement defensive programming for external data sources

## API Endpoints

### Campaign Management
- `GET /api/campaigns` - List user's campaigns
- `POST /api/campaigns` - Create new campaign
- `GET /api/campaigns/<id>` - Get campaign details
- `DELETE /api/campaigns/<id>` - Delete campaign

### Game State
- `GET /api/campaigns/<id>/state` - Get current game state
- `POST /api/campaigns/<id>/state` - Update game state

### AI Interaction
- `POST /api/ai/process` - Process user input through AI
- `POST /api/ai/generate` - Generate content (NPCs, locations, etc.)

### Export
- `GET /api/campaigns/<id>/export/<format>` - Export campaign (pdf/docx/txt)

## Deployment

- Multi-environment deployment via `./deploy.sh` script
- Docker containerization with health checks
- Google Cloud Run with automatic scaling
- Secret management for API keys via Google Secret Manager

## Maintenance Notes

### File Structure Updates
When adding new files or changing the directory structure:
1. Update the File Structure section in this document
2. Update any affected path references in documentation
3. Consider impacts on deployment and test scripts

---
*Last Updated: 2025-01-01*
*For operating protocols, see `.cursor/rules/rules.mdc`*