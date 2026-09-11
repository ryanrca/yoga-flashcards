# Yoga Flashcards - Claude Code Instructions

## Quick Reference

```
Backend:  http://localhost:8000  (Django 4.2 + DRF)
Frontend: http://localhost:9000  (Vue 3 + Quasar 2.16 + Pinia)
Database: MySQL 8.0 on port 3306
Start:    docker-compose up --build
Tests:    docker-compose exec backend python -m pytest
Build:    docker-compose exec frontend npm run build
```

## Test Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | Admin (superuser) |
| admin1@example.com | admin1 | Admin |
| curator1@example.com | curator1 | Curator |
| user1@example.com | user1 | User |

Created by `seed_initial_data`, which `backend/start.sh` runs on container start.

## Architecture

- **Backend**: Django REST Framework with session-based auth (not JWT)
- **Frontend**: Vue 3 Composition API (`<script setup>`) + Quasar components + Pinia stores
- **Versioning**: Every card edit creates a new version; old versions preserved via `version_group` UUID. `DELETE` is a hard delete, not a soft delete.
- **Roles**: Admin > Curator > User. Curators can manage cards/tags. Admins can also manage users.
- **Daily Card**: Public endpoint cycles through all cards before repeating (see `flashcards/services.py`)

## Key Conventions

### Python/Django
- 4 spaces indentation
- Thin views, fat models -- business logic in `services.py`
- DRF ModelViewSets with serializers for all validation
- Apps by domain: `flashcards`, `users`, `core`
- Tests with pytest and Factory Boy

### Vue/JavaScript
- 2 spaces indentation
- Composition API with `<script setup>` (never Options API)
- Pinia for state management (setup store syntax with `ref`/`computed`)
- Scoped SCSS in SFCs
- Route guards via `meta: { requiresAuth, requiresCurator, requiresAdmin }`

### General
- No emojis in code, comments, or documentation
- No frontend testing frameworks -- Django unit tests only
- Session-based auth with cookies (`withCredentials: true` in axios)

## Important Gotchas

- **Card updates return new IDs**: `PUT /api/cards/{id}/` creates a new version with a different `id`. Frontend must redirect to the new ID after update.
- **Frontend Dockerfile order**: Must `COPY . .` BEFORE `RUN npm install` because Quasar's prepare script needs source files.
- **CSRF disabled for ALL API requests**: `DisableCSRFMiddleware` in `yoga_flashcards/middleware.py` skips CSRF for every `/api/` path. Despite the docstring it is not gated on `DEBUG`, so it is off in production too. Gating it requires a CSRF-bootstrap endpoint first -- DRF views are `csrf_exempt`, so Django never sets the `csrftoken` cookie the frontend interceptor looks for.
- **MySQL wait on startup**: `backend/start.sh` polls MySQL for up to 60 seconds before running migrations.

## Common Commands

```bash
# Development
docker-compose up --build                    # Full rebuild
docker-compose restart backend               # Restart single service
docker-compose logs -f backend               # View logs

# Testing
docker-compose exec backend python -m pytest              # All tests
docker-compose exec backend python -m pytest flashcards/   # Single app
docker-compose exec backend python -m pytest -v --cov      # With coverage

# Data management
docker-compose exec backend python manage.py seed_initial_data         # Import seed data
docker-compose exec backend python manage.py seed_initial_data --pull  # Export to JSON
docker-compose exec backend python manage.py import_cards /path/to.csv # Import CSV

# Kubernetes
docker build -t registry/yoga-backend:latest ./backend
docker build -t registry/yoga-frontend:latest ./frontend
helm install yoga-flashcards ./k8s/helm            # NOTE: chart has no templates/ yet
```

## API Overview

Public (no auth): `GET /api/health/`, `GET /api/dailycard/`, `GET /api/tags/`
Authenticated: `GET /api/cards/`, `GET /api/cards/{id}/`, `GET|PUT /api/users/profile/`, `POST /api/users/change-password/`
Curator+: CRUD on `/api/cards/`, `/api/tags/`, version history, revert
Admin only: `/api/users/manage/` for user CRUD, plus its `stats/` and `toggle_active/` actions

Not implemented despite appearing in the UI: favorites, social (Google/Facebook) auth, account deletion.

See `docs/API_REFERENCE.md` for full details.

## Key Files

| Area | Files |
|------|-------|
| Models | `backend/flashcards/models.py`, `backend/users/models.py` |
| API Views | `backend/flashcards/views.py`, `backend/users/views.py` |
| Business Logic | `backend/flashcards/services.py` (DailyCardService) |
| Permissions | `backend/flashcards/permissions.py` |
| Serializers | `backend/flashcards/serializers.py` (handles version creation in `update()`) |
| Stores | `frontend/src/stores/auth.js`, `frontend/src/stores/flashcards.js` |
| Routes | `frontend/src/router/routes.js` (definitions), `frontend/src/router/index.js` (guards) |
| HTTP Client | `frontend/src/boot/axios.js` (base URL, CSRF, credentials, 401 redirect) |
| Config | `docker-compose.yml`, `backend/yoga_flashcards/settings.py`, `frontend/quasar.config.js` |
| Specs | `docs/FUNCTIONAL_SPEC.md`, `docs/API_REFERENCE.md`, `docs/DATABASE_SCHEMA.md` |
