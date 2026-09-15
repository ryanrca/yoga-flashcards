import { boot } from 'quasar/wrappers'
import { initTheme } from 'src/composables/useTheme'

// Boot files run before the app mounts, so the data-theme attribute is on
// <html> before anything paints. Until it is set, :root holds the Studio
// palette, so the pre-boot frame is a valid theme rather than unstyled.
export default boot(() => {
  initTheme()
})
