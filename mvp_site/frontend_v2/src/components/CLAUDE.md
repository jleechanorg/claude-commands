# CLAUDE.md - React Components Library

**Primary Rules**: Inherits from [../../../../CLAUDE.md](../../../../CLAUDE.md) (complete project protocols)

**Module Type**: Frontend Components (React/TypeScript)

## 🚨 MODULE-SPECIFIC PROTOCOLS
- All components must use functional components and hooks (no class components)
- State management via React hooks and context API
- CSS modules and Bootstrap for styling with mobile-first responsive design
- Component props must be TypeScript interfaces for type safety

## Directory Contents Analysis
**Core Application Components** (18 files):
- `CampaignCreation.tsx` / `CampaignCreationV2.tsx` - Campaign creation workflows
- `Dashboard.tsx` - Main user dashboard interface
- `GamePlayView.tsx` / `GameView.tsx` - Game session interfaces
- `Header.tsx` - Global navigation header
- `HomePage.tsx` / `LandingPage.tsx` - Landing and home pages
- `SignupCarousel.tsx` / `SignupForm.tsx` - User onboarding flow
- `ErrorBoundary.tsx` - Error handling wrapper
- `MockModeToggle.tsx` - Development testing toggle
- `ThemeSwitcher.tsx` - UI theme management

**Sub-modules**:
- `figma/` - Figma design system components (ImageWithFallback.tsx)
- `ui/` - Reusable UI component library (46 components including button, card, dialog, etc.)

## Component Architecture Guidelines
**For Core Components**:
- Campaign components should integrate with Firestore for persistence
- Game view components must handle real-time state updates
- Authentication-aware components should use auth context
- Error boundaries required for all route-level components

**For UI Components** (`ui/` directory):
- Follow shadcn/ui patterns for consistency
- Components must be composable and reusable
- Include proper TypeScript definitions
- Support theme switching via CSS variables

## Development Workflow
```bash
# Component development from project root:
cd mvp_site/frontend_v2/src/components

# Test component in isolation:
npm run dev  # Start development server

# Run component tests:
npm test src/components/
```

## Module Context
**Purpose**: Provides React components for WorldArchitect.AI user interface including campaign creation, game sessions, and reusable UI elements
**Role**: Frontend component library serving both application-specific and reusable UI components
**Parent Project**: WorldArchitect.AI - AI-powered tabletop RPG platform

## Quick Reference
- **Complete Protocols**: See [../../../../CLAUDE.md](../../../../CLAUDE.md)
- **Test Execution**: `TESTING_AUTH_BYPASS=true vpython mvp_site/tests/test_frontend.py` from project root
- **All Tests**: `../../../../run_tests.sh` (run from project root; CI simulation by default)
- **Component Documentation**: See individual component files for props and usage