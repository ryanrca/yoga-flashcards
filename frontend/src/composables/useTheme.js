import { ref, readonly } from 'vue'

// The four themes, in the order they appear in the picker.
// `id` is what lands in the data-theme attribute, localStorage and ?theme=.
export const THEMES = [
  { id: 'studio', label: 'Studio', blurb: 'Light, editorial, quiet' },
  { id: 'dusk', label: 'Dusk', blurb: 'Dark, luminous, still' },
  { id: 'clay', label: 'Clay', blurb: 'Warm, organic, tactile' },
  { id: 'neon', label: 'Neon', blurb: 'The original psychedelic' }
]

export const DEFAULT_THEME = 'studio'

const STORAGE_KEY = 'yoga-theme'

const VALID = new Set(THEMES.map((t) => t.id))

const current = ref(DEFAULT_THEME)

function isValid (id) {
  return typeof id === 'string' && VALID.has(id)
}

// The router runs in hash mode, so a shared preview link can put the query
// either before the hash (/?theme=dusk) or inside it (/#/?theme=dusk).
// Accept both rather than making the person sharing the link think about it.
function themeFromUrl () {
  if (typeof window === 'undefined') return null

  const fromSearch = new URLSearchParams(window.location.search).get('theme')
  if (isValid(fromSearch)) return fromSearch

  const hash = window.location.hash || ''
  const q = hash.indexOf('?')
  if (q !== -1) {
    const fromHash = new URLSearchParams(hash.slice(q + 1)).get('theme')
    if (isValid(fromHash)) return fromHash
  }

  return null
}

// localStorage throws in some privacy modes, and can be cleared at any time.
// Never let a storage failure stop the app from rendering.
function readStored () {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return isValid(stored) ? stored : null
  } catch {
    return null
  }
}

function writeStored (id) {
  try {
    window.localStorage.setItem(STORAGE_KEY, id)
  } catch {
    // Preference simply will not persist. Not worth surfacing.
  }
}

// Applying a theme is one attribute write. Quasar's components follow because
// quasar.css consumes --q-primary and friends via var(), and each theme block
// in app.scss redefines them at higher specificity than Quasar's bare :root.
export function applyTheme (id, { persist = true } = {}) {
  const next = isValid(id) ? id : DEFAULT_THEME
  current.value = next

  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = next
  }
  if (persist) writeStored(next)

  return next
}

// Resolution order: ?theme= wins so a preview link always shows what it says,
// then the stored preference, then the default.
// A URL theme is not persisted - following a link should not silently change
// what the recipient sees on their next visit.
export function initTheme () {
  const fromUrl = themeFromUrl()
  if (fromUrl) return applyTheme(fromUrl, { persist: false })
  return applyTheme(readStored() || DEFAULT_THEME, { persist: false })
}

export function useTheme () {
  return {
    theme: readonly(current),
    themes: THEMES,
    setTheme: applyTheme
  }
}
