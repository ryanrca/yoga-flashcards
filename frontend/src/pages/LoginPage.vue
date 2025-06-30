<template>
  <div class="fullscreen bg-blue flex flex-center">
    <q-card style="width: 400px">
      <q-card-section>
        <div class="text-h6 text-center">Yoga Flashcards Admin</div>
        <div class="text-subtitle2 text-center">Please sign in to continue</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="username"
            label="Username"
            outlined
            :rules="[val => !!val || 'Username is required']"
            autofocus
          />

          <q-input
            v-model="password"
            label="Password"
            type="password"
            outlined
            :rules="[val => !!val || 'Password is required']"
          />

          <div>
            <q-btn
              label="Sign In"
              type="submit"
              color="primary"
              class="full-width"
              :loading="authStore.loading"
              :disable="authStore.loading"
            />
          </div>
        </q-form>
      </q-card-section>

      <q-card-section v-if="errorMessage" class="text-center">
        <div class="text-negative">{{ errorMessage }}</div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { defineComponent, ref } from 'vue'
import { useAuthStore } from 'src/stores/auth'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'LoginPage',

  setup() {
    const username = ref('')
    const password = ref('')
    const errorMessage = ref('')
    const authStore = useAuthStore()
    const router = useRouter()
    const $q = useQuasar()

    const onSubmit = async () => {
      errorMessage.value = ''
      
      const result = await authStore.login({
        username: username.value,
        password: password.value
      })

      if (result.success) {
        $q.notify({
          color: 'positive',
          message: 'Login successful'
        })
        router.push('/')
      } else {
        errorMessage.value = result.error
      }
    }

    return {
      username,
      password,
      errorMessage,
      authStore,
      onSubmit
    }
  }
})
</script>

<style lang="sass" scoped>
.bg-blue
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
</style>
