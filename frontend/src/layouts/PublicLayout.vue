<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="psychedelic-header">
      <q-toolbar>
        <q-toolbar-title class="psychedelic-title">
          <router-link to="/" class="no-underline">
            <div class="row items-center no-wrap">
              <q-icon name="self_improvement" size="md" class="q-mr-sm glow-icon" />
              <div class="text-h4 neon-glow" style="font-family: 'Cinzel Decorative', serif; font-weight: 900;">
                YOGA FLASHCARDS
              </div>
            </div>
          </router-link>
        </q-toolbar-title>

        <q-space />

        <!-- Auth buttons when not logged in -->
        <div v-if="!authStore.isAuthenticated" class="row q-gutter-md items-center">
          <q-btn
            flat
            label="SIGN UP"
            @click="$router.push('/signup')"
            class="yoga-btn-secondary auth-btn"
            style="font-weight: 700; letter-spacing: 1.5px; padding: 8px 24px;"
          />
          <q-btn
            unelevated
            label="LOGIN"
            @click="$router.push('/login')"
            class="yoga-btn-primary auth-btn"
            style="font-weight: 700; letter-spacing: 1.5px; padding: 8px 24px;"
          />
        </div>

        <!-- User menu when logged in -->
        <q-btn-dropdown
          v-if="authStore.isAuthenticated"
          flat
          :label="authStore.user?.email || 'User'"
          icon="account_circle"
          class="glow-icon"
          size="lg"
          style="font-weight: 700; letter-spacing: 1px;"
        >
          <q-list style="min-width: 200px; background: linear-gradient(135deg, rgba(26, 11, 46, 0.98) 0%, rgba(74, 20, 140, 0.95) 100%); color: white;">
            <q-item clickable v-close-popup @click="$router.push('/profile')">
              <q-item-section avatar>
                <q-icon name="person" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 600;">PROFILE</q-item-label>
              </q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="$router.push('/favorites')">
              <q-item-section avatar>
                <q-icon name="favorite" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 600;">FAVORITES</q-item-label>
              </q-item-section>
            </q-item>
            <q-item
              v-if="authStore.isCurator"
              clickable
              v-close-popup
              @click="$router.push('/admin')"
            >
              <q-item-section avatar>
                <q-icon name="flare" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 600;">ADMIN</q-item-label>
              </q-item-section>
            </q-item>
            <q-separator style="background: rgba(255, 107, 53, 0.3);" />
            <q-item clickable v-close-popup @click="handleLogout">
              <q-item-section avatar>
                <q-icon name="logout" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="font-weight: 600;">LOGOUT</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
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

.psychedelic-header {
  background: linear-gradient(135deg,
    rgba(26, 11, 46, 0.98) 0%,
    rgba(74, 20, 140, 0.95) 100%
  );
  backdrop-filter: blur(20px);
  border-bottom: 2px solid rgba(255, 107, 53, 0.5);
  box-shadow:
    0 4px 30px rgba(255, 107, 53, 0.4),
    0 0 60px rgba(155, 77, 202, 0.3);
}

.psychedelic-title {
  font-weight: 900;
  letter-spacing: 3px;
}

.glow-icon {
  filter: drop-shadow(0 0 8px currentColor);
  transition: all 0.3s ease;

  &:hover {
    filter: drop-shadow(0 0 15px currentColor) drop-shadow(0 0 25px currentColor);
    transform: scale(1.2);
  }
}

.auth-btn {
  border-radius: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
  }
}
</style>
