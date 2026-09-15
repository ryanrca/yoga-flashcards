import { boot } from 'quasar/wrappers'
import { initTheme } from 'src/composables/useTheme'

// Boot files run before the app mounts. initTheme() paints the cached theme
// synchronously and then reconciles with GET /api/site-settings/, which is
// AllowAny so anonymous visitors resolve it too.
//
// There is no router hook any more: the theme is site-wide admin state, not
// something a URL or a visitor can change, so nothing needs re-resolving on
// navigation.
export default boot(() => {
  initTheme()
})
