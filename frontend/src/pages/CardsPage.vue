<template>
  <q-page padding>
    <div class="row q-mb-lg">
      <div class="col">
        <h4 class="q-my-none">Flashcards</h4>
      </div>
      <div class="col-auto">
        <q-btn 
          color="primary" 
          icon="add" 
          label="New Card" 
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <!-- Filters -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row q-gutter-md">
          <div class="col-md-2 col-sm-6 col-xs-12">
            <q-select
              v-model="enabledFilter"
              :options="enabledOptions"
              label="Status"
              outlined
              dense
              clearable
              @update:model-value="onFilterChange"
            />
          </div>
          
          <div class="col-md-4 col-sm-12 col-xs-12">
            <q-select
              v-model="selectedTags"
              :options="tagOptions"
              label="Tags"
              outlined
              dense
              multiple
              clearable
              use-chips
              @update:model-value="onFilterChange"
            />
          </div>
          
          <div class="col-auto">
            <q-btn 
              flat 
              icon="clear" 
              label="Clear" 
              @click="clearFilters"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Cards Table -->
    <q-table
      :rows="cardStore.cards"
      :columns="columns"
      row-key="id"
      :loading="cardStore.loading"
      v-model:pagination="paginationData"
      @request="onRequest"
      server-pagination
      :rows-per-page-options="[5, 10, 20, 50]"
    >
      <template v-slot:top-right>
        <q-input
          borderless
          dense
          debounce="300"
          v-model="searchInput"
          placeholder="Search"
          @update:model-value="onSearch"
        >
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
      <template v-slot:body-cell-title="props">
        <q-td :props="props">
          <router-link 
            :to="`/cards/${props.row.id}`" 
            class="text-primary text-decoration-none"
          >
            {{ props.value }}
          </router-link>
        </q-td>
      </template>

      <template v-slot:body-cell-enabled="props">
        <q-td :props="props">
          <q-chip
            :color="props.value ? 'positive' : 'negative'"
            :label="props.value ? 'Enabled' : 'Disabled'"
            size="sm"
          />
        </q-td>
      </template>

      <template v-slot:body-cell-tags="props">
        <q-td :props="props">
          <q-chip
            v-for="tag in props.value"
            :key="tag.id"
            :label="tag.name"
            size="sm"
            color="grey-4"
            text-color="dark"
            class="q-mr-xs"
          />
        </q-td>
      </template>

      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            round
            dense
            icon="edit"
            @click="editCard(props.row)"
          />
          <q-btn
            flat
            round
            dense
            icon="delete"
            @click="confirmDelete(props.row)"
          />
        </q-td>
      </template>
    </q-table>

    <!-- Create/Edit Card Dialog -->
    <card-form-dialog
      v-model="showCreateDialog"
      :card="editingCard"
      @saved="onCardSaved"
    />
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useCardStore } from 'src/stores/cards'
import { useTagStore } from 'src/stores/tags'
import { useQuasar } from 'quasar'
import CardFormDialog from 'src/components/CardFormDialog.vue'

export default defineComponent({
  name: 'CardsPage',
  
  components: {
    CardFormDialog
  },

  setup() {
    const cardStore = useCardStore()
    const tagStore = useTagStore()
    const $q = useQuasar()
    
    const showCreateDialog = ref(false)
    const editingCard = ref(null)
    const searchInput = ref('')
    const enabledFilter = ref(null)
    const selectedTags = ref([])

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
        name: 'phrase',
        label: 'Phrase',
        align: 'left',
        field: 'phrase',
        sortable: true
      },
      {
        name: 'enabled',
        label: 'Status',
        align: 'center',
        field: 'enabled',
        sortable: true
      },
      {
        name: 'views',
        label: 'Views',
        align: 'center',
        field: 'views',
        sortable: true
      },
      {
        name: 'tags',
        label: 'Tags',
        align: 'left',
        field: 'tags'
      },
      {
        name: 'created_by_username',
        label: 'Created By',
        align: 'left',
        field: 'created_by_username',
        sortable: true
      },
      {
        name: 'updated_at',
        label: 'Updated',
        align: 'left',
        field: 'updated_at',
        sortable: true,
        format: (val) => new Date(val).toLocaleDateString()
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center'
      }
    ]

    const enabledOptions = [
      { label: 'Enabled', value: true },
      { label: 'Disabled', value: false }
    ]

    const tagOptions = computed(() => 
      tagStore.tags.map(tag => ({
        label: tag.name,
        value: tag.id
      }))
    )

    const paginationData = ref({
      page: 1,
      rowsPerPage: 20,
      rowsNumber: 0,
      sortBy: 'updated_at',
      descending: true
    })

    const onRequest = async (props) => {
      const { page, rowsPerPage, sortBy, descending } = props.pagination
      
      // Update local pagination immediately
      paginationData.value = {
        page,
        rowsPerPage,
        sortBy: sortBy || 'updated_at',
        descending,
        rowsNumber: paginationData.value.rowsNumber // Keep existing rowsNumber until updated
      }
      
      // Update store pagination
      cardStore.pagination.page = page
      cardStore.pagination.rowsPerPage = rowsPerPage
      cardStore.sortBy = sortBy || 'updated_at'
      cardStore.descending = descending
      
      // Fetch cards with new parameters
      await cardStore.fetchCards(props)
      
      // Update rowsNumber after fetch
      paginationData.value.rowsNumber = cardStore.pagination.rowsNumber
    }

    const onSearch = () => {
      cardStore.setFilter({ search: searchInput.value })
      paginationData.value.page = 1 // Reset to first page when searching
      // Trigger onRequest to refresh data with current pagination settings
      onRequest({ pagination: paginationData.value })
    }

    const onFilterChange = () => {
      cardStore.setFilter({
        enabled: enabledFilter.value?.value ?? null,
        tags: selectedTags.value.map(tag => tag.value)
      })
      paginationData.value.page = 1 // Reset to first page when filtering
      // Trigger onRequest to refresh data with current pagination settings
      onRequest({ pagination: paginationData.value })
    }

    const clearFilters = () => {
      searchInput.value = ''
      enabledFilter.value = null
      selectedTags.value = []
      cardStore.clearFilter()
      paginationData.value.page = 1 // Reset to first page
      // Trigger onRequest to refresh data with current pagination settings
      onRequest({ pagination: paginationData.value })
    }

    const editCard = (card) => {
      editingCard.value = card
      showCreateDialog.value = true
    }

    const confirmDelete = (card) => {
      $q.dialog({
        title: 'Confirm Delete',
        message: `Are you sure you want to delete "${card.title}"?`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          await cardStore.deleteCard(card.id)
          $q.notify({
            color: 'positive',
            message: 'Card deleted successfully'
          })
        } catch (error) {
          $q.notify({
            color: 'negative',
            message: 'Failed to delete card'
          })
        }
      })
    }

    const onCardSaved = () => {
      showCreateDialog.value = false
      editingCard.value = null
      // Refresh the cards list after saving using onRequest
      onRequest({ pagination: paginationData.value })
    }

    onMounted(async () => {
      // Initialize pagination from store
      paginationData.value = {
        page: cardStore.pagination.page,
        rowsPerPage: cardStore.pagination.rowsPerPage,
        rowsNumber: cardStore.pagination.rowsNumber,
        sortBy: cardStore.sortBy,
        descending: cardStore.descending
      }
      
      // Fetch tags and cards
      await tagStore.fetchTags()
      await onRequest({ pagination: paginationData.value })
    })

    return {
      cardStore,
      showCreateDialog,
      editingCard,
      searchInput,
      enabledFilter,
      selectedTags,
      columns,
      enabledOptions,
      tagOptions,
      paginationData,
      onRequest,
      onSearch,
      onFilterChange,
      clearFilters,
      editCard,
      confirmDelete,
      onCardSaved
    }
  }
})
</script>
