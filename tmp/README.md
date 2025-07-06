# Temporary Files

This directory contains temporary files that should not be committed.

## Current Contents

- **Backup files**: CLAUDE.md.backup, rules.mdc.backup
- **One-time scripts**: clean_claude_md.py, clean_duplicates.py, cleanup_system_tmp.sh
- **Temporary documentation**: Milestone reports, PR reviews, task results
- **Cache**: __pycache__/

## Note

Test scripts and servers have been moved to:
- `testing_ui/test_scripts/` - Reusable test scripts
- `testing_ui/test_servers/` - Test server implementations
- `testing_ui/test_results/` - Test output files

This directory should only contain truly temporary files that don't need to be preserved or reused.
