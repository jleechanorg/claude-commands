# Discovery Questions for iOS Version

Based on the codebase analysis of WorldArchitect.AI (Flask/Python backend, vanilla JS frontend, Firebase integration, Gemini AI), here are the key discovery questions:

## Q1: Should the iOS app maintain the same AI-powered D&D game master functionality as the web version?
**Default if unknown:** Yes (core value proposition should remain consistent)

## Q2: Will the iOS app need to work offline for basic campaign viewing/reading?
**Default if unknown:** Yes (mobile users expect offline capability for reading content)

## Q3: Should the iOS app use the existing Flask backend via HTTP APIs, or require a new backend architecture?
**Default if unknown:** Yes, use existing backend (maintains consistency and reduces development overhead)

## Q4: Will users need to sync their campaigns between web and iOS versions?
**Default if unknown:** Yes (users expect cross-platform data synchronization)

## Q5: Should the iOS app include the same document export features (PDF, DOCX, TXT) as the web version?
**Default if unknown:** Yes (mobile users benefit from sharing campaign documents)