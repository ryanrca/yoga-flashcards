# Yoga Flashcards Application - Project Status

## [DONE] Completed Components

### Backend (Django + DRF)
- **Project Structure**: Complete Django project with proper app organization
- **Models**: 
  - Custom User model with roles (Admin, Curator, User)
  - Flashcard model with versioning support
  - Tag model for categorization
  - DailyCard and CardUsageLog for daily card rotation
  - UserProfile for extended user data
- **API Endpoints**: RESTful API with proper authentication and permissions
- **Authentication**: Session-based authentication with CORS configured (CSRF is currently bypassed for `/api/` -- see Security below)
- **Management Commands**: 
  - `seed_initial_data`: Creates admin/test users and loads flashcards from JSON (`--pull` exports back out)
  - `import_cards`: Bulk import from CSV files
- **Docker**: Complete containerization with MySQL database

### Frontend (Vue 3 + Quasar)
- **Project Structure**: Complete Quasar CLI project structure
- **Routing**: Vue Router with authentication guards
- **State Management**: Pinia stores for auth and flashcards
- **Pages**:
  - Home page with daily card display
  - User authentication (login/register)
  - Cards library with search and filtering
  - Admin panel with dashboard
  - User profile management
- **Responsive Design**: Mobile-friendly Quasar components

Note: there is no shared flashcard component. Card markup is duplicated inline across
`pages/public/CardsPage.vue`, `DailyCardPage.vue`, `FavoritesPage.vue` and the admin pages.
`src/components/` holds only `EssentialLink.vue`. Extracting one is worthwhile.

### Infrastructure
- **Docker Compose**: Complete development environment
- **Initial Data**: JSON seed with 19 flashcards (8 limbs, yamas, niyamas, plus a "Yoga"
  overview card), loaded by `seed_initial_data`

### Testing
- **Backend**: 120 pytest tests across `core`, `flashcards` and `users`, using Factory Boy
  and a SQLite test settings module (`yoga_flashcards/settings_test.py`)
- **Frontend**: none, by design (see CLAUDE.md)

## [WIP] Areas for Future Development

### Frontend Features
1. **Admin Interface** -- card CRUD, version history and revert, user management and tag
   management are all implemented. Still outstanding:
   - Bulk operations
   - CSV import from the dashboard (the button is a placeholder; use the management command)

2. **Enhanced User Features**:
   - Favorites system -- the `/favorites` page and star buttons are placeholders with no
     backing API, though `UserProfile.favorite_cards` exists on the model
   - Account deletion endpoint (the profile page button has no backend route)
   - Advanced search with filters
   - Progress tracking
   - Email notifications for daily cards (the `daily_email_enabled` preference saves, but
     nothing sends mail)

3. **UI/UX Improvements**:
   - Better card design with image placeholders
   - Animation improvements
   - Dark/light theme toggle
   - Accessibility features

### Backend Enhancements
1. **Email System**:
   - Email verification for registration
   - Daily card email notifications
   - Password reset functionality

2. **Social Authentication**:
   - Google OAuth integration
   - Facebook OAuth integration

3. **Advanced Features**:
   - Card statistics and analytics
   - Learning progress tracking
   - Advanced search with Elasticsearch
   - API rate limiting
   - Caching with Redis

### DevOps & Production
1. **Testing**:
   - Integration tests
   - End-to-end tests

2. **Kubernetes**:
   - `k8s/helm/` has `Chart.yaml` and `values.yaml` but **no `templates/` directory**, so
     `helm install` creates no resources
   - `values.yaml` declares a `mysql` subchart that `Chart.yaml` does not list under
     `dependencies`, so it is never fetched

3. **Production Setup**:
   - Environment-specific configurations
   - Security hardening
   - Performance optimization
   - Monitoring and logging
   - CI/CD pipeline

4. **Security**:
   - `DisableCSRFMiddleware` strips CSRF from every `/api/` path in all environments, not
     just development. Re-enabling it needs a CSRF-bootstrap endpoint, because DRF views are
     `csrf_exempt` so Django never sets the `csrftoken` cookie the frontend reads.
   - Card `DELETE` is permanent; there is no soft delete despite the `is_active` flag.

5. **Content Management**:
   - Approval workflow (creation, image upload and versioning are done)

## [TODO] Next Steps

1. **Immediate**:
   - Write the Helm chart templates so `helm install` actually deploys something
   - Re-enable CSRF for `/api/` in production

2. **Short Term**:
   - Favorites API, then wire up `/favorites` and the star buttons
   - Extract a shared flashcard component
   - Account deletion endpoint
   - Implement email verification (the token is generated and printed, never mailed)

3. **Medium Term**:
   - Add social authentication
   - Daily card email delivery
   - Default placeholder image for cards with no photo

4. **Long Term**:
   - Production deployment
   - Performance optimization
   - Advanced analytics and reporting

## [ARCH] Architecture Overview

```
Frontend (Vue 3 + Quasar)     Backend (Django + DRF)
├── Public App                ├── Core App (health, daily card)
│   ├── Home (daily card)     ├── Users App (auth, profiles)
│   ├── Cards Library         ├── Flashcards App (CRUD, versions)
│   ├── User Profile          └── API Endpoints
│   └── Authentication        
└── Admin App                 Database (MySQL)
    ├── Dashboard             ├── Users (custom model)
    ├── Card Management       ├── Flashcards (with versioning)
    ├── User Management       ├── Tags
    └── Tag Management        ├── DailyCard
                              └── CardUsageLog
```

## File Structure

```
yoga-flashcards/
├── backend/                  # Django backend
│   ├── yoga_flashcards/     # Main project config
│   ├── core/                # Core app (health, daily card)
│   ├── users/               # User management
│   ├── flashcards/          # Flashcard CRUD and logic
│   └── requirements.txt     # Python dependencies
├── frontend/                # Vue 3 + Quasar frontend
│   ├── src/
│   │   ├── layouts/         # Page layouts
│   │   ├── pages/           # Vue pages
│   │   ├── components/      # Reusable components
│   │   ├── stores/          # Pinia state management
│   │   └── router/          # Vue Router config
│   └── package.json         # Node dependencies
├── k8s/                     # Kubernetes deployment (chart incomplete)
├── docs/                    # Functional spec, API reference, DB schema
├── docker-compose.yml       # Development environment
├── initial_data.csv         # Legacy CSV, sample input for import_cards only
└── start-dev.sh            # Development setup script
```

This application provides a solid foundation for a yoga learning platform with room for extensive feature development and scaling.
