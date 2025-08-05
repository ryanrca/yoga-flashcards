<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8 col-lg-6">
        <q-card class="q-pa-lg">
          <q-card-section class="text-center">
            <div class="text-h4 text-primary q-mb-md">Daily Yoga Card</div>
            <div class="text-subtitle1 text-grey-7 q-mb-lg">
              {{ new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              }) }}
            </div>
          </q-card-section>

          <q-card-section v-if="loading">
            <div class="text-center">
              <q-spinner color="primary" size="3em" />
              <div class="q-mt-md">Loading today's card...</div>
            </div>
          </q-card-section>

          <q-card-section v-else-if="error">
            <q-banner type="negative" class="text-white">
              <template v-slot:avatar>
                <q-icon name="error" color="white" />
              </template>
              {{ error }}
            </q-banner>
            <div class="text-center q-mt-md">
              <q-btn 
                color="primary" 
                label="Try Again" 
                @click="loadDailyCard"
              />
            </div>
          </q-card-section>

          <q-card-section v-else-if="dailyCard">
            <div class="text-center">
              <!-- Card Image -->
              <div v-if="dailyCard.front_image" class="q-mb-md">
                <q-img 
                  :src="dailyCard.front_image" 
                  style="max-width: 300px; max-height: 200px; border-radius: 8px;"
                  class="q-mx-auto"
                />
              </div>

              <!-- Card Title -->
              <div class="text-h5 text-primary q-mb-sm">
                {{ dailyCard.title }}
              </div>

              <!-- Sanskrit Phrase -->
              <div v-if="dailyCard.phrase" class="text-h6 text-italic text-grey-8 q-mb-md">
                {{ dailyCard.phrase }}
              </div>

              <!-- Definition -->
              <div class="text-body1 q-mb-lg" style="text-align: justify;">
                {{ dailyCard.definition }}
              </div>

              <!-- Tags -->
              <div v-if="dailyCard.tags && dailyCard.tags.length" class="q-mb-md">
                <q-chip
                  v-for="tag in dailyCard.tags"
                  :key="tag.id"
                  color="primary"
                  text-color="white"
                  :label="tag.name"
                  class="q-ma-xs"
                />
              </div>

              <!-- Back Image -->
              <div v-if="dailyCard.back_image" class="q-mt-md">
                <q-img 
                  :src="dailyCard.back_image" 
                  style="max-width: 300px; max-height: 200px; border-radius: 8px;"
                  class="q-mx-auto"
                />
              </div>
            </div>
          </q-card-section>

          <q-card-actions class="justify-center">
            <q-btn
              v-if="!authStore.isAuthenticated"
              color="primary"
              label="Sign Up to See More Cards"
              @click="$router.push('/signup')"
              icon="person_add"
            />
            <q-btn
              v-if="authStore.isAuthenticated"
              color="primary"
              label="Browse All Cards"
              @click="$router.push('/cards')"
              icon="view_cards"
            />
            <q-btn
              flat
              color="primary"
              label="Share"
              @click="shareCard"
              icon="share"
            />
          </q-card-actions>
        </q-card>

        <!-- Tomorrow's hint -->
        <q-card class="q-mt-lg">
          <q-card-section class="text-center">
            <q-icon name="schedule" size="2em" color="grey-6" />
            <div class="text-h6 q-mt-sm">Tomorrow's Card</div>
            <p class="text-grey-7">
              Come back tomorrow to discover another aspect of yoga wisdom!
            </p>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'
import { useFlashcardsStore } from 'src/stores/flashcards'

const $q = useQuasar()
const authStore = useAuthStore()
const flashcardsStore = useFlashcardsStore()

const dailyCard = ref(null)
const loading = ref(false)
const error = ref(null)

const loadDailyCard = async () => {
  loading.value = true
  error.value = null
  
  const result = await flashcardsStore.fetchDailyCard()
  
  if (result.success) {
    dailyCard.value = result.data
  } else {
    error.value = result.error || 'Failed to load daily card'
  }
  
  loading.value = false
}

const shareCard = () => {
  if (navigator.share && dailyCard.value) {
    navigator.share({
      title: `Daily Yoga Card: ${dailyCard.value.title}`,
      text: `${dailyCard.value.phrase ? dailyCard.value.phrase + ' - ' : ''}${dailyCard.value.definition}`,
      url: window.location.href
    })
  } else {
    // Fallback to copying to clipboard
    const shareText = `Daily Yoga Card: ${dailyCard.value.title}\n${dailyCard.value.phrase ? dailyCard.value.phrase + '\n' : ''}${dailyCard.value.definition}\n\n${window.location.href}`
    
    navigator.clipboard.writeText(shareText).then(() => {
      $q.notify({
        type: 'positive',
        message: 'Card details copied to clipboard!'
      })
    }).catch(() => {
      $q.notify({
        type: 'negative',
        message: 'Unable to share card'
      })
    })
  }
}

onMounted(() => {
  loadDailyCard()
})
</script>
