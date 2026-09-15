import { boot } from 'quasar/wrappers'
import { initTheme, syncThemeFromRoute } from 'src/composables/useTheme'

// Boot files run before the app mounts, so the data-theme attribute is on
// <html> before anything paints. Until it is set, :root holds the Studio
// palette, so the pre-boot frame is a valid theme rather than unstyled.
export default boot(({ router }) => {
  initTheme()

  // The router runs in hash mode. Going from /#/?theme=dusk to /#/?theme=studio
  // changes only the fragment, so the browser does not reload the document and
  // this boot file never runs a second time. Without this hook a preview link
  // only takes effect after a full reload - which presents exactly like a
  // stale-cache bug, and was reported as one.
  router.afterEach((to) => {
    syncThemeFromRoute(to.query.theme)
  })
})
