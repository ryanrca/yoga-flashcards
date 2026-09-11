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
- **Production**: Kubernetes + Helm

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

### Authentication Endpoints

- `POST /api/users/register/` - Signup (email, password, password_confirm)
- `POST /api/users/login/` - Login (email and password)
- `POST /api/users/logout/` - Logout
- `GET /api/users/auth-status/` - Check authentication status
- `GET|PUT /api/users/profile/` - Read or update your own profile (names, email, daily email preference)
- `POST /api/users/change-password/` - Change your own password (current_password, new_password)

Admin only:

- `GET|POST /api/users/manage/` - List or create users
- `PUT|PATCH|DELETE /api/users/manage/{id}/` - Update or delete a user
- `POST /api/users/manage/{id}/toggle_active/` - Activate or deactivate a user
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
- **Edit user** when logged in - name, email, password and the daily card email preference. Account deletion is not implemented.
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
# Backend
docker build -t your-registry/yoga-flashcards-backend:latest ./backend
docker push your-registry/yoga-flashcards-backend:latest

# Frontend
docker build -t your-registry/yoga-flashcards-frontend:latest ./frontend
docker push your-registry/yoga-flashcards-frontend:latest
```

2. Deploy with Helm:
```bash
helm install yoga-flashcards ./k8s/helm \
  --set image.repository=your-registry/yoga-flashcards \
  --set env.DJANGO_SECRET_KEY=your-production-secret \
  --set database.password=your-db-password
```

**Status: incomplete.** `k8s/helm/` currently contains only `Chart.yaml` and `values.yaml`.
There is no `templates/` directory, so `helm install` creates no resources. `values.yaml`
also declares a `mysql` subchart that `Chart.yaml` does not list under `dependencies`, so it
is never fetched. The chart needs Deployment, Service and Ingress templates before this
section is usable.

## Configuration

### Environment Variables

**Backend:**
- `DEBUG` - Enable debug mode (default: 0)
- `DJANGO_SECRET_KEY` - Django secret key
- `DATABASE_URL` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins

**Frontend:**
- `API_BASE_URL` - Backend API base URL. **Not currently wired up:** `build.env` is commented
  out in `quasar.config.js`, so the variable never reaches the client bundle and
  `src/boot/axios.js` falls back to `http://localhost:8000`.

### Database

The application uses MySQL with proper UTF-8 support for international characters in Sanskrit terms.

## Security Features

- **Session-based authentication** - No JWT tokens to manage
- **Role-based permissions** - `IsCuratorOrAdmin` and `IsAdminOnly` gate the API by the
  `role` field; user management is admin-only on every action
- **CORS configuration** - Properly configured for frontend

Known gaps:

- **CSRF protection is disabled for all `/api/` routes**, in production as well as
  development. `DisableCSRFMiddleware` is not gated on `DEBUG`. Turning it on needs a
  CSRF-bootstrap endpoint first, since DRF views are `csrf_exempt` and Django therefore
  never sets the `csrftoken` cookie the frontend looks for.
- **Card deletes are permanent.** `DELETE /api/cards/{id}/` removes the row; there is no
  soft delete, despite the `is_active` flag existing on the model.

## Contributing

1. Follow the coding conventions in `.github/copilot-instructions.md`
2. Write tests for new features
3. Use the provided Docker environment for development
4. Ensure migrations are included for model changes

## TODO
CODE:
- Helm chart templates (see Production Deployment above)
- Favorites API and wire up the `/favorites` page
- Google / Facebook OAuth
- Account deletion endpoint
- Default card placeholder image
- Re-enable CSRF for `/api/` in production
- Soft delete for cards


CONTENT: By a human at later iterations
- Collect images
- Carefully create and edit new card content
- Hire designer to layout flashcards in adobe in-design

## License
None at this time. This program is 100% closed source and proprietary.  All rights reserved by the author.
