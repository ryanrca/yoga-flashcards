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
- **Versioning**: Every card edit creates a new version; old versions preserved via `version_group` UUID. Card `DELETE` is a hard delete.
- **Accounts are soft deleted**: deleting a user sets `is_deleted`/`deleted_at` and clears `is_active`. The row, their profile and every card they authored are kept. `Flashcard.created_by` is `PROTECT`, so a hard delete cannot cascade.
- **Roles**: Admin > Curator > User. Curators can manage cards/tags. Admins can also manage users.
- **Daily Card**: Public endpoint cycles through all cards before repeating (see `flashcards/services.py`)
- **AI card images**: A bot generates one front image per card through OpenRouter. Prompts and unaccepted images are admin-only; users see an image only once an admin accepts it. History is append-only -- regenerating adds a row, never edits one.

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
- **`FlashcardViewSet.get_permissions()` is overridden**, which makes `permission_classes` declared on an `@action` dead code. Any new action needing different permissions must be named inside `get_permissions()` -- that is how the admin-only `images` action is gated.
- **CSRF is enforced on authenticated writes**: DRF views are `csrf_exempt`, so the check comes from `SessionAuthentication.enforce_csrf()`, not `CsrfViewMiddleware`. Django therefore never sets the `csrftoken` cookie for `/api/` on its own -- `GET /api/users/csrf/` hands one out, and `boot/axios.js` primes it before the first unsafe request. Anonymous requests (login, register, public reads) need no token.
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

# AI card images (bot)
docker-compose exec backend python manage.py generate_card_images --dry-run  # show prompts, change nothing
docker-compose exec backend python manage.py generate_card_images --limit 5  # queue + generate
docker-compose exec backend python manage.py generate_card_images --card-id 7

# Data management
docker-compose exec backend python manage.py seed_initial_data         # Import seed data
docker-compose exec backend python manage.py seed_initial_data --pull  # Export to JSON
docker-compose exec backend python manage.py import_cards /path/to.csv # Import CSV

# Kubernetes -- deployed at https://flashcards.jetli.kicks-ass.net (ns yoga-flashcards)
# API_BASE_URL is compiled into the frontend bundle, so it must be set at build time.
REG=repo.jetli.kicks-ass.net; TAG=1.0.0
docker build -t $REG/yoga-flashcards-backend:$TAG ./backend
docker build -f frontend/Dockerfile.prod \
  --build-arg API_BASE_URL=https://flashcards.jetli.kicks-ass.net \
  -t $REG/yoga-flashcards-frontend:$TAG ./frontend
docker push $REG/yoga-flashcards-backend:$TAG && docker push $REG/yoga-flashcards-frontend:$TAG

helm upgrade --install yoga-flashcards ./k8s/helm \
  --namespace yoga-flashcards --create-namespace --wait --timeout 8m
```

See `k8s/README.md` for the cluster-specific choices (Traefik 2.6 legacy CRDs,
per-namespace Issuer, pinned MySQL 8.0.28, probe Host headers).

## API Overview

Public (no auth): `GET /api/health/`, `GET /api/dailycard/`, `GET /api/tags/`, `GET /api/users/csrf/`
Authenticated: `GET /api/cards/`, `GET /api/cards/{id}/`, `GET|PUT /api/users/profile/`, `POST /api/users/change-password/`, `DELETE /api/users/delete-account/`
Curator+: CRUD on `/api/cards/`, `/api/tags/`, version history, revert
Admin only: `/api/users/manage/` for user CRUD, plus its `stats/`, `toggle_active/` and `restore/` actions. `?include_deleted=true` reveals soft-deleted accounts; they are hidden otherwise.
Admin only (card images): `GET|POST /api/cards/{id}/images/`, `/api/card-images/{id}/` with `accept/`, `unaccept/`, `regenerate/`, and `GET|PUT /api/image-settings/`.

Not implemented despite appearing in the UI: favorites, social (Google/Facebook) auth.

See `docs/API_REFERENCE.md` for full details.

## Key Files

| Area | Files |
|------|-------|
| Models | `backend/flashcards/models.py`, `backend/users/models.py` |
| API Views | `backend/flashcards/views.py`, `backend/users/views.py` |
| Business Logic | `backend/flashcards/services.py` (DailyCardService, CardImageService) |
| AI images | `backend/flashcards/openrouter.py`, `management/commands/generate_card_images.py`, `frontend/src/pages/admin/ImageSettingsPage.vue` |
| Permissions | `backend/flashcards/permissions.py` |
| Serializers | `backend/flashcards/serializers.py` (handles version creation in `update()`) |
| Stores | `frontend/src/stores/auth.js`, `frontend/src/stores/flashcards.js` |
| Routes | `frontend/src/router/routes.js` (definitions), `frontend/src/router/index.js` (guards) |
| HTTP Client | `frontend/src/boot/axios.js` (base URL, CSRF, credentials, 401 redirect) |
| Config | `docker-compose.yml`, `backend/yoga_flashcards/settings.py`, `frontend/quasar.config.js` |
| Deployment | `k8s/helm/` (chart), `k8s/README.md`, `backend/Dockerfile`, `frontend/Dockerfile.prod` |
| Specs | `docs/FUNCTIONAL_SPEC.md`, `docs/API_REFERENCE.md`, `docs/DATABASE_SCHEMA.md` |
