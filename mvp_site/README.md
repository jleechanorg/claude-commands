# WorldArchitect.AI - MVP Site Directory

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack & Competitive Positioning](#tech-stack--competitive-positioning)
  - [Core Technology Stack](#core-technology-stack)
  - [Competitive Differentiation](#competitive-differentiation)
  - [Technical Highlights](#technical-highlights)
  - [Architecture Philosophy](#architecture-philosophy)
- [Architecture](#architecture)
  - [File Placement Guidelines](#file-placement-guidelines)
  - [Backend (Python/Flask)](#backend-pythonflask)
  - [Frontend (JavaScript/HTML/CSS)](#frontend-javascripthtmlcss)
- [Key Components](#key-components)
- [Directory Structure](#directory-structure)
- [Testing Infrastructure](#testing-infrastructure)
- [Key Features](#key-features)
- [Development Notes](#development-notes)
- [Dependencies](#dependencies)
- [Configuration](#configuration)

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
- **Frontend Assets**: `mvp_site/frontend_v1/` - CSS, JS, images, themes (formerly static/)
- **AI Prompts**: `mvp_site/prompts/` - AI system instructions and templates
- **MCP Protocol**: Clean separation between HTTP API and D&D business logic via MCP (Model Context Protocol)
  - **main.py**: Pure API gateway translating HTTP requests to MCP tool calls
  - **world_logic.py**: MCP server containing all D&D 5e game mechanics and business logic
  - **mcp_client.py**: HTTP client for communicating with MCP server
  - **Zero breaking changes**: Frontend receives identical JSON response formats

**Rule**: When in doubt about file placement, ask for clarification rather than creating new directories.

### Backend (Python/Flask) - MCP Architecture

#### Core MCP Architecture (NEW)
- **main.py** - Pure API Gateway (HTTP ↔ MCP translation layer)
- **world_logic.py** - Complete D&D business logic (campaigns, AI, game mechanics)
- **mcp_api.py** - MCP protocol wrapper (JSON-RPC 2.0 tool registration)
- **mcp_client.py** - Enhanced MCP client with direct-call optimization (`skip_http=False`)

#### AI & Game Services
- **gemini_service.py** (2,209 lines) - AI service integration and response processing
- **firestore_service.py** (1,101 lines) - Database operations and state management
- **narrative_response_schema.py** (752 lines) - AI response validation and parsing
- **entity_validator.py** (636 lines) - Entity state validation and consistency
- **game_state.py** (488 lines) - Core game state management and validation
- **gemini_response.py** (487 lines) - AI response processing and transformation
- **entity_instructions.py** (407 lines) - Entity handling and instruction generation
- **json_utils.py** (324 lines) - JSON parsing and utility functions
- **dual_pass_generator.py** (326 lines) - Advanced AI generation with dual-pass system
- **memory_integration.py** (303 lines) - Memory and context management
- **entity_preloader.py** (283 lines) - Entity preloading and optimization
- **robust_json_parser.py** (254 lines) - Robust JSON parsing with error handling
- **narrative_sync_validator.py** (227 lines) - Narrative synchronization validation
- **constants.py** (216 lines) - Shared constants and configuration
- **logging_util.py** (212 lines) - Centralized logging with emoji enhancement
- **debug_mode_parser.py** (194 lines) - Debug command parsing and execution
- **debug_hybrid_system.py** (175 lines) - Debug system integration
- **document_generator.py** (157 lines) - Document export functionality
- **custom_types.py** (145 lines) - Custom type definitions and utilities
- **file_cache.py** (142 lines) - File caching system with TTL support
- **world_loader.py** (121 lines) - World content loading and management

### Frontend (JavaScript/HTML/CSS)
- **frontend_v1/index.html** - Main HTML template with theme integration
- **frontend_v1/app.js** - Core frontend application logic
- **frontend_v1/api.js** - API communication layer
- **frontend_v1/auth.js** - Authentication handling
- **frontend_v1/style.css** - Main stylesheet
- **frontend_v1/themes/** - Complete theme system (base, light, dark, fantasy, cyberpunk)

**Architectural Principles**:
- **Separation of Concerns**: Logic (JS modules), presentation (organized CSS), structure (HTML)
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Modularity**: Small, focused files with clear dependencies and reusable components
- **Theme System**: Runtime theme switching with CSS custom properties
- **frontend_v1/js/campaign-wizard.js** (1,190 lines) - Campaign creation wizard system
- **frontend_v1/js/enhanced-search.js** (396 lines) - Advanced search functionality
- **frontend_v1/js/component-enhancer.js** (364 lines) - UI component enhancement
- **frontend_v1/js/visual-validator.js** (297 lines) - Visual validation system
- **frontend_v1/js/test_planning_block_parsing.js** (322 lines) - Planning block parsing tests
- **frontend_v1/js/animation-helpers.js** (215 lines) - Animation system helpers
- **frontend_v1/js/inline-editor.js** (173 lines) - Inline editing functionality
- **frontend_v1/js/theme-manager.js** (161 lines) - Theme switching and management
- **frontend_v1/js/interface-manager.js** (132 lines) - Interface state management
- **frontend_v1/js/settings.js** (130 lines) - Application settings management
- **frontend_v1/js/loading-messages.js** (90 lines) - Dynamic loading message system
- **frontend_v1/js/ui-utils.js** (29 lines) - UI utility functions

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
- **Main Files**: `main.py` (check_token decorator), `frontend_v1/auth.js`
- **Public Methods**:
  - `check_token()` - Decorator for protected routes
  - Firebase integration for user management

### 5. Document Export
- **Purpose**: Export campaigns to various formats (PDF, DOCX, TXT)
- **Main Files**: `document_generator.py`, `main.py` (export route)
- **Public Methods**:
  - `export_campaign()` - Generate downloadable campaign documents
  - Support for PDF, DOCX, and TXT formats

### 6. Advanced AI Generation
- **Purpose**: Sophisticated AI content generation with dual-pass system
- **Main Files**: `dual_pass_generator.py`, `gemini_response.py`, `robust_json_parser.py`
- **Public Methods**:
  - `DualPassGenerator.generate()` - Advanced multi-pass AI generation
  - `GeminiResponse.parse()` - Structured response parsing
  - `RobustJSONParser.parse()` - Error-resilient JSON parsing

### 7. Entity & State Management
- **Purpose**: Comprehensive entity validation and state synchronization
- **Main Files**: `entity_validator.py`, `entity_preloader.py`, `narrative_sync_validator.py`
- **Public Methods**:
  - `EntityValidator.validate()` - Multi-layer entity validation
  - `EntityPreloader.preload()` - Optimized entity loading
  - `NarrativeSyncValidator.validate()` - State-narrative consistency

### 8. Memory & Context Integration
- **Purpose**: Advanced memory management and context preservation
- **Main Files**: `memory_integration.py`, `file_cache.py`
- **Public Methods**:
  - `MemoryIntegration.store()` - Context storage and retrieval
  - `FileCache.get()` - TTL-based file caching

### 9. Frontend Module System
- **Purpose**: Modular JavaScript architecture with theme support
- **Main Files**: `frontend_v1/js/` modules, theme system
- **Public Methods**:
  - `CampaignWizard.create()` - Guided campaign creation
  - `ThemeManager.switch()` - Dynamic theme switching
  - `ComponentEnhancer.enhance()` - UI component enhancement

## Directory Structure

```
mvp_site/
├── main.py                    # Flask application entry point (1,875 lines)
├── gemini_service.py          # AI service integration (2,209 lines)
├── firestore_service.py       # Database operations (1,101 lines)
├── narrative_response_schema.py # AI response validation (752 lines)
├── entity_validator.py        # Entity state validation (636 lines)
├── game_state.py              # Game state management (488 lines)
├── gemini_response.py         # AI response processing (487 lines)
├── entity_instructions.py     # Entity handling (407 lines)
├── dual_pass_generator.py     # Advanced AI generation (326 lines)
├── json_utils.py              # JSON parsing utilities (324 lines)
├── memory_integration.py      # Memory and context management (303 lines)
├── entity_preloader.py        # Entity preloading (283 lines)
├── robust_json_parser.py      # Robust JSON parsing (254 lines)
├── narrative_sync_validator.py # Narrative synchronization (227 lines)
├── constants.py               # Shared constants (216 lines)
├── logging_util.py            # Logging utilities (212 lines)
├── debug_mode_parser.py       # Debug command parsing (194 lines)
├── document_generator.py      # Document export functionality (157 lines)
├── custom_types.py            # Type definitions (145 lines)
├── file_cache.py              # File caching system (142 lines)
├── world_loader.py            # World content management (121 lines)
├── decorators.py              # Common decorators (79 lines)
├── entity_tracking.py         # Entity state tracking (68 lines)
├── frontend_v1/               # Frontend assets
│   ├── index.html            # Main HTML template
│   ├── app.js                # Core frontend logic
│   ├── api.js                # API communication
│   ├── auth.js               # Authentication handling
│   ├── style.css             # Main stylesheet
│   ├── themes/               # Theme support (5 themes)
│   │   ├── base.css         # Base theme foundation
│   │   ├── light.css        # Light theme
│   │   ├── dark.css         # Dark theme
│   │   ├── fantasy.css      # Fantasy theme
│   │   └── cyberpunk.css    # Cyberpunk theme
│   ├── js/                   # Modular JavaScript components
│   │   ├── campaign-wizard.js    # Campaign creation wizard (1,190 lines)
│   │   ├── enhanced-search.js    # Advanced search (396 lines)
│   │   ├── component-enhancer.js # UI enhancement (364 lines)
│   │   ├── visual-validator.js   # Visual validation (297 lines)
│   │   ├── animation-helpers.js  # Animation system (215 lines)
│   │   ├── inline-editor.js      # Inline editing (173 lines)
│   │   ├── theme-manager.js      # Theme management (161 lines)
│   │   ├── interface-manager.js  # Interface state (132 lines)
│   │   ├── settings.js           # Settings management (130 lines)
│   │   ├── loading-messages.js   # Loading messages (90 lines)
│   │   └── ui-utils.js          # UI utilities (29 lines)
│   ├── css/                  # Feature-specific CSS
│   │   ├── inline-editor.css     # Complete inline editing with theme support
│   │   └── pagination-styles.css # Story pagination with responsive design
│   └── styles/               # Organized CSS by purpose
│       ├── globals.css           # Global variables and resets
│       ├── components.css        # Base component styles
│       ├── enhanced-components.css # Advanced component styles
│       ├── interactive-features.css # Interactive element styles
│       ├── animations.css        # Animation definitions
│       ├── planning-blocks.css   # Planning block specific styles
│       └── bridge.css           # Integration/compatibility styles
├── schemas/                   # Pydantic schemas and validators
├── prompts/                   # AI system instructions and templates
├── tests/                     # Unit tests (166 test files)
├── test_integration/          # Integration test suite
├── testing_ui/                # Browser-based UI tests
├── testing_framework/         # Testing utilities and frameworks
├── mocks/                     # Mock services for testing
├── prototype/                 # Prototype and experimental code
├── world/                     # World content and lore data
├── docs/                      # Documentation and guides
├── templates/                 # Additional HTML templates
└── analysis/                  # Code analysis and metrics
```

## Testing Infrastructure

### Unit Tests
- **Location**: `tests/` directory
- **Test Files**: 166 test files covering all core functionality
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

### 5. Advanced AI Systems
- Dual-pass AI generation for complex content
- Sophisticated JSON parsing with error recovery
- Memory integration for context preservation
- Entity-aware prompt construction
- Token management and cost optimization

### 6. Modular Frontend Architecture
- Campaign creation wizard with guided workflows
- Dynamic theme switching (5 themes available)
- Component-based enhancement system
- Advanced search and filtering capabilities
- Inline editing with real-time validation
- Animation system with smooth transitions
- Visual validation and feedback systems

### 7. Comprehensive Testing Framework
- 166 unit test files with 67% coverage
- Browser automation testing with Playwright
- Integration testing with real API endpoints
- Mock service architecture for development
- Performance testing and validation
- Visual regression testing capabilities

## Development Notes

### Areas Needing Cleanup

1. **main.py** (~900 lines) - **✅ SIGNIFICANTLY IMPROVED** with MCP refactor:
   - **Pure API Gateway**: Now only translates HTTP requests to MCP calls
   - **75% code reduction**: Business logic moved to world_logic.py MCP server
   - **Clean separation**: Zero business logic in API layer
   - **Maintainable routes**: Each route is a simple HTTP-to-MCP translation

2. **gemini_service.py** (2,209 lines) - Largest file with complex AI logic:
   - PromptBuilder class has evolved but still handles many concerns
   - Advanced features like dual-pass generation add complexity
   - Model cycling and error handling are sophisticated but dense

3. **Entity system complexity** - Multiple validation layers:
   - `entity_validator.py`, `entity_preloader.py`, `narrative_sync_validator.py`
   - Good separation of concerns but complex interactions
   - Could benefit from unified entity management interface

4. **Frontend organization** - Significantly improved modularization:
   - Successfully separated into focused modules in `frontend_v1/js/`
   - Campaign wizard is comprehensive but very large (1,190 lines)
   - Theme system is well-organized with 5 distinct themes

### MCP Architecture Benefits (NEW)

The recent **Model Context Protocol (MCP)** refactor has dramatically improved the codebase:

1. **Separation of Concerns**:
   - **API Layer** (`main.py`): Pure HTTP-to-MCP translation, no business logic
   - **Business Logic** (`world_logic.py`): Complete D&D game mechanics and AI integration
   - **Protocol Layer** (`mcp_client.py`): JSON-RPC 2.0 communication with context manager support

2. **Improved Testability**:
   - Business logic can be tested independently of HTTP layer
   - MCP tools can be called directly for unit testing
   - Clear interfaces between components

3. **Enhanced Maintainability**:
   - 75% reduction in main.py complexity
   - Single responsibility principle enforced
   - Easy to add new features without touching API gateway

4. **Future Scalability**:
   - MCP server can be deployed independently
   - Multiple API gateways can connect to same business logic
   - Protocol-based architecture enables microservices migration

### Technical Debt

1. **Complex file interdependencies** - Large files create tight coupling
2. **Entity validation layers** - Multiple overlapping validation systems
3. **Testing coverage gaps** - 33% of statements still lack coverage
4. **AI service complexity** - gemini_service.py has grown very large
5. **Memory management** - Multiple memory/context systems need unification
6. **Debug system integration** - Debug tools spread across multiple files

## Next Steps for Improvement

1. **Modularize large files** - Split gemini_service.py and main.py into focused modules
2. **Achieve 80%+ test coverage** - Focus on critical AI and state management paths
3. **Unify entity management** - Create single interface for entity operations
4. **Optimize AI performance** - Improve dual-pass generation efficiency
5. **Enhance memory systems** - Consolidate memory and context management
6. **API documentation** - Add OpenAPI/Swagger documentation for all routes
7. **Performance monitoring** - Add metrics and monitoring for AI operations
8. **Cache optimization** - Expand caching strategy for frequently accessed data

## Dependencies

### Backend
- **Flask 3.0.0** - Modern web framework with latest features
- **Gunicorn 21.2.0** - WSGI HTTP server for production deployment
- **Firebase Admin SDK 6.5.0** - Authentication and database integration
- **Google Generative AI (latest)** - State-of-the-art AI service integration
- **Google Cloud Firestore 2.16.0** - NoSQL document database
- **Pydantic** - Data validation and settings management
- **python-docx** - Microsoft Word document generation
- **fpdf2** - PDF generation and manipulation
- **PyJWT 2.8.0** - JSON Web Token implementation
- **Flask-Cors 4.0.0** - Cross-Origin Resource Sharing support

### Development & Testing
- **Playwright 1.40.0+** - Browser automation for testing
- **Selenium** - Web browser automation (fallback)
- **BeautifulSoup4 4.12.0+** - HTML parsing and manipulation
- **Requests 2.31.0+** - HTTP library for API testing
- **psutil 5.9.0+** - System and process utilities

### Code Quality & Analysis
- **Ruff 0.6.0+** - Fast Python linter and formatter
- **MyPy 1.8.0+** - Static type checker
- **Bandit 1.7.0+** - Security linter for Python
- **isort 5.13.0+** - Import statement organizer
- **Type stubs** - Flask, requests type definitions

### Frontend
- **Bootstrap 5.3.2** - Modern CSS framework
- **Bootstrap Icons 1.11.3** - Comprehensive icon library
- **Vanilla JavaScript ES6+** - Modern JavaScript without framework overhead
- **Custom CSS Grid & Flexbox** - Advanced layout systems
- **CSS Custom Properties** - Dynamic theming support
- **Web APIs** - Local Storage, Fetch API, Web Components

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
