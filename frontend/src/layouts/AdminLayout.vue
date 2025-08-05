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
          >
            <q-list>
              <q-item clickable v-close-popup @click="$router.push('/profile')">
                <q-item-section>
                  <q-item-label>Profile</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item clickable v-close-popup @click="handleLogout">
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
      class="bg-grey-1"
    >
      <q-list>
        <q-item-label header class="text-primary">
          Admin Navigation
        </q-item-label>

        <q-item clickable @click="$router.push('/admin')">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Dashboard</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/cards')">
          <q-item-section avatar>
            <q-icon name="view_cards" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Manage Cards</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/admin/tags')">
          <q-item-section avatar>
            <q-icon name="local_offer" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Manage Tags</q-item-label>
          </q-item-section>
        </q-item>

        <q-item 
          v-if="authStore.isAdmin"
          clickable 
          @click="$router.push('/admin/users')"
        >
          <q-item-section avatar>
            <q-icon name="people" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Manage Users</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator />

        <q-item-label header class="text-grey-7">
          Quick Actions
        </q-item-label>

        <q-item clickable @click="$router.push('/admin/cards/new')">
          <q-item-section avatar>
            <q-icon name="add_circle" color="positive" />
          </q-item-section>
          <q-item-section>
            <q-item-label>New Card</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator />

        <q-item clickable @click="$router.push('/')">
          <q-item-section avatar>
            <q-icon name="public" />
          </q-item-section>
          <q-item-section>
            <q-item-label>View Public Site</q-item-label>
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

<style scoped>
.no-underline {
  text-decoration: none;
}
</style>
