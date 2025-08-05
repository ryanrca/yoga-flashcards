<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8 col-lg-6">
        <q-card class="q-pa-lg">
          <q-card-section class="text-center">
            <q-avatar size="80px" color="primary" text-color="white" class="q-mb-md">
              <q-icon name="person" size="40px" />
            </q-avatar>
            <div class="text-h4 text-primary">My Profile</div>
            <div class="text-subtitle1 text-grey-7">
              {{ authStore.user?.email }}
            </div>
          </q-card-section>

          <q-card-section>
            <q-form @submit="updateProfile" class="q-gutter-md">
              <q-input
                v-model="profileData.email"
                label="Email"
                type="email"
                outlined
                :rules="[
                  val => !!val || 'Email is required',
                  val => isValidEmail(val) || 'Please enter a valid email'
                ]"
              />

              <q-input
                v-model="profileData.first_name"
                label="First Name"
                outlined
              />

              <q-input
                v-model="profileData.last_name"
                label="Last Name"
                outlined
              />

              <div v-if="error" class="text-negative q-mb-md">
                {{ error }}
              </div>

              <div class="text-center">
                <q-btn
                  type="submit"
                  color="primary"
                  label="Update Profile"
                  :loading="loading"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Change Password Card -->
        <q-card class="q-mt-lg q-pa-lg">
          <q-card-section>
            <div class="text-h6 text-primary q-mb-md">Change Password</div>
            
            <q-form @submit="changePassword" class="q-gutter-md">
              <q-input
                v-model="passwordData.current_password"
                label="Current Password"
                type="password"
                outlined
                :rules="[val => !!val || 'Current password is required']"
              />

              <q-input
                v-model="passwordData.new_password"
                label="New Password"
                type="password"
                outlined
                :rules="[
                  val => !!val || 'New password is required',
                  val => val.length >= 8 || 'Password must be at least 8 characters'
                ]"
              />

              <q-input
                v-model="passwordData.confirm_password"
                label="Confirm New Password"
                type="password"
                outlined
                :rules="[
                  val => !!val || 'Please confirm your password',
                  val => val === passwordData.new_password || 'Passwords do not match'
                ]"
              />

              <div v-if="passwordError" class="text-negative q-mb-md">
                {{ passwordError }}
              </div>

              <div class="text-center">
                <q-btn
                  type="submit"
                  color="primary"
                  label="Change Password"
                  :loading="passwordLoading"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Email Preferences Card -->
        <q-card class="q-mt-lg q-pa-lg">
          <q-card-section>
            <div class="text-h6 text-primary q-mb-md">Email Preferences</div>
            
            <q-form @submit="updateEmailPreferences" class="q-gutter-md">
              <q-checkbox
                v-model="emailPreferences.daily_card_email"
                label="Receive daily card via email"
                color="primary"
              />
              
              <q-checkbox
                v-model="emailPreferences.weekly_summary"
                label="Receive weekly summary"
                color="primary"
              />
              
              <q-checkbox
                v-model="emailPreferences.new_cards_notification"
                label="Notify me about new cards"
                color="primary"
              />

              <div class="text-center">
                <q-btn
                  type="submit"
                  color="primary"
                  label="Update Preferences"
                  :loading="preferencesLoading"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Account Actions -->
        <q-card class="q-mt-lg q-pa-lg">
          <q-card-section>
            <div class="text-h6 text-primary q-mb-md">Account Actions</div>
            
            <div class="q-gutter-md">
              <q-btn
                outline
                color="negative"
                label="Delete Account"
                @click="confirmDeleteAccount"
                icon="delete_forever"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Delete Account Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete your account? This action cannot be undone.
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" />
          <q-btn flat label="Delete Account" color="negative" @click="deleteAccount" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'
import axios from 'axios'

const $q = useQuasar()
const authStore = useAuthStore()

// Profile data
const profileData = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: ''
})

// Password change data
const passwordData = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

// Email preferences
const emailPreferences = ref({
  daily_card_email: true,
  weekly_summary: false,
  new_cards_notification: true
})

// Loading states
const loading = ref(false)
const passwordLoading = ref(false)
const preferencesLoading = ref(false)

// Error states
const error = ref('')
const passwordError = ref('')

// Dialog
const showDeleteDialog = ref(false)

// Validation
const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Methods
const loadProfileData = () => {
  if (authStore.user) {
    profileData.value = {
      email: authStore.user.email || '',
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || ''
    }
  }
  
  // Load email preferences (mock data for now)
  emailPreferences.value = {
    daily_card_email: true,
    weekly_summary: false,
    new_cards_notification: true
  }
}

const updateProfile = async () => {
  loading.value = true
  error.value = ''

  try {
    await axios.put('/api/profile/', profileData.value)
    
    // Update the auth store with new data
    await authStore.checkAuthStatus()
    
    $q.notify({
      type: 'positive',
      message: 'Profile updated successfully!'
    })
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

const changePassword = async () => {
  if (passwordData.value.new_password !== passwordData.value.confirm_password) {
    passwordError.value = 'Passwords do not match'
    return
  }

  passwordLoading.value = true
  passwordError.value = ''

  try {
    await axios.post('/api/change-password/', {
      current_password: passwordData.value.current_password,
      new_password: passwordData.value.new_password
    })
    
    // Clear form
    passwordData.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    
    $q.notify({
      type: 'positive',
      message: 'Password changed successfully!'
    })
  } catch (err) {
    passwordError.value = err.response?.data?.message || 'Failed to change password'
  } finally {
    passwordLoading.value = false
  }
}

const updateEmailPreferences = async () => {
  preferencesLoading.value = true

  try {
    await axios.put('/api/email-preferences/', emailPreferences.value)
    
    $q.notify({
      type: 'positive',
      message: 'Email preferences updated successfully!'
    })
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to update email preferences'
    })
  } finally {
    preferencesLoading.value = false
  }
}

const confirmDeleteAccount = () => {
  showDeleteDialog.value = true
}

const deleteAccount = async () => {
  try {
    await axios.delete('/api/delete-account/')
    
    $q.notify({
      type: 'positive',
      message: 'Account deleted successfully'
    })
    
    // Logout and redirect
    await authStore.logout()
    window.location.href = '/'
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete account'
    })
  }
  
  showDeleteDialog.value = false
}

// Lifecycle
onMounted(() => {
  loadProfileData()
})
</script>
