# WorldArchitect.AI - MVP Site Directory

## Overview

This directory contains the core application code for WorldArchitect.AI, an AI-powered tabletop RPG platform that serves as a digital D&D 5e Game Master. The application uses Flask for the backend API and vanilla JavaScript with Bootstrap for the frontend.

**📋 [Comprehensive Code Review & File Responsibilities →](CODE_REVIEW_SUMMARY.md)**

## Tech Stack & Competitive Positioning

### Core Technology Stack

WorldArchitect.AI leverages a carefully selected stack that balances rapid development with production scalability:

#### Backend Foundation
- **Python 3.11** with **Flask 2.x** - Lightweight web framework for rapid API development
- **Google Gemini AI (latest SDK)** - `from google import genai` for state-of-the-art language model integration
- **Firebase Firestore** - NoSQL document database with real-time synchronization capabilities
- **Firebase Authentication** - Enterprise-grade user management and security

#### AI & Content Generation
- **Advanced Prompt Engineering** - Custom `PromptBuilder` class with sophisticated context management
- **Robust Model Fallback** - Model cycling with automatic failover for 99.9% uptime
- **Structured JSON Response Parsing** - Type-safe AI output validation using Pydantic schemas
- **Entity Tracking System** - Maintains narrative consistency across multi-turn conversations
- **Dual-Pass Generation** - Retry mechanisms for complex content generation scenarios

#### Frontend & User Experience
- **Vanilla JavaScript** - Zero-framework frontend for maximum performance and minimal dependencies
- **Bootstrap 5.x** - Responsive design with custom theme system (light/dark/fantasy/cyberpunk)
- **Real-time State Synchronization** - WebSocket-style updates without framework overhead
- **Progressive Web App** - Offline-capable design with service worker integration

#### Testing & Quality Assurance
- **67% Test Coverage** - Comprehensive test suite covering thousands of statements
- **Multi-Modal Testing** - Browser automation (Playwright), HTTP testing, and integration tests
- **Mock Service Architecture** - Granular mocking for cost-effective development and CI/CD
- **Automated Code Quality** - Ruff linting, MyPy type checking, and Bandit security scanning

### Competitive Differentiation

Compared to other GenAI tabletop RPG platforms, WorldArchitect.AI makes several distinctive technical choices:

#### **vs. AI Dungeon / NovelAI** (Pure LLM Approaches)
- **Hybrid Architecture**: Combines rule-based D&D 5e validation with generative content, ensuring mechanical accuracy
- **State Management**: Explicit game state tracking vs. pure context-based memory
- **Export Capabilities**: Multi-format document generation (PDF/DOCX/TXT) for offline campaign management

#### **vs. D&D Beyond AI Features** (Enterprise Integration)
- **Independent Platform**: Not constrained by official content licensing or corporate content policies
- **Open Development**: Transparent architecture vs. closed proprietary systems
- **Custom AI Pipeline**: Direct model access vs. mediated enterprise API layers

#### **vs. Character.AI** (Conversational Focus)
- **Campaign Persistence**: Long-term story continuity with structured state management
- **Multi-Modal Output**: Rich document generation beyond conversational interfaces
- **GM-Centric Design**: Purpose-built for game master workflows vs. general chat applications

#### **vs. Dungeon Alchemist** (Procedural Generation)
- **Narrative Focus**: Story and character development vs. primarily visual/map content
- **AI-Native Design**: LLM-first architecture vs. traditional procedural algorithms
- **Integrated Workflow**: Combined story generation, state management, and export in single platform

### Technical Highlights

#### **Standout Engineering Decisions**

1. **Latest Gemini SDK Integration**: Uses `from google import genai` for cutting-edge AI capabilities
2. **Granular Mock Architecture**: Environment-variable controlled mocking (`USE_MOCK_GEMINI`, `USE_MOCK_FIREBASE`) for development velocity
3. **Token-Aware Design**: Built-in cost management and token counting throughout the AI pipeline
4. **File-Based Prompt Management**: Version-controlled AI system instructions in `/prompts/` directory
5. **Zero-Framework Frontend**: Deliberate choice for performance and maintainability over trendy JS frameworks

#### **Production-Ready Features**

- **Model Cycling**: Automatic fallback between Gemini models for reliability
- **Content Validation**: Multi-layer validation ensuring narrative consistency and D&D rule compliance
- **Caching Strategy**: Intelligent file caching with TTL for frequently accessed content
- **Logging Infrastructure**: Emoji-enhanced logging with structured JSON output for monitoring
- **Security Hardening**: Bandit security scanning, input sanitization, and Firebase Authentication integration

### Architecture Philosophy

WorldArchitect.AI's technical approach reflects a **pragmatic AI-first design**:

- **Minimalism Over Complexity**: Vanilla JS frontend avoids unnecessary framework overhead
- **AI Integration Over Simulation**: Direct LLM integration rather than simulated intelligence patterns
- **Explicit State Over Implicit Context**: Structured game state management for reliable long-term campaigns
- **Developer Experience**: Comprehensive testing, mocking, and debugging infrastructure for sustainable development

This stack positions WorldArchitect.AI as a technically sophisticated yet maintainable platform that bridges the gap between experimental AI tools and production-ready tabletop RPG solutions.

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