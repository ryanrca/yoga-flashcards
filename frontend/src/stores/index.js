import { createPinia } from 'pinia'

const pinia = createPinia()

// Suppress Redux DevTools errors in development
if (import.meta.env.DEV) {
  const originalError = console.error
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('No tab with id') || args[0].includes('redux'))
    ) {
      return
    }
    originalError.apply(console, args)
  }
}

export default pinia
