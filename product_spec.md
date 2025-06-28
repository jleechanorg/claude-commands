# WorldArchitect.AI - Product Specification

## 1. Vision & Mission

**Vision:** To create a living, breathing tabletop roleplaying game experience where players can embark on epic adventures powered by a dynamic AI Game Master that adapts to their every choice.

**Mission:** WorldArchitect.AI is a web application that acts as a digital Game Master (GM) for solo or group Dungeons & Dragons-style adventures. It empowers players to create, manage, and play through dynamic, AI-generated campaigns, removing the need for a human GM and enabling endless storytelling possibilities.

*This document will outline the core product features and user flows to inform the user experience (UX) and user interface (UI) design.*

---

## Executive Summary

WorldArchitect.AI is an AI-powered tabletop RPG platform that serves as a digital Game Master for D&D 5e experiences. The platform combines Google's Gemini AI with a comprehensive state management system to create dynamic, interactive storytelling experiences where players make decisions and the AI responds with narrative progression, combat mechanics, and world-building.

## Product Overview

### Core Value Proposition
- **AI Game Master**: Eliminates the need for a human dungeon master while maintaining engaging gameplay
- **Dynamic Storytelling**: Real-time narrative generation that adapts to player choices
- **Comprehensive Game Mechanics**: Full D&D 5e rule implementation with automated combat and state tracking
- **Persistent Campaigns**: Save and resume long-form adventures with complete state preservation
- **Rich World Building**: Default fantasy settings with deep lore and character integration

### Target Audience
- Tabletop RPG enthusiasts who lack a regular game master
- Solo players seeking immersive RPG experiences  
- Groups wanting AI-assisted adventures
- D&D players looking for always-available gameplay
- Creative writers and storytellers exploring interactive fiction

## Technical Architecture

### Technology Stack
- **Backend**: Python 3.11 + Flask + Gunicorn
- **AI Service**: Google Gemini API (2.5-flash, 2.5-pro models) via `google-genai` SDK
- **Database**: Firebase Firestore for persistence and real-time sync
- **Frontend**: Vanilla JavaScript (ES6+) + Bootstrap 5.3.2
- **Authentication**: Firebase Authentication with Google Sign-In
- **Deployment**: Docker + Google Cloud Run
- **Document Generation**: PDF/DOCX/TXT export capabilities

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend SPA  │◄──►│  Flask Backend  │◄──►│ Firebase/Gemini │
│   (Bootstrap)   │    │   (Python)      │    │    Services     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Features

### 1. Campaign Management
**Create New Campaigns**
- Custom world descriptions and scenarios
- AI persona selection (Narrative Flair, Mechanical Precision, Calibration Rigor)
- Optional companion generation
- Default fantasy world integration (Celestial Wars/Assiah setting)

**Campaign Dashboard**
- List of all user campaigns with last played timestamps
- Quick access to resume campaigns
- Campaign title editing
- Campaign export functionality

### 2. AI-Powered Storytelling
**Multiple AI Personas**
- **Jeff's Narrative Flair**: Focused on storytelling and character development
- **Jeff's Mechanical Precision**: Handles rules and game mechanics
- **Jeff's Calibration Rigor**: Manages game balance and design

**Dynamic Content Generation**
- Real-time story continuation based on player actions
- Character personality assignment using MBTI types
- Contextual world-building that remembers campaign history
- Adaptive difficulty and narrative pacing

### 3. Game State Management
**Comprehensive State Tracking**
- Player character data (stats, inventory, abilities)
- NPC data with full personality profiles
- Combat state with initiative tracking
- Mission and quest management
- World state and time progression
- Campaign-specific custom data

**Advanced Features**
- Automatic defeated enemy cleanup
- Legacy campaign data migration
- Deep recursive state merging
- Append-only operation support
- Data corruption prevention

### 4. Combat System
**Automated Combat Management**
- Initiative tracking and turn order
- HP and status effect monitoring
- Automatic defeat detection and cleanup
- Combat state consistency validation
- Integration with narrative flow

### 5. User Interface

#### Frontend Views
**Authentication View**
- Google Sign-In integration
- User email display in navigation
- Automatic authentication state management

**Dashboard View** 
- Campaign list with metadata
- New campaign creation button
- Last played timestamps
- Quick campaign access

**New Campaign View**
- Campaign title and description input
- AI persona selection checkboxes
- Custom options (companions, default world)
- Form validation and submission

**Game View**
- Story content display with scrolling
- User input textarea with mode selection
- Character Mode vs God Mode interaction
- Share and download functionality
- Response time tracking

#### Interactive Elements
- **Character Mode**: Standard player interactions
- **God Mode**: Administrative commands for direct state manipulation
- **Theme System**: Light, Dark, Fantasy, Cyberpunk themes
- **Download Options**: TXT, PDF, DOCX export formats
- **Share Functionality**: Native device sharing with size optimization

### 6. Advanced Administrative Features

#### God Mode Commands
**GOD_MODE_SET**: Direct state manipulation
```
GOD_MODE_SET:
player_character_data.hp = 100
npc_data.dragon.status = "defeated"
active_missions.append = {"title": "New Quest"}
```

**GOD_ASK_STATE**: Complete state inspection
- Returns full game state as formatted JSON
- Useful for debugging and state verification

**GOD_MODE_UPDATE_STATE**: JSON-based updates
```
GOD_MODE_UPDATE_STATE: {"combat_state": {"round": 5}}
```

### 7. Data Export and Sharing
**Export Formats**
- **TXT**: Plain text story export
- **PDF**: Formatted document with typography
- **DOCX**: Microsoft Word compatible format
- Automatic filename generation based on campaign title

**Sharing Features**
- Native device sharing API integration
- Smart size optimization for large stories
- Fallback handling for unsupported devices
- Copy-friendly story formatting

## API Documentation

### Authentication
All API endpoints require Firebase ID token authentication via `Authorization: Bearer <token>` header. Test mode supports bypass with special headers.

### Core Endpoints

#### Campaign Management
- `GET /api/campaigns` - List user campaigns
- `POST /api/campaigns` - Create new campaign
- `GET /api/campaigns/{id}` - Get campaign and story
- `PATCH /api/campaigns/{id}` - Update campaign title

#### Game Interaction
- `POST /api/campaigns/{id}/interaction` - Process user input and generate AI response

#### Export
- `GET /api/campaigns/{id}/export?format={format}` - Download campaign in specified format

#### Frontend
- `GET /` - Serve SPA application
- `GET /{path}` - SPA routing fallback

## AI Integration

### Gemini AI Models
- **DEFAULT_MODEL**: `gemini-2.5-flash` - Standard gameplay
- **LARGE_CONTEXT_MODEL**: `gemini-2.5-pro` - Complex scenarios
- **TEST_MODEL**: `gemini-1.5-flash` - Development and testing

### AI Prompt System
**System Instructions**
- Stored in `/prompts/` directory
- Personality definitions in `/prompts/personalities/`
- MBTI-based character development
- Game mechanics integration
- World lore incorporation

**Context Management**
- Story history preservation
- Character relationship tracking
- World state consistency
- Narrative continuity maintenance

## Data Architecture

### Firebase Firestore Collections
**Campaigns Collection**
- Campaign metadata (title, creation date, last played)
- Initial prompts and AI persona selections
- User ownership and permissions

**Game States Collection**
- Complete game state documents
- Versioned state management
- Real-time synchronization
- Conflict resolution

### State Structure
```json
{
  "player_character_data": {
    "name": "string",
    "class": "string", 
    "level": "number",
    "hp": "number",
    "mbti": "string"
  },
  "npc_data": {
    "{npc_id}": {
      "name": "string",
      "personality": "object",
      "stats": "object"
    }
  },
  "combat_state": {
    "active": "boolean",
    "round": "number",
    "combatants": "object"
  },
  "active_missions": "array",
  "world_state": "object",
  "custom_campaign_state": "object"
}
```

## Quality Assurance

### Testing Framework
- Comprehensive unit test suite (40+ test files)
- Integration testing for API endpoints
- Data integrity validation
- Combat system testing
- AI response parsing validation
- Export functionality testing

### Error Handling
- Comprehensive error catching and logging
- User-friendly error messages
- Automatic state recovery
- Data corruption prevention
- Fallback mechanisms

### Performance Optimization
- Response time tracking
- AI model selection based on complexity
- Efficient state updates
- Lazy loading of campaign data
- Optimized document export

## Security

### Authentication & Authorization
- Firebase Authentication integration
- Secure token validation
- User data isolation
- API endpoint protection

### Data Protection
- Encrypted data transmission
- Secure API key management
- User privacy compliance
- No sensitive data logging

## Deployment

### Infrastructure
- **Development**: Local Flask server
- **Production**: Google Cloud Run with Docker containers
- **Database**: Firebase Firestore with global distribution
- **CDN**: Bootstrap and Firebase SDK via CDN

### Environment Management
- Multi-environment deployment (`dev`, `stable`)
- Automated deployment scripts
- Health check endpoints
- Container orchestration

### Scalability
- Stateless application design
- Database auto-scaling
- Container-based horizontal scaling
- Global content distribution

## User Experience

### Responsive Design
- Mobile-first responsive layout
- Touch-friendly interaction elements
- Optimized for tablets and smartphones
- Cross-browser compatibility

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- High contrast theme options

### Performance
- Fast initial page load
- Progressive web app features
- Offline story reading capability
- Optimized asset delivery

## Future Roadmap

### Enhanced AI Features
- Multi-language support
- Voice interaction capabilities
- Advanced personality systems
- Collaborative multiplayer modes

### Extended Game Systems
- Additional RPG system support (Pathfinder, Call of Cthulhu)
- Custom rule system creation
- Advanced character sheet integration
- Dice rolling mechanics

### Social Features
- Campaign sharing and collaboration
- Community story galleries
- Player rating systems
- Social media integration

### Content Management
- User-generated content tools
- Story branching and choice tracking
- Achievement systems
- Campaign analytics and insights

## Technical Requirements

### Browser Support
- Modern browsers with ES6+ support
- Progressive enhancement for older browsers
- Mobile browser optimization

### System Requirements
- Internet connection for AI features
- Modern device with 2GB+ RAM
- Local storage for theme preferences

### Development Environment
- Python 3.11+
- Node.js for frontend tooling
- Firebase project setup
- Google Cloud Platform access
- Docker for containerization

## Conclusion

WorldArchitect.AI represents a sophisticated fusion of AI technology and traditional tabletop gaming, providing users with an always-available, intelligent game master that can create engaging, personalized RPG experiences. The platform's comprehensive feature set, robust architecture, and focus on user experience make it a compelling solution for both solo and group RPG gaming.

The product successfully addresses the core challenge of RPG gaming - the need for a skilled game master - while maintaining the creative freedom and narrative depth that makes tabletop gaming enjoyable. Through its advanced AI integration, comprehensive state management, and user-friendly interface, WorldArchitect.AI opens up new possibilities for interactive storytelling and role-playing experiences.

---

## 2. The Core User Journey

The WorldArchitect.AI experience is designed to be simple and intuitive, guiding the user from an initial idea to an immersive, ongoing adventure.

1.  **Authentication:** The user first signs in, typically with a Google account. This is essential to save their unique campaigns and progress.

2.  **Dashboard:** After signing in, the user lands on their personal dashboard. This screen displays a list of all their existing campaigns. From here, they can choose to continue a previous adventure or start a new one.

3.  **Campaign Creation:** To start a new adventure, the user fills out a simple form:
    *   **Campaign Title:** A memorable name for their story.
    *   **The Core Idea (Prompt):** This is the heart of the creation process. The user describes the world, their character, and a starting scenario (e.g., "A grizzled space marine investigating a distress signal on a derelict starship.").
    *   **AI Expertise:** The user can select from different AI "personalities" (Narrative Flair, Mechanical Precision, Game Balance) to tailor the GM's focus.
    *   **Custom Options:** The user can choose to automatically generate companion characters to join them or to set their story within the rich, pre-defined "World of Assiah."

4.  **The Opening Scene:** After submitting the form, the AI takes the user's prompt and generates the opening chapter of the story, setting the scene, introducing the character, and presenting the initial situation.

5.  **The Gameplay Loop:** This is the core interactive experience.
    *   The story is presented in a scrolling text format.
    *   The user reads the latest developments from the AI GM.
    *   At the bottom of the screen, an input box prompts the user: **"What do you do?"**
    *   The user types their action (e.g., "I check the ship's logs," "I attack the creature," "I try to persuade the guard.").
    *   The AI processes the action, updates the internal game state (e.g., character location, inventory, NPC relationships), and generates the next part of the story based on the user's choice.
    *   This loop continues, creating a dynamically unfolding narrative.

6.  **Campaign Management:** The user can exit a campaign at any time and return to the dashboard. All progress is automatically saved. They can also rename or delete campaigns from the dashboard.

7.  **Exporting the Story:** Once a user has a story they love, they can export the entire campaign log as a TXT, PDF, or DOCX file to save or share.

---

## 3. Core Functionality & Features

This section details the key features from a user's perspective, explaining what they do and why they are important.

### 3.1. The AI Game Master (GM)

**What it is:** The heart of WorldArchitect.AI is a powerful AI system that performs all the functions of a human Game Master. It is composed of specialized AI personas that collaborate to create a rich experience.

**Why it matters:** This eliminates the biggest barrier to tabletop RPGs: the need to find a dedicated, prepared human GM. It allows for spontaneous, solo play anytime, anywhere.

**Key Capabilities:**
*   **Dynamic Storytelling:** The AI writes the story, describes locations, and portrays non-player characters (NPCs).
*   **World Simulation:** It keeps track of the game's state, including the player's health, inventory, location, and relationships with other characters.
*   **Responsive Interaction:** It understands and reacts to the player's actions, ensuring that choices have meaningful consequences.
*   **Rule Adjudication:** It manages game mechanics like combat, skill checks, and saving throws according to established TTRPG rules.

### 3.2. Campaign Creation & Customization

**What it is:** The user-friendly process for starting a new adventure.

**Why it matters:** It provides a low-friction entry point for users. Instead of a complex rulebook, they can start playing just by describing an idea.

**Features:**
*   **Prompt-Based World Building:** Users can create a unique campaign simply by writing a descriptive paragraph.
*   **AI Persona Selection:** Users can choose which "expert" AIs to use, tailoring the game's focus (more story, more rules, etc.).
*   **Pre-built World Option:** For users who want a deep, established setting, they can choose to play in the "World of Assiah," which comes with its own rich history, locations, and characters.
*   **Automatic Companion Generation:** Users can opt-in to have the AI create a balanced party of companion characters to join them on their adventure, simplifying party creation.

### 3.3. Interactive Gameplay Modes

**What it is:** The user has two distinct ways to interact with the AI GM, toggleable at any time.

**Why it matters:** This gives the user flexible control over the narrative and game state, catering to different playstyles.

**Modes:**
*   **Character Mode:** This is the default, immersive mode. The user speaks and acts as their character (e.g., "I draw my sword and shout a challenge!"). The AI responds in-character, continuing the story.
*   **God Mode:** This is a meta-level mode. The user speaks as the "director" of the story. They can ask questions about the game state (`GOD_ASK_STATE`), directly modify it (`GOD_MODE_SET`), or give the AI out-of-character instructions (e.g., "Introduce a mysterious stranger," "Let's skip this combat scene.").

### 3.4. Dynamic State Management

**What it is:** Behind the scenes, the application maintains a comprehensive "character sheet" and "world bible" in a structured format (JSON). This includes everything from the player's health points and inventory to the disposition of every NPC and the current state of the world.

**Why it matters:** This is the game's "memory." It ensures consistency in the narrative. If a character is injured, they remain injured until healed. If an NPC becomes an enemy, they will act like an enemy in future interactions.

**Key Data Tracked:**
*   Player Character Data (stats, skills, inventory, health)
*   NPC Data (profiles, relationships, health)
*   World Data (location, time, major events)
*   Campaign State (active quests, plot points)
*   Combat State (turn order, participants, status effects)

### 3.5. Automated Combat System

**What it is:** When conflict breaks out, the system seamlessly transitions into a structured combat mode.

**Why it matters:** It provides exciting, tactical encounters without bogging the user down in complex rule-keeping.

**Features:**
*   **Initiative Tracking:** The AI automatically determines the turn order for all combatants.
*   **Action & Outcome Resolution:** The user describes their action, and the AI determines the outcome (e.g., "You swing your axe and hit, dealing 8 points of damage.").
*   **Automated Cleanup:** When an enemy is defeated (HP reaches 0), the AI automatically removes them from the combat tracker and the game world.
*   **State-Driven Tactics:** Enemies will act intelligently based on their own health and status.

### 3.6. User Account & Campaign Persistence

**What it is:** The application uses Firebase for user authentication and Firestore for database storage.

**Why it matters:** This ensures a secure and persistent experience. Users can sign in from any device and pick up their adventures exactly where they left off. All campaigns are tied to their personal account.

### 3.7. Story Export

**What it is:** A feature that allows users to download their entire campaign history.

**Why it matters:** It gives users ownership of the stories they create. They can save them for posterity, share them with friends, or use them as a basis for other creative works.

**Formats:**
*   `.txt` (Plain Text)
*   `.pdf` (Formatted Document)
*   `.docx` (Word Document)

---

## 4. Target Audience

*   **Solo RPG Players:** Individuals who want a D&D-like experience but don't have a group or a GM.
*   **Game Masters (GMs):** GMs looking for inspiration for their own campaigns, who can use the app to generate plot hooks, NPCs, and scenarios.
*   **Creative Writers & Storytellers:** People who want to collaboratively write a story with an AI partner, using the game mechanics as a creative constraint.
*   **TTRPG Newcomers:** New players who are intimidated by complex rulebooks and want an easy way to learn and experience the core gameplay loop.