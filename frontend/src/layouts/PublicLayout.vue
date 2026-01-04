<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="natural-header">
      <q-toolbar>
        <q-toolbar-title class="natural-title">
          <router-link to="/" class="no-underline">
            <div class="row items-center no-wrap">
              <q-icon name="self_improvement" size="md" class="q-mr-sm" color="primary" />
              <div class="text-h5" style="font-family: 'Playfair Display', serif; font-weight: 600; color: #3D3D3D;">
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
          style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;"
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
            <q-separator style="background: rgba(139, 115, 85, 0.2);" />
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
  background: #FFFFFF;
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(139, 115, 85, 0.15);
  box-shadow: 0 2px 8px rgba(61, 61, 61, 0.06);
}

.natural-title {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.auth-btn {
  border-radius: 6px;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

.natural-user-menu {
  min-width: 200px;
  background: #FFFFFF;
  color: #3D3D3D;
  border: 1px solid rgba(139, 115, 85, 0.15);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(61, 61, 61, 0.12);

  .q-item {
    color: #3D3D3D;
    transition: all 0.2s ease;

    &:hover {
      background: rgba(139, 115, 85, 0.08);
    }
  }
}

.natural-footer {
  background: #FFFFFF;
  border-top: 1px solid rgba(139, 115, 85, 0.15);
  color: #3D3D3D;
}
</style>
