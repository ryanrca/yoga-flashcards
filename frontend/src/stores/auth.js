import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from 'src/boot/axios'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isCurator = computed(() => user.value?.role === 'curator' || user.value?.role === 'admin')
  const isUser = computed(() => !!user.value)

  // Actions
  const login = async (credentials) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/users/login/', credentials)
      user.value = response.data.user
      isAuthenticated.value = true
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.message || 'Login failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    loading.value = true
    
    try {
      await api.post('/api/users/logout/')
      user.value = null
      isAuthenticated.value = false
      return { success: true }
    } catch (err) {
      console.error('Logout error:', err)
      // Still clear local state even if API call fails
      user.value = null
      isAuthenticated.value = false
      return { success: true }
    } finally {
      loading.value = false
    }
  }

  const checkAuthStatus = async () => {
    loading.value = true
    
    try {
      const response = await api.get('/api/users/auth-status/')
      if (response.data.authenticated) {
        user.value = response.data.user
        isAuthenticated.value = true
      } else {
        user.value = null
        isAuthenticated.value = false
      }
    } catch (err) {
      console.error('Auth check failed:', err)
      user.value = null
      isAuthenticated.value = false
    } finally {
      loading.value = false
    }
  }

  const signup = async (userData) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/users/register/', userData)
      
      // After successful signup, automatically log in the user
      const loginResult = await login({
        email: userData.email,
        password: userData.password
      })
      
      if (loginResult.success) {
        return { success: true, data: response.data, autoLogin: true }
      } else {
        // Signup succeeded but auto-login failed
        return { success: true, data: response.data, autoLogin: false }
      }
    } catch (err) {
      error.value = err.response?.data?.message || 'Signup failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchUserStats = async () => {
    try {
      const response = await api.get('/api/users/manage/stats/')
      return response.data
    } catch (err) {
      console.error('Error fetching user stats:', err)
      return { total: 0, active: 0, admins: 0 }
    }
  }

  const fetchUsers = async (params = {}) => {
    try {
      const response = await api.get('/api/users/manage/', { params })
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error fetching users:', err)
      return { success: false, error: err.response?.data || 'Failed to fetch users' }
    }
  }

  const createUser = async (userData) => {
    try {
      const response = await api.post('/api/users/manage/', userData)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error creating user:', err)
      return { success: false, error: err.response?.data || 'Failed to create user' }
    }
  }

  const updateUser = async (userId, userData) => {
    try {
      const response = await api.patch(`/api/users/manage/${userId}/`, userData)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error updating user:', err)
      return { success: false, error: err.response?.data || 'Failed to update user' }
    }
  }

  const deleteUser = async (userId) => {
    try {
      await api.delete(`/api/users/manage/${userId}/`)
      return { success: true }
    } catch (err) {
      console.error('Error deleting user:', err)
      return { success: false, error: err.response?.data || 'Failed to delete user' }
    }
  }

  const toggleUserStatus = async (userId) => {
    try {
      const response = await api.post(`/api/users/manage/${userId}/toggle_active/`)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error toggling user status:', err)
      return { success: false, error: err.response?.data || 'Failed to toggle user status' }
    }
  }

  return {
    // State
    user,
    isAuthenticated,
    loading,
    error,
    
    // Getters
    isAdmin,
    isCurator,
    isUser,
    
    // Actions
    login,
    logout,
    checkAuthStatus,
    signup,
    fetchUserStats,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    toggleUserStatus
  }
})
