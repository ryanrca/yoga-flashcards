<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12">
        <div class="text-h4 text-primary q-mb-md text-center">
          All Yoga Flashcards
        </div>
        
        <!-- Search and Filter Section -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="row q-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="searchQuery"
                  label="Search cards..."
                  outlined
                  clearable
                  @update:model-value="searchCards"
                  @keyup.enter="searchCards"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>
              
              <div class="col-12 col-md-4">
                <q-select
                  v-model="selectedTags"
                  :options="availableTags"
                  option-label="name"
                  option-value="id"
                  label="Filter by tags"
                  multiple
                  outlined
                  clearable
                  @update:model-value="filterCards"
                />
              </div>
              
              <div class="col-12 col-md-2">
                <q-btn
                  color="primary"
                  label="Clear Filters"
                  @click="clearFilters"
                  class="full-width"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Loading State -->
        <div v-if="loading" class="text-center q-py-lg">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md">Loading cards...</div>
        </div>

        <!-- Error State -->
        <q-banner v-else-if="error" type="negative" class="text-white q-mb-md">
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          {{ error }}
          <template v-slot:action>
            <q-btn flat color="white" label="Retry" @click="loadCards" />
          </template>
        </q-banner>

        <!-- Cards Grid -->
        <div v-else class="row q-gutter-md">
          <div 
            v-for="card in cards" 
            :key="card.id"
            class="col-12 col-sm-6 col-md-4 col-lg-3"
          >
            <q-card class="card-hover cursor-pointer" @click="selectCard(card)">
              <q-img
                v-if="card.front_image"
                :src="card.front_image"
                height="200px"
                class="card-image"
              >
                <div class="absolute-bottom bg-transparent">
                  <div class="text-h6">{{ card.title }}</div>
                </div>
              </q-img>
              
              <q-card-section v-else>
                <div class="text-h6 text-primary">{{ card.title }}</div>
                <div v-if="card.phrase" class="text-subtitle2 text-italic text-grey-7">
                  {{ card.phrase }}
                </div>
              </q-card-section>

              <q-card-section class="q-pt-none">
                <p class="text-body2" style="max-height: 60px; overflow: hidden;">
                  {{ card.definition }}
                </p>
              </q-card-section>

              <q-card-section v-if="card.tags && card.tags.length" class="q-pt-none">
                <q-chip
                  v-for="tag in card.tags.slice(0, 3)"
                  :key="tag.id"
                  size="sm"
                  color="primary"
                  text-color="white"
                  :label="tag.name"
                  class="q-mr-xs"
                />
                <span v-if="card.tags.length > 3" class="text-caption text-grey-6">
                  +{{ card.tags.length - 3 }} more
                </span>
              </q-card-section>

              <q-card-actions>
                <q-btn flat color="primary" label="View Details" />
                <q-space />
                <q-btn 
                  flat 
                  round 
                  color="red" 
                  icon="favorite_border"
                  @click.stop="toggleFavorite(card)"
                />
                <q-btn 
                  flat 
                  round 
                  color="primary" 
                  icon="share"
                  @click.stop="shareCard(card)"
                />
              </q-card-actions>
            </q-card>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!loading && !error && cards.length === 0" class="text-center q-py-lg">
          <q-icon name="search_off" size="4em" color="grey-5" />
          <div class="text-h6 text-grey-6 q-mt-md">No cards found</div>
          <p class="text-grey-6">Try adjusting your search or filter criteria</p>
        </div>

        <!-- Pagination -->
        <div v-if="cards.length > 0" class="row justify-center q-mt-lg">
          <q-pagination
            v-model="currentPage"
            :max="totalPages"
            :max-pages="7"
            boundary-links
            @update:model-value="changePage"
          />
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
            color="red" 
            icon="favorite_border"
            label="Add to Favorites"
            @click="toggleFavorite(selectedCard)"
          />
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
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()

// Reactive data
const cards = ref([])
const availableTags = ref([])
const loading = ref(false)
const error = ref('')

// Search and filter
const searchQuery = ref('')
const selectedTags = ref([])

// Pagination
const currentPage = ref(1)
const itemsPerPage = 12
const totalItems = ref(0)

// Dialog
const showCardDialog = ref(false)
const selectedCard = ref(null)

// Computed
const totalPages = computed(() => Math.ceil(totalItems.value / itemsPerPage))

// Methods
const loadCards = async (params = {}) => {
  loading.value = true
  error.value = ''

  const searchParams = {
    page: currentPage.value,
    page_size: itemsPerPage,
    search: searchQuery.value,
    ...params
  }

  if (selectedTags.value && selectedTags.value.length > 0) {
    searchParams.tags = selectedTags.value.map(tag => tag.id).join(',')
  }

  const result = await flashcardsStore.fetchCards(searchParams)

  if (result.success) {
    cards.value = result.data.results || result.data
    totalItems.value = result.data.count || cards.value.length
  } else {
    error.value = result.error || 'Failed to load cards'
  }

  loading.value = false
}

const loadTags = async () => {
  const result = await flashcardsStore.fetchTags()
  if (result.success) {
    availableTags.value = result.data
  }
}

const searchCards = () => {
  currentPage.value = 1
  loadCards()
}

const filterCards = () => {
  // Ensure selectedTags is always an array
  if (!selectedTags.value) {
    selectedTags.value = []
  }
  currentPage.value = 1
  loadCards()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
  currentPage.value = 1
  loadCards()
}

const changePage = (page) => {
  currentPage.value = page
  loadCards()
}

const selectCard = (card) => {
  selectedCard.value = card
  showCardDialog.value = true
}

const toggleFavorite = () => {
  $q.notify({
    type: 'info',
    message: 'Favorites feature coming soon!'
  })
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

// Lifecycle
onMounted(() => {
  loadCards()
  loadTags()
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
