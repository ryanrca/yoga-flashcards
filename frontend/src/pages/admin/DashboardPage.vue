<template>
  <q-page class="q-pa-md">
    <div class="row q-gutter-lg">
      <!-- Welcome Section -->
      <div class="col-12">
        <q-card class="bg-primary text-white">
          <q-card-section>
            <div class="text-h4">Welcome to Admin Dashboard</div>
            <div class="text-subtitle1">
              Manage your yoga flashcards collection
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Stats Cards -->
      <div class="col-12 col-md-3">
        <q-card>
          <q-card-section class="text-center">
            <q-icon name="view_cards" size="3rem" color="primary" />
            <div class="text-h4 text-primary q-mt-sm">{{ stats.totalCards }}</div>
            <div class="text-caption text-grey-6">Total Cards</div>
          </q-card-section>
          <q-card-actions>
            <q-btn 
              flat 
              color="primary" 
              label="Manage Cards" 
              @click="$router.push('/admin/cards')"
              class="full-width"
            />
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card>
          <q-card-section class="text-center">
            <q-icon name="local_offer" size="3rem" color="green" />
            <div class="text-h4 text-green q-mt-sm">{{ stats.totalTags }}</div>
            <div class="text-caption text-grey-6">Tags</div>
          </q-card-section>
          <q-card-actions>
            <q-btn 
              flat 
              color="green" 
              label="Manage Tags" 
              @click="$router.push('/admin/tags')"
              class="full-width"
            />
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card>
          <q-card-section class="text-center">
            <q-icon name="people" size="3rem" color="orange" />
            <div class="text-h4 text-orange q-mt-sm">{{ stats.totalUsers }}</div>
            <div class="text-caption text-grey-6">Users</div>
          </q-card-section>
          <q-card-actions>
            <q-btn 
              v-if="authStore.isAdmin"
              flat 
              color="orange" 
              label="Manage Users" 
              @click="$router.push('/admin/users')"
              class="full-width"
            />
            <q-btn 
              v-else
              flat 
              color="orange" 
              label="Admin Only" 
              disable
              class="full-width"
            />
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card>
          <q-card-section class="text-center">
            <q-icon name="today" size="3rem" color="purple" />
            <div class="text-h6 text-purple q-mt-sm">Daily Card</div>
            <div class="text-caption text-grey-6" v-if="dailyCard">
              {{ dailyCard.title }}
            </div>
          </q-card-section>
          <q-card-actions>
            <q-btn 
              flat 
              color="purple" 
              label="View Daily" 
              @click="$router.push('/daily')"
              class="full-width"
            />
          </q-card-actions>
        </q-card>
      </div>

      <!-- Quick Actions -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h5 q-mb-md">Quick Actions</div>
            <div class="row q-gutter-sm">
              <q-btn
                color="primary"
                label="Add New Card"
                icon="add_circle"
                @click="$router.push('/admin/cards/new')"
              />
              <q-btn
                color="green"
                label="Create Tag"
                icon="local_offer"
                @click="showCreateTag = true"
              />
              <q-btn
                color="blue"
                label="Import CSV"
                icon="upload_file"
                @click="showImportDialog = true"
              />
              <q-btn
                color="orange"
                label="View Public Site"
                icon="public"
                @click="$router.push('/')"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Activity -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Cards</div>
          </q-card-section>
          <q-list>
            <q-item 
              v-for="card in recentCards" 
              :key="card.id"
              clickable
              @click="$router.push(`/admin/cards/${card.id}`)"
            >
              <q-item-section avatar>
                <q-avatar v-if="card.front_image" rounded>
                  <img :src="card.front_image" alt="Card image">
                </q-avatar>
                <q-avatar v-else color="primary" text-color="white" icon="view_cards" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ card.title }}</q-item-label>
                <q-item-label caption>{{ card.phrase || 'No Sanskrit phrase' }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-btn flat round icon="edit" @click.stop="$router.push(`/admin/cards/${card.id}/edit`)" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <!-- System Info -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">System Information</div>
          </q-card-section>
          <q-card-section>
            <div class="row q-gutter-sm">
              <div class="col-12">
                <q-linear-progress 
                  :value="stats.totalCards / 100" 
                  color="primary" 
                  class="q-mt-sm"
                />
                <div class="text-caption">Cards Progress ({{ stats.totalCards }}/100 goal)</div>
              </div>
              <div class="col-12 q-mt-md">
                <div class="text-body2">
                  <strong>Last Updated:</strong> {{ new Date().toLocaleDateString() }}
                </div>
                <div class="text-body2">
                  <strong>Your Role:</strong> {{ authStore.user?.role || 'Unknown' }}
                </div>
                <div class="text-body2">
                  <strong>Version:</strong> 1.0.0
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Create Tag Dialog -->
    <q-dialog v-model="showCreateTag">
      <q-card style="min-width: 400px;">
        <q-card-section>
          <div class="text-h6">Create New Tag</div>
        </q-card-section>
        <q-card-section>
          <q-input
            v-model="newTagName"
            label="Tag Name"
            outlined
            autofocus
            @keyup.enter="createTag"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showCreateTag = false" />
          <q-btn color="primary" label="Create" @click="createTag" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Import Dialog -->
    <q-dialog v-model="showImportDialog">
      <q-card style="min-width: 400px;">
        <q-card-section>
          <div class="text-h6">Import Cards from CSV</div>
        </q-card-section>
        <q-card-section>
          <q-file
            v-model="csvFile"
            label="Select CSV file"
            outlined
            accept=".csv"
          />
          <div class="text-caption text-grey-6 q-mt-sm">
            CSV format: title, phrase, definition, tags
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showImportDialog = false" />
          <q-btn color="primary" label="Import" @click="importCSV" />
        </q-card-actions>
      </q-card>
    </q-dialog>
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

// Reactive data
const stats = ref({
  totalCards: 0,
  totalTags: 0,
  totalUsers: 0
})
const dailyCard = ref(null)
const recentCards = ref([])

// Dialogs
const showCreateTag = ref(false)
const showImportDialog = ref(false)
const newTagName = ref('')
const csvFile = ref(null)

// Methods
const loadDashboardData = async () => {
  try {
    // Load stats
    const cardsResult = await flashcardsStore.fetchCards({ page_size: 5 })
    if (cardsResult.success) {
      stats.value.totalCards = cardsResult.data.count || cardsResult.data.length
      recentCards.value = cardsResult.data.results || cardsResult.data.slice(0, 5)
    }

    // Load tags
    const tagsResult = await flashcardsStore.fetchTags()
    if (tagsResult.success) {
      stats.value.totalTags = tagsResult.data.length
    }

    // Load daily card
    const dailyResult = await flashcardsStore.fetchDailyCard()
    if (dailyResult.success) {
      dailyCard.value = dailyResult.data
    }

    // Mock users count (would come from a users API)
    stats.value.totalUsers = 25
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  }
}

const createTag = async () => {
  if (!newTagName.value.trim()) return

  const result = await flashcardsStore.createTag({ name: newTagName.value })
  
  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Tag created successfully!'
    })
    stats.value.totalTags++
    newTagName.value = ''
    showCreateTag.value = false
  } else {
    $q.notify({
      type: 'negative',
      message: result.error || 'Failed to create tag'
    })
  }
}

const importCSV = () => {
  if (!csvFile.value) {
    $q.notify({
      type: 'negative',
      message: 'Please select a CSV file'
    })
    return
  }

  // This would implement actual CSV import
  $q.notify({
    type: 'info',
    message: 'CSV import feature coming soon!'
  })
  showImportDialog.value = false
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
})
</script>
