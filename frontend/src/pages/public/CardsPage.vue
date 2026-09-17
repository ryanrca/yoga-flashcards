<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12">
        <div class="text-h4 text-primary q-mb-md text-center">
          {{ favoritesMode ? 'My Favorite Cards' : 'All Yoga Flashcards' }}
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
                  popup-content-class="tag-filter-dropdown"
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
        <div v-else class="row q-gutter-md justify-center">
          <div
            v-for="card in cards"
            :key="card.id"
            class="col-12 col-sm-6 col-md-4 col-lg-3"
          >
            <q-card class="card-hover cursor-pointer card-fixed-height" @click="selectCard(card)">
              <q-img
                v-if="card.front_image"
                :src="card.front_image"
                height="200px"
                class="card-image"
              >
                <div class="absolute-bottom bg-transparent">
                  <div class="text-h6 ellipsis">{{ card.title }}</div>
                </div>
              </q-img>

              <q-card-section v-else class="card-header-section">
                <div class="text-h6 text-primary ellipsis">{{ card.title }}</div>
                <div v-if="card.phrase" class="text-subtitle2 text-italic text-grey-7 ellipsis card-phrase">
                  {{ card.phrase }}
                </div>
              </q-card-section>

              <!--
                The short answer, not the definition. Definitions run to a median
                of 239 characters, so two clamped lines of one told you almost
                nothing; short answers median 49 and fit whole.

                Falls back to the definition because short_answer is optional on
                the model and curator-editable - every seeded card has one today,
                but a card created without one would otherwise render blank.
              -->
              <q-card-section class="card-summary-section">
                <div class="text-body2 card-summary-text">
                  {{ card.short_answer || card.definition }}
                </div>
              </q-card-section>

              <q-card-section v-if="card.tags && card.tags.length" class="card-tags-section">
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

              <q-card-actions class="card-actions-section">
                <q-btn flat color="primary" label="View Details" />
                <q-space />
                <q-btn
                  flat
                  round
                  color="red"
                  :icon="card.is_favorited ? 'favorite' : 'favorite_border'"
                  :aria-label="card.is_favorited ? 'Remove from favorites' : 'Add to favorites'"
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
        <!--
          Two different empty states, because they mean different things. An
          empty favourites list is a new user with nothing saved yet, and the
          useful next step is to go and find some cards. An empty card list is
          a search that matched nothing.
        -->
        <div v-if="!loading && !error && cards.length === 0" class="text-center q-py-lg">
          <template v-if="favoritesMode && !searchQuery && !selectedTags.length">
            <q-icon name="favorite_border" size="4em" color="grey-5" />
            <div class="text-h6 text-grey-6 q-mt-md">No favorites yet</div>
            <p class="text-grey-6 q-mb-lg">
              Tap the heart on any card to save it here.
            </p>
            <q-btn color="primary" label="Browse Cards" @click="$router.push('/cards')" />
          </template>
          <template v-else>
            <q-icon name="search_off" size="4em" color="grey-5" />
            <div class="text-h6 text-grey-6 q-mt-md">No cards found</div>
            <p class="text-grey-6">Try adjusting your search or filter criteria</p>
          </template>
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
    <q-dialog v-model="showCardDialog">
      <q-card class="card-detail-dialog">
        <q-card-section v-if="selectedCard">
          <div class="text-h5 text-primary">{{ selectedCard.title }}</div>
          <div v-if="selectedCard.phrase" class="text-h6 text-italic text-grey-8 q-mt-sm">
            {{ selectedCard.phrase }}
          </div>
        </q-card-section>

        <q-card-section v-if="selectedCard" class="q-pt-none">
            <div v-if="selectedCard" class="hero-container" v-ripple>
              <q-img
                v-if="selectedCard.front_image"
                :src="selectedCard.front_image"
                class="hero-image"
                :ratio="16/9"
                fit="cover"
              >
                <div class="absolute-bottom hero-overlay">
                  <div class="text-h5 text-white text-weight-bold">{{ selectedCard.title }}</div>
                  <div v-if="selectedCard.phrase" class="text-subtitle2 text-white text-italic">
                    {{ selectedCard.phrase }}
                  </div>
                </div>
              </q-img>
              <div v-else class="hero-placeholder">
                <div class="text-h5 text-primary">{{ selectedCard.title }}</div>
                <div v-if="selectedCard.phrase" class="text-subtitle2 text-italic text-grey-7">
                  {{ selectedCard.phrase }}
                </div>
              </div>
            </div>

          <!--
            Short answer above the full definition: it is the summary you want
            first, and it matches the order already used on /daily. The
            definition gains a heading to match, since it was previously the
            only unlabelled block on the card.
          -->
          <div v-if="selectedCard.short_answer" class="q-mt-md">
            <div class="text-subtitle1 text-weight-medium text-primary">Short Answer:</div>
            <div class="text-body2 q-mt-xs">{{ selectedCard.short_answer }}</div>
          </div>

          <div class="q-mt-md">
            <div class="text-subtitle1 text-weight-medium text-primary">Full Definition:</div>
            <div class="text-body1 definition-text q-mt-xs">{{ selectedCard.definition }}</div>
          </div>

          <div v-if="selectedCard.back_image" class="text-center q-mt-md">
            <q-img
              :src="selectedCard.back_image"
              class="dialog-image"
              fit="contain"
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

        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn
            flat
            color="red"
            :icon="selectedCard?.is_favorited ? 'favorite' : 'favorite_border'"
            :label="selectedCard?.is_favorited ? 'Remove from Favorites' : 'Add to Favorites'"
            @click="toggleFavorite(selectedCard)"
          />
          <q-btn
            flat
            color="primary"
            icon="share"
            label="Share"
            @click="shareCard(selectedCard)"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const $q = useQuasar()
const route = useRoute()
const flashcardsStore = useFlashcardsStore()

/*
  /favorites is this same page with the list narrowed server-side, which is why
  there is no second component: search, tag filtering, pagination and the card
  dialog are identical, and the only differences are the heading, the empty
  state and what an unfavourite does to the list you are looking at.
*/
const favoritesMode = computed(() => route.name === 'favorites')

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

  // Narrows the same endpoint rather than calling a different one, so every
  // filter above keeps working inside the favourites list.
  if (favoritesMode.value) {
    searchParams.favorites = 'true'
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

const toggleFavorite = async (card) => {
  if (!card) return

  const result = await flashcardsStore.toggleFavorite(card.id)

  if (!result.success) {
    $q.notify({ type: 'negative', message: result.error || 'Failed to update favorites' })
    return
  }

  const { favorited, favorite_count: favoriteCount } = result.data

  // The server is the authority on both values; the grid row and the dialog can
  // be two references to the same object or two different ones depending on how
  // the card was opened, so update whichever exist.
  card.is_favorited = favorited
  card.favorite_count = favoriteCount
  if (selectedCard.value && selectedCard.value.id === card.id) {
    selectedCard.value.is_favorited = favorited
    selectedCard.value.favorite_count = favoriteCount
  }

  $q.notify({
    type: favorited ? 'positive' : 'info',
    message: favorited ? 'Added to favorites' : 'Removed from favorites'
  })

  // On /favorites an unfavourited card no longer belongs in the list you are
  // looking at, so it leaves immediately rather than lingering as an empty
  // heart. Reload instead when that empties the page, so pagination stays
  // honest - otherwise removing the last card on page 3 leaves you staring at
  // nothing with no way back.
  if (favoritesMode.value && !favorited) {
    const index = cards.value.findIndex(c => c.id === card.id)
    if (index !== -1) {
      cards.value.splice(index, 1)
      totalItems.value = Math.max(0, totalItems.value - 1)
    }
    if (selectedCard.value && selectedCard.value.id === card.id) {
      showCardDialog.value = false
    }
    if (cards.value.length === 0 && currentPage.value > 1) {
      currentPage.value -= 1
      loadCards()
    }
  }
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

/*
  /cards and /favorites render the same component, so the router reuses the
  instance and onMounted does NOT fire again when moving between them. Without
  this watch, clicking Favorites while on the card list would leave the old,
  unfiltered results on screen under the new heading.
*/
watch(favoritesMode, () => {
  currentPage.value = 1
  searchQuery.value = ''
  selectedTags.value = []
  loadCards()
})

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

/* Raised from 250px to give the header the room the Devanagari needs. */
.card-fixed-height {
  height: 272px;
  display: flex;
  flex-direction: column;
}

/*
  Was a hard 60px, which is why the Sanskrit was cut off along the bottom: a
  text-h6 title and a text-subtitle2 phrase plus the section's own padding need
  roughly 83px, so the phrase was clipped vertically. Not a horizontal problem -
  the longest phrase in the deck is 13 characters, well inside the ellipsis.
*/
.card-header-section {
  min-height: 78px;
  max-height: 78px;
  overflow: hidden;
}

/*
  Devanagari carries vowel marks above the headstroke and below the baseline, so
  it needs more leading than the Latin default to sit inside its line box.
*/
.card-phrase {
  line-height: 1.9;
}

/* Renamed from card-definition-*: this shows the short answer now. */
.card-summary-section {
  flex: 1;
  min-height: 64px;
  max-height: 64px;
  overflow: hidden;
  padding-top: 8px !important;
}

.card-summary-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
}

.card-tags-section {
  min-height: 48px;
  max-height: 48px;
  overflow: hidden;
  padding-top: 0 !important;
  padding-bottom: 8px !important;
}

.card-actions-section {
  margin-top: auto;
}

.card-detail-dialog {
  min-width: 400px;
  max-width: 700px;
  width: 90vw;
  overflow: hidden;
}

.hero-container {
  overflow: hidden;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.hero-image {
  width: 100%;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.hero-overlay {
  background: linear-gradient(0deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 60%, transparent 100%);
  padding: 16px;
}

.hero-placeholder {
  padding: 24px;
}

.dialog-image {
  max-width: 100%;
  max-height: 400px;
  width: auto;
  height: auto;
  border-radius: 8px;
}

.definition-text {
  word-wrap: break-word;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
</style>

<!--
  The tag filter dropdown used to be styled by an UNSCOPED <style> block here,
  which painted it psychedelic purple with !important and leaked those rules
  app-wide - it would have survived any retheme. It is now themed centrally in
  app.scss alongside the other popups, via the same .tag-filter-dropdown class
  this page still passes as popup-content-class.
-->
