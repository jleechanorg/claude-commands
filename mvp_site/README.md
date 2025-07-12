# WorldArchitect.AI - MVP Site Directory

## Overview

This directory contains the core application code for WorldArchitect.AI, an AI-powered tabletop RPG platform that serves as a digital D&D 5e Game Master. The application uses Flask for the backend API and vanilla JavaScript with Bootstrap for the frontend.

**📋 [Comprehensive Code Review & File Responsibilities →](CODE_REVIEW_SUMMARY.md)**

## Architecture

### 📁 File Placement Guidelines

**🚨 CRITICAL**: Do not create new directories without explicit permission. Follow these guidelines:

#### Testing Files
- **Browser Tests**: `/testing_ui/` (project root) - Playwright browser automation tests
- **HTTP Tests**: `/testing_http/` (project root) - HTTP API endpoint tests  
- **MVP Site Browser Tests**: `mvp_site/testing_ui/` - Browser tests specific to MVP site
- **Integration Tests**: `mvp_site/test_integration/` - Cross-component integration tests
- **Unit Tests**: `mvp_site/tests/` - Individual component unit tests

#### Development Tools
- **Scripts**: `/tools/` (project root) - Development and utility scripts
- **Diagnostic Tools**: `/testing_ui/` - Browser diagnostic and debugging tools

#### Documentation
- **Project Documentation**: `/` (project root) - README, CLAUDE.md, setup guides
- **Roadmap & Planning**: `/roadmap/` - Project planning and milestone documentation
- **Code Documentation**: `mvp_site/` - Architecture and component-specific docs

#### Source Code
- **Core Application**: `mvp_site/` - All production application code
- **Static Assets**: `mvp_site/static/` - CSS, JS, images, themes
- **AI Prompts**: `mvp_site/prompts/` - AI system instructions and templates

**Rule**: When in doubt about file placement, ask for clarification rather than creating new directories.

### Backend (Python/Flask)
- **main.py** (1,222 lines) - Primary Flask application entry point
- **firestore_service.py** (539 lines) - Database operations and state management
- **gemini_service.py** (1,598 lines) - AI service integration and response processing
- **game_state.py** (382 lines) - Core game state management and validation
- **constants.py** (184 lines) - Shared constants and configuration
- **logging_util.py** (207 lines) - Centralized logging with emoji enhancement

### Frontend (JavaScript/HTML/CSS)
- **static/index.html** - Main HTML template
- **static/app.js** - Core frontend application logic
- **static/api.js** - API communication layer
- **static/auth.js** - Authentication handling
- **static/style.css** - Main stylesheet
- **static/themes/** - Multiple theme support (light, dark, fantasy, cyberpunk)

## Key Components

### 1. Campaign Management
- **Purpose**: Create, read, update, and delete RPG campaigns
- **Main Files**: `main.py` (API routes), `firestore_service.py` (database operations)
- **Public Methods**:
  - `create_campaign()` - Initialize new campaigns with AI-generated opening
  - `get_campaigns_for_user()` - List user's campaigns
  - `get_campaign_by_id()` - Retrieve specific campaign with story history
  - `update_campaign_title()` - Modify campaign metadata

### 2. Game State Management
- **Purpose**: Track and synchronize all game data (characters, NPCs, world state)
- **Main Files**: `game_state.py`, `firestore_service.py`
- **Public Methods**:
  - `GameState.from_dict()` / `GameState.to_dict()` - Serialization
  - `validate_checkpoint_consistency()` - Validate narrative vs. state consistency
  - `cleanup_defeated_enemies()` - Combat state cleanup
  - `update_state_with_changes()` - Apply AI-generated state changes

### 3. AI Integration
- **Purpose**: Generate dynamic story content and manage game logic
- **Main Files**: `gemini_service.py`, `entity_tracking.py`, `narrative_response_schema.py`
- **Public Methods**:
  - `get_initial_story()` - Generate campaign opening story
  - `continue_story()` - Process user input and generate responses
  - `PromptBuilder.build_core_system_instructions()` - Construct AI prompts
  - `_call_gemini_api_with_model_cycling()` - Robust API calls with fallback

### 4. Authentication & Authorization
- **Purpose**: Secure user access using Firebase Authentication
- **Main Files**: `main.py` (check_token decorator), `static/auth.js`
- **Public Methods**:
  - `check_token()` - Decorator for protected routes
  - Firebase integration for user management

### 5. Document Export
- **Purpose**: Export campaigns to various formats (PDF, DOCX, TXT)
- **Main Files**: `document_generator.py`, `main.py` (export route)
- **Public Methods**:
  - `export_campaign()` - Generate downloadable campaign documents
  - Support for PDF, DOCX, and TXT formats

## Directory Structure

```
mvp_site/
├── main.py                    # Flask application entry point
├── firestore_service.py       # Database operations
├── gemini_service.py          # AI service integration
├── game_state.py              # Game state management
├── constants.py               # Shared constants
├── logging_util.py            # Logging utilities
├── document_generator.py      # Document export functionality
├── decorators.py              # Common decorators
├── debug_mode_parser.py       # Debug command parsing
├── entity_tracking.py         # Entity state tracking
├── narrative_response_schema.py # AI response parsing
├── static/                    # Frontend assets
│   ├── index.html            # Main HTML template
│   ├── app.js                # Core frontend logic
│   ├── api.js                # API communication
│   ├── auth.js               # Authentication
│   ├── style.css             # Main stylesheet
│   ├── themes/               # Theme support
│   └── js/                   # Additional JavaScript modules
├── prompts/                   # AI system instructions
├── tests/                     # Unit and integration tests
├── test_integration/          # Integration test suite
├── mocks/                     # Mock services for testing
└── world/                     # World content and lore
```

## Testing Infrastructure

### Unit Tests
- **Location**: `tests/` directory
- **Coverage**: 67% overall (21,031 statements, 6,975 missing)
- **Run Command**: `./run_tests.sh`

### Integration Tests
- **Location**: `test_integration/` directory
- **Purpose**: End-to-end testing with real APIs
- **Run Command**: `./run_integration_tests.sh`

### Browser Tests
- **Location**: `../testing_ui/` directory
- **Purpose**: Frontend UI testing with Playwright
- **Run Command**: `./run_ui_tests.sh mock`

## Key Features

### 1. Interactive Story Generation
- Real-time AI-powered narrative generation
- User input processing and response generation
- Planning block enforcement for user choices
- Debug mode for development and testing

### 2. State Synchronization
- Automatic state updates from AI responses
- Consistency validation between narrative and game state
- Legacy state cleanup and migration
- Combat state management

### 3. Multi-Modal Interface
- Character mode for player interactions
- God mode for GM/debugging commands
- Export functionality for campaign documents
- Responsive design with multiple themes

### 4. Robust Error Handling
- Model fallback for AI service reliability
- Comprehensive logging with emoji enhancement
- Graceful degradation for service failures
- Test bypass mechanisms for development

## Development Notes

### Areas Needing Cleanup

1. **main.py** - Too many responsibilities:
   - Should separate god-mode commands into dedicated service
   - Route handlers could be moved to separate modules
   - State update logic should be consolidated

2. **gemini_service.py** - Complex prompt building:
   - PromptBuilder class handles too many concerns
   - Entity tracking logic is scattered
   - Model selection logic could be simplified

3. **firestore_service.py** - State update complexity:
   - Multiple handlers for different update patterns
   - Mission handling is overly complex
   - Could benefit from more explicit state machine

4. **Frontend organization**:
   - app.js is growing too large
   - Could benefit from module separation
   - Some duplicate code in theme handling

### Technical Debt

1. **Legacy state handling** - Complex cleanup logic for old data formats
2. **Entity tracking** - Multiple validation layers with overlapping concerns
3. **Testing coverage** - Some critical paths lack adequate coverage
4. **Error handling** - Inconsistent error response formats across routes

## Next Steps for Improvement

1. **Refactor main.py** - Split into smaller, focused modules
2. **Improve test coverage** - Target 80%+ coverage for critical paths
3. **Simplify entity tracking** - Consolidate validation logic
4. **Frontend modularization** - Break app.js into focused modules
5. **Performance optimization** - Add caching for frequent operations
6. **Documentation** - Add OpenAPI/Swagger documentation for API routes

## Dependencies

### Backend
- Flask 2.x - Web framework
- Firebase Admin SDK - Authentication and database
- Google Generative AI - AI service integration
- python-docx - Document generation
- reportlab - PDF generation

### Frontend
- Bootstrap 5.x - CSS framework
- Vanilla JavaScript - No framework dependencies
- Bootstrap Icons - Icon library
- Custom CSS themes - Multiple theme support

## Configuration

### Environment Variables
- `TESTING` - Enable test mode
- `GEMINI_API_KEY` - AI service API key
- `PORT` - Server port (default: 8080)
- `FIREBASE_CONFIG` - Firebase configuration

### Testing Configuration
- Test bypass headers for authentication
- Mock service implementations
- Separate test database configurations