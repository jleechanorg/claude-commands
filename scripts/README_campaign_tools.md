# Campaign Management Tools

This directory contains consolidated campaign management utilities for safe and efficient campaign operations.

## Tools Overview

### 🔧 Primary Tool: `campaign_manager.py`
Unified campaign management script with all operations:
- Find Firebase UID by email
- Query campaigns by exact name
- Safe campaign deletion with multiple safety features
- Configurable output directories and credentials

### 🚀 Batch Script: `delete_all_my_epic_adventure.sh`
Automated batch deletion script for repetitive operations.

### 📁 Legacy Scripts (Individual Tools)
- `query_campaigns_by_name.py` - Individual query tool
- `delete_campaigns_by_name.py` - Individual deletion tool  
- `find_user_by_email.py` - Individual user lookup tool

## Quick Start

### 1. Find User UID
```bash
# Find Firebase UID from email
python3 scripts/campaign_manager.py find-user jleechan@gmail.com
```

### 2. Query Campaigns
```bash
# Query campaigns by exact name
python3 scripts/campaign_manager.py query vnLp2G3m21PJL6kxcuAqmWSOtm73 "My Epic Adventure"
```

### 3. Safe Deletion
```bash
# Dry-run first (safe preview)
python3 scripts/campaign_manager.py delete vnLp2G3m21PJL6kxcuAqmWSOtm73 "My Epic Adventure"

# Actual deletion with confirmation
python3 scripts/campaign_manager.py delete vnLp2G3m21PJL6kxcuAqmWSOtm73 "My Epic Adventure" --confirm

# Force deletion (no interactive prompt)
python3 scripts/campaign_manager.py delete vnLp2G3m21PJL6kxcuAqmWSOtm73 "My Epic Adventure" --confirm --force
```

### 4. Batch Operations
```bash
# Automated batch deletion
./scripts/delete_all_my_epic_adventure.sh vnLp2G3m21PJL6kxcuAqmWSOtm73 "My Epic Adventure"
```

## Safety Features

### 🛡️ Multiple Safety Layers
- **Exact name matching only** (case-sensitive)
- **Dry-run mode by default** - no accidental deletions
- **Batch size limits** (100 campaigns max per run)
- **Interactive confirmation** with bypass options
- **Comprehensive audit trails** and logging
- **Progress tracking** with success/failure reporting

### 🔍 Smart Detection
- Identifies similar but different campaign names
- Shows preserved campaigns (e.g., "My Epic Adventure 2")
- Prevents accidental deletion of related campaigns

## Configuration

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Firebase service account key
- `OUTPUT_DIR` - Directory for result files (default: `docs/`)
- `USER_ID` - Default user ID for batch operations
- `CAMPAIGN_NAME` - Default campaign name for batch operations

### Example Configuration
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
export OUTPUT_DIR="./campaign_results"
export USER_ID="vnLp2G3m21PJL6kxcuAqmWSOtm73"
```

## Output Files

### Query Results
- `docs/campaign_query_results.json` - Query results with campaign data

### Deletion Operations
- `docs/deletion_preview.json` - Dry-run results preview
- `docs/deletion_results.json` - Actual deletion results
- `docs/campaign_deletion_summary.md` - Human-readable summary

## Error Handling

### Common Issues
1. **Credentials not found** - Set `GOOGLE_APPLICATION_CREDENTIALS`
2. **User not found** - Verify email address and Firebase user exists
3. **No campaigns found** - Check user ID and campaign name spelling
4. **Permission denied** - Verify service account permissions

### Troubleshooting
```bash
# Test Firebase connection
python3 scripts/campaign_manager.py find-user test@example.com

# Verify credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

## Best Practices

### 1. Always Test First
- Run dry-run mode before actual deletion
- Verify campaign counts and names
- Check similar campaign preservation

### 2. Use Batch Limits
- Process max 100 campaigns per run for safety
- Monitor system performance during operations
- Use delays between operations for large datasets

### 3. Maintain Audit Trails
- Save all operation results
- Document deletion rationales
- Keep backup records of important campaigns

### 4. Security
- Never commit credential files to version control
- Use environment variables for sensitive data
- Rotate service account keys regularly

## Migration from Legacy Scripts

### From Individual Scripts
```bash
# Old way
python3 scripts/find_user_by_email.py jleechan@gmail.com
python3 scripts/query_campaigns_by_name.py uid "campaign name"
python3 scripts/delete_campaigns_by_name.py uid "campaign name" --confirm

# New way
python3 scripts/campaign_manager.py find-user jleechan@gmail.com
python3 scripts/campaign_manager.py query uid "campaign name"
python3 scripts/campaign_manager.py delete uid "campaign name" --confirm
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the error messages and logs
3. Verify environment configuration
4. Consult the project documentation

## Version History

- **v2.0** - Consolidated campaign_manager.py with unified interface
- **v1.0** - Individual scripts with basic functionality