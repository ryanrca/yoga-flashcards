<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="natural-header">
      <q-toolbar>
        <q-toolbar-title class="natural-title">
          <router-link to="/" class="no-underline">
            <div class="row items-center no-wrap">
              <q-icon name="self_improvement" size="md" class="q-mr-sm" color="primary" />
              <div class="text-h5">
                Yoga Flashcards
              </div>
            </div>
          </router-link>
        </q-toolbar-title>

        <q-space />

        <!-- Auth buttons when not logged in -->
        <div v-if="!authStore.isAuthenticated" class="row q-gutter-md items-center">
          <q-btn
            flat
            label="Sign Up"
            @click="$router.push('/signup')"
            class="yoga-btn-secondary auth-btn"
            style="font-weight: 500; letter-spacing: 0.3px; padding: 8px 24px;"
          />
          <q-btn
            unelevated
            label="Login"
            @click="$router.push('/login')"
            class="yoga-btn-primary auth-btn"
            style="font-weight: 500; letter-spacing: 0.3px; padding: 8px 24px;"
          />
        </div>

        <!-- User menu when logged in -->
        <q-btn-dropdown
          v-if="authStore.isAuthenticated"
          flat
          :label="authStore.user?.email || 'User'"
          icon="account_circle"
          size="lg"
          style="font-weight: 500; letter-spacing: 0.3px;"
        >
          <q-list class="natural-user-menu">
            <q-item clickable v-close-popup @click="$router.push('/profile')">
              <q-item-section avatar>
                <q-icon name="person" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 500;">Profile</q-item-label>
              </q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="$router.push('/favorites')">
              <q-item-section avatar>
                <q-icon name="favorite" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 500;">Favorites</q-item-label>
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
                <q-item-label style="font-weight: 500;">Admin</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator class="menu-separator" />
            <q-item clickable v-close-popup @click="handleLogout">
              <q-item-section avatar>
                <q-icon name="logout" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 500;">Logout</q-item-label>
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
.no-underline {
  text-decoration: none;
  color: inherit;
}

.natural-header {
  background: rgba(20, 22, 28, 0.88);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
  box-shadow: none;
}

.natural-title {
  font-family: 'Cinzel Decorative', Georgia, serif;
  font-weight: 700;
  letter-spacing: 0.02em;
  font-size: 1.3rem;
  color: #F2F0EC;
}

.auth-btn {
  border-radius: 6px;
  transition: background-color 180ms ease, border-color 180ms ease;
}

.natural-user-menu {
  min-width: 210px;
  background: #1E222C;
  color: #F2F0EC;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 8px;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.5);

  .q-item {
    color: #F2F0EC;
    &:hover { background: rgba(255, 255, 255, 0.07); }
  }
}

.menu-separator { background: rgba(255, 255, 255, 0.10); }

.natural-footer {
  background: rgba(20, 22, 28, 0.9);
  border-top: 1px solid rgba(255, 255, 255, 0.10);
  color: rgba(242, 240, 236, 0.66);
}
</style>
