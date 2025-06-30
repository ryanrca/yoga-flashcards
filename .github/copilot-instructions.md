# Copilot Instructions for Yoga Flashcard Admin App

> For Django + DRF (MySQL) backend with Vue 3 + Quasar frontend

---

## Overall Stack Guidelines

- **Backend:** Python 3.x, Django, Django REST Framework, MySQL
- **Frontend:** Vue 3, Quasar Framework, Pinia, SASS
- **Infra:** Docker (dev), Kubernetes (prod via Helm)
- **Auth:** Django session-based login only (no signup)

---

## Django Backend Best Practices

- Use **thin views, fat models**; move logic to `services.py`.
- Always use Django **migrations** (keep in VCS).
- REST API with DRF **ModelViewSets** when practical.
- Use **serializers** for validation, never raw request data.
- Log to **STDOUT/STDERR** only in Docker; avoid file handlers.
- Settings via **django-environ** or env vars for 12-factor compliance.
- CSRF/CORS:
  - Include localhost ports in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.
  - Add middleware to disable CSRF for `/api/` routes in dev.
- Define explicit **auth** endpoints:
  - `/api/users/login/`, `/logout/`, `/auth-status/`.
- Tests:
  - Use `pytest` or Django `unittest`.
  - Include CRUD, permissions, versioning, regressions.
  - Use factories (e.g. `factory_boy`).
- Organize:
  - Apps by domain.
  - Separate `serializers.py`, `views.py`, `services.py`, `urls.py`, `tests.py`.

---

## Vue 3 + Quasar Frontend Best Practices

- Scaffold with Quasar CLI; install **Pinia** early.
- Use **SFCs** (Single File Components); break into logical components.
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
- **ESLint**:
  - Add `.eslintrc.js` at project start to avoid config errors.
  - Can disable linting in `quasar.config.js` if needed.

---

## Docker / Dev Environment

- Use **docker-compose** for local dev.
- Mount source for hot reload:
  - Django: `runserver` with autoreload.
  - Quasar: `quasar dev`.
- Install MySQL client dependencies in container.
- Include initial DB seed script:
  - Superuser creation.
  - ~5 example cards with minimal fields.

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

---

## Additional Reminders

- Don’t include frontend testing frameworks. **Django unit tests only**.
- Emit frontend build to `/dist` for static serving.
- Always configure environment variables for dev vs prod.

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


