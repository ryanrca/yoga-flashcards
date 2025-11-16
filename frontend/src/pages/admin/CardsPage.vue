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
                  @update:model-value="searchCards"
                  @keyup.enter="searchCards"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>

              <div class="col-12 col-md-3">
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
                  popup-content-class="admin-dropdown-menu"
                />
              </div>

              <div class="col-12 col-md-3">
                <q-select
                  v-model="sortBy"
                  :options="sortOptions"
                  label="Sort by"
                  outlined
                  @update:model-value="loadCards"
                  popup-content-class="admin-dropdown-menu"
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
                <q-avatar v-if="props.row.front_image" size="40px" rounded>
                  <img :src="props.row.front_image" alt="Card image">
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const router = useRouter()
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
const sortBy = ref('created_at')

// Pagination
const pagination = ref({
  sortBy: 'created_at',
  descending: true,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
})

// Delete dialog
const showDeleteDialog = ref(false)
const cardToDelete = ref(null)

// Sort options
const sortOptions = [
  { label: 'Created Date', value: 'created_at' },
  { label: 'Title', value: 'title' },
  { label: 'Updated Date', value: 'updated_at' }
]

// Table columns
const columns = [
  {
    name: 'title',
    required: true,
    label: 'Title',
    align: 'left',
    field: 'title',
    sortable: true
  },
  {
    name: 'definition',
    label: 'Definition',
    align: 'left',
    field: 'definition',
    sortable: false
  },
  {
    name: 'tags',
    label: 'Tags',
    align: 'left',
    field: 'tags',
    sortable: false
  },
  {
    name: 'created_at',
    label: 'Created',
    align: 'left',
    field: 'created_at',
    sortable: true
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center',
    field: 'actions',
    sortable: false
  }
]

// Methods
const loadCards = async () => {
  loading.value = true
  error.value = ''

  const searchParams = {
    page: pagination.value.page,
    page_size: pagination.value.rowsPerPage,
    search: searchQuery.value,
    ordering: pagination.value.descending ? `-${pagination.value.sortBy}` : pagination.value.sortBy
  }

  if (selectedTags.value && selectedTags.value.length > 0) {
    searchParams.tags = selectedTags.value.map(tag => tag.id).join(',')
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

const onRequest = (props) => {
  const { page, rowsPerPage, sortBy, descending } = props.pagination

  pagination.value.page = page
  pagination.value.rowsPerPage = rowsPerPage
  pagination.value.sortBy = sortBy
  pagination.value.descending = descending

  loadCards()
}

const searchCards = () => {
  pagination.value.page = 1
  loadCards()
}

const filterCards = () => {
  // Ensure selectedTags is always an array
  if (!selectedTags.value) {
    selectedTags.value = []
  }
  pagination.value.page = 1
  loadCards()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
  sortBy.value = 'created_at'
  pagination.value.page = 1
  pagination.value.sortBy = 'created_at'
  pagination.value.descending = true
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
    $q.notify({
      type: 'positive',
      message: 'Card deleted successfully'
    })
    loadCards()
  } else {
    $q.notify({
      type: 'negative',
      message: result.error || 'Failed to delete card'
    })
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

// Lifecycle
onMounted(() => {
  loadCards()
  loadTags()
})
</script>

<style>
/* Global style for admin dropdown menus */
.admin-dropdown-menu {
  background: linear-gradient(135deg,
    rgba(26, 11, 46, 0.98) 0%,
    rgba(74, 20, 140, 0.95) 100%
  ) !important;
  color: white !important;
  border: 1px solid rgba(255, 107, 53, 0.3) !important;
}

.admin-dropdown-menu .q-item {
  color: rgba(255, 255, 255, 0.9) !important;
}

.admin-dropdown-menu .q-item:hover {
  background: linear-gradient(90deg,
    rgba(255, 107, 53, 0.2) 0%,
    rgba(155, 77, 202, 0.2) 100%
  ) !important;
}

.admin-dropdown-menu .q-item__label {
  color: white !important;
}

.admin-dropdown-menu .q-checkbox__inner {
  color: white !important;
}

/* Definition column truncation */
.definition-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Style for table pagination dropdown (Records per page) */
.q-table__bottom .q-select__dialog {
  background: white !important;
  color: black !important;
}

.q-table__bottom .q-item {
  color: black !important;
}

.q-table__bottom .q-item:hover {
  background: rgba(155, 77, 202, 0.1) !important;
}

.q-table__bottom .q-item__label {
  color: black !important;
}
</style>
