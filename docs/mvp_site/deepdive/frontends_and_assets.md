# Front-end Bundles and Static Assets

> **Last updated:** 2025-10-16

## Legacy Front-end (`frontend_v1`)

The V1 bundle consists of vanilla JS/CSS served directly by Flask. Its README
enumerates the important files:

- `index.html` – SPA entry point with static markup. 【F:mvp_site/frontend_v1/README.md†L10-L34】
- `app.js`, `api.js`, `auth.js` – Core UI logic, API client, and auth helpers. 【F:mvp_site/frontend_v1/README.md†L12-L17】
- `js/` modules (e.g., `campaign-wizard.js`, `interface-manager.js`) – Feature
  enhancements layered onto the DOM. 【F:mvp_site/frontend_v1/README.md†L18-L26】
- `styles/` and `themes/` – Legacy CSS organization for animations, planning
  blocks, and dark/light themes. 【F:mvp_site/frontend_v1/README.md†L27-L36】
- Specialized assets (`parallel_dual_pass.js`, `campaign-click-fix.css`,
  `loading-messages.css`) smooth over specific regressions.

Retain these files as reference for layout and behavior while building the new
TypeScript SPA; every API interaction mirrors the Flask routes described in
[`backend_core.md`](backend_core.md).

## Modern Front-end (`frontend_v2`)

A Vite + React TypeScript implementation that achieves feature parity with V1.
Key artifacts:

- `main.tsx` bootstraps the React tree, wrapping `AppWithRouter` in an error
  boundary. 【F:mvp_site/frontend_v2/main.tsx†L1-L13】
- `src/` contains routed pages (`pages/`), shared components (`components/`),
  stores (Zustand-like state), services for API calls, and utility hooks.
- `V2_IMPLEMENTATION_COMPLETE.md` documents completed features: character
  creation wizard, campaign navigation fixes, gameplay integrations, and state
  management. 【F:mvp_site/frontend_v2/V2_IMPLEMENTATION_COMPLETE.md†L1-L40】
- Build configuration is handled by `vite.config.ts`, `tsconfig.json`, and
  Tailwind/PostCSS configs (for utility-first styling). 【F:mvp_site/frontend_v2/vite.config.ts†L1-L60】
- Testing harness includes HTML fixtures (`test-*.html`) and mock-mode scripts
  to validate flows without the backend.

The rewrite can reuse most of this structure; porting to a fresh TypeScript
codebase primarily involves copying component logic and re-binding API clients
to the new server implementation.

## Shared Assets

- `templates/base.html` and `templates/settings.html` supply server-rendered
  fallbacks and legacy settings page scaffolding. 【F:mvp_site/templates/base.html†L1-L160】
- `static/v2/` houses compiled assets generated from `frontend_v2`; treat as
  build output.
- `assets/DejaVuSans.ttf` provides the serif font used in PDF exports. 【F:mvp_site/document_generator.py†L70-L132】

Ensure the TypeScript rewrite includes equivalent entry points, routing, and
styling hooks so both the gameplay dashboard and campaign wizard behave exactly
as outlined in the V2 feature doc.
