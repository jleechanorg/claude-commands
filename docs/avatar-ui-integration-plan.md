# Engineering Plan: User Avatar UI Integration

**Author:** Claude (Genesis Coder)
**Date:** 2026-01-15
**Branch:** `claude/plan-avatar-ui-integration-Gd838`
**Status:** Planning
**Last Updated:** 2026-01-15
**Related Docs:** [Firebase Setup](../docs/firebase-setup.md), [API Reference](./api-reference.md)

### Change Log
| Date | Change |
|------|--------|
| 2026-01-15 | Initial plan created |
| 2026-01-15 | Added security considerations per code review |

---

## 1. Executive Summary

This document outlines the engineering plan for integrating user avatars into the campaign play UI. The feature allows users to:
1. **Upload a custom avatar** via a button in the top-right header area during gameplay
2. **Display their avatar** in the bottom-left corner during campaign gameplay
3. **Optionally upload an avatar during campaign creation** as part of the creation wizard

---

## 2. Current State Analysis

### 2.1 Frontend Architecture

**Campaign Play Page:** `mvp_site/frontend_v2/src/components/GamePlayView.tsx`

**Current Top-Right Layout (lines 371-386):**
```tsx
<div className="flex items-center space-x-2">
  <Button variant="ghost" size="sm">
    <Download className="w-4 h-4" />      {/* Download button */}
  </Button>
  <Button variant="ghost" size="sm">
    <Share className="w-4 h-4" />         {/* Share button */}
  </Button>
</div>
```

**Current Bottom Area (lines 431-470):**
- Input textarea for player actions
- God Mode toggle button
- Send button
- No avatar display currently

**Existing Avatar Component:** `mvp_site/frontend_v2/src/components/ui/avatar.tsx`
- Uses Radix UI `@radix-ui/react-avatar`
- Exports: `Avatar`, `AvatarImage`, `AvatarFallback`
- Already used in `Header.tsx` (lines 38-42) with fallback to initials

### 2.2 Backend Architecture

**User Settings Storage:** Firestore at `users/{user_id}/settings`

**Current Settings Schema:**
```python
{
    "llm_provider": str,
    "gemini_model": str,
    "openrouter_model": str,
    "cerebras_model": str,
    "theme": str,
    "auto_save": bool,
    "debug_mode": bool,
    "spicy_mode": bool,
    # Avatar fields to be added:
    # "avatar_url": str | None
}
```

**Firebase Storage:** Configured but not yet integrated
- Bucket: `FIREBASE_STORAGE_BUCKET` env var
- Frontend already imports storageBucket config in `lib/firebase.ts`

**Existing API Patterns:**
- `GET /api/settings` - Retrieve user settings
- `POST /api/settings` - Update user settings
- Export endpoint uses temp files + Flask `send_file()`

### 2.3 Authentication Flow
- Firebase Auth tokens via `Authorization: Bearer <token>`
- `@check_token` decorator validates and extracts `user_id`
- Frontend uses `useAuth()` hook for user state

### 2.3 Campaign Creation Architecture

**Campaign Creation Component:** `mvp_site/frontend_v2/src/components/CampaignCreationV2.tsx`

**Current 3-Step Wizard:**
1. **Step 1 - Campaign Basics:** title, type, character, setting, description
2. **Step 2 - AI Personalities:** defaultWorld, mechanicalPrecision, companions
3. **Step 3 - Review & Launch:** summary before creation

**Current API Request (`CampaignCreateRequest`):**
```typescript
{
  title: string;
  character?: string;
  setting?: string;
  description?: string;
  selected_prompts?: string[];
  custom_options?: string[];
}
```

**Backend Storage:** Firestore at `users/{user_id}/campaigns/{campaign_id}`
- Campaign document with title, initial_prompt, timestamps, settings
- Subcollections for game_states and story entries

---

## 3. Proposed UI Design

### 3.1 Avatar Upload in Campaign Creation (Step 1)

**Location:** Step 1 of campaign creation wizard, after character name field

**Visual Mockup:**
```
┌────────────────────────────────────────────────────────────────┐
│  Campaign Basics                                    Step 1/3   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Campaign Title *                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ My Epic Adventure                                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Character Name                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Thorin Ironforge                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Character Avatar (Optional)                                   │
│  ┌────────┐                                                    │
│  │  👤    │  Click to upload your character's portrait         │
│  │ +Add   │  PNG, JPG, GIF up to 5MB                          │
│  └────────┘                                                    │
│                                                                │
│  Setting                                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ A dark medieval world...                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Design Specifications:**
- Avatar upload is **optional** (not blocking campaign creation)
- Square clickable area with dashed border and "+" icon
- Preview thumbnail after selection (before upload)
- Option to remove selected image
- Upload happens during campaign creation API call

### 3.2 Avatar Upload Button (Top Right)

**Location:** To the LEFT of the existing Download button

**Visual Mockup:**
```
┌────────────────────────────────────────────────────────────────┐
│  < Back   Campaign Title   [Fantasy Badge]     [📷] [⬇️] [📤] │
│                                                Upload DL Share │
└────────────────────────────────────────────────────────────────┘
```

**Component Behavior:**
- Icon: Camera or User-Plus icon from lucide-react
- Click opens file picker dialog (accept: image/*)
- Shows loading spinner during upload
- Toast notification on success/failure

### 3.3 Avatar Display (Bottom Left)

**Location:** Bottom-left corner, above/beside the input area

**Visual Mockup:**
```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    Story/Narrative Display                     │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  ┌─────┐                                                       │
│  │ 👤  │  [Textarea: "What do you do?"]                       │
│  │Avatar│                                                      │
│  └─────┘                                                       │
│         [God Mode]                               [Send]        │
└────────────────────────────────────────────────────────────────┘
```

**Design Specifications:**
- Size: 48x48px (w-12 h-12) or 64x64px (w-16 h-16)
- Border: 2px ring with purple accent (`ring-2 ring-purple-500/50`)
- Fallback: User initials or default avatar icon
- Position: Fixed bottom-left, floating over content or docked

---

## 4. Technical Implementation

### 4.1 Backend Changes

#### 4.1.1 Firebase Storage Integration

**File:** `mvp_site/firestore_service.py`

```python
from firebase_admin import storage
from google.cloud.exceptions import GoogleCloudError

# Whitelist of allowed MIME types and their extensions
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}

class AvatarUploadError(Exception):
    """Custom exception for avatar upload failures."""
    pass

def upload_user_avatar(user_id: str, file_data: bytes, content_type: str) -> str:
    """Upload avatar to Firebase Storage and return public URL.

    Args:
        user_id: The authenticated user's ID
        file_data: Raw image bytes
        content_type: MIME type of the image

    Returns:
        Public URL of the uploaded avatar

    Raises:
        AvatarUploadError: If validation fails or upload errors occur
    """
    # Validate content_type is non-empty and contains "/"
    if not content_type or "/" not in content_type:
        raise AvatarUploadError(f"Invalid content type: {content_type}")

    # Validate against whitelist and get safe extension
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise AvatarUploadError(f"Unsupported image type: {content_type}")

    safe_ext = ALLOWED_AVATAR_TYPES[content_type]

    try:
        bucket = storage.bucket()
        blob = bucket.blob(f"avatars/{user_id}/avatar.{safe_ext}")
        blob.upload_from_string(file_data, content_type=content_type)
        blob.make_public()
        return blob.public_url
    except GoogleCloudError as e:
        logging_util.error(f"Firebase Storage upload failed for user {user_id}: {e}")
        raise AvatarUploadError(f"Storage upload failed: {e}") from e

def delete_user_avatar(user_id: str) -> bool:
    """Delete user's avatar from Firebase Storage.

    Args:
        user_id: The authenticated user's ID

    Returns:
        True if deletion succeeded

    Raises:
        AvatarUploadError: If deletion fails
    """
    try:
        bucket = storage.bucket()
        blobs = list(bucket.list_blobs(prefix=f"avatars/{user_id}/"))
        for blob in blobs:
            blob.delete()
        return True
    except GoogleCloudError as e:
        logging_util.error(f"Firebase Storage delete failed for user {user_id}: {e}")
        raise AvatarUploadError(f"Storage delete failed: {e}") from e
```

**Note:** The `upload_user_avatar` and `delete_user_avatar` functions will be implemented in `mvp_site/firestore_service.py`. The `update_user_settings` function already exists at `mvp_site/firestore_service.py:2094-2171`.

#### 4.1.2 New API Endpoint

**File:** `mvp_site/main.py`

```python
from mvp_site.firestore_service import (
    upload_user_avatar,
    delete_user_avatar,
    update_user_settings,
    AvatarUploadError,
    ALLOWED_AVATAR_TYPES,
)

MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file_size_streaming(file_storage, max_size: int) -> tuple[bool, bytes]:
    """Validate file size by streaming chunks without loading entire file.

    Args:
        file_storage: Flask FileStorage object
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, file_data) - file_data only populated if valid
    """
    chunks = []
    total_size = 0
    chunk_size = 8192  # 8KB chunks

    for chunk in iter(lambda: file_storage.stream.read(chunk_size), b""):
        total_size += len(chunk)
        if total_size > max_size:
            return False, b""
        chunks.append(chunk)

    return True, b"".join(chunks)


@app.route("/api/avatar", methods=["POST"])
@limiter.limit("5 per hour")  # Rate limit avatar uploads
@check_token
async def upload_avatar():
    """Upload user avatar image."""
    user_id = request.user_id

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    # Validate file type against whitelist
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    # Validate file size via streaming (doesn't load entire file if too large)
    is_valid_size, file_data = validate_file_size_streaming(file, MAX_AVATAR_SIZE)
    if not is_valid_size:
        return jsonify({"success": False, "error": "File too large (max 5MB)"}), 400

    try:
        # Upload to Firebase Storage (see firestore_service.py implementation)
        avatar_url = upload_user_avatar(user_id, file_data, file.content_type)

        # Save URL to user settings (existing function in firestore_service.py:2094)
        update_user_settings(user_id, {"avatar_url": avatar_url})

        return jsonify({"success": True, "avatar_url": avatar_url})
    except AvatarUploadError as e:
        logging_util.error(f"Avatar upload failed for user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/avatar", methods=["DELETE"])
@check_token
async def delete_avatar():
    """Delete user avatar."""
    user_id = request.user_id
    try:
        delete_user_avatar(user_id)
        update_user_settings(user_id, {"avatar_url": None})
        return jsonify({"success": True})
    except AvatarUploadError as e:
        logging_util.error(f"Avatar delete failed for user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

#### 4.1.3 Settings Schema Update

**File:** `mvp_site/main.py` (line ~2390)

Add `"avatar_url"` to the valid settings keys set.

### 4.2 Frontend Changes

#### 4.2.1 API Service Extension

**File:** `mvp_site/frontend_v2/src/services/api.service.ts`

```typescript
/**
 * Upload user avatar
 */
async uploadAvatar(file: File): Promise<{ success: boolean; avatar_url?: string; error?: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await this.authenticatedRequest('/avatar', {
    method: 'POST',
    body: formData,
    // Don't set Content-Type - browser will set multipart/form-data with boundary
  });

  return response.json();
}

/**
 * Delete user avatar
 */
async deleteAvatar(): Promise<{ success: boolean }> {
  const response = await this.authenticatedRequest('/avatar', {
    method: 'DELETE',
  });
  return response.json();
}
```

#### 4.2.2 Type Definitions

**File:** `mvp_site/frontend_v2/src/services/api.types.ts`

```typescript
export interface UserSettings {
  // Existing fields...
  avatar_url?: string | null;
}
```

#### 4.2.3 Auth Store Extension

**File:** `mvp_site/frontend_v2/src/stores/authStore.ts`

Add `avatarUrl` to user state and fetch it with settings.

#### 4.2.4 GamePlayView Component Changes

**File:** `mvp_site/frontend_v2/src/components/GamePlayView.tsx`

**A. Add Upload Button (top right, before Download):**

```tsx
import { Camera, Download, Share } from 'lucide-react';
import { useRef } from 'react';

// Inside component:
const fileInputRef = useRef<HTMLInputElement>(null);
const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
const [isUploading, setIsUploading] = useState(false);

const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;

  setIsUploading(true);
  try {
    const result = await apiService.uploadAvatar(file);
    if (result.success && result.avatar_url) {
      setAvatarUrl(result.avatar_url);
      // Show success toast
    }
  } catch (error) {
    // Show error toast
  } finally {
    setIsUploading(false);
  }
};

// In JSX (top right buttons area):
<div className="flex items-center space-x-2">
  <input
    type="file"
    ref={fileInputRef}
    onChange={handleAvatarUpload}
    accept="image/*"
    className="hidden"
  />
  <Button
    variant="ghost"
    size="sm"
    className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
    onClick={() => fileInputRef.current?.click()}
    disabled={isUploading}
  >
    {isUploading ? (
      <RefreshCw className="w-4 h-4 animate-spin" />
    ) : (
      <Camera className="w-4 h-4" />
    )}
  </Button>
  <Button variant="ghost" size="sm" /* Download button */ >
    <Download className="w-4 h-4" />
  </Button>
  <Button variant="ghost" size="sm" /* Share button */ >
    <Share className="w-4 h-4" />
  </Button>
</div>
```

**B. Add Avatar Display (bottom left):**

```tsx
import { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';

// In JSX (input area, left side):
<div className="bg-white/80 backdrop-blur-md border border-purple-200 rounded-lg p-6 shadow-lg">
  <div className="flex gap-4">
    {/* Avatar Display - Bottom Left */}
    <div className="flex-shrink-0">
      <Avatar className="w-12 h-12 ring-2 ring-purple-500/50">
        {avatarUrl ? (
          <AvatarImage src={avatarUrl} alt="Your avatar" />
        ) : null}
        <AvatarFallback className="bg-gradient-to-br from-purple-600 to-purple-700 text-white text-sm font-semibold">
          {user?.displayName?.charAt(0) || 'P'}
        </AvatarFallback>
      </Avatar>
    </div>

    {/* Input Area */}
    <div className="flex-1">
      <Textarea
        ref={textareaRef}
        value={playerInput}
        // ... existing props
      />
    </div>
  </div>

  {/* Existing button row */}
  <div className="flex items-center justify-between mt-4">
    {/* ... existing God Mode and Send buttons */}
  </div>
</div>
```

### 4.3 Campaign Creation Avatar (Optional)

#### 4.3.1 Backend: Campaign Avatar Storage

**File:** `mvp_site/firestore_service.py`

```python
def upload_campaign_avatar(user_id: str, campaign_id: str, file_data: bytes, content_type: str) -> str:
    """Upload campaign-specific avatar to Firebase Storage.

    Args:
        user_id: The authenticated user's ID
        campaign_id: The campaign ID to associate avatar with
        file_data: Raw image bytes
        content_type: MIME type of the image

    Returns:
        Public URL of the uploaded avatar

    Raises:
        AvatarUploadError: If validation fails or upload errors occur
    """
    # Reuse same validation as user avatars
    if not content_type or "/" not in content_type:
        raise AvatarUploadError(f"Invalid content type: {content_type}")

    if content_type not in ALLOWED_AVATAR_TYPES:
        raise AvatarUploadError(f"Unsupported image type: {content_type}")

    safe_ext = ALLOWED_AVATAR_TYPES[content_type]

    try:
        bucket = storage.bucket()
        blob = bucket.blob(f"campaign_avatars/{user_id}/{campaign_id}/avatar.{safe_ext}")
        blob.upload_from_string(file_data, content_type=content_type)
        blob.make_public()
        return blob.public_url
    except GoogleCloudError as e:
        logging_util.error(f"Campaign avatar upload failed for {user_id}/{campaign_id}: {e}")
        raise AvatarUploadError(f"Storage upload failed: {e}") from e
```

#### 4.3.2 Backend: Extended Campaign Creation

**File:** `mvp_site/main.py`

Modify `POST /api/campaigns` to optionally accept multipart/form-data with avatar:

```python
@app.route("/api/campaigns", methods=["POST"])
@check_token
async def create_campaign_route():
    user_id = request.user_id

    # Handle both JSON and multipart/form-data
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Extract form fields
        campaign_data = {
            "title": request.form.get("title"),
            "character": request.form.get("character"),
            "setting": request.form.get("setting"),
            "description": request.form.get("description"),
            "selected_prompts": json.loads(request.form.get("selected_prompts", "[]")),
        }
        avatar_file = request.files.get("avatar")
    else:
        # Standard JSON request
        campaign_data = request.json
        avatar_file = None

    # Create campaign first
    result = await mcp_client.call_tool("create_campaign", {
        "user_id": user_id,
        **campaign_data
    })

    campaign_id = result.get("campaign_id")

    # If avatar provided, upload and store URL
    if avatar_file and campaign_id:
        avatar_url = upload_campaign_avatar(
            user_id, campaign_id,
            avatar_file.read(),
            avatar_file.content_type
        )
        # Store avatar_url in campaign document
        update_campaign_avatar(user_id, campaign_id, avatar_url)
        result["avatar_url"] = avatar_url

    return jsonify(result), 201
```

#### 4.3.3 Frontend: Campaign Creation Form Changes

**File:** `mvp_site/frontend_v2/src/components/CampaignCreationV2.tsx`

**A. Add State for Avatar:**

```tsx
const [avatarFile, setAvatarFile] = useState<File | null>(null);
const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
const avatarInputRef = useRef<HTMLInputElement>(null);

const handleAvatarSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please select a valid image file (JPEG, PNG, GIF, or WebP)');
      return;
    }
    // Validate file size
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be under 5MB');
      return;
    }
    setAvatarFile(file);

    // Create preview URL with proper error handling
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === 'string') {
        setAvatarPreview(result);
      }
    };
    reader.onerror = () => {
      toast.error('Failed to read image file. Please try again.');
      setAvatarFile(null);
      setAvatarPreview(null);
    };
    reader.onabort = () => {
      toast.warning('Image loading was cancelled.');
      setAvatarFile(null);
      setAvatarPreview(null);
    };
    reader.readAsDataURL(file);
  }
};

const removeAvatar = () => {
  setAvatarFile(null);
  setAvatarPreview(null);
  if (avatarInputRef.current) avatarInputRef.current.value = '';
};
```

**B. Add Avatar UI in Step 1 (after Character Name):**

```tsx
{/* Character Avatar (Optional) */}
<div className="space-y-2">
  <Label>Character Avatar (Optional)</Label>
  <div className="flex items-center gap-4">
    <input
      type="file"
      ref={avatarInputRef}
      onChange={handleAvatarSelect}
      accept="image/jpeg,image/png,image/gif,image/webp"
      className="hidden"
    />

    {avatarPreview ? (
      <div className="relative">
        <Avatar className="w-20 h-20 ring-2 ring-purple-500/50">
          <AvatarImage src={avatarPreview} alt="Character avatar preview" />
        </Avatar>
        <button
          onClick={removeAvatar}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    ) : (
      <button
        type="button"
        onClick={() => avatarInputRef.current?.click()}
        className="w-20 h-20 border-2 border-dashed border-purple-300 rounded-lg flex flex-col items-center justify-center hover:border-purple-500 transition-colors"
      >
        <Plus className="w-6 h-6 text-purple-400" />
        <span className="text-xs text-purple-500 mt-1">Add</span>
      </button>
    )}

    <div className="text-sm text-gray-500">
      <p>Click to upload your character's portrait</p>
      <p>PNG, JPG, GIF, WebP up to 5MB</p>
    </div>
  </div>
</div>
```

**C. Modify Form Submission to Include Avatar:**

```tsx
const handleCreate = async () => {
  // ... existing validation ...

  // If avatar selected, use FormData
  if (avatarFile) {
    const formData = new FormData();
    formData.append('title', formState.title);
    formData.append('character', formState.character);
    formData.append('setting', formState.setting);
    formData.append('description', formState.description);
    formData.append('selected_prompts', JSON.stringify(selectedPrompts));
    formData.append('avatar', avatarFile);

    const response = await apiService.createCampaignWithAvatar(formData);
    // ... handle response
  } else {
    // Standard JSON request
    const response = await apiService.createCampaign(campaignData);
    // ... handle response
  }
};
```

#### 4.3.4 API Service: Campaign Creation with Avatar

**File:** `mvp_site/frontend_v2/src/services/api.service.ts`

```typescript
/**
 * Create campaign with optional avatar upload
 */
async createCampaignWithAvatar(formData: FormData): Promise<CampaignCreateResponse> {
  const response = await this.authenticatedRequest('/campaigns', {
    method: 'POST',
    body: formData,
    // Don't set Content-Type - browser will set multipart/form-data with boundary
  });

  return response.json();
}
```

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GamePlayView.tsx                                               │
│  ┌─────────────────┐    ┌────────────────────────────────────┐ │
│  │ Upload Button   │───▶│ handleAvatarUpload()               │ │
│  │ (Camera icon)   │    │  - Read file                       │ │
│  └─────────────────┘    │  - Call apiService.uploadAvatar()  │ │
│                         └────────────────────────────────────┘ │
│                                       │                         │
│  ┌─────────────────┐                  ▼                         │
│  │ Avatar Display  │◀─── avatarUrl state                        │
│  │ (Bottom Left)   │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  api.service.ts                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ uploadAvatar(file: File)                                   │ │
│  │  - Create FormData                                         │ │
│  │  - POST /api/avatar with auth header                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flask Backend (main.py)                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ POST /api/avatar                                           │ │
│  │  - @check_token decorator validates auth                   │ │
│  │  - Validate file type and size                             │ │
│  │  - Call upload_user_avatar()                               │ │
│  │  - Call update_user_settings()                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Firebase Storage                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Bucket: worldarchitecture-ai.firebasestorage.app           │ │
│  │ Path: avatars/{user_id}/avatar.{ext}                       │ │
│  │ Access: Public URL returned                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Firestore                                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ users/{user_id}/settings.avatar_url = <public_url>         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. File Changes Summary

| File | Action | Changes |
|------|--------|---------|
| `mvp_site/firestore_service.py` | MODIFY | Add `upload_user_avatar()`, `delete_user_avatar()`, `upload_campaign_avatar()` |
| `mvp_site/main.py` | MODIFY | Add `POST/DELETE /api/avatar` endpoints, modify `POST /api/campaigns` for multipart, add `avatar_url` to valid settings |
| `frontend_v2/src/services/api.service.ts` | MODIFY | Add `uploadAvatar()`, `deleteAvatar()`, `createCampaignWithAvatar()` methods |
| `frontend_v2/src/services/api.types.ts` | MODIFY | Add `avatar_url` to `UserSettings` and `Campaign` interfaces |
| `frontend_v2/src/components/GamePlayView.tsx` | MODIFY | Add upload button (top right), avatar display (bottom left) |
| `frontend_v2/src/components/CampaignCreationV2.tsx` | MODIFY | Add optional avatar upload field in Step 1, modify submission to use FormData |
| `mvp_site/tests/test_avatar_api.py` | CREATE | Unit tests for avatar upload/delete endpoints |
| `mvp_site/tests/test_campaign_avatar.py` | CREATE | Unit tests for campaign creation with avatar |

---

## 7. Implementation Phases

### Phase 1: Backend Foundation
1. Add Firebase Storage helper functions to `firestore_service.py`
   - `upload_user_avatar()` - User profile avatar
   - `delete_user_avatar()` - Remove user avatar
   - `upload_campaign_avatar()` - Campaign-specific avatar
2. Add `POST /api/avatar` endpoint to `main.py`
3. Add `DELETE /api/avatar` endpoint to `main.py`
4. Modify `POST /api/campaigns` to accept multipart/form-data with optional avatar
5. Update valid settings keys to include `avatar_url`
6. Write unit tests for new endpoints

### Phase 2: Frontend - Campaign Play Avatar
1. Add `uploadAvatar()` and `deleteAvatar()` to `api.service.ts`
2. Update `api.types.ts` with avatar_url field
3. Add upload button to `GamePlayView.tsx` (top right)
4. Add avatar display to `GamePlayView.tsx` (bottom left)
5. Fetch and display existing avatar on component mount

### Phase 3: Frontend - Campaign Creation Avatar
1. Add avatar selection state to `CampaignCreationV2.tsx`
2. Add avatar upload UI in Step 1 (after character name)
3. Add `createCampaignWithAvatar()` to `api.service.ts`
4. Modify form submission to use FormData when avatar selected
5. Display avatar preview in Step 3 review

### Phase 4: Polish & Edge Cases
1. Add loading states and error handling
2. Add toast notifications for upload success/failure
3. Handle image compression for large files (optional)
4. Add avatar removal UI (click avatar to show remove option)
5. Cache avatar URL in local state to avoid refetching
6. Display campaign avatar in campaign list cards (optional)

---

## 8. Security Considerations

### Core Security (Must Have)
1. **File Type Validation:** Only accept `image/jpeg`, `image/png`, `image/gif`, `image/webp` via whitelist
2. **File Size Limit:** Max 5MB per upload, validated via streaming (not loading entire file)
3. **Authentication Required:** All avatar endpoints require valid Firebase token via `@check_token`
4. **Storage Path Isolation:** Each user's avatar stored under `avatars/{user_id}/`
5. **Public URL:** Avatar images are public (required for display), but path includes user_id

### Production Hardening (Recommended)
6. **Rate Limiting:** Per-user upload caps (5 uploads/hour) via `@limiter.limit()` decorator on upload handler
7. **Image Sanitization/Re-encoding:** Server-side re-encode to strip EXIF/metadata and neutralize image-bombs or embedded exploits. Enforcement: upload handler before storage write
8. **CORS Configuration:** Explicit Firebase Storage bucket CORS rules for browser access. Enforcement: Firebase Storage bucket settings
9. **Content Security Policy (CSP):** CSP headers restricting `img-src` when serving avatars. Enforcement: CDN/web server response headers
10. **Storage Cleanup:** Periodic job to remove orphaned avatars for deleted users. Enforcement: Cloud Function or cron job on storage lifecycle
11. **Malware Scanning:** Optional integration with virus/malware scanning for uploaded files. Enforcement: upload handler before storage write (e.g., VirusTotal API, Cloud Functions trigger)

### Implementation Notes
- Items 1-5 are implemented in the upload handler (`main.py`)
- Items 6-7 should be added during Phase 1 implementation
- Items 8-11 are infrastructure-level and can be added in Phase 4 (Polish)

---

## 9. Testing Strategy

### Unit Tests - User Avatar
- `test_avatar_upload_success`: Valid image upload returns URL
- `test_avatar_upload_invalid_type`: Reject non-image files
- `test_avatar_upload_too_large`: Reject files > 5MB
- `test_avatar_upload_no_auth`: Reject unauthenticated requests
- `test_avatar_delete_success`: Delete removes from storage and settings
- `test_avatar_url_in_settings`: Avatar URL persisted in user settings

### Unit Tests - Campaign Avatar
- `test_campaign_create_with_avatar`: Campaign creation with avatar returns campaign_id and avatar_url
- `test_campaign_create_without_avatar`: Campaign creation without avatar works normally (backward compatible)
- `test_campaign_avatar_stored_correctly`: Avatar URL stored in campaign document
- `test_campaign_avatar_invalid_type`: Reject non-image files during creation

### Integration Tests
- Upload avatar and verify it appears in campaign view
- Delete avatar and verify fallback displays
- Cross-session persistence (avatar persists after refresh)
- Create campaign with avatar and verify it displays in play view
- Create campaign without avatar and verify fallback works

---

## 10. Open Questions

1. **Avatar in Settings Page?** Should we also add avatar management to `/settings`?
2. **Avatar Size Options?** Should we offer different sizes (small/medium/large)?
3. **Avatar Cropping?** Should we add client-side cropping before upload?
4. **Default Avatars?** Should we offer a set of preset fantasy-themed avatars?

---

## 11. Dependencies

### Backend
- `firebase-admin` (already installed) - for Firebase Storage
- No new dependencies required

### Frontend
- `lucide-react` (already installed) - Camera icon
- `@radix-ui/react-avatar` (already installed) - Avatar component
- No new dependencies required

---

## 12. Appendix: Existing Code References

### Avatar Component Usage (Header.tsx)
```tsx
<Avatar className="w-8 h-8 sm:w-10 sm:h-10 ring-2 ring-purple-500/50">
  <AvatarFallback className="bg-gradient-to-br from-purple-600 to-purple-700 text-white">
    {user.displayName?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
  </AvatarFallback>
</Avatar>
```

### Firebase Config (firebase.ts)
```typescript
const firebaseConfig = {
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  // ... other config
}
```

### Settings API Pattern (main.py)
```python
@app.route("/api/settings", methods=["GET", "POST"])
@check_token
async def api_settings():
    user_id = request.user_id
    if request.method == "GET":
        settings = get_user_settings(user_id)
        return jsonify(settings)
    # POST handling...
```
