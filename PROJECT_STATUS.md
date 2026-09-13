# Yoga Flashcards Application - Project Status

## [DONE] Completed Components

### Backend (Django + DRF)
- **Project Structure**: Complete Django project with proper app organization
- **Models**: 
  - Custom User model with roles (Admin, Curator, User) and soft deletion
  - Flashcard model with versioning support
  - Tag model for categorization
  - DailyCard and CardUsageLog for daily card rotation
  - CardImage and ImageGenerationSettings for AI card illustration
  - UserProfile for extended user data
- **API Endpoints**: RESTful API with proper authentication and permissions
- **Authentication**: Session-based authentication with CORS configured and CSRF enforced on authenticated writes
- **Management Commands**: 
  - `seed_initial_data`: Creates admin/test users and loads flashcards from JSON (`--pull` exports back out)
  - `import_cards`: Bulk import from CSV files
  - `generate_card_images`: the image bot (queues missing cards, drains the queue, bounded per run)
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
  - Card image panel (prompt editing, generation history, accept/withdraw) and a global
    image look-and-feel settings page
  - User profile management
- **Responsive Design**: Mobile-friendly Quasar components

Note: there is no shared flashcard component. Card markup is duplicated inline across
`pages/public/CardsPage.vue`, `DailyCardPage.vue`, `FavoritesPage.vue` and the admin pages.
`src/components/` holds only `EssentialLink.vue`. Extracting one is worthwhile.

### Infrastructure
- **Docker Compose**: Complete development environment
- **Kubernetes**: Helm chart in `k8s/helm/` -- Deployments, MySQL StatefulSet, PVCs,
  Traefik ingress with a Let's Encrypt certificate, and a post-install seed Job.
  Deployed at https://flashcards.jetli.kicks-ass.net
- **Production images**: gunicorn + WhiteNoise for the backend, nginx-served static
  build for the SPA
- **Initial Data**: JSON seed with 19 flashcards (8 limbs, yamas, niyamas, plus a "Yoga"
  overview card), loaded by `seed_initial_data`

### Testing
- **Backend**: 197 pytest tests across `core`, `flashcards` and `users`, using Factory Boy
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
   - Advanced search with filters
   - Progress tracking
   - Email notifications for daily cards (the `daily_email_enabled` preference saves, but
     nothing sends mail)

3. **AI card images** -- generation, prompt editing, history and acceptance are implemented.
   Still outstanding:
   - No scheduler: the bot runs by hand. Add a Kubernetes CronJob once the Helm chart lands
     (PR #5), or a cron entry otherwise.
   - No queue overview: an admin cannot see pending generations across all cards in one place.
   - Not smoke-tested against the live OpenRouter API. The response parser accepts both
     documented shapes but has only been exercised against fakes.

4. **UI/UX Improvements**:
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

2. **Kubernetes** -- the chart is complete and deployed. Still outstanding:
   - No CI/CD; images are built and pushed by hand
   - Single replica throughout. More backend replicas need the migrations moved out
     of the init container into a Job, and the media PVC moved to ReadWriteMany
   - No backup schedule for the MySQL PVC

3. **Production Setup**:
   - Environment-specific configurations
   - Security hardening
   - Performance optimization
   - Monitoring and logging
   - CI/CD pipeline

4. **Security**:
   - Card `DELETE` is permanent; there is no soft delete for cards despite the `is_active`
     flag. Accounts *are* soft deleted.
   - Login itself is not CSRF-protected: DRF only enforces CSRF once a session
     authenticates, and login is anonymous. Standard DRF behaviour.

5. **Content Management**:
   - Approval workflow (creation, image upload and versioning are done)

## [TODO] Next Steps

1. **Immediate**:
   - Change the seeded admin@example.com password on the deployed instance
   - Back up the generated `yoga-flashcards-secrets` Secret
   - Fix the expired TLS cert on `repo.jetli.kicks-ass.net` (the registry ingress still
     references `jetli-sept-2021-3year`, so pushes fall back to the insecure-registry
     path over HTTP)

2. **Short Term**:
   - Favorites API, then wire up `/favorites` and the star buttons
   - Extract a shared flashcard component
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
