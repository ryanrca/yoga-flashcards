<template>
  <q-page>
    <div class="yoga-container">
      <!-- Hero: centred, with a single warm rule. Nothing animates. -->
      <section class="dusk-hero">
        <div class="dusk-eyebrow">Daily practice</div>
        <h1 class="q-mb-md">Yoga Sutra Flashcards</h1>
        <hr class="dusk-rule" />
        <p class="dusk-lede q-mb-lg">
          The eight limbs, the yamas and niyamas, and the Sanskrit that carries them.
          Studied one card at a time.
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

      <!-- Today's card, presented as the single bright object on the page -->
      <section v-if="dailyCard" class="q-mb-xl">
        <q-card>
          <q-card-section class="text-center">
            <div class="dusk-eyebrow q-mb-sm">Today</div>
            <div v-if="dailyCard.phrase" class="text-h3 text-primary q-mb-xs">
              {{ dailyCard.phrase }}
            </div>
            <div class="text-h5 q-mb-md">{{ dailyCard.title }}</div>
            <p v-if="dailyCard.short_answer" class="dusk-lede q-mb-none">
              {{ dailyCard.short_answer }}
            </p>
            <p v-else class="dusk-lede q-mb-none">{{ dailyCard.definition }}</p>
          </q-card-section>
          <q-card-section class="text-center q-pt-none">
            <q-btn flat dense color="primary" label="Read the full card" @click="$router.push('/daily')" />
          </q-card-section>
        </q-card>
      </section>

      <section class="row q-col-gutter-md q-pb-xl">
        <div class="col-12 col-md-4">
          <q-card><q-card-section>
            <q-icon name="search" size="1.75rem" color="primary" class="q-mb-sm" />
            <div class="text-h6 q-mb-sm">Search and learn</div>
            <p class="text-grey-7 q-mb-none">
              The full collection, searchable by word or by theme.
            </p>
          </q-card-section></q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card><q-card-section>
            <q-icon name="favorite" size="1.75rem" color="primary" class="q-mb-sm" />
            <div class="text-h6 q-mb-sm">Keep what matters</div>
            <p class="text-grey-7 q-mb-none">
              Save the cards you return to and build a personal study set.
            </p>
          </q-card-section></q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card><q-card-section>
            <q-icon name="school" size="1.75rem" color="primary" class="q-mb-sm" />
            <div class="text-h6 q-mb-sm">Philosophy, in order</div>
            <p class="text-grey-7 q-mb-none">
              Each limb, yama and niyama with its own card and Devanagari.
            </p>
          </q-card-section></q-card>
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
