# Discovery Answers

**Q1: Should the iOS app maintain the same AI-powered D&D game master functionality as the web version?**
Answer: Yes (default)

**Q2: Will the iOS app need to work offline for basic campaign viewing/reading?**
Answer: Yes (default)

**Q3: Should the iOS app use the existing Flask backend via HTTP APIs, or require a new backend architecture?**
Answer: Yes, use existing backend - specifically as an MCP server (user specified MCP server communication)

**Q4: Will users need to sync their campaigns between web and iOS versions?**
Answer: Yes (default)

**Q5: Should the iOS app include the same document export features (PDF, DOCX, TXT) as the web version?**
Answer: Yes (default)

## Additional Context
- iOS app should communicate with existing backend as an MCP (Model Context Protocol) server
- Need to research iOS MCP SDKs for native implementation