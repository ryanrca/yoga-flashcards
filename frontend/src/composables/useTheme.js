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

// The last ?theme= value seen, valid or not. Used so route changes only act on
// an actual change to the query - otherwise every in-app navigation would
// re-apply the URL theme and stomp a choice made in the picker.
let lastUrlTheme = null

function isValid (id) {
  return typeof id === 'string' && VALID.has(id)
}

// A silent no-op is the wrong failure mode here: ?theme=dark looks like it
// should work, and without this you just get the previous theme with no clue why.
function warnInvalid (raw) {
  console.warn(
    `[theme] "${raw}" is not a theme. Valid ids: ${THEMES.map((t) => t.id).join(', ')}`
  )
}

// The router runs in hash mode, so a shared preview link can put the query
// either before the hash (/?theme=dusk) or inside it (/#/?theme=dusk).
// Accept both rather than making the person sharing the link think about it.
function rawThemeFromUrl () {
  if (typeof window === 'undefined') return null

  const fromSearch = new URLSearchParams(window.location.search).get('theme')
  if (fromSearch) return fromSearch

  const hash = window.location.hash || ''
  const q = hash.indexOf('?')
  if (q !== -1) {
    const fromHash = new URLSearchParams(hash.slice(q + 1)).get('theme')
    if (fromHash) return fromHash
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
  const raw = rawThemeFromUrl()
  lastUrlTheme = raw

  if (raw) {
    if (isValid(raw)) return applyTheme(raw, { persist: false })
    warnInvalid(raw)
  }

  return applyTheme(readStored() || DEFAULT_THEME, { persist: false })
}

// Called on every route change. In hash mode, editing ?theme= in the address
// bar changes only the fragment, so the document never reloads and the boot
// file never runs again - without this, a preview link only takes effect on a
// full reload, which looks exactly like a caching bug.
export function syncThemeFromRoute (queryValue) {
  // Vue Router hands back an array if the key appears more than once.
  const raw = Array.isArray(queryValue) ? queryValue[0] : queryValue
  if (raw === undefined || raw === null || raw === '') return

  // Only react to an actual change, so navigating around the app does not
  // override a theme picked from the menu.
  if (raw === lastUrlTheme) return
  lastUrlTheme = raw

  if (!isValid(raw)) {
    warnInvalid(raw)
    return
  }

  applyTheme(raw, { persist: false })
}

export function useTheme () {
  return {
    theme: readonly(current),
    themes: THEMES,
    setTheme: applyTheme
  }
}
