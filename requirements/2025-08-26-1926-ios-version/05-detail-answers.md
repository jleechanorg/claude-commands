# Expert Detail Answers

**Q1: Should the iOS app use SwiftUI with MVVM architecture to mirror the modular frontend structure in frontend_v1/js/?**
Answer: Yes

**Q2: Should we implement offline CoreData caching that syncs with the existing Firebase Firestore backend in firestore_service.py?**
Answer: No - Skip offline for now (user specified)

**Q3: Should the iOS app extend the current dual transport MCP server in mcp_api.py to support streamable HTTP transport?**
Answer: Yes

**Q4: Should we implement the same 5-theme system (light, dark, fantasy, cyberpunk) from frontend_v1/themes/ as iOS native themes?**
Answer: No - Just implement dark theme only (user specified)

**Q5: Should the AI story generation use streaming MCP responses to provide real-time narrative updates like the web version's planning blocks?**
Answer: Yes