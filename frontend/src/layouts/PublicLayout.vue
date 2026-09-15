<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="natural-header">
      <q-toolbar>
        <q-toolbar-title class="natural-title">
          <router-link to="/" class="no-underline">
            <div class="row items-center no-wrap">
              <q-icon name="self_improvement" size="md" class="q-mr-sm" color="primary" />
              <div class="text-h5 site-title">
                Yoga Flashcards
              </div>
            </div>
          </router-link>
        </q-toolbar-title>

        <q-space />

        <theme-switcher class="q-mr-sm" />

        <!-- Auth buttons when not logged in -->
        <div v-if="!authStore.isAuthenticated" class="row q-gutter-md items-center">
          <q-btn
            flat
            label="Sign Up"
            class="yoga-btn-secondary auth-btn"
            @click="$router.push('/signup')"
          />
          <q-btn
            unelevated
            label="Login"
            class="yoga-btn-primary auth-btn"
            @click="$router.push('/login')"
          />
        </div>

        <!-- User menu when logged in -->
        <q-btn-dropdown
          v-if="authStore.isAuthenticated"
          flat
          no-caps
          :label="authStore.user?.email || 'User'"
          icon="account_circle"
          content-class="user-dropdown-menu"
        >
          <q-list class="natural-user-menu">
            <q-item clickable v-close-popup @click="$router.push('/profile')">
              <q-item-section avatar>
                <q-icon name="person" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Profile</q-item-label>
              </q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="$router.push('/favorites')">
              <q-item-section avatar>
                <q-icon name="favorite" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Favorites</q-item-label>
              </q-item-section>
            </q-item>
            <q-item
              v-if="authStore.isCurator"
              clickable
              v-close-popup
              @click="$router.push('/admin')"
            >
              <q-item-section avatar>
                <q-icon name="dashboard" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Admin</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator class="menu-separator" />
            <q-item clickable v-close-popup @click="handleLogout">
              <q-item-section avatar>
                <q-icon name="logout" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Logout</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <q-page-container class="q-pb-xl">
      <router-view />
    </q-page-container>

    <q-footer elevated class="natural-footer">
      <q-toolbar>
        <q-toolbar-title class="text-center">
          <div class="text-body2">
            © {{ new Date().getFullYear() }} Yoga Flashcards · Made with ❤️ for the yoga community
          </div>
        </q-toolbar-title>
      </q-toolbar>
    </q-footer>
  </q-layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'
import ThemeSwitcher from 'components/ThemeSwitcher.vue'

const $q = useQuasar()
const authStore = useAuthStore()

const handleLogout = async () => {
  const result = await authStore.logout()
  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Logged out successfully'
    })
    window.location.href = '/'
  }
}

onMounted(() => {
  authStore.checkAuthStatus()
})
</script>

<style scoped lang="scss">
// Everything here reads the theme vocabulary from app.scss. This block used to
// hardcode #3D3D3D (light-theme ink) in five places and set Playfair Display
// inline on the title, a font the stylesheet never actually loaded - the
// leftovers of a half-finished retheme.
.no-underline {
  text-decoration: none;
  color: inherit;
}

.natural-header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  box-shadow: none;
}

.natural-title {
  font-weight: 600;
}

.site-title {
  font-family: var(--font-head);
  font-weight: 700;
  letter-spacing: var(--head-spacing);
  text-transform: var(--head-transform);
  font-size: 1.35rem;
  color: var(--ink);
}

.auth-btn {
  border-radius: var(--radius-btn);
  padding: 8px 24px;
  transition: background-color var(--motion) ease, border-color var(--motion) ease;
}

.natural-user-menu {
  min-width: 210px;
  background: var(--surface);
  color: var(--ink);

  .q-item { color: var(--ink); }
}

.menu-separator { background: var(--line); }

.natural-footer {
  background: var(--surface);
  border-top: 1px solid var(--line);
  color: var(--ink-soft);
}
</style>
