# Serena MCP Configuration

This directory contains the Serena MCP Server configuration for the WorldArchitect.AI project.

## Setup Instructions

1. **Copy config to user directory**:
   ```bash
   mkdir -p ~/.serena
   cp .serena/serena_config.yml ~/.serena/serena_config.yml
   ```

2. **Configuration Overview**:
   - `web_dashboard_open_on_launch: false` - Prevents automatic browser opening
   - `web_dashboard: true` - Dashboard still available at http://localhost:24282/dashboard/
   - `log_level: 20` - Info level logging (20 = info, 10 = debug, 30 = warning, 40 = error)

## Manual Access

If you need to access the Serena dashboard manually:
- Primary URL: http://localhost:24282/dashboard/
- If port 24282 is busy, try: 24283, 24284, etc.

## Alternative Command-Line Usage

You can also start Serena with the dashboard not opening automatically via command line:
```bash
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --web-dashboard-open-on-launch false
```

> **Note**: The command-line flag `--web-dashboard-open-on-launch` matches the YAML key `web_dashboard_open_on_launch`. Both control whether the dashboard automatically opens in your browser when the server starts. For consistency, use the same naming in both config and command-line usage.

## Troubleshooting

1. **Browser still opens**: Ensure config file is in `~/.serena/` directory
2. **Multiple instances**: Check for zombie processes and terminate them
3. **Port conflicts**: Try higher port numbers (24283, 24284, etc.)

## Team Usage

All team members should copy the config file to their local `~/.serena/` directory to maintain consistent behavior across the project.

**Note**: The `projects` section will be empty initially and auto-populated when each user activates projects through Serena chat commands. This prevents user-specific path conflicts.