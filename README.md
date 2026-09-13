# Yoga Flashcard Admin App

A comprehensive web-based system for creating, editing, managing, and versioning flashcards for yoga teacher study decks.  Users can come to the site and see a "flash card of the day".  They do not get to choose which flashcard they can see, the system picks a new one every day.  Dont duplicate which flashcard is choosen as the flashcard of the day until all the cards have been used, then repeat.

Logged in users can see all flashcards.

## Features
- **Apps**: - Make two apps:
  - A "front-end" public accessible app. Users can sign up, edit their profile, password, and adjust daily email settings. Non-registered users can see most content, and cannot see a profile or daily email settings.
  - A "back-end" admin and curator accessible app.  (Admins and curators can log in and edit content and users)
- **User Roles**: - Three levels of users:
  - Admin (Full access, can CRUD everything including users and user permissions)
  - Curator (CRUD all flash cards, and other content.  Cannot edit users.)
  - User (front-end access only, no admin app access.)
- **Sign up**: - users can enter email and password (twice) to create new user. Email is used as the login identifier. After successful signup, users are automatically logged in and redirected to the home page.
- **Sign up with facebook or google**: *(planned, not implemented)* The login and signup pages show disabled Google/Facebook buttons; no OAuth provider is wired up.
- **Admin and curator access** - All admin and curator routes require authentication.  
- **Flashcard management** - Curators have all CRUD operations with versioning.
- **Version Control** - All card edits create new versions while preserving history. Each edit creates a new version marked as "LIVE". Previous versions remain accessible and can be reverted to at any time. All versions of a card share a version_group UUID.
- **Image support** - Front and back photos can be uploaded, edited and deleted for each card
- **Tagging system** - Organize cards with flexible tags
- **Search and filtering** - Find cards across all text fields
- **Version history** - View complete edit history for each card with ability to revert to any previous version
- **AI card images** - A bot illustrates each card's front through OpenRouter, seeding the prompt from the card's own text. Prompts and unaccepted images are admin-only; an image reaches users only when an admin accepts it. Every prompt and image is kept.
- **CSV import** - Bulk import cards from CSV files.  A script is provided to import new or update existing cards in bulk.
- **Default photo** *(planned, not implemented)* - A single .jpg or vector placeholder for cards with no image. Cards without an image currently render a CSS placeholder block.
- **Initial Data** - `backend/flashcards/management/commands/data/flashcards.json` seeds 19 cards:
  - The 8 limbs of yoga, title and sanscrit phrase, english definition, tagged as "8 Limbs"
  - The 5 yamas, title and sanscrit phrase, english definition, and tagged as "Yamas".
  - The 5 niyamas, title and sanscrit phrase, english definition, and tagged as "Niyamas".
  - A "Yoga" overview card, tagged as "8 Limbs".

  The legacy `initial_data.csv` at the repo root is no longer read by the seeder; it is kept
  only as sample input for `import_cards`.

## Tech Stack

- **Backend**: Django + Django REST Framework + MySQL
- **Frontend**: Vue 3 + Quasar Framework + Pinia
- **Development**: Docker Compose
- **Production**: Kubernetes + Helm, behind Traefik with a Let's Encrypt certificate

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd yoga-flashcards
```

2. Start the development environment:
```bash
./start-dev.sh
```

Alternatively, start manually:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:9000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

The setup script will automatically:
- Build Docker containers
- Set up the database
- Run migrations
- Create admin user
- Load initial flashcard data

### Default Login

- Email: `admin@example.com`
- Password: `admin123`

## API Documentation

The API follows REST principles with the following main endpoints:

- `GET /api/cards/` - List cards (with pagination, search, filtering), all users, authenticated only
- `GET /api/dailycard/` - See the card of the day, all users, regardless of authenticated status
- `POST /api/cards/` - Create new card (Admin and curators only)
- `GET /api/cards/{id}/` - Get card details (any authenticated user)
- `PUT /api/cards/{id}/` - Update card (creates new version, marks it as live) (admin and curator only)
- `DELETE /api/cards/{id}/` - Delete card, permanently (admin and curator only)
- `GET /api/cards/{id}/versions/` - Get version history for a card (admin and curator only)
- `POST /api/cards/{id}/revert_version/` - Revert to previous version (creates new live version from selected version) (admin and curator only)
- `GET /api/tags/` - List tags (all users, no auth required)
- `GET /api/health/` - Health check for Kubernetes probes (no auth required)
- `POST /api/tags/` - Create tag  (admin and curator only)
- `PUT /api/tags/{id}/` - Update tag (admin and curator only)
- `DELETE /api/tags/{id}/` - Delete tag (admin and curator only)

All data provided by the API is in JSON format. The API supports server-side pagination, search, and filtering for cards.

### Versioning System

The flashcard versioning system works as follows:

- **Version Groups**: All versions of the same card share a unique `version_group` UUID
- **Live Version**: Only one version per group is marked as `is_live=True` - this is the current active version
- **Creating Versions**: When a card is edited, a new copy is created with an incremented `version_number` and marked as live. The previous live version remains in the database but `is_live` is set to False
- **Version History**: All previous versions are preserved and can be viewed in the admin interface
- **Reverting**: Reverting to a previous version creates a new version (with the highest version number) that copies the content from the selected version and marks it as live
- **Querying**: By default, only live versions are returned in list queries. Version history can be accessed via the `/api/cards/{id}/versions/` endpoint

### Card Image Endpoints

All admin only. Prompts are never returned to any other role.

- `GET /api/cards/{id}/images/` - Generation history for the card, plus `preview`: the prompt a new generation would use
- `POST /api/cards/{id}/images/` - Queue a generation. Optional `prompt`, `look_and_feel_override`, `model`
- `GET /api/card-images/` - All generations (`?version_group=`, `?status=`)
- `POST /api/card-images/{id}/accept/` - Make this the image users see
- `POST /api/card-images/{id}/unaccept/` - Withdraw it from public view; the row is kept
- `POST /api/card-images/{id}/regenerate/` - Queue a new generation from this row's prompt
- `GET|PUT /api/image-settings/` - Global look and feel, default model and bot switches

Cards expose a single public field, `generated_image`: the URL of the accepted image, or `null`.

### Authentication Endpoints

- `POST /api/users/register/` - Signup (email, password, password_confirm)
- `POST /api/users/login/` - Login (email and password)
- `POST /api/users/logout/` - Logout
- `GET /api/users/auth-status/` - Check authentication status
- `GET|PUT /api/users/profile/` - Read or update your own profile (names, email, daily email preference)
- `POST /api/users/change-password/` - Change your own password (current_password, new_password)
- `DELETE /api/users/delete-account/` - Delete your own account (soft delete; signs you out)
- `GET /api/users/csrf/` - Issue a CSRF token and set the `csrftoken` cookie (no auth required)

Admin only:

- `GET|POST /api/users/manage/` - List or create users
- `PUT|PATCH|DELETE /api/users/manage/{id}/` - Update or delete a user
- `POST /api/users/manage/{id}/toggle_active/` - Activate or deactivate a user
- `POST /api/users/manage/{id}/restore/` - Restore a soft-deleted account
- `GET /api/users/manage/?include_deleted=true` - Include soft-deleted accounts in the list
- `GET /api/users/manage/stats/` - User counts for the admin dashboard

**Note**: The system uses email addresses as the primary login identifier. Users log in with their email address and password.

### Authentication Flow

**Login Process:**
1. User enters email and password on login page
2. After successful authentication, user is redirected to home page (`/`)
3. If user was redirected to login from a protected page, they return to that page after login

**Signup Process:**
1. User enters email and password (twice for confirmation) on signup page
2. After successful account creation, user is automatically logged in
3. User is redirected to home page (`/`) and can immediately access the application

**Session Management:**
- Uses Django session-based authentication (no JWT tokens)
- Sessions persist across browser sessions
- Automatic logout on session expiry

## AI Card Images

A bot generates one front image per card through [OpenRouter](https://openrouter.ai).
The default model is `black-forest-labs/flux.2-pro`; an admin can change it globally or
per image.

### How a prompt is built

```
<card title, Sanskrit phrase, short answer, definition, tags>
+ "Do not render any text, letters, words or numbers in the image."

Style: <look and feel>
```

The look and feel is a single global field an admin edits once, and any individual image
can override it. Admins can also replace the whole prompt for a given generation.

### Rules the bot follows

- **Generates each card's first image exactly once.** Auto-queueing only picks up card
  families with no image rows at all, so a failed or rejected image is never retried on
  its own. Regenerating is always a deliberate admin action.
- **Bounded retries.** `max_attempts` (default 3) caps provider calls per image row.
- **No parallel duplicates.** Rows are claimed with `SELECT ... FOR UPDATE SKIP LOCKED`,
  so overlapping bot runs cannot send the same row twice.
- **Append-only history.** Regenerating adds a row; nothing is edited or deleted.
- **Images follow `version_group`,** not a card id, so editing a card keeps its images.

### Running the bot

```bash
# Show the prompts that would be used; changes nothing, calls nothing
docker-compose exec backend python manage.py generate_card_images --dry-run

# Queue anything missing an image, then generate up to 5
docker-compose exec backend python manage.py generate_card_images --limit 5

# One specific card, even if it already has images
docker-compose exec backend python manage.py generate_card_images --card-id 7
```

Schedule it however you like (cron, or a Kubernetes CronJob). Each run is bounded by
`--limit`, so it is safe to run often. Generation costs money per image -- roughly
$0.03/MP on FLUX.2 Pro -- and the cost OpenRouter reports is recorded on each row.

## CSV Import

Import cards in bulk using the Django management command:

```bash
docker-compose exec backend python manage.py import_cards /path/to/cards.csv
```

CSV format:
```csv
title,phrase,definition,tags
"Downward Dog","Adho Mukha Svanasana","A foundational pose","Asana,Sanskrit"
```

`title` and `definition` are required; `phrase` and `tags` are optional. Separate multiple
tags with commas inside the single `tags` field.

Options:
- `--dry-run` - Preview import without making changes
- `--user username` - Specify the creating user (default: admin)
If the tag does not yet exist, it will be created. If the tag already exists, it will be added to the card.

## Frontend Admin and Curator app Features

- **Responsive design** with Quasar components
- **Real-time search** and filtering
- **Image upload** with preview
- **Version history** with revert functionality
- **Tag management** interface
- **Session-based authentication**

## Frontend User app Features

- **Responsive design** with Quasar components
- **Login/Logout** with Quasar components. After successful login, users are redirected to the home page.
- **Signup** asks users for password twice. After successful signup, users are automatically logged in and redirected to the home page.
- **Flashcard of the day** Displays today's flashcard (all visitors)
- **Real-time search** and filtering when logged in
- **User favorites** *(planned, not implemented)* - The `/favorites` page and the star buttons are placeholders; there is no favorites API yet, though `UserProfile.favorite_cards` exists on the model. Card sharing (Web Share API / copy to clipboard) does work.
- **Edit user** when logged in - name, email, password and the daily card email preference, plus account deletion.
- **Session-based authentication**

## Development

### Backend Development

The Django backend uses:
- **Thin views, fat models** - Business logic in services
- **DRF ModelViewSets** - RESTful API endpoints
- **Django migrations** - Database schema management
- **Factory Boy** - Test data generation
- **Pytest** - Unit testing

### Frontend Development

The Vue 3 frontend uses:
- **Composition API** - Modern Vue 3 patterns
- **Pinia** - State management
- **Quasar** - UI components and build system
- **Axios** - HTTP client with interceptors
- **Vue Router** - Navigation with auth guards

### Testing

Run backend tests:
```bash
docker-compose exec backend python -m pytest
```

## Production Deployment

### Kubernetes with Helm

1. Build and push Docker images:
```bash
REG=your-registry
TAG=1.0.0

# Backend: gunicorn + WhiteNoise, with static files baked in at build time
docker build -t $REG/yoga-flashcards-backend:$TAG ./backend
docker push $REG/yoga-flashcards-backend:$TAG

# Frontend: built SPA served by nginx. API_BASE_URL is compiled into the bundle,
# so it has to be supplied here -- it cannot be changed at run time.
docker build -f frontend/Dockerfile.prod \
  --build-arg API_BASE_URL=https://flashcards.example.net \
  -t $REG/yoga-flashcards-frontend:$TAG ./frontend
docker push $REG/yoga-flashcards-frontend:$TAG
```

2. Deploy with Helm:
```bash
helm upgrade --install yoga-flashcards ./k8s/helm \
  --namespace yoga-flashcards --create-namespace --wait --timeout 8m
```

The chart brings up the backend, the SPA, MySQL, both PVCs, the Traefik ingress with a
Let's Encrypt certificate, and a post-install Job that loads the starter flashcards.
Secrets are generated on first install and preserved across upgrades.

See **[k8s/README.md](k8s/README.md)** for the full deployment guide, the
cluster-specific choices, and day-to-day operations.

## Configuration

### Environment Variables

**Backend:**
- `DEBUG` - Enable debug mode (default: 0)
- `DJANGO_SECRET_KEY` - Django secret key
- `DATABASE_URL` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins (comma separated)
- `CSRF_TRUSTED_ORIGINS` - Origins allowed to send unsafe requests. Falls back to
  `CORS_ALLOWED_ORIGINS` when unset.
- `DJANGO_ALLOWED_HOSTS` - Comma-separated hostnames. Defaults to `*`; **set this in
  production**.
- `CSRF_COOKIE_SECURE` / `SESSION_COOKIE_SECURE` - Set both to `1` in production (HTTPS).
- `CSRF_COOKIE_SAMESITE` / `SESSION_COOKIE_SAMESITE` - Default `Lax`. Only a genuinely
  cross-site deployment needs `None`, which also requires the Secure flags above.
- `OPENROUTER_API_KEY` - Required for image generation. Read from the environment only; never
  stored in the database or returned by the API. Without it the bot refuses to run.
- `OPENROUTER_BASE_URL` - Default `https://openrouter.ai/api/v1`
- `OPENROUTER_TIMEOUT` - Seconds per generation request (default 180)
- `OPENROUTER_SITE_URL` / `OPENROUTER_SITE_NAME` - Optional attribution on the OpenRouter dashboard

**Frontend:**
- `API_BASE_URL` - Backend API base URL, injected via `build.env` in `quasar.config.js`.
  Read at **build** time, not run time: a production image must be built with it set.

### Database

The application uses MySQL with proper UTF-8 support for international characters in Sanskrit terms.

## Security Features

- **Session-based authentication** - No JWT tokens to manage
- **Role-based permissions** - `IsCuratorOrAdmin` and `IsAdminOnly` gate the API by the
  `role` field; user management is admin-only on every action
- **CORS configuration** - Properly configured for frontend

- **CSRF protection** - Enforced on every authenticated API write. DRF views are
  `csrf_exempt`, so the check comes from `SessionAuthentication.enforce_csrf()` rather than
  `CsrfViewMiddleware`; Django therefore never sets the `csrftoken` cookie for `/api/` by
  itself, and `GET /api/users/csrf/` exists to issue one. The frontend primes it
  automatically before its first unsafe request. Requests from an origin outside
  `CSRF_TRUSTED_ORIGINS` are rejected even with a valid token.
- **Accounts are soft deleted** - Deleting a user disables the account and hides it, but
  removes nothing. `Flashcard.created_by` uses `PROTECT`, so a user delete can never cascade
  into their card library.

Known gaps:

- **Card deletes are permanent.** `DELETE /api/cards/{id}/` removes the row; there is no
  soft delete for cards, despite the `is_active` flag existing on the model.
- **Login itself is not CSRF-protected.** DRF only enforces CSRF once a session
  authenticates, and login is anonymous. This is standard DRF behaviour.

## Contributing

1. Follow the coding conventions in `.github/copilot-instructions.md`
2. Write tests for new features
3. Use the provided Docker environment for development
4. Ensure migrations are included for model changes

## TODO
CODE:
- Favorites API and wire up the `/favorites` page
- Google / Facebook OAuth
- Default card placeholder image
- Soft delete for cards


CONTENT: By a human at later iterations
- Collect images
- Carefully create and edit new card content
- Hire designer to layout flashcards in adobe in-design

## License
None at this time. This program is 100% closed source and proprietary.  All rights reserved by the author.
