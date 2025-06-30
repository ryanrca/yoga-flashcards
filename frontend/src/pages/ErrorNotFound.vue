<template>
  <div>
    <div class="text-h6">404 - Not Found</div>
    <p>Sorry, the page you are looking for could not be found.</p>
    <q-btn color="primary" @click="$router.push('/')">Go Home</q-btn>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ErrorNotFound'
})
</script>
