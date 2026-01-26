# AI Assistant Instructions - Yoga Flashcard Admin App

This document provides instructions for AI coding assistants (GitHub Copilot, Claude Code, etc.) working on the Yoga Flashcards application.

## Documentation Reference

For comprehensive information, see:
- `CLAUDE.md` - Main AI assistant instructions (root directory)
- `backend/CLAUDE.md` - Backend-specific instructions
- `frontend/CLAUDE.md` - Frontend-specific instructions
- `docs/FUNCTIONAL_SPEC.md` - Complete functional specification
- `docs/API_REFERENCE.md` - API endpoint documentation

---

## Development Environment

### CRITICAL: Always Use WSL Ubuntu Shell

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

### Quick Start

```bash
# Start development environment
docker-compose up --build

# Or use the start script
./start-dev.sh
```

**URLs:**
- Frontend: http://localhost:9000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

**Test Accounts:**
| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | Admin |
| curator1@example.com | curator1 | Curator |
| user1@example.com | user1 | User |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2 + Django REST Framework |
| Frontend | Vue 3 + Quasar 2.16 + Pinia |
| Database | MySQL 8.0 |
| Dev Environment | Docker Compose |
| Production | Kubernetes + Helm |

---

## Django Backend Best Practices

### Architecture
- Use **thin views, fat models** - move logic to `services.py`
- Always use Django **migrations** (keep in VCS)
- REST API with DRF **ModelViewSets** when practical
- Use **serializers** for validation, never raw request data
- Log to **STDOUT/STDERR** only in Docker

### Key Patterns

```python
# Permission classes
class IsCuratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_curator()

# Versioning in serializer.update()
def update(self, instance, validated_data):
    return instance.create_new_version(**validated_data)

# Daily card service
card = DailyCardService.get_daily_card()
```

### Organization
- Apps by domain: flashcards, users, core
- Separate `serializers.py`, `views.py`, `services.py`, `urls.py`
- Tests with pytest and Factory Boy

---

## Vue 3 + Quasar Frontend Best Practices

### Architecture
- Scaffold with Quasar CLI; use **Pinia** for state
- Use **SFCs** (Single File Components) with Composition API
- Vue Router with auth guards for protected routes
- Central Axios wrapper with base URL from env

### Key Patterns

```javascript
// Store pattern (Pinia)
export const useFlashcardsStore = defineStore('flashcards', () => {
  const cards = ref([])
  const loading = ref(false)

  async function fetchCards(params) {
    loading.value = true
    const response = await api.get('/cards/', { params })
    cards.value = response.data.results
    loading.value = false
  }

  return { cards, loading, fetchCards }
})

// Route guard
meta: { requiresCurator: true }
```

### ESLint
- Add `.eslintrc.js` at project start
- Can disable linting in `quasar.config.js` if needed

---

## Docker Configuration

### Working Setup

- **Node.js**: Use Node.js 24 LTS in containers
- **Quasar**: Always use official Quasar quick start: `npm create quasar`
- **Docker**: Use `node:24-alpine` base image for frontend

### Frontend Dockerfile - CRITICAL

```dockerfile
FROM node:24-alpine
WORKDIR /app

# Copy package files AND source code first
COPY package*.json ./
COPY . .

# Then install (quasar prepare needs source code)
RUN npm install

EXPOSE 9000
CMD ["npm", "run", "dev"]
```

**WRONG order (will fail):**
```dockerfile
COPY package*.json ./
RUN npm install  # FAILS: quasar prepare needs source
COPY . .
```

### Docker Compose

```yaml
frontend:
  build: ./frontend
  ports:
    - "9000:9000"
  environment:
    - API_BASE_URL=http://localhost:8000
  volumes:
    - ./frontend:/app
    - /app/node_modules
  command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## Common Issues and Solutions

### Quasar/Node.js Issues
**Problem**: Webpack inject.style-rules.js errors
**Solution**: Use Node.js 24 and recreate with official CLI:
```bash
rm -rf frontend
npm create quasar
cd frontend
npm install pinia axios
```

### CSRF/CORS Issues
Ensure settings include:
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:9000"]
CORS_ALLOW_CREDENTIALS = True
```

### Database Connection
Backend waits for MySQL in `start.sh` (up to 60 seconds).

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
- `camelCase` for variables/methods
- `PascalCase` for component names
- `kebab-case` for filenames
- Scoped SCSS in SFCs

### General
- **NO emojis** in code, comments, or documentation
- Keep code DRY but don't over-abstract
- Prefer explicit over implicit

---

## CSRF/CORS Config Snippet

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Dev-only middleware to disable CSRF for API
class DisableCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)
```

---

## AI Interaction Tips

- Comment your intent before starting generation
- Isolate DRF serializers, models, or Vue components for focused prompts
- Review queries for Django ORM correctness
- Prefer small, incremental generations over giant multi-file dumps
- Reference the documentation files for detailed specifications

---

## Additional Reminders

- Don't include frontend testing frameworks. **Django unit tests only**.
- Emit frontend build to `/dist` for static serving
- Always configure environment variables for dev vs staging vs prod
- Session-based auth (not JWT)
- Versioning: every edit creates a new version, old versions preserved
