<template>
  <q-page class="flex flex-center">
    <q-card class="q-pa-lg" style="min-width: 400px; max-width: 500px;">
      <q-card-section class="text-center">
        <div class="text-h4 text-primary q-mb-md">Sign Up</div>
        <p class="text-grey-7">Create your account to access all yoga flashcards</p>
      </q-card-section>

      <q-card-section>
        <q-form @submit="handleSignup" class="q-gutter-md">
          <q-input
            v-model="userData.email"
            label="Email"
            type="email"
            outlined
            :rules="[
              val => !!val || 'Email is required',
              val => isValidEmail(val) || 'Please enter a valid email'
            ]"
            autocomplete="email"
          />

          <q-input
            v-model="userData.password"
            label="Password"
            type="password"
            outlined
            :rules="[
              val => !!val || 'Password is required',
              val => val.length >= 8 || 'Password must be at least 8 characters'
            ]"
            autocomplete="new-password"
          />

          <q-input
            v-model="userData.password2"
            label="Confirm Password"
            type="password"
            outlined
            :rules="[
              val => !!val || 'Please confirm your password',
              val => val === userData.password || 'Passwords do not match'
            ]"
            autocomplete="new-password"
          />

          <q-checkbox
            v-model="acceptTerms"
            label="I agree to the terms and conditions"
            color="primary"
          />

          <div v-if="error" class="text-negative q-mb-md">
            {{ error }}
          </div>

          <div class="text-center q-gutter-sm">
            <q-btn
              type="submit"
              color="primary"
              label="Sign Up"
              :loading="loading"
              :disable="!acceptTerms"
              class="full-width"
            />
            
            <div class="q-mt-md">
              <q-btn
                flat
                color="primary"
                label="Already have an account? Login"
                @click="$router.push('/login')"
                class="full-width"
              />
            </div>
          </div>
        </q-form>
      </q-card-section>

      <!-- Social Signup Section (Future Enhancement) -->
      <q-card-section class="text-center">
        <q-separator class="q-mb-md" />
        <div class="text-grey-7 q-mb-md">Or sign up with</div>
        <div class="q-gutter-sm">
          <q-btn
            outline
            color="red"
            icon="fab fa-google"
            label="Google"
            @click="handleGoogleSignup"
            disabled
          />
          <q-btn
            outline
            color="blue"
            icon="fab fa-facebook"
            label="Facebook"
            @click="handleFacebookSignup"
            disabled
          />
        </div>
        <div class="text-caption text-grey-6 q-mt-sm">
          Social signup coming soon
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'

const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()

const userData = ref({
  email: '',
  password: '',
  password2: ''
})

const acceptTerms = ref(false)
const loading = ref(false)
const error = ref('')

const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleSignup = async () => {
  if (!userData.value.email || 
      !userData.value.password || !userData.value.password2) {
    error.value = 'Please fill in all fields'
    return
  }

  if (userData.value.password !== userData.value.password2) {
    error.value = 'Passwords do not match'
    return
  }

  if (!acceptTerms.value) {
    error.value = 'Please accept the terms and conditions'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.signup(userData.value)

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Account created successfully! Please check your email to verify your account.',
      timeout: 5000
    })

    // Redirect to login page
    router.push('/login')
  } else {
    error.value = result.error || 'Signup failed'
  }

  loading.value = false
}

const handleGoogleSignup = () => {
  $q.notify({
    type: 'info',
    message: 'Google signup will be available soon'
  })
}

const handleFacebookSignup = () => {
  $q.notify({
    type: 'info',
    message: 'Facebook signup will be available soon'
  })
}
</script>
