<template>
  <q-page class="flex flex-center">
    <div class="column items-center q-gutter-lg" style="max-width: 800px; width: 100%;">
      <!-- Hero Section -->
      <div class="text-center q-pa-lg">
        <h1 class="text-h2 text-primary q-mb-md">Yoga Flashcards</h1>
        <p class="text-h6 text-grey-7 q-mb-lg">
          Discover the wisdom of yoga through daily practice with our curated flashcards
        </p>
      </div>

      <!-- Daily Card Preview - Moved to top -->
      <q-card v-if="dailyCard" class="full-width">
        <q-card-section>
          <div class="text-h5 text-center q-mb-md">Today's Featured Card</div>
          <div class="text-center">
            <div class="text-h6 text-primary">{{ dailyCard.title }}</div>
            <div v-if="dailyCard.phrase" class="text-subtitle1 text-italic q-mt-sm">
              {{ dailyCard.phrase }}
            </div>
            <p class="q-mt-md">{{ dailyCard.definition }}</p>
          </div>
        </q-card-section>
      </q-card>

      <!-- Action Buttons -->
      <div class="q-gutter-md">
        <q-btn
          v-if="!authStore.isAuthenticated"
          size="lg"
          outline
          color="primary"
          label="SIGN UP"
          @click="$router.push('/signup')"
          icon="person_add"
          style="font-weight: 700; letter-spacing: 1.5px;"
        />
        <q-btn
          v-if="authStore.isAuthenticated"
          size="lg"
          outline
          color="primary"
          label="BROWSE ALL CARDS"
          @click="$router.push('/cards')"
          icon="auto_stories"
          style="font-weight: 700; letter-spacing: 1.5px;"
        />
      </div>

      <!-- Features Section -->
      <div class="row q-gutter-md full-width justify-center">
        <q-card class="col-md-3 col-sm-6 col-xs-12">
          <q-card-section class="text-center">
            <q-icon name="search" size="3rem" color="primary" />
            <div class="text-h6 q-mt-sm">Search & Learn</div>
            <p class="text-grey-7 q-mt-sm">
              Explore our comprehensive collection of yoga poses, philosophy, and Sanskrit terms
            </p>
          </q-card-section>
        </q-card>

        <q-card class="col-md-3 col-sm-6 col-xs-12">
          <q-card-section class="text-center">
            <q-icon name="favorite" size="3rem" color="primary" />
            <div class="text-h6 q-mt-sm">Personal Favorites</div>
            <p class="text-grey-7 q-mt-sm">
              Save your favorite cards and create your personal yoga study collection
            </p>
          </q-card-section>
        </q-card>

        <q-card class="col-md-3 col-sm-6 col-xs-12">
          <q-card-section class="text-center">
            <q-icon name="school" size="3rem" color="primary" />
            <div class="text-h6 q-mt-sm">Yoga Philosophy</div>
            <p class="text-grey-7 q-mt-sm">
              Learn the 8 limbs of yoga, yamas, niyamas and deepen your understanding
            </p>
          </q-card-section>
        </q-card>
      </div>
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
  // Fetch daily card for preview
  const result = await flashcardsStore.fetchDailyCard()
  if (result.success) {
    dailyCard.value = result.data
  }
})
</script>
