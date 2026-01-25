# Yoga Flashcards - API Reference

**Base URL:** `http://localhost:8000/api/`

**Authentication:** Session-based (Django sessions)

**Content-Type:** `application/json` (except file uploads: `multipart/form-data`)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Flashcards](#flashcards)
3. [Tags](#tags)
4. [Daily Card](#daily-card)
5. [User Management (Admin)](#user-management-admin)
6. [Health Check](#health-check)

---

## Authentication

### POST /users/register/

Create a new user account.

**Permission:** AllowAny

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

**Errors:**
- `400` - Validation error (passwords don't match, email exists, etc.)

---

### POST /users/login/

Authenticate user and create session.

**Permission:** AllowAny

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

**Errors:**
- `400` - Invalid credentials
- `400` - Account inactive

**Note:** Sets `sessionid` and `csrftoken` cookies.

---

### POST /users/logout/

End user session.

**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /users/auth-status/

Check current authentication status.

**Permission:** AllowAny

**Response (200 OK) - Authenticated:**
```json
{
  "is_authenticated": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  }
}
```

**Response (200 OK) - Not Authenticated:**
```json
{
  "is_authenticated": false
}
```

---

### GET /users/profile/

Get current user's profile.

**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "bio": "Yoga enthusiast",
  "avatar": "/media/avatars/user1.jpg",
  "favorite_cards": [1, 3, 5]
}
```

---

### PUT /users/profile/

Update current user's profile.

**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "bio": "Updated bio",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response (200 OK):** Updated profile object

---

## Flashcards

### GET /cards/

List all live, active flashcards with pagination.

**Permission:** IsAuthenticated

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search across title, phrase, definition, tags |
| `tags` | string | Comma-separated tag IDs or names |
| `page` | integer | Page number (default: 1) |

**Example:** `GET /cards/?search=yoga&tags=Yamas,Sanskrit&page=1`

**Response (200 OK):**
```json
{
  "count": 18,
  "next": "http://localhost:8000/api/cards/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Ahimsa",
      "phrase": "अहिंसा",
      "definition": "Non-violence or non-harming is the first and most important of the yamas...",
      "short_answer": "Non-violence",
      "front_image": "http://localhost:8000/media/flashcard_images/ahimsa_front.jpg",
      "back_image": null,
      "tags": [
        {"id": 1, "name": "Yamas", "description": "Ethical restraints"}
      ],
      "version_group": "550e8400-e29b-41d4-a716-446655440000",
      "version_number": 1,
      "is_live": true,
      "created_by": "admin",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST /cards/

Create a new flashcard.

**Permission:** IsCuratorOrAdmin

**Content-Type:** `multipart/form-data`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Card title (max 200 chars) |
| `phrase` | string | Yes | Sanskrit phrase (max 500 chars) |
| `definition` | string | Yes | Full definition |
| `short_answer` | string | No | Brief summary |
| `tags` | string/array | No | Tag names or IDs (repeatable) |
| `front_image` | file | No | Front image file |
| `back_image` | file | No | Back image file |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/cards/ \
  -H "Cookie: sessionid=..." \
  -F "title=Satya" \
  -F "phrase=सत्य" \
  -F "definition=Truthfulness in thought, word, and deed..." \
  -F "short_answer=Truthfulness" \
  -F "tags=Yamas" \
  -F "tags=Sanskrit" \
  -F "front_image=@/path/to/image.jpg"
```

**Response (201 Created):**
```json
{
  "id": 2,
  "title": "Satya",
  "phrase": "सत्य",
  "definition": "Truthfulness in thought, word, and deed...",
  "short_answer": "Truthfulness",
  "front_image": "http://localhost:8000/media/flashcard_images/satya_front.jpg",
  "back_image": null,
  "tags": [
    {"id": 1, "name": "Yamas"},
    {"id": 2, "name": "Sanskrit"}
  ],
  "version_group": "660e8400-e29b-41d4-a716-446655440001",
  "version_number": 1,
  "is_live": true,
  "created_by": "curator1",
  "created_at": "2025-01-25T10:00:00Z",
  "updated_at": "2025-01-25T10:00:00Z"
}
```

---

### GET /cards/{id}/

Get single card details.

**Permission:** IsAuthenticated

**Response (200 OK):** Single flashcard object (same structure as list results)

**Errors:**
- `404` - Card not found

---

### PUT /cards/{id}/

Update a card. **Creates a new version** rather than updating in place.

**Permission:** IsCuratorOrAdmin

**Content-Type:** `multipart/form-data`

**Request Body:** Same as POST /cards/

**Response (200 OK):**
```json
{
  "id": 5,
  "title": "Ahimsa",
  "phrase": "अहिंसा",
  "definition": "Updated definition...",
  "short_answer": "Non-violence",
  "front_image": "...",
  "back_image": null,
  "tags": [...],
  "version_group": "550e8400-e29b-41d4-a716-446655440000",
  "version_number": 2,
  "is_live": true,
  "created_by": "curator1",
  "created_at": "2025-01-25T12:00:00Z",
  "updated_at": "2025-01-25T12:00:00Z"
}
```

**Important:** The response contains a **NEW ID** because a new version was created. The old version (ID 1) now has `is_live=false`.

---

### DELETE /cards/{id}/

Soft delete a card. Sets `is_active=false`.

**Permission:** IsCuratorOrAdmin

**Response (204 No Content)**

**Errors:**
- `404` - Card not found

---

### GET /cards/{id}/versions/

Get complete version history for a card.

**Permission:** IsCuratorOrAdmin

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "version_number": 2,
    "is_live": true,
    "is_active": true,
    "title": "Ahimsa",
    "phrase": "अहिंसा",
    "definition": "Updated definition...",
    "short_answer": "Non-violence",
    "created_by_username": "curator1",
    "created_at": "2025-01-25T12:00:00Z"
  },
  {
    "id": 1,
    "version_number": 1,
    "is_live": false,
    "is_active": true,
    "title": "Ahimsa",
    "phrase": "अहिंसा",
    "definition": "Original definition...",
    "short_answer": "Non-violence",
    "created_by_username": "admin",
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

**Note:** Versions are ordered by `version_number` descending (newest first).

---

### POST /cards/{id}/revert_version/

Revert to a previous version. Creates a **new version** copying content from the selected version.

**Permission:** IsCuratorOrAdmin

**Request Body:**
```json
{
  "version_id": 1
}
```

**Response (200 OK):**
```json
{
  "id": 6,
  "title": "Ahimsa",
  "phrase": "अहिंसा",
  "definition": "Original definition...",
  "short_answer": "Non-violence",
  "version_group": "550e8400-e29b-41d4-a716-446655440000",
  "version_number": 3,
  "is_live": true,
  "created_by": "curator1",
  "created_at": "2025-01-25T14:00:00Z",
  "message": "Successfully reverted to version 1"
}
```

**Important:** A **new version** is created with `version_number=3`. The content is copied from version 1.

**Errors:**
- `400` - version_id not provided
- `404` - Target version not found or not in same version group

---

## Tags

### GET /tags/

List all tags.

**Permission:** AllowAny

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {"id": 1, "name": "8 Limbs", "description": "The eight limbs of yoga"},
    {"id": 2, "name": "Niyamas", "description": "Observances"},
    {"id": 3, "name": "Sanskrit", "description": "Sanskrit terms"},
    {"id": 4, "name": "Yamas", "description": "Ethical restraints"},
    {"id": 5, "name": "Asana", "description": "Physical postures"}
  ]
}
```

---

### POST /tags/

Create a new tag.

**Permission:** IsCuratorOrAdmin

**Request Body:**
```json
{
  "name": "Pranayama",
  "description": "Breath control techniques"
}
```

**Response (201 Created):**
```json
{
  "id": 6,
  "name": "Pranayama",
  "description": "Breath control techniques"
}
```

**Errors:**
- `400` - Tag name already exists

---

### GET /tags/{id}/

Get single tag details.

**Permission:** AllowAny

**Response (200 OK):** Single tag object

---

### PUT /tags/{id}/

Update a tag.

**Permission:** IsCuratorOrAdmin

**Request Body:**
```json
{
  "name": "Pranayama",
  "description": "Updated description"
}
```

**Response (200 OK):** Updated tag object

---

### DELETE /tags/{id}/

Delete a tag.

**Permission:** IsCuratorOrAdmin

**Response (204 No Content)**

**Note:** Deleting a tag removes it from all associated cards.

---

## Daily Card

### GET /dailycard/

Get today's daily card.

**Permission:** AllowAny (public access)

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Ahimsa",
  "phrase": "अहिंसा",
  "definition": "Non-violence or non-harming is the first and most important of the yamas...",
  "short_answer": "Non-violence",
  "front_image": "http://localhost:8000/media/flashcard_images/ahimsa_front.jpg",
  "back_image": null,
  "tags": [
    {"id": 1, "name": "Yamas", "description": "Ethical restraints"}
  ]
}
```

**Behavior:**
1. Returns the same card for the entire calendar day (UTC)
2. On the first request of each day, selects a new card
3. Cards rotate through all available cards before repeating
4. Only selects from `is_active=True` and `is_live=True` cards

---

## User Management (Admin)

### GET /users/manage/

List all users with filtering.

**Permission:** IsAdminOnly

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search email, username, first/last name |
| `role` | string | Filter by role (user, curator, admin) |
| `is_active` | boolean | Filter by active status |
| `page` | integer | Page number |

**Response (200 OK):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "admin@example.com",
      "username": "admin",
      "first_name": "",
      "last_name": "",
      "role": "admin",
      "is_active": true,
      "date_joined": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-25T10:00:00Z"
    }
  ]
}
```

---

### POST /users/manage/

Create a new user with specified role.

**Permission:** IsAdminOnly

**Request Body:**
```json
{
  "email": "newcurator@example.com",
  "password": "securepassword123",
  "first_name": "New",
  "last_name": "Curator",
  "role": "curator"
}
```

**Response (201 Created):** User object

---

### GET /users/manage/{id}/

Get user details.

**Permission:** IsAdminOnly

**Response (200 OK):** User object

---

### PATCH /users/manage/{id}/

Update user details.

**Permission:** IsAdminOnly

**Request Body:**
```json
{
  "role": "admin",
  "first_name": "Updated"
}
```

**Response (200 OK):** Updated user object

**Note:** Password is optional on updates.

---

### DELETE /users/manage/{id}/

Delete a user.

**Permission:** IsAdminOnly

**Response (204 No Content)**

---

### POST /users/manage/{id}/toggle_active/

Toggle user's active status.

**Permission:** IsAdminOnly

**Response (200 OK):**
```json
{
  "id": 5,
  "is_active": false,
  "message": "User deactivated successfully"
}
```

---

### GET /users/manage/stats/

Get user statistics.

**Permission:** IsAdminOnly

**Response (200 OK):**
```json
{
  "total_users": 10,
  "active_users": 8,
  "inactive_users": 2,
  "admins": 2,
  "curators": 3,
  "users": 5
}
```

---

## Health Check

### GET /health/

Health check endpoint for Kubernetes probes.

**Permission:** AllowAny

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message here",
  "detail": "Additional details (optional)"
}
```

**Common HTTP Status Codes:**

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (successful delete) |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (not logged in) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found |
| `500` | Internal Server Error |

---

## Authentication Notes

### Session Cookies

After successful login, the server sets:
- `sessionid` - Session identifier
- `csrftoken` - CSRF protection token

### Making Authenticated Requests

Include cookies in requests:
```javascript
fetch('/api/cards/', {
  credentials: 'include'  // Include cookies
})
```

Or with axios:
```javascript
axios.defaults.withCredentials = true
```

### CSRF Token

For non-GET requests, include the CSRF token:
```javascript
const csrfToken = document.cookie
  .split('; ')
  .find(row => row.startsWith('csrftoken='))
  ?.split('=')[1]

fetch('/api/cards/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken
  },
  credentials: 'include'
})
```

---

## Pagination

Paginated endpoints return:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/cards/?page=2",
  "previous": null,
  "results": [...]
}
```

- Default page size: 20 items
- Use `?page=N` to navigate pages
