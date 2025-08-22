# CLAUDE.md - React Components Library

**Primary Rules**: Inherits from [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md) (complete project protocols)

**Module Type**: Frontend Components (React/TypeScript)

## 🚨 MODULE-SPECIFIC PROTOCOLS
- All components must use functional components and hooks (no class components)
- State management via React hooks and context API
- CSS modules and Bootstrap for styling with mobile-first responsive design
- Component props must be TypeScript interfaces for type safety

## Directory Contents Analysis
**Core Application Components** ({{COMPONENT_COUNT}} files):
{{COMPONENT_LIST}}

**Sub-modules**:
{{SUB_MODULES}}

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
cd {{DIRECTORY_NAME}}

# Test component in isolation:
npm run dev  # Start development server

# Run component tests:
npm test src/components/
```

## Module Context
**Purpose**: Provides React components for {{PROJECT_NAME}} user interface including {{PRIMARY_FEATURES}}
**Role**: Frontend component library serving both application-specific and reusable UI components
**Parent Project**: {{PARENT_PROJECT}}

## Quick Reference
- **Complete Protocols**: See [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md)
- **Test Execution**: `TESTING=true vpython` from project root
- **All Tests**: `./run_tests.sh` (CI simulation by default)
- **Component Documentation**: See individual component files for props and usage