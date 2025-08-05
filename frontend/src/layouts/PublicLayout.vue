<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
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
          <router-link to="/" class="text-white no-underline">
            Yoga Flashcards
          </router-link>
        </q-toolbar-title>

        <div class="q-gutter-sm row items-center no-wrap">
          <q-btn
            v-if="!authStore.isAuthenticated"
            flat
            label="Login"
            @click="$router.push('/login')"
          />
          <q-btn
            v-if="!authStore.isAuthenticated"
            flat
            label="Sign Up"
            @click="$router.push('/signup')"
          />
          
          <q-btn-dropdown
            v-if="authStore.isAuthenticated"
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
              <q-item clickable v-close-popup @click="$router.push('/favorites')">
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
                <q-item-section>
                  <q-item-label>Admin Panel</q-item-label>
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
    >
      <q-list>
        <q-item-label header>
          Navigation
        </q-item-label>

        <q-item clickable @click="$router.push('/')">
          <q-item-section avatar>
            <q-icon name="home" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Home</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable @click="$router.push('/daily')">
          <q-item-section avatar>
            <q-icon name="today" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Daily Card</q-item-label>
          </q-item-section>
        </q-item>

        <q-item 
          v-if="authStore.isAuthenticated"
          clickable 
          @click="$router.push('/cards')"
        >
          <q-item-section avatar>
            <q-icon name="view_cards" />
          </q-item-section>
          <q-item-section>
            <q-item-label>All Cards</q-item-label>
          </q-item-section>
        </q-item>

        <q-item 
          v-if="authStore.isAuthenticated"
          clickable 
          @click="$router.push('/favorites')"
        >
          <q-item-section avatar>
            <q-icon name="favorite" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Favorites</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator v-if="!authStore.isAuthenticated" />

        <q-item 
          v-if="!authStore.isAuthenticated"
          clickable 
          @click="$router.push('/login')"
        >
          <q-item-section avatar>
            <q-icon name="login" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Login</q-item-label>
          </q-item-section>
        </q-item>

        <q-item 
          v-if="!authStore.isAuthenticated"
          clickable 
          @click="$router.push('/signup')"
        >
          <q-item-section avatar>
            <q-icon name="person_add" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Sign Up</q-item-label>
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
import { ref, onMounted } from 'vue'
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

onMounted(() => {
  // Check auth status on app load
  authStore.checkAuthStatus()
})
</script>

<style scoped>
.no-underline {
  text-decoration: none;
}
</style>
