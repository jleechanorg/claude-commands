# Expert Detail Questions for iOS Implementation

Based on deep codebase analysis and MCP research, here are the key architectural decisions needed:

## Q1: Should the iOS app use SwiftUI with MVVM architecture to mirror the modular frontend structure in frontend_v1/js/?
**Default if unknown:** Yes (maintains architectural consistency and leverages modern iOS patterns)

## Q2: Should we implement offline CoreData caching that syncs with the existing Firebase Firestore backend in firestore_service.py?
**Default if unknown:** Yes (mobile users expect offline access, and existing sync patterns can be extended)

## Q3: Should the iOS app extend the current dual transport MCP server in mcp_api.py to support streamable HTTP transport?
**Default if unknown:** Yes (enables direct connection to existing backend without architectural changes)

## Q4: Should we implement the same 5-theme system (light, dark, fantasy, cyberpunk) from frontend_v1/themes/ as iOS native themes?
**Default if unknown:** Yes (maintains brand consistency and user experience expectations)

## Q5: Should the AI story generation use streaming MCP responses to provide real-time narrative updates like the web version's planning blocks?
**Default if unknown:** Yes (preserves core user experience and leverages MCP's real-time capabilities)