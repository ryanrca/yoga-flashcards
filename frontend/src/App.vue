<template>
  <!--
    Decorative sunbeams, behind everything: two counter-rotating fans of soft
    rays whose angular periods differ slightly, so they beat against each other
    into a slow moire shimmer.

    It lives here rather than on a pseudo-element because both of body's are
    already taken by Neon's gradient wash and mandala overlay, and html's
    pseudo-elements paint behind body, whose opaque --page-bg would bury them.
    App.vue is the one place both layouts inherit.

    aria-hidden and pointer-events: none - it is pure decoration and must never
    take focus or intercept a click. Styled in css/app.scss.
  -->
  <div class="sunbeams" aria-hidden="true"></div>
  <router-view />
</template>

<script setup>
//
</script>
