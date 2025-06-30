import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null
  },

  actions: {
    async login(credentials) {
      this.loading = true
      try {
        const response = await api.post('/api/users/login/', credentials)
        this.user = response.data.user
        this.isAuthenticated = true
        return { success: true }
      } catch (error) {
        this.user = null
        this.isAuthenticated = false
        return { 
          success: false, 
          error: error.response?.data?.error || 'Login failed' 
        }
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.loading = true
      try {
        await api.post('/api/users/logout/')
        this.user = null
        this.isAuthenticated = false
        return { success: true }
      } catch (error) {
        // Even if logout fails on server, clear local state
        this.user = null
        this.isAuthenticated = false
        return { success: true }
      } finally {
        this.loading = false
      }
    },

    async checkAuthStatus() {
      this.loading = true
      try {
        const response = await api.get('/api/users/auth-status/')
        if (response.data.authenticated) {
          this.user = response.data.user
          this.isAuthenticated = true
        } else {
          this.user = null
          this.isAuthenticated = false
        }
        return this.isAuthenticated
      } catch (error) {
        this.user = null
        this.isAuthenticated = false
        return false
      } finally {
        this.loading = false
      }
    }
  }
})
