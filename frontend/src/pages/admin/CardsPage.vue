<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12">
        <div class="row items-center q-mb-lg">
          <div class="col">
            <div class="text-h4 text-primary">Manage Flashcards</div>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              label="Add New Card"
              icon="add_circle"
              @click="$router.push('/admin/cards/new')"
            />
          </div>
        </div>

        <!-- Search and Filter Section -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="row q-gutter-md">
              <div class="col-12 col-md-4">
                <q-input
                  v-model="searchQuery"
                  label="Search cards..."
                  outlined
                  clearable
                  @update:model-value="onSearchInput"
                  @keyup.enter="applyFilters"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>

              <div class="col-12 col-md-3">
                <q-select
                  v-model="selectedTagIds"
                  :options="availableTags"
                  option-label="name"
                  option-value="id"
                  emit-value
                  map-options
                  label="Filter by tags"
                  multiple
                  outlined
                  clearable
                  @update:model-value="onTagsChange"
                  popup-content-class="admin-dropdown-menu"
                />
              </div>

              <div class="col-12 col-md-3">
                <q-select
                  v-model="sortBy"
                  :options="sortOptions"
                  emit-value
                  map-options
                  label="Sort by"
                  outlined
                  @update:model-value="onSortChange"
                  popup-content-class="admin-dropdown-menu"
                />
              </div>

              <div class="col-12 col-md-2">
                <q-btn
                  color="primary"
                  label="Clear Filters"
                  :disable="!hasFilters"
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

        <!-- Cards Table -->
        <q-table
          v-else
          :rows="cards"
          :columns="columns"
          :loading="loading"
          :pagination="pagination"
          @request="onRequest"
          row-key="id"
          flat
          bordered
        >
          <template v-slot:body-cell-title="props">
            <q-td :props="props">
              <div class="row items-center q-gutter-sm">
                <!--
                  An accepted AI image is the card's front for everyone outside
                  the admin area, so it belongs in this thumbnail too. An
                  uploaded front_image still wins: it is an explicit choice.
                -->
                <q-avatar v-if="cardImage(props.row)" size="40px" rounded>
                  <img :src="cardImage(props.row)" alt="">
                </q-avatar>
                <q-avatar v-else color="grey-4" text-color="grey-8" icon="view_cards" size="40px" />
                <div>
                  <div class="text-weight-medium">{{ props.value }}</div>
                  <div v-if="props.row.phrase" class="text-caption text-grey-6 text-italic">
                    {{ props.row.phrase }}
                  </div>
                </div>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-definition="props">
            <q-td :props="props">
              <div class="definition-cell">
                {{ props.value }}
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-tags="props">
            <q-td :props="props">
              <q-chip
                v-for="tag in props.value.slice(0, 2)"
                :key="tag.id"
                size="sm"
                color="primary"
                text-color="white"
                :label="tag.name"
                class="q-mr-xs"
              />
              <q-chip
                v-if="props.value.length > 2"
                size="sm"
                color="grey-4"
                text-color="grey-8"
                :label="`+${props.value.length - 2}`"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-created_at="props">
            <q-td :props="props">
              {{ formatDate(props.value) }}
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <div class="q-gutter-xs">
                <q-btn
                  flat
                  round
                  color="primary"
                  icon="visibility"
                  @click="viewCard(props.row)"
                  size="sm"
                >
                  <q-tooltip>View Details</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  round
                  color="green"
                  icon="edit"
                  @click="editCard(props.row)"
                  size="sm"
                >
                  <q-tooltip>Edit Card</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  round
                  color="red"
                  icon="delete"
                  @click="confirmDelete(props.row)"
                  size="sm"
                >
                  <q-tooltip>Delete Card</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete "{{ cardToDelete?.title }}"?
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" />
          <q-btn flat label="Delete" color="negative" @click="deleteCard" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()

// Where the filter selection is remembered between visits. The URL is the
// primary home for it -- that is what makes the browser back button restore
// the view -- and this is the fallback for arriving with a bare /admin/cards.
const STORAGE_KEY = 'yoga-admin-cards-view'

const DEFAULTS = { sort: 'created_at', descending: true, page: 1, size: 10 }

// Reactive data
const cards = ref([])
const availableTags = ref([])
const loading = ref(false)
const error = ref('')

// Search and filter. Tags are held as ids rather than tag objects so the state
// can be restored from a URL before the tag list has finished loading.
const searchQuery = ref('')
const selectedTagIds = ref([])
const sortBy = ref(DEFAULTS.sort)

const pagination = ref({
  sortBy: DEFAULTS.sort,
  descending: DEFAULTS.descending,
  page: DEFAULTS.page,
  rowsPerPage: DEFAULTS.size,
  rowsNumber: 0
})

// Delete dialog
const showDeleteDialog = ref(false)
const cardToDelete = ref(null)

const sortOptions = [
  { label: 'Created Date', value: 'created_at' },
  { label: 'Title', value: 'title' },
  { label: 'Updated Date', value: 'updated_at' }
]

const columns = [
  { name: 'title', required: true, label: 'Title', align: 'left', field: 'title', sortable: true },
  { name: 'definition', label: 'Definition', align: 'left', field: 'definition', sortable: false },
  { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
  { name: 'created_at', label: 'Created', align: 'left', field: 'created_at', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center', field: 'actions', sortable: false }
]

// `clearable` on the tag select writes null, not an empty array, and this
// recomputes the moment v-model lands -- before onTagsChange can normalise it.
// So every read of selectedTagIds has to tolerate null.
const hasFilters = computed(() =>
  Boolean(searchQuery.value) ||
  (selectedTagIds.value?.length ?? 0) > 0 ||
  sortBy.value !== DEFAULTS.sort ||
  pagination.value.descending !== DEFAULTS.descending
)

// An accepted AI image is the card front everywhere outside the admin area.
// An explicitly uploaded image still takes precedence over a generated one.
// One field now: a card points at its media, whoever made it. The fallback this
// used to carry existed only because AI images lived somewhere uploads did not.
const cardImage = (card) => card.front_image || null

// ---- filter state <-> URL ---------------------------------------------------

// Only non-default values go in the query, so a clean view has a clean URL.
const toQuery = () => {
  const q = {}
  if (searchQuery.value) q.search = searchQuery.value
  if (selectedTagIds.value?.length) q.tags = selectedTagIds.value.join(',')
  if (pagination.value.sortBy !== DEFAULTS.sort) q.sort = pagination.value.sortBy
  if (pagination.value.descending !== DEFAULTS.descending) q.dir = 'asc'
  if (pagination.value.page !== DEFAULTS.page) q.page = String(pagination.value.page)
  if (pagination.value.rowsPerPage !== DEFAULTS.size) q.size = String(pagination.value.rowsPerPage)
  return q
}

const fromQuery = (src) => {
  searchQuery.value = src.search || ''

  // TagsPage links here with a single ?tags=<id>; the filter also serialises a
  // comma separated list. Accept both.
  const raw = src.tags
  selectedTagIds.value = raw
    ? String(raw).split(',').map(Number).filter((n) => Number.isInteger(n) && n > 0)
    : []

  pagination.value.sortBy = src.sort || DEFAULTS.sort
  sortBy.value = pagination.value.sortBy
  pagination.value.descending = src.dir !== 'asc'
  pagination.value.page = Number(src.page) > 0 ? Number(src.page) : DEFAULTS.page
  pagination.value.rowsPerPage = Number(src.size) > 0 ? Number(src.size) : DEFAULTS.size
}

function readStored () {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeStored (q) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(q))
  } catch {
    // Remembering the view is a convenience; never let storage break the page.
  }
}

// `replace` rather than `push`: a filter change should update the current
// history entry, not add one. Otherwise going Back would step through every
// intermediate filter state instead of leaving the page.
const syncUrl = () => {
  const q = toQuery()
  writeStored(q)
  router.replace({ name: 'admin-cards', query: q }).catch(() => {})
}

// ---- data ------------------------------------------------------------------

const loadCards = async () => {
  loading.value = true
  error.value = ''

  const searchParams = {
    page: pagination.value.page,
    page_size: pagination.value.rowsPerPage,
    search: searchQuery.value,
    ordering: pagination.value.descending
      ? `-${pagination.value.sortBy}`
      : pagination.value.sortBy
  }

  if (selectedTagIds.value?.length) {
    searchParams.tags = selectedTagIds.value.join(',')
  }

  const result = await flashcardsStore.fetchCards(searchParams)

  if (result.success) {
    cards.value = result.data.results || result.data
    pagination.value.rowsNumber = result.data.count || cards.value.length
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

const applyFilters = () => {
  pagination.value.page = 1
  syncUrl()
  loadCards()
}

// The search box fired one request per keystroke. Wait for a pause instead.
let searchTimer = null
const onSearchInput = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 350)
}

const onTagsChange = () => {
  // `clearable` hands back null rather than an empty array.
  if (!selectedTagIds.value) selectedTagIds.value = []
  applyFilters()
}

const onSortChange = (value) => {
  // The Sort by control used to write a ref that nothing read, so choosing a
  // sort did nothing. It drives the pagination state the query is built from.
  pagination.value.sortBy = value
  applyFilters()
}

const onRequest = (props) => {
  const { page, rowsPerPage, sortBy: tableSortBy, descending } = props.pagination

  pagination.value.page = page
  pagination.value.rowsPerPage = rowsPerPage
  pagination.value.sortBy = tableSortBy
  pagination.value.descending = descending
  sortBy.value = tableSortBy

  syncUrl()
  loadCards()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedTagIds.value = []
  sortBy.value = DEFAULTS.sort
  pagination.value.sortBy = DEFAULTS.sort
  pagination.value.descending = DEFAULTS.descending
  pagination.value.page = DEFAULTS.page
  syncUrl()
  loadCards()
}

const viewCard = (card) => {
  router.push(`/admin/cards/${card.id}`)
}

const editCard = (card) => {
  router.push(`/admin/cards/${card.id}/edit`)
}

const confirmDelete = (card) => {
  cardToDelete.value = card
  showDeleteDialog.value = true
}

const deleteCard = async () => {
  if (!cardToDelete.value) return

  const result = await flashcardsStore.deleteCard(cardToDelete.value.id)

  if (result.success) {
    $q.notify({ type: 'positive', message: 'Card deleted successfully' })
    loadCards()
  } else {
    $q.notify({ type: 'negative', message: result.error || 'Failed to delete card' })
  }

  showDeleteDialog.value = false
  cardToDelete.value = null
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(() => {
  // A query in the URL wins: that is the back button restoring a previous
  // view, or TagsPage linking in with ?tags=<id>. With a bare /admin/cards,
  // fall back to whatever was last used and put it back in the URL, so Back
  // behaves the same on the next hop.
  const hasQuery = Object.keys(route.query).length > 0
  fromQuery(hasQuery ? route.query : (readStored() || {}))
  if (!hasQuery) syncUrl()

  loadTags()
  loadCards()
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
})
</script>

<!--
  The .admin-dropdown-menu rules that used to live here were UNSCOPED and
  marked !important, so they leaked app-wide and would have overridden any
  theme. The same block was copied into four admin pages. It is now themed
  once in app.scss alongside the other popups, keyed off the same
  .admin-dropdown-menu class these pages still pass as content-class.

  The .q-table__bottom overrides forcing white-on-black pagination went with
  them: they existed to claw pagination text back from the psychedelic theme,
  and app.scss now colours it with --ink-soft for whichever theme is active.
-->

<style scoped>
/* Definition column truncation */
.definition-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
