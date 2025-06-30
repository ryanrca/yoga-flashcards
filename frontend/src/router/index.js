import { route } from 'quasar/wrappers'
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from 'src/stores/auth'

import routes from './routes'

export default route(function (/* { store, ssrContext } */) {
  const createHistory = createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE)
  })

  // Navigation guard for authentication
  Router.beforeEach(async (to) => {
    const authStore = useAuthStore()
    
    // Allow access to login page
    if (to.path === '/login') {
      return true
    }
    
    // Check authentication status
    const isAuthenticated = await authStore.checkAuthStatus()
    
    if (!isAuthenticated) {
      return '/login'
    }
    
    return true
  })

  return Router
})
