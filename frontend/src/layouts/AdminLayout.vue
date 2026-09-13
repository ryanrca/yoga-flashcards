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
            size="lg"
            style="font-weight: 500; letter-spacing: 0.3px;"
          >
            <q-list class="user-dropdown-menu">
              <q-item clickable v-close-popup @click="$router.push('/profile')">
                <q-item-section avatar>
                  <q-icon name="person" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label style="font-weight: 500;">Profile</q-item-label>
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
          <div class="text-h5 q-mt-md" style="font-family: 'Playfair Display', serif; font-weight: 600; color: #3D3D3D;">
            Admin
          </div>
          <div class="text-subtitle2" style="color: #8B7355; letter-spacing: 1px; font-weight: 500;">
            Content Management
          </div>
          <div class="yoga-divider q-my-md"></div>
        </div>

        <q-item clickable @click="$router.push('/admin')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="dashboard" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Dashboard</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Overview</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/cards')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="auto_stories" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Cards</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Manage content</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/tags')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="local_offer" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Tags</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Organize cards</q-item-label>
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
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Users</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Manage access</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isAdmin"
          clickable
          @click="$router.push('/admin/image-settings')"
          class="nav-item"
        >
          <q-item-section avatar>
            <q-icon name="auto_awesome" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Card Images</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Look and feel</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/admin/cards/new')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="add_circle" size="md" color="positive" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">New Card</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">Create content</q-item-label>
          </q-item-section>
        </q-item>

        <div class="yoga-divider q-my-md"></div>

        <q-item clickable @click="$router.push('/')" class="nav-item">
          <q-item-section avatar>
            <q-icon name="public" size="md" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label style="font-weight: 500; letter-spacing: 0.3px; color: #3D3D3D;">Public Site</q-item-label>
            <q-item-label caption style="color: #6B6B6B;">View frontend</q-item-label>
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
.no-underline {
  text-decoration: none;
}

.admin-drawer {
  background: #FFFFFF;
  border-right: 1px solid rgba(139, 115, 85, 0.12);
  color: #3D3D3D;
}

.nav-item {
  border-radius: 6px;
  margin: 4px 8px;
  transition: all 0.2s ease;
  color: #3D3D3D;

  &:hover {
    background: rgba(139, 115, 85, 0.08);
    transform: translateX(4px);
  }
}

.user-dropdown-menu {
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

.admin-footer {
  background: #FFFFFF;
  border-top: 1px solid rgba(139, 115, 85, 0.15);
  color: #3D3D3D;
}
</style>
