# Firebase Production Campaign Database Access

## Overview
This skill documents how to query the **production Firestore database** for WorldArchitect.AI campaigns and user data.

## CRITICAL: Campaign Lookup

**Campaigns are NESTED under users, NOT at root level!**

```python
# WRONG - This queries the wrong collection (test data only):
db.collection('campaigns').document('VqqJLpABua9bvAG4ArTg')

# CORRECT - Campaigns are nested under user UID:
db.collection('users').document(uid).collection('campaigns').document('VqqJLpABua9bvAG4ArTg')
```

### Quick Lookup for Known Campaign ID
```python
# 1. Get user UID from email
user_record = auth.get_user_by_email('jleechan@gmail.com')
uid = user_record.uid  # e.g., 'vnLp2G3m21PJL6kxcuAqmWSOtm73'

# 2. Query nested path
doc = db.collection('users').document(uid).collection('campaigns').document('CAMPAIGN_ID').get()
```

## Database Structure

```
Firestore Database: worldarchitecture-ai
├── campaigns/                    # ← WRONG: Only test data here (5 campaigns)
│   └── {test_campaign_id}/
│
└── users/                        # ← CORRECT: Real user data here (146+ campaigns)
    └── {Firebase_Auth_UID}/      # e.g., vnLp2G3m21PJL6kxcuAqmWSOtm73
        └── campaigns/
            └── {campaign_id}/    # e.g., VqqJLpABua9bvAG4ArTg
                ├── title         # "Nocturne post bg3 zhent"
                ├── created_at
                ├── last_played
                ├── world_name
                ├── game_states/              # ← SUBCOLLECTION for game state
                │   └── current_state/        # Main game state document
                │       ├── player_character_data
                │       ├── combat_state
                │       ├── npc_data
                │       └── custom_campaign_state/
                │           └── god_mode_directives[]  # ← Persisted rules
                └── story/
                    └── {entry_id}/
                        ├── actor (user/gemini)
                        ├── text
                        └── timestamp
```

## IMPORTANT: Game State Location

**Game state is in a SUBCOLLECTION, not a field!**

```python
# WRONG - game_state is NOT a field on the campaign document:
campaign = db.collection('users').document(uid).collection('campaigns').document(campaign_id).get()
game_state = campaign.to_dict().get('game_state')  # Returns empty!

# CORRECT - game_state is in a subcollection called 'game_states':
game_state_ref = db.collection('users').document(uid).collection('campaigns').document(campaign_id).collection('game_states').document('current_state')
game_state = game_state_ref.get().to_dict()
```

### Querying God Mode Directives

```python
# Get god mode directives for a campaign
game_state_ref = campaign_ref.collection('game_states').document('current_state')
game_state = game_state_ref.get().to_dict()

custom_campaign_state = game_state.get('custom_campaign_state', {})
god_mode_directives = custom_campaign_state.get('god_mode_directives', [])

for directive in god_mode_directives:
    if isinstance(directive, dict):
        print(f"Rule: {directive.get('rule')}")
        print(f"Added: {directive.get('added')}")
```

## User Identification
- Users are identified by **Firebase Auth UID**, NOT email
- Primary user: `jleechan@gmail.com` → UID: `vnLp2G3m21PJL6kxcuAqmWSOtm73`
- Test user: `jleechantest@gmail.com`
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
python scripts/campaign_manager.py find-user jleechan@gmail.com
```

### Analyze User Activity (with token/cost estimation)
```bash
# Analyze last 3 months
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py analytics jleechan@gmail.com

# Specific month
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python scripts/campaign_manager.py analytics jleechan@gmail.com --month 2025-11
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
email = 'jleechan@gmail.com'
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

From `mvp_site/llm_service.py`:
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
```
Invalid JWT: Token must be a short-lived token (60 minutes)
```
**Solution:** Ensure `apply_clock_skew_patch()` is called BEFORE importing Firebase.

### Auth Provider Not Found
```
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
