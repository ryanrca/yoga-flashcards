# Claude Code Instructions - Frontend (Vue/Quasar)

## Quick Reference

```
Framework:  Vue 3 + Quasar 2.16
State:      Pinia 3.x
HTTP:       Axios
Port:       9000
Build:      npm run build
Dev:        npm run dev -- --host 0.0.0.0
```

## Project Structure

```
frontend/
├── src/
│   ├── boot/                     # App initialization
│   │   ├── axios.js             # HTTP client config
│   │   └── pinia.js             # State management setup
│   ├── stores/                   # Pinia stores
│   │   ├── auth.js              # Authentication state
│   │   ├── flashcards.js        # Flashcard state
│   │   └── index.js             # Store initialization
│   ├── router/                   # Vue Router
│   │   ├── index.js             # Router setup with guards
│   │   └── routes.js            # Route definitions
│   ├── layouts/                  # Layout components
│   │   ├── PublicLayout.vue     # Public pages layout
│   │   ├── AdminLayout.vue      # Admin pages layout
│   │   └── MainLayout.vue       # Base layout
│   ├── pages/                    # Page components
│   │   ├── public/              # Public-facing pages
│   │   │   ├── HomePage.vue
│   │   │   ├── DailyCardPage.vue
│   │   │   ├── LoginPage.vue
│   │   │   ├── SignupPage.vue
│   │   │   ├── CardsPage.vue
│   │   │   ├── ProfilePage.vue
│   │   │   └── FavoritesPage.vue
│   │   ├── admin/               # Admin panel pages
│   │   │   ├── DashboardPage.vue
│   │   │   ├── CardsPage.vue
│   │   │   ├── CardEditPage.vue
│   │   │   ├── CardDetailPage.vue
│   │   │   ├── TagsPage.vue
│   │   │   └── UsersPage.vue
│   │   ├── IndexPage.vue
│   │   └── ErrorNotFound.vue
│   ├── components/               # Reusable components
│   │   └── EssentialLink.vue
│   ├── css/                      # Global styles
│   │   └── app.scss
│   └── App.vue                   # Root component
├── public/                       # Static assets
├── quasar.config.js             # Quasar configuration
├── package.json                  # Dependencies
├── vite.config.js               # Vite configuration
├── .eslintrc.json               # ESLint config
├── .prettierrc.json             # Prettier config
└── Dockerfile                    # Container config
```

## Architecture Principles

1. **Composition API** with `<script setup>`
2. **Pinia** for global state management
3. **SFCs** (Single File Components)
4. **Quasar components** for UI
5. **Scoped SCSS** for component styles
6. **Session-based auth** with cookies

---

## State Management (Pinia)

### Auth Store (stores/auth.js)

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from 'boot/axios'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isCurator = computed(() =>
    ['curator', 'admin'].includes(user.value?.role)
  )
  const isUser = computed(() => !!user.value)

  // Actions
  async function login(credentials) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/users/login/', credentials)
      user.value = response.data
      isAuthenticated.value = true
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await api.post('/users/logout/')
    } finally {
      user.value = null
      isAuthenticated.value = false
    }
  }

  async function checkAuthStatus() {
    try {
      const response = await api.get('/users/auth-status/')
      if (response.data.is_authenticated) {
        user.value = response.data.user
        isAuthenticated.value = true
      }
    } catch {
      user.value = null
      isAuthenticated.value = false
    }
  }

  async function signup(userData) {
    loading.value = true
    error.value = null
    try {
      await api.post('/users/register/', userData)
      // Auto-login after signup
      await login({
        email: userData.email,
        password: userData.password
      })
    } catch (err) {
      error.value = err.response?.data?.error || 'Signup failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    user, isAuthenticated, loading, error,
    // Getters
    isAdmin, isCurator, isUser,
    // Actions
    login, logout, checkAuthStatus, signup
  }
})
```

### Flashcards Store (stores/flashcards.js)

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from 'boot/axios'

export const useFlashcardsStore = defineStore('flashcards', () => {
  // State
  const cards = ref([])
  const dailyCard = ref(null)
  const currentCard = ref(null)
  const tags = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    count: 0,
    page: 1,
    pageSize: 20,
    totalPages: 0
  })

  // Actions
  async function fetchCards(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/cards/', { params })
      cards.value = response.data.results
      pagination.value = {
        count: response.data.count,
        page: params.page || 1,
        pageSize: 20,
        totalPages: Math.ceil(response.data.count / 20)
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch cards'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchDailyCard() {
    loading.value = true
    try {
      const response = await api.get('/dailycard/')
      dailyCard.value = response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch daily card'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCard(id) {
    loading.value = true
    try {
      const response = await api.get(`/cards/${id}/`)
      currentCard.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch card'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createCard(formData) {
    loading.value = true
    try {
      const response = await api.post('/cards/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create card'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateCard(id, formData) {
    loading.value = true
    try {
      const response = await api.put(`/cards/${id}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data  // Returns NEW version with different ID
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update card'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteCard(id) {
    loading.value = true
    try {
      await api.delete(`/cards/${id}/`)
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete card'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTags() {
    try {
      const response = await api.get('/tags/')
      tags.value = response.data.results || response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch tags'
    }
  }

  async function fetchCardVersions(id) {
    try {
      const response = await api.get(`/cards/${id}/versions/`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch versions'
      throw err
    }
  }

  async function revertCardVersion(cardId, versionId) {
    loading.value = true
    try {
      const response = await api.post(`/cards/${cardId}/revert_version/`, {
        version_id: versionId
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to revert version'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    cards, dailyCard, currentCard, tags, loading, error, pagination,
    // Actions
    fetchCards, fetchDailyCard, fetchCard, createCard, updateCard,
    deleteCard, fetchTags, fetchCardVersions, revertCardVersion
  }
})
```

---

## Axios Configuration (boot/axios.js)

```javascript
import { boot } from 'quasar/wrappers'
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:8000/api',
  withCredentials: true,  // Send session cookies
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add CSRF token from cookie
api.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1]

  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/#/login'
    }
    return Promise.reject(error)
  }
)

export default boot(({ app }) => {
  app.config.globalProperties.$api = api
})

export { api }
```

---

## Router Configuration

### Route Definitions (router/routes.js)

```javascript
const routes = [
  // Public routes
  {
    path: '/',
    component: () => import('layouts/PublicLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('pages/public/HomePage.vue') },
      { path: 'daily', name: 'daily-card', component: () => import('pages/public/DailyCardPage.vue') },
      { path: 'login', name: 'login', component: () => import('pages/public/LoginPage.vue') },
      { path: 'signup', name: 'signup', component: () => import('pages/public/SignupPage.vue') },
      {
        path: 'cards',
        name: 'public-cards',
        component: () => import('pages/public/CardsPage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('pages/public/ProfilePage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'favorites',
        name: 'favorites',
        component: () => import('pages/public/FavoritesPage.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },

  // Admin routes
  {
    path: '/admin',
    component: () => import('layouts/AdminLayout.vue'),
    meta: { requiresCurator: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('pages/admin/DashboardPage.vue') },
      { path: 'cards', name: 'admin-cards', component: () => import('pages/admin/CardsPage.vue') },
      { path: 'cards/new', name: 'admin-card-new', component: () => import('pages/admin/CardEditPage.vue') },
      { path: 'cards/:id', name: 'admin-card-detail', component: () => import('pages/admin/CardDetailPage.vue') },
      { path: 'cards/:id/edit', name: 'admin-card-edit', component: () => import('pages/admin/CardEditPage.vue') },
      { path: 'tags', name: 'admin-tags', component: () => import('pages/admin/TagsPage.vue') },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('pages/admin/UsersPage.vue'),
        meta: { requiresAdmin: true }
      }
    ]
  },

  // 404
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
```

### Navigation Guards (router/index.js)

```javascript
import { route } from 'quasar/wrappers'
import { createRouter, createWebHashHistory } from 'vue-router'
import routes from './routes'
import { useAuthStore } from 'stores/auth'

export default route(function () {
  const Router = createRouter({
    history: createWebHashHistory(),
    routes
  })

  let authChecked = false

  Router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Check auth status on first navigation
    if (!authChecked) {
      await authStore.checkAuthStatus()
      authChecked = true
    }

    // Check route requirements
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      return next({ name: 'home' })
    }

    if (to.meta.requiresCurator && !authStore.isCurator) {
      return next({ name: 'home' })
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }

    next()
  })

  return Router
})
```

---

## Page Components

### DailyCardPage.vue Example

```vue
<template>
  <q-page class="daily-card-page">
    <div class="container">
      <q-card v-if="flashcardsStore.dailyCard" class="daily-card">
        <q-card-section>
          <div class="text-h4">{{ flashcardsStore.dailyCard.title }}</div>
          <div class="text-h6 text-grey">{{ flashcardsStore.dailyCard.phrase }}</div>
        </q-card-section>

        <q-card-section v-if="flashcardsStore.dailyCard.front_image">
          <q-img :src="flashcardsStore.dailyCard.front_image" />
        </q-card-section>

        <q-card-section>
          <div class="text-subtitle1">{{ flashcardsStore.dailyCard.short_answer }}</div>
          <div class="text-body1">{{ flashcardsStore.dailyCard.definition }}</div>
        </q-card-section>

        <q-card-section>
          <q-chip
            v-for="tag in flashcardsStore.dailyCard.tags"
            :key="tag.id"
            color="primary"
            text-color="white"
          >
            {{ tag.name }}
          </q-chip>
        </q-card-section>

        <q-card-actions>
          <q-btn flat icon="share" label="Share" @click="shareCard" />
        </q-card-actions>
      </q-card>

      <q-spinner v-else-if="flashcardsStore.loading" size="lg" />

      <q-banner v-else class="bg-negative text-white">
        Failed to load daily card
      </q-banner>
    </div>
  </q-page>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFlashcardsStore } from 'stores/flashcards'

const flashcardsStore = useFlashcardsStore()

onMounted(async () => {
  await flashcardsStore.fetchDailyCard()
})

async function shareCard() {
  const card = flashcardsStore.dailyCard
  const shareData = {
    title: card.title,
    text: `${card.phrase} - ${card.short_answer}`,
    url: window.location.href
  }

  if (navigator.share) {
    await navigator.share(shareData)
  } else {
    await navigator.clipboard.writeText(window.location.href)
    // Show notification
  }
}
</script>

<style lang="scss" scoped>
.daily-card-page {
  padding: 20px;

  .container {
    max-width: 800px;
    margin: 0 auto;
  }

  .daily-card {
    margin-bottom: 20px;
  }
}
</style>
```

### CardEditPage.vue Structure

```vue
<template>
  <q-page class="card-edit-page">
    <q-form @submit="onSubmit">
      <!-- Title -->
      <q-input
        v-model="form.title"
        label="Title"
        :rules="[val => !!val || 'Title is required']"
      />

      <!-- Phrase (Sanskrit) -->
      <q-input
        v-model="form.phrase"
        label="Phrase (Sanskrit)"
        :rules="[val => !!val || 'Phrase is required']"
      />

      <!-- Definition -->
      <q-input
        v-model="form.definition"
        label="Definition"
        type="textarea"
        :rules="[val => !!val || 'Definition is required']"
      />

      <!-- Short Answer -->
      <q-input
        v-model="form.short_answer"
        label="Short Answer"
        type="textarea"
      />

      <!-- Tags -->
      <q-select
        v-model="form.tags"
        :options="tagOptions"
        label="Tags"
        multiple
        use-chips
        use-input
        @new-value="createTag"
      />

      <!-- Front Image -->
      <q-file
        v-model="form.front_image"
        label="Front Image"
        accept="image/*"
      >
        <template v-slot:prepend>
          <q-icon name="attach_file" />
        </template>
      </q-file>

      <!-- Back Image -->
      <q-file
        v-model="form.back_image"
        label="Back Image"
        accept="image/*"
      >
        <template v-slot:prepend>
          <q-icon name="attach_file" />
        </template>
      </q-file>

      <!-- Version History (if editing) -->
      <div v-if="isEditing && versions.length > 0">
        <h6>Version History</h6>
        <q-table
          :rows="versions"
          :columns="versionColumns"
          row-key="id"
        >
          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                v-if="!props.row.is_live"
                flat
                label="Revert"
                @click="revertToVersion(props.row.id)"
              />
              <q-badge v-else color="green">Current</q-badge>
            </q-td>
          </template>
        </q-table>
      </div>

      <q-btn type="submit" color="primary" :label="isEditing ? 'Update' : 'Create'" />
      <q-btn flat label="Cancel" @click="$router.back()" />
    </q-form>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFlashcardsStore } from 'stores/flashcards'

const route = useRoute()
const router = useRouter()
const flashcardsStore = useFlashcardsStore()

const isEditing = computed(() => !!route.params.id)
const versions = ref([])

const form = ref({
  title: '',
  phrase: '',
  definition: '',
  short_answer: '',
  tags: [],
  front_image: null,
  back_image: null
})

const tagOptions = computed(() =>
  flashcardsStore.tags.map(t => ({ label: t.name, value: t.id }))
)

onMounted(async () => {
  await flashcardsStore.fetchTags()

  if (isEditing.value) {
    const card = await flashcardsStore.fetchCard(route.params.id)
    form.value = {
      title: card.title,
      phrase: card.phrase,
      definition: card.definition,
      short_answer: card.short_answer || '',
      tags: card.tags.map(t => ({ label: t.name, value: t.id })),
      front_image: null,
      back_image: null
    }
    versions.value = await flashcardsStore.fetchCardVersions(route.params.id)
  }
})

async function onSubmit() {
  const formData = new FormData()
  formData.append('title', form.value.title)
  formData.append('phrase', form.value.phrase)
  formData.append('definition', form.value.definition)
  formData.append('short_answer', form.value.short_answer)

  // Tags
  form.value.tags.forEach(tag => {
    formData.append('tags', tag.value || tag.label)
  })

  // Images
  if (form.value.front_image) {
    formData.append('front_image', form.value.front_image)
  }
  if (form.value.back_image) {
    formData.append('back_image', form.value.back_image)
  }

  if (isEditing.value) {
    const newVersion = await flashcardsStore.updateCard(route.params.id, formData)
    // Redirect to new version (ID changes!)
    router.push({ name: 'admin-card-edit', params: { id: newVersion.id } })
  } else {
    await flashcardsStore.createCard(formData)
    router.push({ name: 'admin-cards' })
  }
}

async function revertToVersion(versionId) {
  const newVersion = await flashcardsStore.revertCardVersion(route.params.id, versionId)
  router.push({ name: 'admin-card-edit', params: { id: newVersion.id } })
}
</script>
```

---

## Quasar Components Reference

Common components used in this app:

| Component | Purpose |
|-----------|---------|
| `q-page` | Page container |
| `q-card` | Card container |
| `q-btn` | Buttons |
| `q-input` | Text inputs |
| `q-select` | Dropdowns |
| `q-file` | File upload |
| `q-img` | Images |
| `q-table` | Data tables |
| `q-chip` | Tags/badges |
| `q-spinner` | Loading indicator |
| `q-banner` | Alerts |
| `q-dialog` | Modals |
| `q-form` | Form wrapper |
| `q-notify` | Toast notifications |
| `q-layout` | App layout |
| `q-header` | Header section |
| `q-drawer` | Sidebar |
| `q-toolbar` | Toolbar |

---

## Common Patterns

### Loading State

```vue
<template>
  <q-spinner v-if="store.loading" size="lg" />
  <div v-else-if="store.error">{{ store.error }}</div>
  <div v-else>Content here</div>
</template>
```

### Form Validation

```vue
<q-input
  v-model="email"
  label="Email"
  type="email"
  :rules="[
    val => !!val || 'Email is required',
    val => /.+@.+\..+/.test(val) || 'Invalid email'
  ]"
/>
```

### Confirmation Dialog

```javascript
import { useQuasar } from 'quasar'

const $q = useQuasar()

function confirmDelete() {
  $q.dialog({
    title: 'Confirm',
    message: 'Are you sure you want to delete this?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    // Delete action
  })
}
```

### Toast Notification

```javascript
import { useQuasar } from 'quasar'

const $q = useQuasar()

$q.notify({
  type: 'positive',
  message: 'Card created successfully'
})
```

---

## Style Guide

- 2 spaces indentation
- `camelCase` for variables, methods
- `PascalCase` for component names
- `kebab-case` for filenames
- Scoped SCSS in SFCs
- No emojis in code or comments

### SCSS Variables

Define global variables in `src/css/quasar.variables.scss`:

```scss
$primary   : #1976D2;
$secondary : #26A69A;
$accent    : #9C27B0;
$dark      : #1D1D1D;
$positive  : #21BA45;
$negative  : #C10015;
$info      : #31CCEC;
$warning   : #F2C037;
```

---

## Dockerfile

```dockerfile
FROM node:24-alpine

WORKDIR /app

# Copy package files AND source code first
COPY package*.json ./
COPY . .

# Install dependencies (quasar prepare needs source code)
RUN npm install

EXPOSE 9000

CMD ["npm", "run", "dev"]
```

**Critical**: Copy source before `npm install` - Quasar's prepare script needs the source files.

---

## Environment Variables

Set in docker-compose.yml or .env:

```
API_BASE_URL=http://localhost:8000
```

Access in code:

```javascript
const baseUrl = process.env.API_BASE_URL || 'http://localhost:8000'
```

---

## Troubleshooting

### "package.json not found"
Always use explicit paths:
```bash
cd ~/repos/yoga-flashcards/frontend && npm run dev
```

### Webpack errors with Quasar
Use Node.js 24 and recreate with official CLI:
```bash
rm -rf frontend
npm create quasar
```

### CORS errors
Ensure backend has:
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:9000"]
CORS_ALLOW_CREDENTIALS = True
```

### Session not persisting
Ensure axios has:
```javascript
withCredentials: true
```
