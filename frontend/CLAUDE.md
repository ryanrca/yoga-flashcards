# Frontend - Claude Code Instructions

## Quick Reference

```
Framework:  Vue 3 + Quasar 2.16
State:      Pinia 3.x
HTTP:       Axios (session cookies, CSRF)
Port:       9000
Dev:        npm run dev -- --host 0.0.0.0
Build:      npm run build
Lint:       npx eslint src/
```

## Architecture

- **Composition API** with `<script setup>` (never Options API)
- **Pinia** setup store syntax (`defineStore` with `ref`/`computed`, not options syntax)
- **Quasar components** for all UI (q-page, q-card, q-btn, q-input, q-table, q-dialog, etc.)
- **Scoped SCSS** in SFCs
- **Hash-based routing** (`createWebHashHistory`)
- **Session-based auth** with cookies (`withCredentials: true`)

## Key Files

| File | Purpose |
|------|---------|
| `src/stores/auth.js` | Auth state, login/logout/signup, role computed properties |
| `src/stores/flashcards.js` | Cards CRUD, daily card, tags, pagination, version history |
| `src/router/routes.js` | Route definitions with `meta` flags |
| `src/router/index.js` | Navigation guards (checks auth/role before route access) |
| `src/boot/axios.js` | Axios instance: base URL, CSRF token from cookie, 401 redirect |
| `src/layouts/PublicLayout.vue` | Public pages layout |
| `src/layouts/AdminLayout.vue` | Admin panel layout (sidebar navigation) |
| `quasar.config.js` | Quasar plugins, build config |

## Route Guards

Routes use `meta` flags checked in `router/index.js` beforeEach guard:
- `meta: { requiresAuth: true }` -- any logged-in user
- `meta: { requiresCurator: true }` -- curator or admin
- `meta: { requiresAdmin: true }` -- admin only

Unauthorized users redirect to home or login.

## Important Patterns

- **Card update returns new ID**: After `PUT /api/cards/{id}/`, the response has a different `id` (new version). Always redirect to the new ID.
- **Auth check on first navigation**: Router checks `authStore.checkAuthStatus()` once on first route, then caches the result.
- **Store error handling**: All store actions set `loading`/`error` refs. Components use `v-if="store.loading"` / `v-else-if="store.error"` pattern.
- **Multipart uploads**: Card create/update uses `FormData` with `Content-Type: multipart/form-data` for image uploads.
- **Tag selection**: Tag selects use `{ label, value }` objects mapped from the tags array.
- **401 redirects use the hash**: routing is hash-based, so `boot/axios.js` redirects to
  `#/login`, not `/login`.
- **`API_BASE_URL` is not wired in**: `build.env` is commented out in `quasar.config.js`, so
  the env var never reaches the bundle and `boot/axios.js` falls back to its hardcoded
  default. Setting it in `docker-compose.yml` alone has no effect.

## Dockerfile Gotcha

Must copy source BEFORE `npm install` -- Quasar's prepare script needs source files:
```dockerfile
COPY package*.json ./
COPY . .
RUN npm install
```

## Style

- 2 spaces indentation
- `camelCase` for variables/methods, `PascalCase` for components and for `.vue` filenames
- No emojis in code or comments
- ESLint + Prettier configured (see `eslint.config.js`, `.prettierrc.json`)
