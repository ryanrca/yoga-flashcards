<template>
  <div class="yoga-container">
    <!-- The original hero: centred, loud, gradient-filled heading. -->
    <section class="neon-hero">
      <h1 class="q-mb-md neon-glow">Yoga Sutra Flashcards</h1>
      <p class="hero-lede hero-lede--center q-mb-lg">
        Discover the wisdom of yoga through daily practice with our curated flashcards
      </p>
    </section>

    <!-- Daily card preview -->
    <section v-if="dailyCard" class="q-mb-xl">
      <q-card>
        <q-card-section>
          <div class="text-h5 text-center q-mb-md">Today's Sutra</div>
          <div class="text-center">
            <div class="text-h6 text-primary">{{ dailyCard.title }}</div>
            <div v-if="dailyCard.phrase" class="text-subtitle1 text-italic q-mt-sm">
              {{ dailyCard.phrase }}
            </div>

            <div v-if="dailyCard.short_answer" class="answer-callout q-mt-md text-left">
              <p class="text-body1 q-mb-none">{{ dailyCard.short_answer }}</p>
            </div>

            <p v-else class="q-mt-md">{{ dailyCard.definition }}</p>
          </div>
        </q-card-section>

        <q-card-actions align="center">
          <q-btn
            class="yoga-btn-primary"
            label="Go Deeper"
            icon="info"
            unelevated
            @click="$router.push('/daily')"
          />
        </q-card-actions>
      </q-card>
    </section>

    <!-- Action buttons -->
    <div class="row justify-center q-gutter-md q-mb-xl">
      <q-btn
        v-if="!authStore.isAuthenticated"
        size="lg"
        class="yoga-btn-primary"
        label="Sign Up"
        icon="person_add"
        unelevated
        @click="$router.push('/signup')"
      />
      <q-btn
        v-if="authStore.isAuthenticated"
        size="lg"
        class="yoga-btn-primary"
        label="Browse All Cards"
        icon="auto_stories"
        unelevated
        @click="$router.push('/cards')"
      />
    </div>

    <!-- Features -->
    <section class="row q-col-gutter-md q-pb-xl">
      <div class="col-12 col-sm-6 col-md-4">
        <q-card><q-card-section class="text-center">
          <q-icon name="search" size="3rem" color="primary" />
          <div class="text-h6 q-mt-sm">Search &amp; Learn</div>
          <p class="text-grey-7 q-mt-sm q-mb-none">
            Explore our comprehensive collection of yoga poses, philosophy, and Sanskrit terms
          </p>
        </q-card-section></q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-4">
        <q-card><q-card-section class="text-center">
          <q-icon name="favorite" size="3rem" color="primary" />
          <div class="text-h6 q-mt-sm">Personal Favorites</div>
          <p class="text-grey-7 q-mt-sm q-mb-none">
            Save your favorite cards and create your personal yoga study collection
          </p>
        </q-card-section></q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-4">
        <q-card><q-card-section class="text-center">
          <q-icon name="school" size="3rem" color="primary" />
          <div class="text-h6 q-mt-sm">Yoga Philosophy</div>
          <p class="text-grey-7 q-mt-sm q-mb-none">
            Learn the 8 limbs of yoga, yamas, niyamas and deepen your understanding
          </p>
        </q-card-section></q-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useAuthStore } from 'src/stores/auth'

defineProps({
  dailyCard: { type: Object, default: null }
})

const authStore = useAuthStore()
</script>
