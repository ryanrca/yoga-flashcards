# Yoga Flashcard Admin App

A comprehensive web-based admin system for creating, editing, managing, and versioning flashcards for yoga teacher study decks.

## Features

- **Admin-only access** - All routes require authentication
- **Flashcard management** - CRUD operations with versioning
- **Image support** - Front and back photos for each card
- **Tagging system** - Organize cards with flexible tags
- **Search and filtering** - Find cards across all text fields
- **Version history** - Track changes and revert when needed
- **CSV import** - Bulk import cards from CSV files

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
docker-compose up
```

3. Access the application:
- Frontend: http://localhost:9000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

### Default Login

- Username: `admin`
- Password: `admin123`

## API Documentation

The API follows REST principles with the following main endpoints:

- `GET /api/cards/` - List cards (with pagination, search, filtering)
- `POST /api/cards/` - Create new card
- `GET /api/cards/{id}/` - Get card details with version history
- `PUT /api/cards/{id}/` - Update card (creates new version)
- `POST /api/cards/{id}/soft_delete/` - Soft delete card
- `POST /api/cards/{id}/revert_version/` - Revert to previous version
- `GET /api/tags/` - List tags
- `POST /api/tags/` - Create tag
- `PUT /api/tags/{id}/` - Update tag
- `DELETE /api/tags/{id}/` - Delete tag

### Authentication Endpoints

- `POST /api/users/login/` - Login
- `POST /api/users/logout/` - Logout  
- `GET /api/users/auth-status/` - Check authentication status

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

Options:
- `--dry-run` - Preview import without making changes
- `--user username` - Specify the creating user (default: admin)

## Frontend Features

- **Responsive design** with Quasar components
- **Real-time search** and filtering
- **Image upload** with preview
- **Version history** with revert functionality
- **Tag management** interface
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
  --set image.backend.repository=your-registry/yoga-flashcards-backend \
  --set image.frontend.repository=your-registry/yoga-flashcards-frontend \
  --set env.SECRET_KEY=your-production-secret \
  --set database.password=your-db-password
```

## Configuration

### Environment Variables

**Backend:**
- `DEBUG` - Enable debug mode (default: 0)
- `DJANGO_SECRET_KEY` - Django secret key
- `DATABASE_URL` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins

**Frontend:**
- `API_BASE_URL` - Backend API base URL

### Database

The application uses MySQL with proper UTF-8 support for international characters in Sanskrit terms.

## Security Features

- **Session-based authentication** - No JWT tokens to manage
- **CSRF protection** - Disabled for API routes in development
- **CORS configuration** - Properly configured for frontend
- **Admin-only access** - No public registration
- **Soft deletes** - Cards are never permanently deleted

## Contributing

1. Follow the coding conventions in `.github/copilot-instructions.md`
2. Write tests for new features
3. Use the provided Docker environment for development
4. Ensure migrations are included for model changes

## TODO
- Collect images
- Build script to rapidly input inital data
- Build frontend
- Hire designer to layout flashcards

## License


