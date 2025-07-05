# Firebase User Activity Report

Generated: 2025-07-04

## Executive Summary

Using Firebase collection group queries, we analyzed user activity across the WorldArchitect.AI platform:

- **Total Users**: 68 active users
- **Total Campaigns**: 1,787 campaigns created
- **Total Story Entries**: 15,885 story interactions
- **Average Campaigns per User**: 26.28
- **Average Entries per User**: 233.60

## Key Findings

### Most Active User
User `vnLp2G3m21PJL6kxcuAqmWSOtm73` dominates platform usage with:
- 228 campaigns (12.8% of all campaigns)
- 5,343 story entries (33.6% of all entries)
- Most active campaign: "Itachi Evil Campaign 2" with 1,069 entries

### User Engagement Patterns

1. **High Test Activity**: Many top users have IDs starting with "test-", indicating significant automated testing:
   - `test-validation-comparison`: 285 campaigns
   - `test-integration-user`: 259 campaigns
   - Test users represent ~50% of top 10 most active users

2. **Real User Engagement**: The top real user (`vnLp2G3m21PJL6kxcuAqmWSOtm73`) shows extremely high engagement with:
   - Average 23.4 entries per campaign (vs 6-7 for test users)
   - Long-running campaigns with hundreds of entries
   - Diverse campaign themes (Itachi, Sariel, Daemon)

3. **Campaign Depth**: Users show varying engagement patterns:
   - Power users: 20+ entries per campaign
   - Regular users: 5-10 entries per campaign
   - Test users: 3-7 entries per campaign (consistent with automated testing)

## Top 10 Most Active Users

| Rank | User ID | Campaigns | Entries | Avg/Campaign | Most Active Campaign |
|------|---------|-----------|---------|--------------|---------------------|
| 1 | vnLp2G3m21PJL6kxcuAqmWSOtm73 | 228 | 5,343 | 23.4 | Itachi Evil Campaign 2 (1,069 entries) |
| 2 | test-validation-comparison | 285 | 1,887 | 6.6 | Validation Test pydantic_run_5 |
| 3 | test-integration-user | 259 | 1,844 | 7.1 | Test |
| 4 | integration_test_user_standalone | 8 | 714 | 89.2 | Truncation Test Campaign |
| 5 | test-sariel-user | 63 | 644 | 10.2 | Sariel Test Campaign |
| 6 | test-validation-simple_run_0 | 36 | 387 | 10.8 | Validation Test simple_run_0 |
| 7 | test-validation-simple_run_1 | 32 | 338 | 10.6 | Validation Test simple_run_1 |
| 8 | test-cassian-simple_0 | 69 | 252 | 3.7 | Cassian Test simple_0 |
| 9 | test-cassian-simple_1 | 62 | 229 | 3.7 | Cassian Test simple_1 |
| 10 | test-sariel-0 | 34 | 257 | 7.6 | Sariel Test Campaign 1 |

## Technical Notes

### Collection Group Queries
This analysis used Firebase collection group queries to efficiently access all data:
- `collectionGroup('campaigns')` - Query all campaigns across all users
- `collectionGroup('story')` - Query all story entries across all campaigns

This approach is more efficient than iterating through individual user documents and provides a complete view of platform activity.

### Data Structure
The Firebase structure follows this pattern:
```
users/
  {user_id}/
    campaigns/
      {campaign_id}/
        story/
          {story_entry_id}
```

## Recommendations

1. **User Segmentation**: Separate test users from real users in analytics
2. **Engagement Metrics**: Track session length and return frequency
3. **Campaign Success**: Analyze what makes campaigns like "Itachi Evil Campaign 2" so engaging
4. **Performance Optimization**: Consider archiving old test data to improve query performance

## Files Generated

- `analysis/firebase_collection_group_analytics.csv` - Raw data export
- `analysis/firebase_user_activity_report.md` - This detailed report