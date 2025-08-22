# CLAUDE Module Documentation: frontend_v2

## 1. Overview

This document provides a comprehensive technical overview of the `frontend_v2` module, a modern React application built with Vite, TypeScript, and Tailwind CSS. It serves as the primary user interface for the WorldArchitect MVP.

This document inherits from the root `CLAUDE.md`. Please refer to `../../CLAUDE.md` for project-wide conventions and guidelines.

## 2. Technology Stack

- **Framework:** React 19.1.0
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** Radix UI (via `shadcn/ui`)
- **State Management:** Zustand
- **Backend Integration:** Firebase (Firestore, Auth)
- **API Layer:** Custom service layer with built-in mock mode

## 3. Architecture

The `frontend_v2` module follows a modern, component-based architecture designed for scalability and maintainability.

- **Presentation Layer:** The UI is composed of React components, primarily located in `src/pages` for top-level views and `src/components` for reusable UI elements. The `src/components/ui` directory contains a rich set of `shadcn/ui` components built on Radix UI primitives.
- **State Management:** Global application state is managed by Zustand, with stores defined in `src/stores`. This provides a simple, hook-based API for managing state across components without the boilerplate of traditional Redux. Key stores include `authStore.ts` and `campaignStore.ts`.
- **Service Layer:** All interactions with the backend API (Firebase) are abstracted into a dedicated service layer located in `src/services`. The primary service file is `api.service.ts`.
- **Mock Mode Integration:** The application features a robust mock mode for development and testing. The `api-with-mock.service.ts` provides a wrapper that can be toggled to return mock data from `mock.service.ts` instead of making live API calls. This is controlled via environment variables and the `MockModeToggle.tsx` component.

## 4. File Inventory

### 4.1. Core Application Files

- `index.html`: Main entry point
- `main.tsx`: React application root
- `AppWithRouter.tsx`: Top-level component with routing
- `vite.config.ts`: Vite build configuration
- `tailwind.config.js`: Tailwind CSS configuration

### 4.2. Page Components (`src/pages`)

- `CampaignCreationPage.tsx`: Page for creating new campaigns.
- `CampaignListPage.tsx`: Displays a list of all campaigns.
- `CampaignPage.tsx`: Detailed view of a single campaign.
- `LandingPage.tsx`: The public-facing landing page.
- `SettingsPage.tsx`: User settings and profile management.

### 4.3. Reusable Components (`src/components`)

- `CampaignCreation.tsx`: The core campaign creation form.
- `CampaignList.tsx`: Component to display and filter campaigns.
- `Dashboard.tsx`: Main dashboard view for authenticated users.
- `Header.tsx`: Application header and navigation.
- `MockModeToggle.tsx`: Developer utility to switch between live and mock APIs.
- `SignupForm.tsx`: User registration form.
- `ThemeSwitcher.tsx`: Component to toggle between light and dark themes.

### 4.4. UI Primitives (`src/components/ui`)

This directory contains over 40 `shadcn/ui` components, including:
- `button.tsx`
- `card.tsx`
- `dialog.tsx`
- `form.tsx`
- `input.tsx`
- `table.tsx`
- `tabs.tsx`

### 4.5. Services (`src/services`)

- `api.service.ts`: The primary service for interacting with the Firebase backend.
- `mock.service.ts`: Contains mock data and functions for development.
- `api-with-mock.service.ts`: A wrapper that dynamically selects between the real and mock service based on the application's mode.
- `campaignService.ts`: Service specifically for campaign-related API calls.

### 4.6. State Management (`src/stores`)

- `authStore.ts`: Manages user authentication state.
- `campaignStore.ts`: Manages state related to campaigns.
- `gameStore.ts`: Manages the state of the game view.
- `themeStore.ts`: Manages the application's theme (light/dark).

## 5. Development Guidelines

### 5.1. Component Development

- **Functional Components:** All new components must be functional components using React Hooks.
- **TypeScript:** Use TypeScript for all new code. Define clear types for props, state, and API payloads in `src/types`.
- **Styling:** Use Tailwind CSS utility classes for styling. Avoid writing custom CSS files unless absolutely necessary.
- **Component Structure:** Keep components small and focused on a single responsibility. Complex components should be broken down into smaller, reusable sub-components.

### 5.2. State Management

- **Zustand:** Use Zustand for global state. Create new stores in the `src/stores` directory as needed.
- **Local State:** For component-level state, use the `useState` and `useReducer` hooks.

### 5.3. API Integration

- **Service Layer:** All API calls must be made through the service layer in `src/services`. Do not make direct API calls from components.
- **Mock Mode:** When adding new API endpoints, provide corresponding mock implementations in `mock.service.ts`. Use the `api-with-mock.service.ts` to ensure your feature works in both live and mock modes.

### 5.4. Running the Application

To run the development server:
```bash
npm install
npm run dev
```

To build for production:
```bash
npm run build
```

## 6. Testing

All tests are located in the main `mvp_site/tests/` directory following the project's testing protocol. Use the mock mode for isolated component testing.

## 7. Quick Reference

- **Development:** `npm run dev` (runs on port 3002)
- **Build:** `npm run build`
- **Mock Mode:** Toggle via `MockModeToggle.tsx` component
- **State Management:** Zustand stores in `src/stores/`
- **API Services:** `src/services/api-with-mock.service.ts`