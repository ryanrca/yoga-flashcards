<template>
  <q-page class="flex flex-center">
    <q-card class="q-pa-lg" style="min-width: 400px; max-width: 500px;">
      <q-card-section class="text-center">
        <div class="text-h4 text-primary q-mb-md">Login</div>
        <p class="text-grey-7">Sign in to access all flashcards and features</p>
      </q-card-section>

      <q-card-section>
        <q-form @submit="handleLogin" class="q-gutter-md">
          <q-input
            v-model="credentials.email"
            label="Email"
            type="email"
            outlined
            :rules="[
              val => !!val || 'Email is required',
              val => /.+@.+\..+/.test(val) || 'Please enter a valid email'
            ]"
            autocomplete="email"
          />

          <q-input
            v-model="credentials.password"
            label="Password"
            type="password"
            outlined
            :rules="[val => !!val || 'Password is required']"
            autocomplete="current-password"
          />

          <div v-if="error" class="text-negative q-mb-md">
            {{ error }}
          </div>

          <div class="text-center q-gutter-sm">
            <q-btn
              type="submit"
              color="primary"
              label="Login"
              :loading="loading"
              class="full-width"
            />
            
            <div class="q-mt-md">
              <q-btn
                flat
                color="primary"
                label="Don't have an account? Sign up"
                @click="$router.push('/signup')"
                class="full-width"
              />
            </div>
          </div>
        </q-form>
      </q-card-section>

      <!-- Social Login Section (Future Enhancement) -->
      <q-card-section class="text-center">
        <q-separator class="q-mb-md" />
        <div class="text-grey-7 q-mb-md">Or sign in with</div>
        <div class="q-gutter-sm">
          <q-btn
            outline
            color="red"
            icon="fab fa-google"
            label="Google"
            @click="handleGoogleLogin"
            disabled
          />
          <q-btn
            outline
            color="blue"
            icon="fab fa-facebook"
            label="Facebook"
            @click="handleFacebookLogin"
            disabled
          />
        </div>
        <div class="text-caption text-grey-6 q-mt-sm">
          Social login coming soon
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'

const router = useRouter()
const route = useRoute()
const $q = useQuasar()
const authStore = useAuthStore()

const credentials = ref({
  email: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!credentials.value.email || !credentials.value.password) {
    error.value = 'Please fill in all fields'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.login(credentials.value)

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Login successful!'
    })

    // Redirect to the intended page or home
    const redirectTo = route.query.redirect || '/'
    router.push(redirectTo)
  } else {
    error.value = result.error || 'Login failed'
  }

  loading.value = false
}

const handleGoogleLogin = () => {
  $q.notify({
    type: 'info',
    message: 'Google login will be available soon'
  })
}

const handleFacebookLogin = () => {
  $q.notify({
    type: 'info',
    message: 'Facebook login will be available soon'
  })
}
</script>
