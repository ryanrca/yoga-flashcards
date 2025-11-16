<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8">
        <div class="row items-center q-mb-lg">
          <div class="col">
            <div class="text-h4 text-primary">
              {{ isEditing ? 'Edit Card' : 'Create New Card' }}
            </div>
          </div>
          <div class="col-auto">
            <q-btn
              flat
              label="Back to Cards"
              icon="arrow_back"
              @click="$router.push('/admin/cards')"
            />
          </div>
        </div>

        <q-card>
          <q-card-section>
            <q-form @submit="saveCard" class="q-gutter-md">
              <!-- Title -->
              <q-input
                v-model="cardData.title"
                label="Title *"
                outlined
                :rules="[val => !!val || 'Title is required']"
              />

              <!-- Sanskrit Phrase -->
              <q-input
                v-model="cardData.phrase"
                label="Sanskrit Phrase"
                outlined
                hint="Optional Sanskrit term or phrase"
              />

              <!-- Definition -->
              <q-input
                v-model="cardData.definition"
                label="Definition *"
                type="textarea"
                rows="4"
                outlined
                :rules="[val => !!val || 'Definition is required']"
              />

              <!-- Tags -->
              <q-select
                v-model="cardData.tags"
                :options="availableTags"
                option-label="name"
                option-value="id"
                label="Tags"
                multiple
                outlined
                use-chips
                clearable
                hint="Select or create tags for this card"
                popup-content-class="admin-dropdown-menu"
              >
                <template v-slot:no-option>
                  <q-item>
                    <q-item-section class="text-grey">
                      No tags available
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>

              <!-- Front Image -->
              <div>
                <div class="text-body1 q-mb-sm">Front Image</div>
                <q-file
                  v-model="frontImageFile"
                  label="Upload front image"
                  outlined
                  accept="image/*"
                  @update:model-value="onFrontImageChange"
                >
                  <template v-slot:prepend>
                    <q-icon name="attach_file" />
                  </template>
                </q-file>
                <div v-if="frontImagePreview" class="q-mt-sm">
                  <q-img
                    :src="frontImagePreview"
                    style="max-width: 200px; max-height: 150px; border-radius: 8px;"
                  />
                  <q-btn
                    flat
                    color="negative"
                    icon="delete"
                    label="Remove"
                    @click="removeFrontImage"
                    class="q-mt-xs"
                  />
                </div>
              </div>

              <!-- Back Image -->
              <div>
                <div class="text-body1 q-mb-sm">Back Image</div>
                <q-file
                  v-model="backImageFile"
                  label="Upload back image"
                  outlined
                  accept="image/*"
                  @update:model-value="onBackImageChange"
                >
                  <template v-slot:prepend>
                    <q-icon name="attach_file" />
                  </template>
                </q-file>
                <div v-if="backImagePreview" class="q-mt-sm">
                  <q-img
                    :src="backImagePreview"
                    style="max-width: 200px; max-height: 150px; border-radius: 8px;"
                  />
                  <q-btn
                    flat
                    color="negative"
                    icon="delete"
                    label="Remove"
                    @click="removeBackImage"
                    class="q-mt-xs"
                  />
                </div>
              </div>

              <!-- Form Actions -->
              <div class="q-pt-md">
                <q-btn
                  type="submit"
                  color="primary"
                  :label="isEditing ? 'Update Card' : 'Create Card'"
                  :loading="loading"
                />
                <q-btn
                  flat
                  label="Cancel"
                  @click="$router.push('/admin/cards')"
                  class="q-ml-sm"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Version History Section -->
        <q-card v-if="isEditing" class="q-mt-lg">
          <q-card-section>
            <div class="text-h5 text-primary q-mb-md">Version History</div>

            <div v-if="versionHistory.length === 0" class="text-center text-grey-6 q-pa-md">
              No version history available yet. Edit this card to create a new version.
            </div>

            <q-table
              v-else
              :rows="versionHistory"
              :columns="versionColumns"
              row-key="id"
              flat
              bordered
              :rows-per-page-options="[10, 25, 50]"
              class="version-history-table"
            >
              <template v-slot:body-cell-version_number="props">
                <q-td :props="props">
                  <q-badge
                    :color="props.row.is_live ? 'positive' : 'grey'"
                    :label="props.row.is_live ? `v${props.row.version_number} (LIVE)` : `v${props.row.version_number}`"
                  />
                </q-td>
              </template>

              <template v-slot:body-cell-title="props">
                <q-td :props="props">
                  <div class="text-weight-medium">{{ props.row.title }}</div>
                  <div v-if="props.row.phrase" class="text-caption text-grey-7">{{ props.row.phrase }}</div>
                </q-td>
              </template>

              <template v-slot:body-cell-definition="props">
                <q-td :props="props">
                  <div class="ellipsis-2-lines">{{ props.row.definition }}</div>
                </q-td>
              </template>

              <template v-slot:body-cell-created_at="props">
                <q-td :props="props">
                  <div>{{ formatDate(props.row.created_at) }}</div>
                  <div class="text-caption text-grey-7">{{ props.row.created_by_username }}</div>
                </q-td>
              </template>

              <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                  <q-btn
                    v-if="!props.row.is_live"
                    flat
                    dense
                    round
                    icon="restore"
                    color="primary"
                    @click="revertToVersion(props.row)"
                  >
                    <q-tooltip>Revert to this version</q-tooltip>
                  </q-btn>
                  <span v-else class="text-grey">Current</span>
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()

// Computed
const isEditing = computed(() => !!route.params.id)

// Reactive data
const cardData = ref({
  title: '',
  phrase: '',
  definition: '',
  tags: [],
  front_image: null,
  back_image: null
})

const availableTags = ref([])
const loading = ref(false)
const versionHistory = ref([])

// Version history table columns
const versionColumns = [
  {
    name: 'version_number',
    label: 'Version',
    field: 'version_number',
    align: 'left',
    sortable: true
  },
  {
    name: 'title',
    label: 'Title',
    field: 'title',
    align: 'left',
    sortable: true
  },
  {
    name: 'definition',
    label: 'Definition',
    field: 'definition',
    align: 'left'
  },
  {
    name: 'created_at',
    label: 'Modified',
    field: 'created_at',
    align: 'left',
    sortable: true
  },
  {
    name: 'actions',
    label: 'Actions',
    field: 'actions',
    align: 'center'
  }
]

// File handling
const frontImageFile = ref(null)
const backImageFile = ref(null)
const frontImagePreview = ref(null)
const backImagePreview = ref(null)

// Methods
const loadCard = async () => {
  if (!isEditing.value) return

  loading.value = true
  const result = await flashcardsStore.fetchCard(route.params.id)

  if (result.success) {
    const card = result.data
    cardData.value = {
      title: card.title || '',
      phrase: card.phrase || '',
      definition: card.definition || '',
      tags: card.tags || [],
      front_image: card.front_image,
      back_image: card.back_image
    }

    // Set image previews if they exist
    if (card.front_image) {
      frontImagePreview.value = card.front_image
    }
    if (card.back_image) {
      backImagePreview.value = card.back_image
    }

    // Load version history
    await loadVersionHistory()
  } else {
    $q.notify({
      type: 'negative',
      message: 'Failed to load card'
    })
    router.push('/admin/cards')
  }

  loading.value = false
}

const loadVersionHistory = async () => {
  const result = await flashcardsStore.fetchCardVersions(route.params.id)
  if (result.success) {
    versionHistory.value = result.data
    console.log('Version history loaded:', result.data)
  } else {
    console.error('Failed to load version history:', result.error)
  }
}

const loadTags = async () => {
  const result = await flashcardsStore.fetchTags()
  if (result.success) {
    availableTags.value = result.data
  }
}

const onFrontImageChange = (file) => {
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      frontImagePreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const onBackImageChange = (file) => {
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      backImagePreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const removeFrontImage = () => {
  frontImageFile.value = null
  frontImagePreview.value = null
  cardData.value.front_image = null
}

const removeBackImage = () => {
  backImageFile.value = null
  backImagePreview.value = null
  cardData.value.back_image = null
}

const saveCard = async () => {
  if (!cardData.value.title || !cardData.value.definition) {
    $q.notify({
      type: 'negative',
      message: 'Please fill in all required fields'
    })
    return
  }

  loading.value = true

  try {
    // Prepare form data for file upload
    const formData = new FormData()
    formData.append('title', cardData.value.title)
    formData.append('phrase', cardData.value.phrase || '')
    formData.append('definition', cardData.value.definition)

    // Add tags
    if (cardData.value.tags.length > 0) {
      cardData.value.tags.forEach(tag => {
        formData.append('tags', tag.id)
      })
    }

    // Add images if they exist
    if (frontImageFile.value) {
      formData.append('front_image', frontImageFile.value)
    }
    if (backImageFile.value) {
      formData.append('back_image', backImageFile.value)
    }

    let result
    if (isEditing.value) {
      result = await flashcardsStore.updateCard(route.params.id, formData)
    } else {
      result = await flashcardsStore.createCard(formData)
    }

    if (result.success) {
      $q.notify({
        type: 'positive',
        message: isEditing.value ? 'Card updated successfully!' : 'Card created successfully!'
      })
      
      if (isEditing.value) {
        // When editing, stay on page and reload version history
        await loadVersionHistory()
        
        // Update the form with the returned data (don't reload, just use what we got back)
        const card = result.data
        cardData.value = {
          title: card.title || '',
          phrase: card.phrase || '',
          definition: card.definition || '',
          tags: card.tags || [],
          front_image: card.front_image,
          back_image: card.back_image
        }
        
        // Update image previews
        if (card.front_image) {
          frontImagePreview.value = card.front_image
        }
        if (card.back_image) {
          backImagePreview.value = card.back_image
        }
        
        // Clear the file inputs since images are now saved
        frontImageFile.value = null
        backImageFile.value = null
      } else {
        // When creating new card, redirect to cards list
        router.push('/admin/cards')
      }
    } else {
      $q.notify({
        type: 'negative',
        message: result.error || 'Failed to save card'
      })
    }
  } catch {
    $q.notify({
      type: 'negative',
      message: 'An error occurred while saving the card'
    })
  }

  loading.value = false
}

const revertToVersion = async (version) => {
  $q.dialog({
    title: 'Revert to Version',
    message: `Are you sure you want to revert to version ${version.version_number}? This will create a new version with the content from version ${version.version_number}.`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    loading.value = true
    const result = await flashcardsStore.revertCardVersion(route.params.id, version.id)

    if (result.success) {
      $q.notify({
        type: 'positive',
        message: `Successfully reverted to version ${version.version_number}`
      })
      // Reload card and version history
      await loadCard()
    } else {
      $q.notify({
        type: 'negative',
        message: result.error || 'Failed to revert version'
      })
    }
    loading.value = false
  })
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadTags()
  if (isEditing.value) {
    loadCard()
  }
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

/* Version history table styling */
.version-history-table .q-table__top,
.version-history-table .q-table__bottom {
  background: linear-gradient(90deg,
    rgba(255, 107, 53, 0.1) 0%,
    rgba(155, 77, 202, 0.1) 100%
  );
}

.version-history-table .q-table thead tr,
.version-history-table .q-table tbody td {
  border-color: rgba(155, 77, 202, 0.2);
}

.version-history-table .ellipsis-2-lines {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
</style>
