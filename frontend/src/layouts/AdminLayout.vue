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
            no-caps
            :label="authStore.user?.email || 'User'"
            icon="account_circle"
            content-class="user-dropdown-menu"
          >
            <q-list>
              <q-item clickable v-close-popup @click="$router.push('/profile')">
                <q-item-section avatar>
                  <q-icon name="person" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Profile</q-item-label>
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
          <q-icon name="self_improvement" size="xl" color="primary" />
          <div class="text-h5 q-mt-md drawer-title">
            Admin
          </div>
          <div class="text-subtitle2 drawer-subtitle">
            Content Management
          </div>
          <div class="yoga-divider q-my-md"></div>
        </div>

        <q-item clickable @click="$router.push('/admin')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="dashboard" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Dashboard</q-item-label>
            <q-item-label caption class="nav-caption">Overview</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/cards')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="auto_stories" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Cards</q-item-label>
            <q-item-label caption class="nav-caption">Manage content</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/tags')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="local_offer" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Tags</q-item-label>
            <q-item-label caption class="nav-caption">Organize cards</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isAdmin"
          clickable
          @click="$router.push('/admin/users')"
          class="nav-item"
        >
          <q-item-section avatar>
            <q-icon name="people" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Users</q-item-label>
            <q-item-label caption class="nav-caption">Manage access</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isAdmin"
          clickable
          @click="$router.push('/admin/appearance')"
          class="nav-item"
        >
          <q-item-section avatar>
            <q-icon name="palette" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Appearance</q-item-label>
            <q-item-label caption class="nav-caption">Site theme</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isCurator"
          clickable
          @click="$router.push('/admin/image-settings')"
          class="nav-item"
        >
          <q-item-section avatar>
            <q-icon name="auto_awesome" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Card Images</q-item-label>
            <q-item-label caption class="nav-caption">Look and feel</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/admin/cards/new')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="add_circle" size="md" color="positive" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">New Card</q-item-label>
            <q-item-label caption class="nav-caption">Create content</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="public" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="nav-label">Public Site</q-item-label>
            <q-item-label caption class="nav-caption">View frontend</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container class="q-pb-xl">
      <router-view />
    </q-page-container>

    <q-footer elevated class="admin-footer">
      <q-toolbar>
        <q-toolbar-title class="text-center">
          <div class="text-body2">
            © {{ new Date().getFullYear() }} Yoga Flashcards · Admin Panel
          </div>
        </q-toolbar-title>
      </q-toolbar>
    </q-footer>
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
// The theme tokens live on :root, so the admin area inherits whatever theme is
// active. This block used to hardcode #FFFFFF surfaces and #3D3D3D ink, with a
// further eight inline colours on the drawer labels - all of which rendered
// white-on-white under Dusk and Neon once theming went in.
.no-underline {
  text-decoration: none;
}

.admin-drawer {
  background: var(--surface);
  border-right: 1px solid var(--line);
  color: var(--ink);
}

.drawer-title {
  font-family: var(--font-head);
  font-weight: 700;
  letter-spacing: var(--head-spacing);
  text-transform: var(--head-transform);
  color: var(--ink);
}

.drawer-subtitle {
  color: var(--brand);
  letter-spacing: 1px;
  font-weight: 500;
}

.nav-item {
  border-radius: var(--radius-item);
  margin: 4px 8px;
  transition: background-color var(--motion) ease, transform var(--motion) ease;
  color: var(--ink);

  &:hover {
    background: var(--surface-2);
    transform: translateX(4px);
  }
}

.nav-label {
  font-weight: 500;
  letter-spacing: 0.3px;
  color: var(--ink);
}

.nav-caption {
  color: var(--ink-soft) !important;
}

// The user menu renders into a portal, so a scoped rule here could never reach
// it. It is themed globally in app.scss and selected with content-class.

.admin-footer {
  background: var(--surface);
  border-top: 1px solid var(--line);
  color: var(--ink-soft);
}
</style>
