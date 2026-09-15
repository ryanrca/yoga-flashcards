<template>
  <q-page>
    <div class="yoga-container">
      <!-- Hero: left aligned and editorial. The impact is the type scale. -->
      <section class="studio-hero">
        <div class="studio-eyebrow">Daily practice</div>
        <h1 class="q-mb-md">Yoga Sutra<br />Flashcards</h1>
        <p class="studio-lede q-mb-lg">
          A quiet, studied deck of the eight limbs, the yamas and niyamas, and the
          Sanskrit that carries them. One card a day, or the whole library at once.
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

      <!-- Today's card -->
      <section v-if="dailyCard" class="q-mb-xl">
        <div class="studio-eyebrow">Today</div>
        <q-card>
          <q-card-section>
            <div class="row items-baseline q-gutter-md q-mb-sm">
              <div class="text-h3">{{ dailyCard.title }}</div>
              <div v-if="dailyCard.phrase" class="text-h5 text-italic text-grey-7">
                {{ dailyCard.phrase }}
              </div>
            </div>
            <p v-if="dailyCard.short_answer" class="text-body1 q-mb-none">
              {{ dailyCard.short_answer }}
            </p>
            <p v-else class="text-body1 q-mb-none">{{ dailyCard.definition }}</p>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-btn flat dense color="primary" label="Read the full card" @click="$router.push('/daily')" />
          </q-card-section>
        </q-card>
      </section>

      <!-- Three columns, ruled rather than boxed -->
      <section class="row q-col-gutter-xl q-pb-xl">
        <div class="col-12 col-md-4">
          <q-card flat class="studio-feature">
            <div class="text-h6 q-mb-sm">Search and learn</div>
            <p class="text-grey-7 q-mb-none">
              The full collection of poses, philosophy and Sanskrit terms, searchable
              by word or by theme.
            </p>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat class="studio-feature">
            <div class="text-h6 q-mb-sm">Keep what matters</div>
            <p class="text-grey-7 q-mb-none">
              Save the cards you return to and build a personal study set.
            </p>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat class="studio-feature">
            <div class="text-h6 q-mb-sm">Philosophy, in order</div>
            <p class="text-grey-7 q-mb-none">
              The eight limbs, the five yamas and the five niyamas, each with its
              own card and its own Devanagari.
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
