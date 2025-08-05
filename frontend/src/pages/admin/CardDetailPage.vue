<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8">
        <div class="row items-center q-mb-lg">
          <div class="col">
            <div class="text-h4 text-primary">Card Details</div>
          </div>
          <div class="col-auto q-gutter-sm">
            <q-btn
              color="primary"
              label="Edit"
              icon="edit"
              @click="$router.push(`/admin/cards/${$route.params.id}/edit`)"
            />
            <q-btn
              flat
              label="Back"
              icon="arrow_back"
              @click="$router.push('/admin/cards')"
            />
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center q-py-lg">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md">Loading card...</div>
        </div>

        <!-- Error State -->
        <q-banner v-else-if="error" type="negative" class="text-white q-mb-md">
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          {{ error }}
          <template v-slot:action>
            <q-btn flat color="white" label="Retry" @click="loadCard" />
          </template>
        </q-banner>

        <!-- Card Content -->
        <div v-else-if="card">
          <q-card>
            <q-card-section>
              <div class="text-h5 text-primary">{{ card.title }}</div>
              <div v-if="card.phrase" class="text-h6 text-italic text-grey-8 q-mt-sm">
                {{ card.phrase }}
              </div>
            </q-card-section>

            <q-card-section v-if="card.front_image">
              <div class="text-body1 q-mb-sm">Front Image:</div>
              <q-img 
                :src="card.front_image" 
                style="max-width: 400px; max-height: 300px; border-radius: 8px;"
              />
            </q-card-section>

            <q-card-section>
              <div class="text-body1 q-mb-sm">Definition:</div>
              <p class="text-body1">{{ card.definition }}</p>
            </q-card-section>

            <q-card-section v-if="card.back_image">
              <div class="text-body1 q-mb-sm">Back Image:</div>
              <q-img 
                :src="card.back_image" 
                style="max-width: 400px; max-height: 300px; border-radius: 8px;"
              />
            </q-card-section>

            <q-card-section v-if="card.tags && card.tags.length">
              <div class="text-body1 q-mb-sm">Tags:</div>
              <q-chip
                v-for="tag in card.tags"
                :key="tag.id"
                color="primary"
                text-color="white"
                :label="tag.name"
                class="q-ma-xs"
              />
            </q-card-section>

            <q-card-section>
              <div class="text-body1 q-mb-sm">Metadata:</div>
              <div class="text-body2 text-grey-7">
                <div><strong>Created:</strong> {{ formatDate(card.created_at) }}</div>
                <div><strong>Updated:</strong> {{ formatDate(card.updated_at) }}</div>
                <div v-if="card.created_by"><strong>Created by:</strong> {{ card.created_by.email }}</div>
                <div v-if="card.version"><strong>Version:</strong> {{ card.version }}</div>
              </div>
            </q-card-section>
          </q-card>

          <!-- Version History -->
          <q-card v-if="card.versions && card.versions.length > 1" class="q-mt-lg">
            <q-card-section>
              <div class="text-h6 q-mb-md">Version History</div>
              
              <q-list bordered>
                <q-item 
                  v-for="version in card.versions" 
                  :key="version.id"
                  :class="version.id === card.id ? 'bg-green-1' : ''"
                >
                  <q-item-section avatar>
                    <q-avatar :color="version.id === card.id ? 'green' : 'grey'" text-color="white">
                      {{ version.version }}
                    </q-avatar>
                  </q-item-section>
                  
                  <q-item-section>
                    <q-item-label>
                      {{ version.title }}
                      <q-chip v-if="version.id === card.id" size="sm" color="green" text-color="white" label="Current" />
                    </q-item-label>
                    <q-item-label caption>
                      Updated {{ formatDate(version.updated_at) }}
                      <span v-if="version.updated_by"> by {{ version.updated_by.email }}</span>
                    </q-item-label>
                  </q-item-section>
                  
                  <q-item-section side>
                    <q-btn
                      v-if="version.id !== card.id"
                      flat
                      round
                      color="primary"
                      icon="restore"
                      @click="revertToVersion(version)"
                    >
                      <q-tooltip>Revert to this version</q-tooltip>
                    </q-btn>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>

    <!-- Revert Confirmation Dialog -->
    <q-dialog v-model="showRevertDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="restore" color="primary" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to revert to version {{ versionToRevert?.version }}?
          </span>
        </q-card-section>

        <q-card-section>
          <q-banner type="info">
            This will create a new version with the content from version {{ versionToRevert?.version }}.
            The current version will be preserved in the history.
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showRevertDialog = false" />
          <q-btn 
            flat 
            label="Revert" 
            color="primary" 
            @click="confirmRevert"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const route = useRoute()
const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()

// Reactive data
const card = ref(null)
const loading = ref(false)
const error = ref('')

// Revert dialog
const showRevertDialog = ref(false)
const versionToRevert = ref(null)

// Methods
const loadCard = async () => {
  loading.value = true
  error.value = ''

  const result = await flashcardsStore.fetchCard(route.params.id)

  if (result.success) {
    card.value = result.data
  } else {
    error.value = result.error || 'Failed to load card'
  }

  loading.value = false
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const revertToVersion = (version) => {
  versionToRevert.value = version
  showRevertDialog.value = true
}

const confirmRevert = async () => {
  if (!versionToRevert.value) return

  try {
    // This would call the revert API endpoint
    // const result = await axios.post(`/api/cards/${route.params.id}/revert_version/`, {
    //   version_id: versionToRevert.value.id
    // })
    
    $q.notify({
      type: 'info',
      message: 'Version revert feature coming soon!'
    })
    
    // Reload card data
    // loadCard()
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to revert to version'
    })
  }

  showRevertDialog.value = false
  versionToRevert.value = null
}

// Lifecycle
onMounted(() => {
  loadCard()
})
</script>
