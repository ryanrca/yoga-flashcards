import { ref, readonly } from 'vue'
import { api } from 'src/boot/axios'

// The four themes, in the order they appear in the admin picker.
// `id` is what lands in the data-theme attribute and in SiteSettings.theme -
// these ids must stay in step with the Theme choices on the Django model.
export const THEMES = [
  { id: 'studio', label: 'Studio', blurb: 'Light, editorial, quiet' },
  { id: 'dusk', label: 'Dusk', blurb: 'Dark, luminous, still' },
  { id: 'clay', label: 'Clay', blurb: 'Warm, organic, tactile' },
  { id: 'neon', label: 'Neon', blurb: 'The original psychedelic' }
]

export const DEFAULT_THEME = 'studio'

// A paint-time cache of the admin's choice, NOT a per-visitor preference.
// Visitors cannot pick a theme; this only exists so a repeat visit paints the
// right colours before the API call returns.
const CACHE_KEY = 'yoga-site-theme'

const VALID = new Set(THEMES.map((t) => t.id))

const current = ref(DEFAULT_THEME)

function isValid (id) {
  return typeof id === 'string' && VALID.has(id)
}

function readCache () {
  try {
    const cached = window.localStorage.getItem(CACHE_KEY)
    return isValid(cached) ? cached : null
  } catch {
    return null
  }
}

function writeCache (id) {
  try {
    window.localStorage.setItem(CACHE_KEY, id)
  } catch {
    // Cache is an optimisation. Without it the first paint uses the default
    // and corrects itself a moment later.
  }
}

// Applying a theme is one attribute write. Quasar's components follow because
// quasar.css consumes --q-primary and friends via var(), and each theme block
// in app.scss redefines them at higher specificity than Quasar's bare :root.
export function applyTheme (id, { cache = false } = {}) {
  const next = isValid(id) ? id : DEFAULT_THEME
  current.value = next

  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = next
  }
  if (cache) writeCache(next)

  return next
}

// GET is AllowAny - anonymous visitors need the theme on every page load.
export async function fetchSiteTheme () {
  try {
    const response = await api.get('/api/site-settings/')
    return { success: true, data: response.data }
  } catch (err) {
    console.error('Error fetching site settings:', err)
    return { success: false, error: 'Failed to load site settings' }
  }
}

// PUT is admin-only, enforced server side by IsAdminOnly.
export async function saveSiteTheme (theme) {
  try {
    const response = await api.put('/api/site-settings/', { theme })
    applyTheme(response.data.theme, { cache: true })
    return { success: true, data: response.data }
  } catch (err) {
    console.error('Error saving site settings:', err)
    return { success: false, error: err.response?.data || 'Failed to save site settings' }
  }
}

// Paint the cached theme immediately, then reconcile with the server.
//
// The theme is now server state, so resolving it is asynchronous. Without the
// cache every visitor would get a frame of Studio before the real theme
// arrived. The cache is only ever written from a server response, so it cannot
// drift into being a personal preference.
export function initTheme () {
  applyTheme(readCache() || DEFAULT_THEME, { cache: false })

  fetchSiteTheme().then((result) => {
    if (result.success && result.data?.theme) {
      applyTheme(result.data.theme, { cache: true })
    }
  })

  return current.value
}

export function useTheme () {
  return {
    theme: readonly(current),
    themes: THEMES,
    applyTheme,
    fetchSiteTheme,
    saveSiteTheme
  }
}
