# Copilot Instructions for Yoga Flashcard Admin App

## Overall Stack Guidelines

- **Backend:** Python 3.x, Django, Django REST Framework (DRF), MySQL
- **Frontend:*## Hints to Avoid Past Gotchas

### Docker & Node.js Issues - LESSONS LEARNED

**[X] Common Quasar/Node.js Pitfalls:**
- Using Node.js 18/20 with latest Quasar (causes webpack inject.style-rules.js errors)
- Manually creating Quasar projects instead of using official CLI
- Copying package.json before source code in Dockerfile
- Using old Quasar CLI versions or webpack instead of Vite
- Not using `--host 0.0.0.0` for Docker container access

**[OK] Solutions that Work:**
- **Always use Node.js 24 LTS** (24.4.1+)
- **Always use `npm create quasar`** for new projects
- **Copy source code before `npm install`** in Dockerfile
- **Use latest Quasar with Vite** (not webpack)
- **Test locally first** with `npm run dev` before Docker

**[FIX] If Quasar Build Fails:**
```bash
# Clean slate approach (always works):
rm -rf frontend
npm create quasar
# Follow interactive prompts
cd frontend
npm install pinia axios
npm run dev  # Test locally first
```

**[NOTE] Terminal Directory Issues:**
- Always use explicit paths: `cd ~/repos/yoga-flashcards/frontend && npm run dev`
- NPM often runs from wrong directory, causing "package.json not found"

### Database & Backend Issues

- **CSRF/CORS**:
  - Add `localhost:9000` in settings.
  - Use dev middleware to disable CSRF for `/api/` paths.
- **Auth endpoints**:
  - Implement login/logout/auth-status early.
  - Ensure session cookies are sent with Axios requests.
- **ESLint Errors**:
  - Create minimal `.eslintrc.js` if needed.
  - Don't forget Quasar config lint options.
- **Django Logging**:
  - Console handler only in container.
- **Container Startup**:
  - Add wait-for-db logic in scripts (30s for MySQL).
  - Health check DB before running migrations.
- **Static/Index.html**:
  - Ensure `src/index.template.html` and root `index.html` exist in Quasar.
- **Volumes**:
  - Mount static/media folders in Docker.ework, Pinia, SASS
- **Infra:** Docker compose (dev), Kubernetes (staging and prod via Helm)
- **Auth:** Django session-based login with user roles

---

## Django Backend Best Practices

- Use **thin views, fat models**; move logic to `services.py`.
- Always use Django **migrations** (keep in VCS).
- REST API with DRF **ModelViewSets** when practical.
- Use **serializers** for validation, never raw request data.
- Log to **STDOUT/STDERR** only in Docker; do not usea file handlers for logging.
- Settings via **django-environ** or env vars for 12-factor compliance.
- CSRF/CORS:
  - Include localhost ports in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.
  - Add middleware to disable CSRF for `/api/` routes in dev.
- Define explicit **auth** endpoints:
  - `/api/users/login/`, `/logout/`, `/auth-status/`.
- Tests:
  - Use `pytest` or Django `unittest`.
  - Include CRUD, permissions, versioning, regressions.
  - Use factories (e.g. `factory_boy`) for mock data.
- Organize:
  - Apps by domain.
  - Separate `serializers.py`, `views.py`, `services.py`, `urls.py`, `tests.py`.

---

## Vue 3 + Quasar Frontend Best Practices

- Scaffold with Quasar CLI; install **Pinia** early.
- Use **SFCs** (Single File Components); break into logical, resuable, compseable, components.
- Routing: Vue Router with auth-guard for all routes except login.
- State: Pinia for reactive global state.
- API:
  - Central Axios wrapper with base URL from env.
  - Handle errors, CSRF, retries.
- Form handling:
  - Use `v-model`.
  - Include validation (Vuelidate or custom).
- Styling:
  - Scoped SASS/Quasar utilities.
  - Variables in `/src/styles/variables.scss`.
  - Effort to centralize all styles in a single file or directory.  Minimize component styling unless necessary for composability.
- **ESLint**:
  - Add `.eslintrc.js` at project start to avoid config errors.
  - Can disable linting in `quasar.config.js` if needed.

---

## Docker / Dev Environment

### Working Setup (Verified Working)

- **Node.js**: Use **Node.js 24 LTS** (latest stable) in containers
- **Quasar**: Always use **official Quasar quick start**: `npm create quasar`
- **Docker**: Use `node:24-alpine` base image for frontend
- Use **docker-compose** for local dev.
- Mount source for hot reload:
  - Django: `runserver` with autoreload.
  - Quasar: `quasar dev --host 0.0.0.0`.
- Install MySQL client dependencies in container.
- Include initial DB seed script:
  - Superuser creation.
  - ~5 example cards with minimal fields.

### Quasar Setup - CRITICAL INSTRUCTIONS

**[X] NEVER manually create Quasar projects or try to fix version conflicts**

**[OK] ALWAYS use official Quasar CLI:**

```bash
# Remove any existing frontend directory first
rm -rf frontend

# Use official Quasar quick start (always works)
npm create quasar

# Choose these options:
# - App with Quasar CLI, let's go!
# - Project folder: yoga-flashcards (or desired name)
# - Javascript (not TypeScript for this project)
# - Quasar App CLI with Vite (recommended)
# - Composition API with <script setup> (recommended)
# - Sass with SCSS syntax
# - Features: Linting (vite-plugin-checker + ESLint)
# - Add Prettier: Yes
# - Install dependencies: Yes, use npm

# Then install additional dependencies:
cd frontend
npm install pinia axios
```

**[OK] This gives you the latest tested versions:**
- Quasar v2.18.2+
- @quasar/app-vite v2.3.0+
- Vue 3.4.18+
- Node.js 24+ support
- Vite (fast, modern build tool)

### Frontend Dockerfile - CRITICAL

**[X] Wrong order causes build failures:**
```dockerfile
# DON'T copy package.json first, then source later
COPY package*.json ./
RUN npm install  # FAILS: quasar prepare needs source code
COPY . .
```

**[OK] Correct Dockerfile for Quasar:**
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

### Docker Compose Configuration

**[OK] Working frontend service:**
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
  depends_on:
    - backend
  command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## Kubernetes / Helm Notes

- Define Helm charts:
  - Backend Deployment/Service.
  - Frontend Deployment/Service.
  - Ingress, ConfigMaps, Secrets.
- Ensure Django supports readiness probes (e.g. `/health/` endpoint).
- Production server: Gunicorn behind NGINX.

---

## Hints to Avoid Past Gotchas

- **CSRF/CORS**:
  - Add `localhost:9000` in settings.
  - Use dev middleware to disable CSRF on `/api/` paths.
- **Auth endpoints**:
  - Implement login/logout/auth-status early.
  - Ensure session cookies are sent with Axios requests.
- **ESLint Errors**:
  - Create minimal `.eslintrc.js` if needed.
  - Don’t forget Quasar config lint options.
- **Django Logging**:
  - Console handler only in container.
- **Container Startup**:
  - Add wait-for-db logic in scripts (30s for MySQL).
  - Health check DB before running migrations.
- **Static/Index.html**:
  - Ensure `src/index.template.html` and root `index.html` exist in Quasar.
- **Volumes**:
  - Mount static/media folders in Docker.
  - Map DB data if using local volume.

---

## Copilot Interaction Tips

- Comment your intent before starting generation.
- Isolate DRF serializers, models, or Vue components for focused prompts.
- Review queries for Django ORM correctness.
- Prefer small, incremental generations over giant multi-file dumps.

---

## Style Conventions

**Python/Django**
- 4 spaces
- `snake_case` variables and files
- `CamelCase` classes
- `UPPER_CASE` constants

**Vue/JS**
- `camelCase` variables/methods
- `PascalCase` component names
- `kebab-case` filenames
- 2-space indentation
- Scoped SASS in SFCs
- **NO EMOJI or non-ASCII characters** in any code, comments, or documentation files

---

## Additional Reminders

- Don’t include frontend testing frameworks. **Django unit tests only**.
- Emit frontend build to `/dist` for static serving.
- Always configure environment variables for dev vs staging vs prod.

---

## Example CSRF/CORS Config Snippet

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

# Dev-only middleware
class DisableCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)

```
