<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-10">
        <div class="text-h4 text-primary q-mb-md text-center">
          My Favorite Cards
        </div>
        
        <!-- Empty State -->
        <div v-if="favorites.length === 0 && !loading" class="text-center q-py-xl">
          <q-icon name="favorite_border" size="6em" color="grey-5" />
          <div class="text-h6 text-grey-6 q-mt-md">No favorites yet</div>
          <p class="text-grey-6 q-mb-lg">
            Start building your personal collection by adding cards to your favorites!
          </p>
          <q-btn
            color="primary"
            label="Browse Cards"
            @click="$router.push('/cards')"
            icon="view_cards"
          />
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center q-py-lg">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md">Loading your favorites...</div>
        </div>

        <!-- Favorites Grid -->
        <div v-else-if="favorites.length > 0" class="row q-gutter-md">
          <div 
            v-for="favorite in favorites" 
            :key="favorite.id"
            class="col-12 col-sm-6 col-md-4 col-lg-3"
          >
            <q-card class="card-hover cursor-pointer" @click="selectCard(favorite.card)">
              <q-img
                v-if="favorite.card.front_image"
                :src="favorite.card.front_image"
                height="200px"
                class="card-image"
              >
                <div class="absolute-top-right q-pa-sm">
                  <q-btn
                    round
                    color="red"
                    icon="favorite"
                    size="sm"
                    @click.stop="removeFavorite(favorite)"
                  />
                </div>
                <div class="absolute-bottom bg-transparent">
                  <div class="text-h6">{{ favorite.card.title }}</div>
                </div>
              </q-img>
              
              <q-card-section v-else>
                <div class="row items-center">
                  <div class="col">
                    <div class="text-h6 text-primary">{{ favorite.card.title }}</div>
                    <div v-if="favorite.card.phrase" class="text-subtitle2 text-italic text-grey-7">
                      {{ favorite.card.phrase }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <q-btn
                      round
                      color="red"
                      icon="favorite"
                      size="sm"
                      @click.stop="removeFavorite(favorite)"
                    />
                  </div>
                </div>
              </q-card-section>

              <q-card-section class="q-pt-none">
                <p class="text-body2" style="max-height: 60px; overflow: hidden;">
                  {{ favorite.card.definition }}
                </p>
                <div class="text-caption text-grey-6">
                  Added {{ formatDate(favorite.created_at) }}
                </div>
              </q-card-section>

              <q-card-section v-if="favorite.card.tags && favorite.card.tags.length" class="q-pt-none">
                <q-chip
                  v-for="tag in favorite.card.tags.slice(0, 3)"
                  :key="tag.id"
                  size="sm"
                  color="primary"
                  text-color="white"
                  :label="tag.name"
                  class="q-mr-xs"
                />
                <span v-if="favorite.card.tags.length > 3" class="text-caption text-grey-6">
                  +{{ favorite.card.tags.length - 3 }} more
                </span>
              </q-card-section>

              <q-card-actions>
                <q-btn flat color="primary" label="View Details" />
                <q-space />
                <q-btn 
                  flat 
                  round 
                  color="primary" 
                  icon="share"
                  @click.stop="shareCard(favorite.card)"
                />
              </q-card-actions>
            </q-card>
          </div>
        </div>
      </div>
    </div>

    <!-- Card Detail Dialog -->
    <q-dialog v-model="showCardDialog" persistent>
      <q-card style="min-width: 400px; max-width: 600px;">
        <q-card-section v-if="selectedCard">
          <div class="text-h5 text-primary">{{ selectedCard.title }}</div>
          <div v-if="selectedCard.phrase" class="text-h6 text-italic text-grey-8 q-mt-sm">
            {{ selectedCard.phrase }}
          </div>
        </q-card-section>

        <q-card-section v-if="selectedCard">
          <div v-if="selectedCard.front_image" class="text-center q-mb-md">
            <q-img 
              :src="selectedCard.front_image" 
              style="max-width: 100%; max-height: 300px; border-radius: 8px;"
            />
          </div>

          <p class="text-body1">{{ selectedCard.definition }}</p>

          <div v-if="selectedCard.back_image" class="text-center q-mt-md">
            <q-img 
              :src="selectedCard.back_image" 
              style="max-width: 100%; max-height: 300px; border-radius: 8px;"
            />
          </div>

          <div v-if="selectedCard.tags && selectedCard.tags.length" class="q-mt-md">
            <q-chip
              v-for="tag in selectedCard.tags"
              :key="tag.id"
              color="primary"
              text-color="white"
              :label="tag.name"
              class="q-ma-xs"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn 
            flat 
            color="primary" 
            icon="share"
            label="Share"
            @click="shareCard(selectedCard)"
          />
          <q-btn flat label="Close" @click="showCardDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'

const $q = useQuasar()

// Reactive data
const favorites = ref([])
const loading = ref(false)
const showCardDialog = ref(false)
const selectedCard = ref(null)

// Mock data for now (will be replaced with actual API calls)
const loadFavorites = async () => {
  loading.value = true
  
  // Simulate API call
  setTimeout(() => {
    favorites.value = []
    loading.value = false
  }, 1000)
}

const removeFavorite = async (favorite) => {
  try {
    // Simulate API call
    const index = favorites.value.findIndex(f => f.id === favorite.id)
    if (index !== -1) {
      favorites.value.splice(index, 1)
    }
    
    $q.notify({
      type: 'positive',
      message: 'Removed from favorites'
    })
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to remove favorite'
    })
  }
}

const selectCard = (card) => {
  selectedCard.value = card
  showCardDialog.value = true
}

const shareCard = (card) => {
  if (navigator.share) {
    navigator.share({
      title: `Yoga Card: ${card.title}`,
      text: `${card.phrase ? card.phrase + ' - ' : ''}${card.definition}`,
      url: window.location.href
    })
  } else {
    const shareText = `Yoga Card: ${card.title}\n${card.phrase ? card.phrase + '\n' : ''}${card.definition}\n\n${window.location.href}`
    
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

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Lifecycle
onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.card-hover {
  transition: transform 0.2s, box-shadow 0.2s;
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.card-image {
  position: relative;
}
</style>
