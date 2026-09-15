<template>
  <q-page>
    <div class="yoga-container">
      <!-- Hero sits inside a soft clay block rather than on the bare page -->
      <section class="clay-hero">
        <div class="clay-eyebrow">Daily practice</div>
        <h1 class="q-mb-md">Yoga Sutra Flashcards</h1>
        <p class="clay-lede q-mb-lg">
          The eight limbs, the yamas and niyamas, and the Sanskrit that carries them -
          gathered into one warm, unhurried deck.
        </p>
        <div class="q-gutter-sm">
          <q-btn
            v-if="!authStore.isAuthenticated"
            class="yoga-btn-primary"
            label="Create an account"
            unelevated
            @click="$router.push('/signup')"
          />
          <q-btn
            v-if="authStore.isAuthenticated"
            class="yoga-btn-primary"
            label="Browse all cards"
            unelevated
            @click="$router.push('/cards')"
          />
          <q-btn
            class="yoga-btn-secondary"
            label="Today's card"
            unelevated
            @click="$router.push('/daily')"
          />
        </div>
      </section>

      <section v-if="dailyCard" class="q-mb-xl">
        <div class="clay-eyebrow">Today</div>
        <q-card>
          <q-card-section>
            <div v-if="dailyCard.phrase" class="text-h3 q-mb-xs">{{ dailyCard.phrase }}</div>
            <div class="text-h5 q-mb-md">{{ dailyCard.title }}</div>
            <div v-if="dailyCard.short_answer" class="answer-callout">
              <p class="text-body1 q-mb-none">{{ dailyCard.short_answer }}</p>
            </div>
            <p v-else class="text-body1 q-mb-none">{{ dailyCard.definition }}</p>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-btn flat dense color="primary" label="Read the full card" @click="$router.push('/daily')" />
          </q-card-section>
        </q-card>
      </section>

      <!-- Features as colour tiles, not cards -->
      <section class="row q-col-gutter-md q-pb-xl">
        <div class="col-12 col-md-4">
          <q-card flat class="clay-tile tile-terra">
            <div class="text-h6 q-mb-sm">Search and learn</div>
            <p class="text-grey-7 q-mb-none">
              The full collection, searchable by word or by theme.
            </p>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat class="clay-tile tile-sage">
            <div class="text-h6 q-mb-sm">Keep what matters</div>
            <p class="text-grey-7 q-mb-none">
              Save the cards you return to and build a personal study set.
            </p>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat class="clay-tile">
            <div class="text-h6 q-mb-sm">Philosophy, in order</div>
            <p class="text-grey-7 q-mb-none">
              Each limb, yama and niyama with its own card and Devanagari.
            </p>
          </q-card>
        </div>
      </section>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from 'src/stores/auth'
import { useFlashcardsStore } from 'src/stores/flashcards'

const authStore = useAuthStore()
const flashcardsStore = useFlashcardsStore()

const dailyCard = ref(null)

onMounted(async () => {
  const result = await flashcardsStore.fetchDailyCard()
  if (result.success) {
    dailyCard.value = result.data
  }
})
</script>
