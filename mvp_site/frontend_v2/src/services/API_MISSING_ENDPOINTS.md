# Missing API Endpoints Documentation

This document lists API endpoints that the frontend needs but are not currently implemented in the Flask backend.

## 1. DELETE /api/campaigns/{campaign_id}

**Purpose**: Delete a campaign and all its associated data.

**Expected Behavior**:
- Remove the campaign from the user's campaign list
- Delete all associated story entries
- Delete the game state
- Return 204 No Content on success

**Current Status**: Not implemented. The backend has no delete endpoint for campaigns.

**Frontend Implementation**: The `deleteCampaign()` method in api.service.ts throws an error indicating this is not implemented.

## 2. GET /api/user or GET /api/me

**Purpose**: Get detailed information about the currently authenticated user.

**Expected Response**:
```json
{
  "uid": "user123",
  "email": "user@example.com",
  "displayName": "User Name",
  "photoURL": "https://...",
  "created_at": "2024-01-01T00:00:00Z",
  "settings": {
    "debug_mode": false,
    "gemini_model": "gemini-2.5-flash"
  }
}
```

**Current Status**: User information is only available through Firebase Auth on the client side. No backend endpoint provides user profile data.

**Workaround**: The frontend uses Firebase Auth directly to get user information.

## 3. POST /api/auth/login and POST /api/auth/logout

**Purpose**: Server-side authentication endpoints for session management.

**Current Status**: Authentication is handled entirely client-side through Firebase. The backend only validates tokens on each request.

**Note**: This might be intentional design, as Firebase Auth is designed for client-side use.

## 4. GET /api/health

**Purpose**: Health check endpoint for monitoring backend availability.

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

**Current Status**: Not implemented. The frontend api.js file references this endpoint for health checks but it doesn't exist.

## 5. GET /api/campaigns/{campaign_id}/stats

**Purpose**: Get statistics and analytics for a campaign.

**Potential Response**:
```json
{
  "total_interactions": 42,
  "total_play_time": 3600,
  "character_level": 5,
  "last_played": "2024-01-01T00:00:00Z",
  "created_at": "2023-12-01T00:00:00Z"
}
```

**Current Status**: Not implemented. Campaign statistics would need to be calculated from existing data.

## 6. POST /api/campaigns/{campaign_id}/fork

**Purpose**: Create a copy of an existing campaign.

**Expected Behavior**:
- Create a new campaign with the same initial state
- Copy the prompt and settings
- Don't copy the story history
- Return the new campaign ID

**Current Status**: Not implemented.

## 7. PATCH /api/campaigns/{campaign_id}/archive

**Purpose**: Archive/unarchive a campaign without deleting it.

**Expected Request**:
```json
{
  "archived": true
}
```

**Current Status**: Not implemented. Campaigns have no archive functionality.

## Notes for Frontend Developers

1. **Error Handling**: All missing endpoints are documented in the service methods with appropriate error messages.

2. **Test Mode**: The API service supports test mode bypass for authentication, which works with existing endpoints.

3. **Future Compatibility**: The service methods are implemented with the expected signatures, so when backend endpoints are added, only the error throwing needs to be removed.

4. **Workarounds**:
   - User info comes from Firebase Auth directly
   - Campaign deletion is not available (users must keep all campaigns)
   - Health checks fail silently with a console warning
