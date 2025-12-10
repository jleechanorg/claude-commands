# Firebase Production Campaign Database Access

## Overview
This skill documents how to query the **production Firestore database** for Your Project campaigns and user data.

## Critical Information

### Database Structure
```bash
Firestore Database: worldarchitecture-ai
└── users/
    └── {Firebase_Auth_UID}/
        └── campaigns/
            └── {campaign_id}/
                ├── title
                ├── created_at
                ├── last_played
                ├── world_name
                └── story/
                    └── {entry_id}/
                        ├── actor (user/gemini)
                        ├── text
                        └── timestamp
```

### User Identification
- Users are identified by **Firebase Auth UID**, NOT email
- Example UID: `vnLp2G3m21PJL6kxcuAqmWSOtm73`
- Use `auth.get_user_by_email()` to convert email → UID

## Prerequisites

### Environment Variables
```bash
export WORLDAI_DEV_MODE=true
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json
```

### Service Account Key
Location: `~/serviceAccountKey.json`
Project: `worldarchitecture-ai`

## Using campaign_manager.py

The recommended tool for production queries is `scripts/campaign_manager.py`.

### Find User by Email
```bash
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py find-user $USER@gmail.com
```

### Analyze User Activity (with token/cost estimation)
```bash
# Analyze last 3 months
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py analytics $USER@gmail.com

# Specific month
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py analytics $USER@gmail.com --month 2025-11
```

### Query Campaigns by Name
```bash
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py query <UID> "Campaign Name"
```

## Direct Python Query (Ad-hoc)

For custom queries, use this pattern:

```python
import sys
sys.path.insert(0, 'mvp_site')

# CRITICAL: Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, firestore, credentials
import os

# Initialize with explicit credentials
if firebase_admin._apps:
    firebase_admin.delete_app(firebase_admin.get_app())

cred = credentials.Certificate(os.path.expanduser('~/serviceAccountKey.json'))
firebase_admin.initialize_app(cred)
db = firestore.client()

# Find user by email
email = '$USER@gmail.com'
user_record = auth.get_user_by_email(email)
uid = user_record.uid

# Get campaigns
campaigns_ref = db.collection('users').document(uid).collection('campaigns')
for campaign in campaigns_ref.stream():
    data = campaign.to_dict()
    print(f"{campaign.id}: {data.get('title')}")

    # Get story entries
    story_ref = campaigns_ref.document(campaign.id).collection('story')
    entry_count = sum(1 for _ in story_ref.stream())
    print(f"  Entries: {entry_count}")
```

## Token/Cost Estimation Constants

From `$PROJECT_ROOT/llm_service.py`:
- **Base system instructions:** ~43,000 tokens
- **World content estimate:** ~50,000 tokens
- **Tokens per story entry:** ~500 tokens
- **Max history turns:** 100 (truncation limit)
- **200K threshold:** Above this = "long context" pricing (2x cost)

### Gemini 3 Pro Pricing
| Context Size | Input | Output |
|--------------|-------|--------|
| ≤200K tokens | $2/M  | $12/M  |
| >200K tokens | $4/M  | $18/M  |

## Common Issues

### Clock Skew Error
```text
Invalid JWT: Token must be a short-lived token (60 minutes)
```
**Solution:** Ensure `apply_clock_skew_patch()` is called BEFORE importing Firebase.

### Auth Provider Not Found
```text
No auth provider found for the given identifier
```
**Solution:** Use explicit credentials with `credentials.Certificate()`.

### Empty User List
If `firebase_user_analytics.py` shows only test users, you're likely missing real production users because:
1. The script was limiting to first 10 users
2. Real users have Firebase Auth UIDs, not test IDs like `test-user-123`

**Solution:** Use `campaign_manager.py analytics` with a known email address.

## Related Scripts
- `scripts/campaign_manager.py` - Main production query tool
- `scripts/firebase_user_analytics.py` - User behavior analytics
- `scripts/CLAUDE.md` - Script documentation
