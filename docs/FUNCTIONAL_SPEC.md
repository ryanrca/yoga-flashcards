# Yoga Flashcards - Functional Specification

**Version:** 1.0
**Last Updated:** 2026-09-10
**Status:** Specification -- describes intended behaviour, not all of it is built yet

> **Implementation status.** This document is the target spec. The following sections
> describe behaviour that is **not implemented**; treat them as requirements, not as a
> description of the running system:
>
> - **Favorites** (save/star a card, the `/favorites` page, the favourites list): the page
>   and buttons are placeholders. `UserProfile.favorite_cards` exists on the model but no
>   API endpoint reads or writes it.
> - **Social authentication** (Google / Facebook): buttons are rendered disabled.
> - **Email delivery**: the `daily_email_enabled` preference saves, and a verification token
>   is generated on registration, but nothing is ever mailed -- the token is printed to the
>   server log.
> - **Default placeholder image** for cards without a photo.
> - **Soft delete** for cards: `DELETE` is permanent.
> - **Kubernetes / Helm**: the chart has no `templates/` directory.
>
> See `PROJECT_STATUS.md` for the current state and `README.md` for what ships today.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Functional Requirements](#4-functional-requirements)
5. [Data Models](#5-data-models)
6. [API Specification](#6-api-specification)
7. [Frontend Specification](#7-frontend-specification)
8. [Authentication & Security](#8-authentication--security)
9. [Infrastructure](#9-infrastructure)
10. [Business Rules](#10-business-rules)

---

## 1. Executive Summary

### 1.1 Purpose

Yoga Flashcards is a web-based flashcard management system designed for yoga teacher training and study. The application enables curators to create, manage, and version yoga-related flashcards containing Sanskrit terms, definitions, and images. Users can browse cards and receive a daily featured card.

### 1.2 Core Value Proposition

- **Daily Card Feature**: Visitors receive one card per day, rotating through all cards before repeating
- **Version Control**: Complete edit history with ability to revert to any previous version
- **Role-Based Access**: Three-tier permission system (Admin, Curator, User)
- **Sanskrit Support**: UTF-8MB4 encoding for proper Sanskrit character display

### 1.3 Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend API | Django + Django REST Framework | 4.2.7 / 3.14.0 |
| Frontend | Vue.js + Quasar Framework | 3.x / 2.16 |
| State Management | Pinia | 3.x |
| Database | MySQL | 8.0 |
| Development | Docker Compose | 3.8 |
| Production | Kubernetes + Helm | - |

---

## 2. System Overview

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Vue 3 + Quasar SPA                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ Public Pages │  │ Admin Pages  │  │   Stores     │   │    │
│  │  │ - Home       │  │ - Dashboard  │  │ - auth.js    │   │    │
│  │  │ - Daily Card │  │ - Cards CRUD │  │ - flashcards │   │    │
│  │  │ - Login      │  │ - Tags CRUD  │  │   .js        │   │    │
│  │  │ - Signup     │  │ - Users CRUD │  │              │   │    │
│  │  │ - Cards      │  │              │  │              │   │    │
│  │  │ - Profile    │  │              │  │              │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │ Axios (HTTP)                      │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                         BACKEND API                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Django REST Framework                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ users app    │  │ flashcards   │  │ core app     │   │    │
│  │  │ - User model │  │ - Flashcard  │  │ - Health     │   │    │
│  │  │ - Profile    │  │ - Tag        │  │ - DailyCard  │   │    │
│  │  │ - Auth views │  │ - DailyCard  │  │   endpoint   │   │    │
│  │  │              │  │ - UsageLog   │  │              │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │ MySQL Client                      │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                         DATABASE                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    MySQL 8.0                             │    │
│  │          Character Set: UTF8MB4 (Sanskrit support)       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

#### Backend (`/backend/`)
- **Django Project**: `yoga_flashcards/`
- **Apps**:
  - `flashcards/` - Card management, tags, versioning, daily card service
  - `users/` - User authentication, profiles, role management
  - `core/` - Health checks, shared utilities

#### Frontend (`/frontend/`)
- **Framework**: Quasar 2.16 with Vue 3
- **State**: Pinia stores for auth and flashcards
- **Routing**: Vue Router with auth guards
- **HTTP**: Axios with session cookie support

### 2.3 Directory Structure

```
yoga-flashcards/
├── backend/
│   ├── yoga_flashcards/          # Django project settings
│   │   ├── settings.py           # Main configuration
│   │   ├── urls.py               # Root URL routing
│   │   └── wsgi.py               # WSGI application
│   ├── flashcards/               # Flashcard management app
│   │   ├── models.py             # Flashcard, Tag, DailyCard, UsageLog
│   │   ├── views.py              # API ViewSets
│   │   ├── serializers.py        # DRF serializers
│   │   ├── services.py           # DailyCardService
│   │   ├── permissions.py        # IsCuratorOrAdmin, IsAdminOnly
│   │   ├── pagination.py         # CardPagination
│   │   └── management/commands/  # seed_initial_data, import_cards
│   ├── users/                    # User management app
│   │   ├── models.py             # User, UserProfile
│   │   ├── views.py              # Auth views
│   │   ├── serializers.py        # User serializers
│   │   └── services.py           # Email verification
│   ├── core/                     # Core utilities
│   │   ├── views.py              # Health check, daily card endpoint
│   │   └── urls.py               # Core URL routing
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container
│   └── start.sh                  # Container startup script
├── frontend/
│   ├── src/
│   │   ├── boot/                 # App initialization
│   │   │   ├── axios.js          # HTTP client config
│   │   │   └── pinia.js          # State management setup
│   │   ├── stores/               # Pinia stores
│   │   │   ├── auth.js           # Authentication state
│   │   │   └── flashcards.js     # Flashcard state
│   │   ├── router/               # Vue Router
│   │   │   ├── index.js          # Router setup with guards
│   │   │   └── routes.js         # Route definitions
│   │   ├── layouts/              # Layout components
│   │   │   ├── PublicLayout.vue  # Public pages layout
│   │   │   └── AdminLayout.vue   # Admin pages layout
│   │   ├── pages/                # Page components
│   │   │   ├── public/           # Public-facing pages
│   │   │   └── admin/            # Admin panel pages
│   │   └── components/           # Reusable components
│   ├── quasar.config.js          # Quasar configuration
│   ├── package.json              # Node dependencies
│   └── Dockerfile                # Frontend container
├── docker-compose.yml            # Development environment
├── k8s/helm/                     # Kubernetes deployment
├── docs/                         # Documentation
│   └── FUNCTIONAL_SPEC.md        # This document
├── CLAUDE.md                     # AI assistant instructions
└── README.md                     # Project overview
```

---

## 3. User Roles & Permissions

### 3.1 Role Hierarchy

```
Admin (Superuser)
  └── Curator
       └── User
```

### 3.2 Permission Matrix

| Action | Admin | Curator | User | Anonymous |
|--------|-------|---------|------|-----------|
| View daily card | Yes | Yes | Yes | Yes |
| View all cards | Yes | Yes | Yes | No |
| Create cards | Yes | Yes | No | No |
| Edit cards | Yes | Yes | No | No |
| Delete cards | Yes | Yes | No | No |
| View version history | Yes | Yes | No | No |
| Revert versions | Yes | Yes | No | No |
| Manage tags | Yes | Yes | No | No |
| Manage users | Yes | No | No | No |
| Access admin panel | Yes | Yes | No | No |
| Edit own profile | Yes | Yes | Yes | No |
| Save favorites | Yes | Yes | Yes | No |

### 3.3 Role Definitions

#### Admin
- Full system access
- Can create, edit, delete all content
- Can manage user accounts and permissions
- Can promote users to Curator or Admin
- Can access Django admin panel

#### Curator
- Content management access
- Can create, edit, delete flashcards
- Can manage tags
- Can view version history and revert
- Cannot manage user accounts

#### User
- Frontend access only
- Can browse all flashcards (when logged in)
- Can save favorites
- Can edit own profile and password
- Cannot access admin panel

---

## 4. Functional Requirements

### 4.1 Daily Card Feature

**FR-DC-001**: The system SHALL display one flashcard per day to all visitors.

**FR-DC-002**: The daily card selection algorithm SHALL:
1. Select a random card that has not been used in the current cycle
2. Track usage in `CardUsageLog` with cycle number
3. When all cards have been used, increment cycle and start fresh
4. Never repeat a card within the same cycle

**FR-DC-003**: The daily card endpoint SHALL be publicly accessible without authentication.

**FR-DC-004**: The daily card SHALL remain the same for the entire calendar day (UTC).

### 4.2 Flashcard Management

**FR-FC-001**: Flashcards SHALL contain the following fields:
- `title` (required, max 200 characters)
- `phrase` (required, max 500 characters, Sanskrit term)
- `definition` (required, full English description)
- `short_answer` (optional, key points summary)
- `front_image` (optional, image file)
- `back_image` (optional, image file)
- `tags` (optional, many-to-many relationship)

**FR-FC-002**: Flashcard CRUD operations SHALL require Curator or Admin role.

**FR-FC-003**: Flashcard listing SHALL support:
- Pagination (20 items per page)
- Search across title, phrase, definition, and tag names
- Filter by tags (multiple tags, comma-separated)

**FR-FC-004**: Soft delete SHALL be implemented - cards are never permanently deleted, only marked `is_active=False`.

### 4.3 Version Control System

**FR-VC-001**: Every flashcard edit SHALL create a new version rather than updating in place.

**FR-VC-002**: Version tracking SHALL use:
- `version_group` (UUID) - Groups all versions of the same logical card
- `version_number` (integer) - Increments with each edit
- `is_live` (boolean) - Only one version per group is live

**FR-VC-003**: When a card is edited:
1. The current live version's `is_live` is set to `False`
2. A new version is created with `version_number + 1`
3. The new version is marked `is_live=True`
4. Tags are copied to the new version

**FR-VC-004**: Version history SHALL be viewable by Curators and Admins.

**FR-VC-005**: Any previous version SHALL be revertable, which:
1. Creates a NEW version (highest version_number)
2. Copies content from the selected old version
3. Marks the new version as live

### 4.4 Tag Management

**FR-TG-001**: Tags SHALL have:
- `name` (required, unique, max 50 characters)
- `description` (optional)

**FR-TG-002**: Tag listing SHALL be publicly accessible.

**FR-TG-003**: Tag CRUD (create, update, delete) SHALL require Curator or Admin role.

**FR-TG-004**: Tags SHALL be automatically created when referenced by name during card creation.

### 4.5 User Management

**FR-UM-001**: Users SHALL have the following fields:
- `email` (required, unique, used for login)
- `username` (auto-generated from email)
- `password` (hashed)
- `first_name`, `last_name` (optional)
- `role` (user, curator, admin)
- `is_active` (boolean)
- `daily_email_enabled` (boolean, default False)
- `email_verified` (boolean, default False)

**FR-UM-002**: User management (CRUD) SHALL require Admin role.

**FR-UM-003**: Admins SHALL be able to toggle user active status.

**FR-UM-004**: User profiles SHALL support:
- Bio (optional text)
- Avatar (optional image)
- Favorite cards (many-to-many)

### 4.6 Authentication

**FR-AU-001**: Authentication SHALL use Django session-based authentication (not JWT).

**FR-AU-002**: Login SHALL use email address as the identifier.

**FR-AU-003**: Registration SHALL:
1. Accept email and password (entered twice)
2. Validate password match
3. Auto-generate username from email
4. Create UserProfile automatically
5. Auto-login user after successful registration

**FR-AU-004**: Protected routes SHALL redirect to login with return URL preservation.

### 4.7 Search and Filtering

**FR-SF-001**: Card search SHALL search across:
- Title
- Phrase (Sanskrit)
- Definition
- Tag names

**FR-SF-002**: Search SHALL be case-insensitive.

**FR-SF-003**: Tag filtering SHALL support:
- Multiple tags (comma-separated)
- Filter by tag ID or tag name

---

## 5. Data Models

### 5.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│      User       │       │   UserProfile   │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──1:1──│ id (PK)         │
│ email           │       │ user_id (FK)    │
│ username        │       │ bio             │
│ password        │       │ avatar          │
│ first_name      │       │ favorite_cards  │──┐
│ last_name       │       └─────────────────┘  │
│ role            │                            │
│ is_active       │       ┌─────────────────┐  │
│ daily_email_en. │──1:M──│   Flashcard     │◄─┘ (M:M)
│ email_verified  │       ├─────────────────┤
│ created_at      │       │ id (PK)         │
│ updated_at      │       │ title           │
└─────────────────┘       │ phrase          │
                          │ definition      │
                          │ short_answer    │
                          │ front_image     │
                          │ back_image      │
                          │ version_group   │
                          │ version_number  │
                          │ is_live         │
                          │ is_active       │
                          │ created_by (FK) │
                          │ created_at      │
                          │ updated_at      │
                          └────────┬────────┘
                                   │
                                   │ M:M
                                   ▼
                          ┌─────────────────┐
                          │      Tag        │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ name            │
                          │ description     │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│   DailyCard     │       │  CardUsageLog   │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ card_id (FK)    │       │ card_id (FK)    │
│ date (unique)   │       │ used_date       │
└─────────────────┘       │ cycle_number    │
                          └─────────────────┘
```

### 5.2 Model Specifications

#### User Model
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('curator', 'Curator'),
        ('admin', 'Admin'),
    ]

    role = CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    daily_email_enabled = BooleanField(default=False)
    email_verified = BooleanField(default=False)
    email_verification_token = CharField(max_length=100, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # Methods
    def is_admin(self) -> bool
    def is_curator(self) -> bool
    def can_edit_cards(self) -> bool
    def can_edit_users(self) -> bool
```

#### UserProfile Model
```python
class UserProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    bio = TextField(blank=True)
    avatar = ImageField(upload_to='avatars/', blank=True, null=True)
    favorite_cards = ManyToManyField('flashcards.Flashcard', blank=True)
```

#### Flashcard Model
```python
class Flashcard(Model):
    title = CharField(max_length=200)
    phrase = CharField(max_length=500)  # Sanskrit
    definition = TextField()
    short_answer = TextField(blank=True)
    front_image = ImageField(upload_to='flashcard_images/', blank=True, null=True)
    back_image = ImageField(upload_to='flashcard_images/', blank=True, null=True)
    tags = ManyToManyField('Tag', blank=True)

    # Versioning
    version_group = UUIDField(default=uuid.uuid4)
    version_number = PositiveIntegerField(default=1)
    is_live = BooleanField(default=True)
    is_active = BooleanField(default=True)  # Soft delete

    # Audit
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # Methods
    def get_version_history(self) -> QuerySet
    def create_new_version(self, **kwargs) -> 'Flashcard'
    def revert_to_this_version(self, reverted_by: User) -> 'Flashcard'
```

#### Tag Model
```python
class Tag(Model):
    name = CharField(max_length=50, unique=True)
    description = TextField(blank=True)

    class Meta:
        ordering = ['name']
```

#### DailyCard Model
```python
class DailyCard(Model):
    card = ForeignKey(Flashcard, on_delete=CASCADE)
    date = DateField(unique=True)
```

#### CardUsageLog Model
```python
class CardUsageLog(Model):
    card = ForeignKey(Flashcard, on_delete=CASCADE)
    used_date = DateField()
    cycle_number = PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['card', 'used_date', 'cycle_number']
```

---

## 6. API Specification

### 6.1 Base URL

- Development: `http://localhost:8000/api/`
- Production: `https://your-domain.com/api/`

### 6.2 Authentication Endpoints

#### POST /api/users/register/
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "password_confirm": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
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

#### POST /api/users/login/
Authenticate user and create session.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user",
  "role": "user"
}
```

#### POST /api/users/logout/
End user session. Requires authentication.

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

#### GET /api/users/auth-status/
Check current authentication status.

**Response (200) - Authenticated:**
```json
{
  "is_authenticated": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user"
  }
}
```

**Response (200) - Not authenticated:**
```json
{
  "is_authenticated": false
}
```

### 6.3 Flashcard Endpoints

#### GET /api/cards/
List all live, active flashcards. Requires authentication.

**Query Parameters:**
- `search` (string): Search across title, phrase, definition, tags
- `tags` (string): Comma-separated tag IDs or names
- `page` (integer): Page number (default: 1)

**Response (200):**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/cards/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Ahimsa",
      "phrase": "अहिंसा",
      "definition": "Non-violence or non-harming...",
      "short_answer": "Non-violence",
      "front_image": "/media/flashcard_images/ahimsa_front.jpg",
      "back_image": null,
      "tags": [
        {"id": 1, "name": "Yamas"}
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

#### POST /api/cards/
Create a new flashcard. Requires Curator or Admin role.

**Request (multipart/form-data):**
```
title: "Satya"
phrase: "सत्य"
definition: "Truthfulness in thought, word, and deed..."
short_answer: "Truthfulness"
tags: "Yamas,Sanskrit"
front_image: [file]
back_image: [file]
```

**Response (201):**
```json
{
  "id": 2,
  "title": "Satya",
  "phrase": "सत्य",
  "definition": "Truthfulness in thought, word, and deed...",
  "short_answer": "Truthfulness",
  "front_image": "/media/flashcard_images/satya_front.jpg",
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

#### GET /api/cards/{id}/
Get single card details. Requires authentication.

#### PUT /api/cards/{id}/
Update card (creates new version). Requires Curator or Admin role.

**Note:** Returns the NEW version with a different ID.

#### DELETE /api/cards/{id}/
Soft delete card (sets is_active=False). Requires Curator or Admin role.

#### GET /api/cards/{id}/versions/
Get complete version history. Requires Curator or Admin role.

**Response (200):**
```json
[
  {
    "id": 5,
    "version_number": 3,
    "is_live": true,
    "title": "Ahimsa",
    "definition": "Updated definition...",
    "created_by_username": "curator1",
    "created_at": "2025-01-25T12:00:00Z"
  },
  {
    "id": 3,
    "version_number": 2,
    "is_live": false,
    "title": "Ahimsa",
    "definition": "Previous definition...",
    "created_by_username": "admin",
    "created_at": "2025-01-15T10:00:00Z"
  },
  {
    "id": 1,
    "version_number": 1,
    "is_live": false,
    "title": "Ahimsa",
    "definition": "Original definition...",
    "created_by_username": "admin",
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST /api/cards/{id}/revert_version/
Revert to a previous version. Requires Curator or Admin role.

**Request:**
```json
{
  "version_id": 1
}
```

**Response (200):**
```json
{
  "id": 6,
  "version_number": 4,
  "is_live": true,
  "message": "Successfully reverted to version 1"
}
```

### 6.4 Tag Endpoints

#### GET /api/tags/
List all tags. Public access.

#### POST /api/tags/
Create new tag. Requires Curator or Admin role.

#### PUT /api/tags/{id}/
Update tag. Requires Curator or Admin role.

#### DELETE /api/tags/{id}/
Delete tag. Requires Curator or Admin role.

### 6.5 Daily Card Endpoint

#### GET /api/dailycard/
Get today's daily card. Public access (no authentication required).

**Response (200):**
```json
{
  "id": 1,
  "title": "Ahimsa",
  "phrase": "अहिंसा",
  "definition": "Non-violence or non-harming...",
  "short_answer": "Non-violence",
  "front_image": "/media/flashcard_images/ahimsa_front.jpg",
  "back_image": null,
  "tags": [
    {"id": 1, "name": "Yamas"}
  ]
}
```

### 6.6 User Management Endpoints (Admin Only)

#### GET /api/users/manage/
List all users with filtering.

#### POST /api/users/manage/
Create new user with specified role.

#### PATCH /api/users/manage/{id}/
Update user details.

#### DELETE /api/users/manage/{id}/
Delete user.

#### POST /api/users/manage/{id}/toggle_active/
Toggle user active status.

#### GET /api/users/manage/stats/
Get user statistics.

### 6.7 Utility Endpoints

#### GET /api/health/
Health check for Kubernetes.

**Response (200):**
```json
{
  "status": "healthy"
}
```

---

## 7. Frontend Specification

### 7.1 Route Structure

#### Public Routes (PublicLayout)

| Path | Name | Component | Auth Required |
|------|------|-----------|---------------|
| `/` | home | HomePage.vue | No |
| `/daily` | daily-card | DailyCardPage.vue | No |
| `/login` | login | LoginPage.vue | No |
| `/signup` | signup | SignupPage.vue | No |
| `/cards` | public-cards | CardsPage.vue | Yes |
| `/profile` | profile | ProfilePage.vue | Yes |
| `/favorites` | favorites | FavoritesPage.vue | Yes |

#### Admin Routes (AdminLayout)

| Path | Name | Component | Auth Required |
|------|------|-----------|---------------|
| `/admin` | admin-dashboard | DashboardPage.vue | Curator+ |
| `/admin/cards` | admin-cards | CardsPage.vue | Curator+ |
| `/admin/cards/new` | admin-card-new | CardEditPage.vue | Curator+ |
| `/admin/cards/:id` | admin-card-detail | CardDetailPage.vue | Curator+ |
| `/admin/cards/:id/edit` | admin-card-edit | CardEditPage.vue | Curator+ |
| `/admin/tags` | admin-tags | TagsPage.vue | Curator+ |
| `/admin/users` | admin-users | UsersPage.vue | Admin |

### 7.2 State Management

#### Auth Store (`stores/auth.js`)

**State:**
```javascript
{
  user: null | UserObject,
  isAuthenticated: boolean,
  loading: boolean,
  error: string | null
}
```

**Actions:**
- `login(credentials)` - Authenticate user
- `logout()` - End session
- `checkAuthStatus()` - Verify session on app load
- `signup(userData)` - Register and auto-login
- `fetchUsers(params)` - Admin: list users
- `createUser(userData)` - Admin: create user
- `updateUser(id, data)` - Admin: update user
- `deleteUser(id)` - Admin: delete user
- `toggleUserStatus(id)` - Admin: toggle active

**Getters:**
- `isAdmin` - Check admin role
- `isCurator` - Check curator or admin role
- `isUser` - Check if logged in

#### Flashcards Store (`stores/flashcards.js`)

**State:**
```javascript
{
  cards: [],
  dailyCard: null,
  currentCard: null,
  tags: [],
  loading: boolean,
  error: string | null,
  pagination: {
    count: 0,
    page: 1,
    pageSize: 20,
    totalPages: 0
  }
}
```

**Actions:**
- `fetchCards(params)` - Get paginated cards
- `fetchDailyCard()` - Get today's card
- `fetchCard(id)` - Get single card
- `createCard(formData)` - Create card
- `updateCard(id, formData)` - Update card (new version)
- `deleteCard(id)` - Soft delete card
- `fetchTags()` - Get all tags
- `createTag(data)` - Create tag
- `fetchCardVersions(id)` - Get version history
- `revertCardVersion(cardId, versionId)` - Revert to version

### 7.3 Page Specifications

#### HomePage
- Hero section with app branding
- Daily card preview (fetches from `/api/dailycard/`)
- Call-to-action buttons (Sign Up / Browse Cards)
- Feature highlights

#### DailyCardPage
- Full daily card display
- Shows: title, phrase, short_answer, definition, images, tags
- Share button (Web Share API or clipboard)
- Link to browse all cards (if authenticated)

#### LoginPage
- Email input field
- Password input field
- Submit button
- Link to signup
- Error display
- Redirect handling

#### SignupPage
- Email input field
- Password input field (with visibility toggle)
- Password confirmation field
- First name (optional)
- Last name (optional)
- Submit button
- Link to login
- Validation messages

#### CardsPage (Public)
- Search input
- Tag filter dropdown
- Card grid/list
- Pagination controls
- Favorite button per card
- Share button per card

#### ProfilePage
- User info display
- Edit password form
- Daily email preference toggle
- Edit profile button

#### Admin DashboardPage
- Statistics cards (total cards, users, etc.)
- Quick action buttons
- Recent activity (optional)

#### Admin CardsPage
- Data table with all cards
- Search input
- Tag filter
- Sort controls
- Add new card button
- Row click to view/edit
- Delete button per row
- Version count indicator

#### Admin CardEditPage
- Form fields: title, phrase, definition, short_answer
- Tag multi-select with create option
- Image upload with preview
- Version history table (if editing)
- Revert buttons
- Save/Cancel buttons
- Form validation

#### Admin TagsPage
- Data table with all tags
- Add new tag button
- Edit button per row
- Delete button per row
- Search input

#### Admin UsersPage
- Data table with all users
- Role filter
- Active status filter
- Add new user button
- Edit button per row
- Toggle active button
- Delete button per row
- Search input

### 7.4 Component Library

The application uses Quasar Framework components:

- `q-page` - Page container
- `q-card` - Card containers
- `q-btn` - Buttons
- `q-input` - Text inputs
- `q-select` - Dropdowns
- `q-file` - File upload
- `q-img` - Image display
- `q-table` - Data tables
- `q-chip` - Tag chips
- `q-spinner` - Loading indicators
- `q-banner` - Alerts
- `q-dialog` - Modals
- `q-form` - Form wrapper
- `q-notify` - Toast notifications

---

## 8. Authentication & Security

### 8.1 Session-Based Authentication

- Uses Django's built-in session framework
- Session cookie: `sessionid`
- CSRF protection with `csrftoken` cookie
- Sessions stored in database

### 8.2 CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]
CORS_ALLOW_CREDENTIALS = True
```

### 8.3 Permission Classes

```python
class IsCuratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_curator() or request.user.is_admin()
        )

class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()
```

### 8.4 Security Features

- Password hashing (Django PBKDF2)
- Session expiry
- HTTPS in production
- CSRF tokens for non-API requests
- Input validation on all endpoints
- Soft deletes (audit trail)

---

## 9. Infrastructure

### 9.1 Development Environment

**Docker Compose Services:**

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| db | mysql:8.0 | 3306 | Database |
| backend | ./backend | 8000 | Django API |
| frontend | ./frontend | 9000 | Vue SPA |

**Startup Sequence:**
1. MySQL starts and health check passes
2. Backend waits for MySQL, runs migrations, seeds data
3. Frontend starts and proxies to backend

### 9.2 Production Environment

**Kubernetes Resources:**
- Deployment: backend (Django + Gunicorn)
- Deployment: frontend (Nginx + Vue build)
- Service: backend-service (ClusterIP)
- Service: frontend-service (LoadBalancer)
- ConfigMap: environment configuration
- Secret: database credentials, Django secret key
- PersistentVolumeClaim: media files

### 9.3 Environment Variables

**Backend:**
```
DEBUG=0|1
DJANGO_SECRET_KEY=<secret>
DATABASE_URL=mysql://user:pass@host:3306/dbname
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

**Frontend:**
```
API_BASE_URL=https://api.your-domain.com
```

---

## 10. Business Rules

### 10.1 Daily Card Selection

1. Each calendar day has exactly one daily card
2. Cards are selected randomly from unused cards in current cycle
3. When all cards are used, cycle increments and selection restarts
4. Cards marked `is_active=False` are excluded from selection
5. Only `is_live=True` versions are considered

### 10.2 Version Control Rules

1. First version always has `version_number=1`
2. Each edit increments version_number by 1
3. Only one version per `version_group` can have `is_live=True`
4. Reverting creates a NEW version (not modifying old)
5. Version history is never deleted

### 10.3 User Registration

1. Email must be unique
2. Password must be entered twice and match
3. Username is auto-generated from email (before @)
4. If username exists, append counter (user1, user2, etc.)
5. New users default to 'user' role
6. UserProfile is created automatically on registration

### 10.4 Image Handling

1. Images stored in `media/flashcard_images/`
2. Accepted formats: JPEG, PNG, GIF, WebP
3. Images are copied when creating new versions
4. Original filenames are preserved with unique prefix

### 10.5 Tag Management

1. Tag names must be unique (case-sensitive)
2. Tags can be created inline during card creation
3. Deleting a tag removes it from all cards
4. Tags are copied when creating new card versions

---

## Appendix A: Initial Data

The system should be seeded with the following yoga content:

### 8 Limbs of Yoga (Ashtanga)
1. Yama - Ethical restraints
2. Niyama - Observances
3. Asana - Physical postures
4. Pranayama - Breath control
5. Pratyahara - Sense withdrawal
6. Dharana - Concentration
7. Dhyana - Meditation
8. Samadhi - Enlightenment

### 5 Yamas
1. Ahimsa - Non-violence
2. Satya - Truthfulness
3. Asteya - Non-stealing
4. Brahmacharya - Right use of energy
5. Aparigraha - Non-attachment

### 5 Niyamas
1. Saucha - Cleanliness
2. Santosha - Contentment
3. Tapas - Discipline
4. Svadhyaya - Self-study
5. Ishvara Pranidhana - Surrender

---

## Appendix B: Development Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | Admin |
| admin1@example.com | admin1 | Admin |
| curator1@example.com | curator1 | Curator |
| user1@example.com | user1 | User |

---

## Appendix C: File Naming Conventions

- Models: `snake_case` (flashcard, daily_card)
- Views/ViewSets: `PascalCase` (FlashcardViewSet)
- Serializers: `PascalCaseSerializer` (FlashcardSerializer)
- URLs: `kebab-case` (/api/daily-card/)
- Vue components: `PascalCase.vue` (CardEditPage.vue)
- Stores: `camelCase.js` (flashcards.js)
- CSS classes: `kebab-case` (.card-container)

---

*End of Functional Specification*
