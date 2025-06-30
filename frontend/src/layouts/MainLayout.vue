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
          Yoga Flashcards Admin
        </q-toolbar-title>

        <div>
          <q-btn-dropdown flat icon="account_circle" :label="user?.username">
            <q-list>
              <q-item clickable v-close-popup @click="logout">
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
        <q-item-label
          header
        >
          Navigation
        </q-item-label>

        <q-item
          clickable
          :active="$route.path === '/cards'"
          @click="$router.push('/cards')"
        >
          <q-item-section avatar>
            <q-icon name="style" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Flashcards</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          :active="$route.path === '/tags'"
          @click="$router.push('/tags')"
        >
          <q-item-section avatar>
            <q-icon name="local_offer" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Tags</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { useAuthStore } from 'src/stores/auth'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'MainLayout',

  setup() {
    const leftDrawerOpen = ref(false)
    const authStore = useAuthStore()
    const router = useRouter()
    const $q = useQuasar()

    const user = computed(() => authStore.user)

    const toggleLeftDrawer = () => {
      leftDrawerOpen.value = !leftDrawerOpen.value
    }

    const logout = async () => {
      const result = await authStore.logout()
      if (result.success) {
        $q.notify({
          color: 'positive',
          message: 'Logged out successfully'
        })
        router.push('/login')
      }
    }

    return {
      leftDrawerOpen,
      toggleLeftDrawer,
      user,
      logout
    }
  }
})
</script>
