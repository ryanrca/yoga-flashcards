<template>
  <q-page>
    <component :is="variant" :daily-card="dailyCard" />
  </q-page>
</template>

<script setup>
import { computed, ref, onMounted, defineAsyncComponent } from 'vue'
import { useFlashcardsStore } from 'src/stores/flashcards'
import { useTheme, DEFAULT_THEME } from 'src/composables/useTheme'

// The four home designs differ by about half their markup, which is too much
// to fold into one parameterised component - so each stays whole and the
// theme picks one. They are lazy so a visitor only downloads the one they see.
const VARIANTS = {
  studio: defineAsyncComponent(() => import('./home/HomeStudio.vue')),
  dusk: defineAsyncComponent(() => import('./home/HomeDusk.vue')),
  clay: defineAsyncComponent(() => import('./home/HomeClay.vue')),
  neon: defineAsyncComponent(() => import('./home/HomeNeon.vue'))
}

const { theme } = useTheme()
const flashcardsStore = useFlashcardsStore()

const dailyCard = ref(null)

const variant = computed(() => VARIANTS[theme.value] || VARIANTS[DEFAULT_THEME])

// Fetched once here rather than in each variant, so switching theme does not
// refetch and the four files stay purely presentational.
onMounted(async () => {
  const result = await flashcardsStore.fetchDailyCard()
  if (result.success) {
    dailyCard.value = result.data
  }
})
</script>
