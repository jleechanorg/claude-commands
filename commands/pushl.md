# Push Lite Command (pushl alias)

**Purpose**: Alias for `/pushlite` - Enhanced reliable push to GitHub with LLM intelligence

**Action**: This command is an alias that delegates all functionality to `/pushlite`

**Usage**: `/pushl [arguments]` → executes `/pushlite [arguments]`

**Implementation**: Execute: `./claude_command_scripts/commands/pushlite.sh $ARGUMENTS`

**Note**: All features and options are documented in `/pushlite`. This is a convenience alias for faster typing.

---

**See**: `/pushlite` for complete documentation of all features including:
- LLM-powered smart PR creation
- Intelligent change detection
- Post-push verification
- Conditional lint fixes
- Commit hash URL output
- Auto-generated labels and descriptions
- Outdated description detection
