---
description: /memory Command - Native Claude Memory Interaction
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: 🎯 Actions

**Action Steps:**
1. **search** [query] - Perform native memory search
2. **learn** [content] - Save content to native memory
3. **recall** [topic] - Retrieve specific knowledge by topic
4. **read** - Display memory contents overview
5. **forget** [query] - Remove specific memories

### Phase 2: 🔍 SEARCH Action

**Action Steps:**
1. **Native Search**: Use `memory_search` with the query
2. **Result Display**: Show results with relevance scores
3. **Context Integration**: Incorporate findings into current context

### Phase 3: 📚 LEARN Action

**Action Steps:**
1. **Content Analysis**: Parse user content for key information
2. **Native Save**: Use `memory_save` to persist the content
3. **Confirmation**: Report successful saves

### Phase 4: 🧠 RECALL Action

**Action Steps:**
1. **Direct Search**: Use `memory_search` with topic
2. **Knowledge Retrieval**: Display memories related to the topic
3. **Context Display**: Show key information and learnings

### Phase 5: 📊 READ Action

**Action Steps:**
1. **Full Read**: Use `memory_read` for complete memory overview
2. **Summary Display**: Show memory statistics and key content
3. **Overview**: Show coverage areas and recent additions

### Phase 6: 🗑️ FORGET Action

**Action Steps:**
1. **Remove Memories**: Use `memory_forget` to remove specific memories
2. **Confirmation**: Report successful removals

## 📋 REFERENCE DOCUMENTATION

# /memory Command - Native Claude Memory Interaction

**Usage**: `/memory [action] [query/params]`

**Purpose**: Native Claude memory interaction for persistent knowledge storage

## 📚 Examples

```bash
/memory search "decision influence patterns"
/memory learn "Important note about authentication patterns"
/memory recall investigation
/memory read
/memory forget "outdated information"
```

## 🚀 Implementation

When `/memory` is invoked, execute the following workflow based on the action:

## 🛠️ Native Memory Integration

**Core Features**:
- **Native Search**: Uses Claude's built-in `memory_search` for retrieval
- **Direct Save**: Uses `memory_save` to persist learnings
- **Simple Retrieval**: Uses `memory_search` for recall operations
- **Memory Management**: Uses `memory_forget` for removal when needed

**Universal Usage**: All operations use native Claude memory commands.

## 📊 Features

- **Native Integration**: Uses Claude's built-in memory commands
- **Simple Operations**: Straightforward search, save, and recall
- **Persistent Storage**: Memories persist across sessions
- **Easy Management**: Simple forget command for cleanup

## 🚨 Error Handling

- **Invalid Actions**: Show help text with available actions and examples
- **Empty Parameters**: Prompt user for required query/content with specific guidance
- **Memory Failures**: Clear error messages with fallback suggestions

## 🔗 Integration Points

**Native Memory**: Uses Claude's built-in memory commands:
- **Search**: `memory_search` for querying memories
- **Save**: `memory_save` for persisting learnings
- **Read**: `memory_read` for overview
- **Forget**: `memory_forget` for removal
- **Learning Integration**: Compatible with `/learn` command workflows
- **Guidelines System**: Enhances `/guidelines` memory consultations

## 💡 Usage Tips

**For Best Results**:
- Use natural language queries for search
- Include specific technical terms when learning new content
- Use recall for quick knowledge retrieval on familiar topics
- Use forget to remove outdated information

**Example Workflow**:
```bash
# Search for existing knowledge:
/memory search "authentication patterns"

# Learn new information:
/memory learn "Important pattern: Always validate tokens server-side"

# Recall specific topics:
/memory recall investigation
```

## 🎯 Expected Outcomes

- **Enhanced Search**: Native memory search for relevant results
- **Knowledge Building**: Direct interface for storing important information
- **Persistent Learning**: Continuous improvement through saved memories
- **Decision Support**: Better memory consultation for all commands

---

**Integration Status**: Updated to use native Claude memory commands
