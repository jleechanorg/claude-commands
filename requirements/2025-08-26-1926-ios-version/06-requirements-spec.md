# iOS App Requirements Specification - WorldArchitect.AI

## Problem Statement
Create a native iOS application for WorldArchitect.AI that provides the same AI-powered D&D game master functionality as the existing web application, while leveraging mobile-specific capabilities and maintaining seamless integration with the current backend infrastructure.

## Solution Overview
A SwiftUI-based iOS app using MVVM architecture that communicates with the existing Flask backend via the Model Context Protocol (MCP). The app will provide real-time D&D campaign management with AI story generation, state synchronization, and document export capabilities, all optimized for mobile interaction patterns.

## Functional Requirements

### F1: Campaign Management
- **F1.1**: List user campaigns with thumbnail previews and last-played timestamps
- **F1.2**: Create new campaigns with AI-generated opening stories
- **F1.3**: Access and continue existing campaigns with full story history
- **F1.4**: Update campaign titles and metadata
- **F1.5**: Delete campaigns with confirmation prompts

### F2: AI Story Generation & Interaction
- **F2.1**: Process user input and generate AI-powered story responses in real-time
- **F2.2**: Display streaming narrative updates during AI generation
- **F2.3**: Support planning blocks that enforce user choice structure
- **F2.4**: Maintain conversation history with "Scene #X" formatting
- **F2.5**: Handle debug mode commands for development/testing

### F3: Game State Management
- **F3.1**: Track and display character stats, NPCs, and world state
- **F3.2**: Synchronize game state changes from AI responses
- **F3.3**: Validate state consistency between narrative and data
- **F3.4**: Support combat state tracking and cleanup
- **F3.5**: Handle entity management (characters, NPCs, items, locations)

### F4: User Authentication
- **F4.1**: OAuth 2.1 with PKCE integration with Firebase Authentication
- **F4.2**: Secure token storage using iOS Keychain
- **F4.3**: Automatic token refresh and session management
- **F4.4**: Cross-platform login synchronization with web version

### F5: Document Export
- **F5.1**: Generate campaign summaries in PDF format
- **F5.2**: Export campaign data as DOCX documents
- **F5.3**: Create plain text exports for sharing
- **F5.4**: Integrate with iOS native sharing capabilities
- **F5.5**: Support AirDrop and other iOS sharing methods

### F6: User Interface
- **F6.1**: Native iOS dark theme implementation
- **F6.2**: Responsive design for iPhone and iPad
- **F6.3**: Accessibility support following iOS guidelines
- **F6.4**: Intuitive navigation with tab-based architecture
- **F6.5**: Loading states and progress indicators for AI operations

## Technical Requirements

### T1: Architecture
- **T1.1**: SwiftUI-based user interface with MVVM architecture
- **T1.2**: Modular code structure mirroring frontend_v1/js/ organization
- **T1.3**: Type-safe Swift implementation using modern Swift 6.0+ features
- **T1.4**: Async/await patterns for network operations and UI updates
- **T1.5**: Combine framework integration for reactive data binding

### T2: MCP Integration
- **T2.1**: Official Swift MCP SDK (modelcontextprotocol/swift-sdk v0.10.0+)
- **T2.2**: Streamable HTTP transport for backend communication
- **T2.3**: Real-time bidirectional communication for story streaming
- **T2.4**: Robust error handling and connection resilience
- **T2.5**: Tool and resource discovery from MCP server

### T3: Backend Communication
- **T3.1**: Extend existing mcp_api.py with HTTP transport support
- **T3.2**: Maintain compatibility with current world_logic.py MCP tools
- **T3.3**: OAuth 2.1 endpoint integration with existing Flask routes
- **T3.4**: JSON-RPC 2.0 protocol compliance
- **T3.5**: Network connectivity requirement (no offline mode)

### T4: Data Management
- **T4.1**: In-memory data models using Swift structs and classes
- **T4.2**: Firebase Firestore synchronization through MCP backend
- **T4.3**: Efficient state management without local persistence
- **T4.4**: Memory optimization for long campaign histories
- **T4.5**: Background app state preservation

### T5: Performance & Reliability
- **T5.1**: Efficient MCP connection pooling and management
- **T5.2**: Battery optimization for real-time connections
- **T5.3**: Network retry logic with exponential backoff
- **T5.4**: Graceful degradation for network interruptions
- **T5.5**: Memory management for large story histories

## Implementation Hints and Patterns

### Backend Extensions Required
- **mcp_api.py**: Add `StreamableHTTPTransport` alongside existing stdio transport
- **world_logic.py**: Ensure mobile-optimized JSON responses (smaller payloads)
- **main.py**: Add OAuth 2.1 endpoints (`/auth/ios/authorize`, `/auth/ios/token`)
- **firestore_service.py**: Add mobile session tracking and optimization

### iOS Architecture Patterns
```
WorldArchitectApp/
├── Models/              # Swift structs mirroring game_state.py entities
├── Services/            # MCP client, authentication, and API services  
├── ViewModels/          # MVVM business logic and MCP tool orchestration
├── Views/               # SwiftUI views organized by feature
├── Resources/           # Dark theme assets and configuration
└── Utilities/           # Helper functions and extensions
```

### MCP Tool Mapping
- `create_campaign` → CampaignService.createCampaign()
- `process_action` → StoryService.processUserInput()  
- `get_campaign_state` → CampaignService.loadCampaign()
- `export_campaign` → ExportService.generateDocument()
- `update_campaign` → CampaignService.updateMetadata()

### UI Component Structure
Mirror existing frontend_v1/js/ modules:
- CampaignWizardView (campaign-wizard.js equivalent)
- StoryView with real-time updates (enhanced-search.js patterns)
- GameStateView (visual-validator.js equivalent)
- SettingsView (theme-manager.js equivalent)

## Acceptance Criteria

### AC1: Campaign Management
- [ ] User can view list of campaigns with proper authentication
- [ ] New campaigns generate opening story within 10 seconds
- [ ] Campaign history displays with proper "Scene #X" formatting
- [ ] Campaign metadata updates reflect immediately in UI

### AC2: Real-time Story Generation  
- [ ] User input processes and streams AI response in real-time
- [ ] Planning blocks enforce proper user interaction patterns
- [ ] Game state updates automatically from AI responses
- [ ] Error states handle gracefully with retry options

### AC3: Cross-platform Synchronization
- [ ] Campaigns created on web appear in iOS app immediately
- [ ] Story progress syncs bidirectionally between platforms
- [ ] User authentication works seamlessly across platforms
- [ ] Document exports maintain formatting consistency

### AC4: Performance Standards
- [ ] App launches within 3 seconds on target devices
- [ ] Story generation begins streaming within 2 seconds
- [ ] UI remains responsive during AI operations
- [ ] Memory usage stays under 100MB for typical campaigns

### AC5: Export & Sharing
- [ ] PDF exports generate properly formatted campaign summaries
- [ ] Native iOS sharing integrates with system share sheet
- [ ] Documents maintain formatting across export formats
- [ ] AirDrop and other sharing methods work correctly

## Assumptions for Unanswered Questions

1. **Device Support**: iPhone iOS 17+ and iPad iOS 17+ (latest 2 major versions)
2. **Network Requirements**: Stable internet connection required for all major features
3. **User Authentication**: Existing Firebase user base will migrate to OAuth 2.1 flow
4. **Backend Scalability**: Current Flask backend can handle increased mobile load
5. **App Store Compliance**: AI-generated content follows Apple's content guidelines
6. **Development Timeline**: 5-6 weeks for MVP with core functionality
7. **Testing Strategy**: Real device testing with actual MCP backend integration
8. **Deployment**: Standard App Store distribution with TestFlight beta testing

## Success Metrics

- **User Adoption**: 25% of web users try iOS app within first month
- **Engagement**: 60% of mobile users complete at least one full campaign
- **Performance**: 95% of story generation requests complete within 10 seconds
- **Reliability**: 99.5% uptime for MCP backend integration
- **User Satisfaction**: 4.5+ App Store rating with focus on AI quality and responsiveness