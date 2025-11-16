<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          <router-link to="/admin" class="text-white no-underline">
            Admin Panel - Yoga Flashcards
          </router-link>
        </q-toolbar-title>

        <div class="q-gutter-sm row items-center no-wrap">
          <q-btn
            flat
            label="Public Site"
            icon="public"
            @click="$router.push('/')"
          />

          <q-btn-dropdown
            flat
            :label="authStore.user?.email || 'User'"
            icon="account_circle"
            class="glow-icon"
            size="lg"
            style="font-weight: 700; letter-spacing: 1px;"
          >
            <q-list class="user-dropdown-menu">
              <q-item clickable v-close-popup @click="$router.push('/profile')">
                <q-item-section avatar>
                  <q-icon name="person" />
                </q-item-section>
                <q-item-section>
                  <q-item-label style="font-weight: 600;">PROFILE</q-item-label>
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
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      class="admin-drawer"
    >
      <q-list padding>
        <div class="q-pa-md text-center">
          <q-icon name="flare" size="xl" class="glow-icon" color="primary" />
          <div class="text-h5 q-mt-md neon-glow" style="font-family: 'Cinzel Decorative', serif; font-weight: 900;">
            ADMIN
          </div>
          <div class="text-subtitle2" style="color: rgba(255,255,255,0.8); letter-spacing: 2px;">
            COSMIC CONTROL
          </div>
          <div class="yoga-divider q-my-md"></div>
        </div>

        <q-item clickable @click="$router.push('/admin')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="dashboard" size="md" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">DASHBOARD</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">Overview</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/cards')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="auto_stories" size="md" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">CARDS</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">Manage content</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/tags')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="local_offer" size="md" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">TAGS</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">Organize cards</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isAdmin"
          clickable
          @click="$router.push('/admin/users')"
          class="nav-item"
        >
          <q-item-section avatar>
            <q-icon name="people" size="md" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">USERS</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">Manage access</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/admin/cards/new')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="add_circle" size="md" color="positive" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">NEW CARD</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">Create content</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="public" size="md" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 700; letter-spacing: 1px;">PUBLIC SITE</q-item-label>
            <q-item-label caption style="color: rgba(255,255,255,0.7);">View frontend</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()

const leftDrawerOpen = ref(false)

const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value
}

const handleLogout = async () => {
  const result = await authStore.logout()
  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Logged out successfully'
    })
    // Redirect to home
    window.location.href = '/'
  }
}
</script>

<style scoped lang="scss">
.no-underline {
  text-decoration: none;
}

.admin-drawer {
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 107, 53, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 70% 70%, rgba(155, 77, 202, 0.15) 0%, transparent 50%),
    linear-gradient(180deg, rgba(26, 11, 46, 0.98) 0%, rgba(74, 20, 140, 0.95) 100%);
  border-right: 2px solid rgba(255, 107, 53, 0.4);
  color: white;
}

.glow-icon {
  filter: drop-shadow(0 0 8px currentColor);
  transition: all 0.3s ease;

  &:hover {
    filter: drop-shadow(0 0 15px currentColor) drop-shadow(0 0 25px currentColor);
    transform: scale(1.2);
  }
}

.nav-item {
  border-radius: 16px;
  margin: 6px 12px;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.9);

  &:hover {
    background: linear-gradient(90deg,
      rgba(255, 107, 53, 0.2) 0%,
      rgba(155, 77, 202, 0.2) 100%
    );
    transform: translateX(8px);
    box-shadow:
      0 0 20px rgba(255, 107, 53, 0.3),
      inset 0 0 20px rgba(255, 107, 53, 0.1);
  }

  .q-icon {
    filter: drop-shadow(0 0 5px currentColor);
  }
}

.user-dropdown-menu {
  min-width: 200px;
  background: linear-gradient(135deg,
    rgba(26, 11, 46, 0.98) 0%,
    rgba(74, 20, 140, 0.95) 100%
  );
  color: white;
  border: 1px solid rgba(255, 107, 53, 0.3);
  border-radius: 8px;

  .q-item {
    color: rgba(255, 255, 255, 0.9);
    transition: all 0.3s ease;

    &:hover {
      background: linear-gradient(90deg,
        rgba(255, 107, 53, 0.2) 0%,
        rgba(155, 77, 202, 0.2) 100%
      );
    }
  }
}
</style>
