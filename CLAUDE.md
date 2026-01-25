# Claude Code Instructions - Yoga Flashcards

This document provides instructions for Claude Code to understand and work with the Yoga Flashcards application.

## Quick Reference

```
Backend:  http://localhost:8000  (Django REST API)
Frontend: http://localhost:9000  (Quasar/Vue SPA)
Database: MySQL 8.0 on port 3306
Start:    docker-compose up --build
```

## Project Overview

Yoga Flashcards is a web-based flashcard management system for yoga teacher training. It features:
- **Daily Card**: Public endpoint rotates through all cards before repeating
- **Version Control**: Every edit creates a new version; complete history preserved
- **Role-Based Access**: Admin > Curator > User hierarchy
- **Sanskrit Support**: UTF-8MB4 encoding for proper character display

**See**: `docs/FUNCTIONAL_SPEC.md` for complete functional requirements.

---

## Development Environment

### Critical: Always Use WSL Ubuntu Shell

- **NEVER use Windows PowerShell** for this project
- **ALWAYS use WSL Ubuntu shell** for all terminal commands
- All Docker, npm, and bash commands must execute in WSL

```bash
# Correct
cd ~/repos/yoga-flashcards
docker compose up --build

# Wrong (PowerShell)
cd \\wsl.localhost\Ubuntu\home\ryan\repos\yoga-flashcards
```

### Starting Development

```bash
# Full rebuild
docker-compose up --build

# Or use the start script
./start-dev.sh

# Restart single service
docker-compose restart backend
docker-compose restart frontend
```

### Test Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | Admin |
| curator1@example.com | curator1 | Curator |
| user1@example.com | user1 | User |

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Django + DRF | 4.2.7 / 3.14.0 |
| Frontend | Vue 3 + Quasar | 3.x / 2.16 |
| State | Pinia | 3.x |
| Database | MySQL | 8.0 |
| Dev | Docker Compose | 3.8 |
| Prod | Kubernetes + Helm | - |

---

## Project Structure

```
yoga-flashcards/
├── backend/                    # Django REST API
│   ├── yoga_flashcards/       # Project settings
│   ├── flashcards/            # Cards, tags, versioning, daily card
│   ├── users/                 # Auth, profiles, roles
│   ├── core/                  # Health check, utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Vue 3 + Quasar SPA
│   ├── src/
│   │   ├── boot/              # axios.js, pinia.js
│   │   ├── stores/            # auth.js, flashcards.js
│   │   ├── router/            # routes.js, guards
│   │   ├── layouts/           # PublicLayout, AdminLayout
│   │   ├── pages/             # public/, admin/
│   │   └── components/
│   ├── quasar.config.js
│   └── Dockerfile
├── docker-compose.yml
├── k8s/helm/                   # Kubernetes deployment
├── docs/FUNCTIONAL_SPEC.md     # Complete specification
└── CLAUDE.md                   # This file
```

---

## Backend Development (Django)

### Architecture Principles

- **Thin views, fat models** - Business logic in `services.py`
- **DRF ModelViewSets** for RESTful endpoints
- **Serializers** for all validation (never raw request data)
- **Apps by domain**: flashcards, users, core

### Key Files

| File | Purpose |
|------|---------|
| `flashcards/models.py` | Flashcard, Tag, DailyCard, CardUsageLog |
| `flashcards/views.py` | FlashcardViewSet, TagViewSet |
| `flashcards/serializers.py` | Data serialization, version creation |
| `flashcards/services.py` | DailyCardService |
| `flashcards/permissions.py` | IsCuratorOrAdmin, IsAdminOnly |
| `users/models.py` | User (with role), UserProfile |
| `users/views.py` | register, login, logout, auth_status |

### Versioning System

The flashcard versioning works as follows:

```python
# When creating a new card
flashcard = Flashcard.objects.create(
    title="...",
    version_group=uuid.uuid4(),  # New UUID
    version_number=1,
    is_live=True
)

# When editing (in serializer.update())
new_version = instance.create_new_version(**validated_data)
# - Old version: is_live=False
# - New version: version_number+1, is_live=True

# When reverting
new_version = old_version.revert_to_this_version(user)
# - Creates NEW version with highest version_number
# - Copies content from old version
# - Marks new version as live
```

### API Endpoints

```
# Public
GET  /api/dailycard/          # Daily card (no auth)
GET  /api/tags/               # List tags (no auth)

# Authenticated
GET  /api/cards/              # List cards (?search=&tags=&page=)
GET  /api/cards/{id}/         # Card detail
POST /api/users/login/        # Login
POST /api/users/logout/       # Logout
GET  /api/users/auth-status/  # Check auth
POST /api/users/register/     # Sign up

# Curator/Admin only
POST   /api/cards/                    # Create card
PUT    /api/cards/{id}/               # Update (new version)
DELETE /api/cards/{id}/               # Soft delete
GET    /api/cards/{id}/versions/      # Version history
POST   /api/cards/{id}/revert_version/  # Revert
POST   /api/tags/                     # Create tag
PUT    /api/tags/{id}/                # Update tag
DELETE /api/tags/{id}/                # Delete tag

# Admin only
GET    /api/users/manage/             # List users
POST   /api/users/manage/             # Create user
PATCH  /api/users/manage/{id}/        # Update user
DELETE /api/users/manage/{id}/        # Delete user
```

### Running Tests

```bash
docker-compose exec backend python -m pytest
```

### Management Commands

```bash
# Seed initial data (runs automatically on start)
docker-compose exec backend python manage.py seed_initial_data

# Export flashcards to JSON
docker-compose exec backend python manage.py seed_initial_data --pull

# Import from CSV
docker-compose exec backend python manage.py import_cards /path/to/file.csv
```

---

## Frontend Development (Vue/Quasar)

### Architecture Principles

- **Composition API** with `<script setup>`
- **Pinia** for state management
- **SFCs** (Single File Components)
- **Quasar components** for UI

### Key Files

| File | Purpose |
|------|---------|
| `stores/auth.js` | User state, login/logout, admin operations |
| `stores/flashcards.js` | Cards state, CRUD, daily card |
| `router/routes.js` | Route definitions with guards |
| `boot/axios.js` | HTTP client with CSRF, credentials |
| `pages/public/DailyCardPage.vue` | Public daily card view |
| `pages/admin/CardEditPage.vue` | Card create/edit with versioning |

### State Stores

```javascript
// Auth store (stores/auth.js)
const authStore = useAuthStore()
authStore.isAuthenticated  // boolean
authStore.user             // user object or null
authStore.isAdmin          // computed
authStore.isCurator        // computed
await authStore.login({ email, password })
await authStore.logout()

// Flashcards store (stores/flashcards.js)
const flashcardsStore = useFlashcardsStore()
flashcardsStore.cards      // array
flashcardsStore.dailyCard  // object or null
await flashcardsStore.fetchCards({ search, tags, page })
await flashcardsStore.fetchDailyCard()
await flashcardsStore.createCard(formData)
await flashcardsStore.updateCard(id, formData)
```

### Route Guards

Routes use meta flags for protection:

```javascript
{
  path: '/admin/cards',
  meta: { requiresCurator: true }  // Curator or Admin
}
{
  path: '/admin/users',
  meta: { requiresAdmin: true }    // Admin only
}
{
  path: '/cards',
  meta: { requiresAuth: true }     // Any logged-in user
}
```

### Axios Configuration

The axios instance in `boot/axios.js`:
- Base URL from `API_BASE_URL` env var
- `withCredentials: true` for session cookies
- CSRF token from cookie added to headers
- 401 responses redirect to login

---

## Docker Configuration

### Services

| Service | Port | Purpose |
|---------|------|---------|
| db | 3306 | MySQL 8.0 database |
| backend | 8000 | Django API |
| frontend | 9000 | Quasar dev server |

### Rebuild After Changes

```bash
# Full rebuild
docker-compose down && docker-compose up --build

# Rebuild single service
docker-compose up --build backend
docker-compose up --build frontend
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## Common Issues and Solutions

### Quasar/Node.js Issues

**Problem**: Webpack inject.style-rules.js errors
**Solution**: Use Node.js 24 LTS and official Quasar CLI

```bash
# If frontend breaks, recreate it:
rm -rf frontend
npm create quasar
# Choose: Vite, Composition API, SCSS, ESLint+Prettier
cd frontend
npm install pinia axios
```

### Frontend Dockerfile

**Critical**: Copy source code BEFORE npm install (quasar prepare needs source):

```dockerfile
# Correct order
COPY package*.json ./
COPY . .
RUN npm install

# Wrong order (will fail)
COPY package*.json ./
RUN npm install  # Fails: quasar prepare needs source
COPY . .
```

### CSRF/CORS Issues

Settings must include:
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:9000"]
CORS_ALLOW_CREDENTIALS = True
```

Middleware disables CSRF for `/api/` in dev:
```python
class DisableCSRFMiddleware:
    def __call__(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)
```

### Database Connection

Backend waits for MySQL in `start.sh`:
```bash
# Waits up to 60 seconds for MySQL
for i in {1..30}; do
    if python -c "import MySQLdb; MySQLdb.connect(...)"; then
        break
    fi
    sleep 2
done
```

### NPM Directory Issues

Always use explicit paths:
```bash
cd ~/repos/yoga-flashcards/frontend && npm run dev
```

---

## Style Conventions

### Python/Django
- 4 spaces indentation
- `snake_case` for variables, functions, files
- `CamelCase` for classes
- `UPPER_CASE` for constants

### Vue/JavaScript
- 2 spaces indentation
- `camelCase` for variables, methods
- `PascalCase` for component names
- `kebab-case` for filenames
- Scoped SCSS in SFCs

### General
- **NO emojis** in code, comments, or documentation
- Keep code DRY but don't over-abstract
- Prefer explicit over implicit

---

## Database Schema

### Core Tables

```
users_user
  - id, email, username, password, role, is_active
  - daily_email_enabled, email_verified
  - created_at, updated_at

users_userprofile
  - id, user_id (FK), bio, avatar
  - favorite_cards (M2M to Flashcard)

flashcards_flashcard
  - id, title, phrase, definition, short_answer
  - front_image, back_image
  - version_group (UUID), version_number, is_live, is_active
  - created_by (FK), created_at, updated_at

flashcards_tag
  - id, name (unique), description

flashcards_flashcard_tags (M2M)
  - flashcard_id, tag_id

flashcards_dailycard
  - id, card_id (FK), date (unique)

flashcards_cardusagelog
  - id, card_id (FK), used_date, cycle_number
```

---

## Kubernetes Deployment

### Build Images

```bash
docker build -t your-registry/yoga-flashcards-backend:latest ./backend
docker build -t your-registry/yoga-flashcards-frontend:latest ./frontend
```

### Deploy with Helm

```bash
helm install yoga-flashcards ./k8s/helm \
  --set image.backend.repository=your-registry/yoga-flashcards-backend \
  --set image.frontend.repository=your-registry/yoga-flashcards-frontend \
  --set env.SECRET_KEY=your-production-secret \
  --set database.password=your-db-password
```

---

## File Reference

### Backend Key Files

- `backend/yoga_flashcards/settings.py` - Django configuration
- `backend/flashcards/models.py` - Data models
- `backend/flashcards/views.py` - API ViewSets
- `backend/flashcards/serializers.py` - DRF serializers
- `backend/flashcards/services.py` - Business logic
- `backend/users/models.py` - User model
- `backend/users/views.py` - Auth endpoints

### Frontend Key Files

- `frontend/src/stores/auth.js` - Auth state
- `frontend/src/stores/flashcards.js` - Cards state
- `frontend/src/router/routes.js` - Route definitions
- `frontend/src/boot/axios.js` - HTTP client
- `frontend/src/pages/public/DailyCardPage.vue` - Daily card
- `frontend/src/pages/admin/CardEditPage.vue` - Card management

### Configuration Files

- `docker-compose.yml` - Development environment
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node dependencies
- `frontend/quasar.config.js` - Quasar configuration

---

## Testing Checklist

When making changes, verify:

- [ ] Backend tests pass: `docker-compose exec backend python -m pytest`
- [ ] Frontend builds: `docker-compose exec frontend npm run build`
- [ ] Daily card works for anonymous users
- [ ] Login/logout flow works
- [ ] Card CRUD works for curators
- [ ] Version history and revert work
- [ ] Tag management works
- [ ] User management works for admins
- [ ] Search and filtering work
