<template>
  <q-page padding>
    <div v-if="cardStore.loading" class="flex flex-center q-pa-lg">
      <q-spinner size="50px" />
    </div>

    <div v-else-if="card">
      <!-- Header -->
      <div class="row q-mb-lg">
        <div class="col">
          <q-btn flat icon="arrow_back" @click="$router.back()" />
          <span class="text-h4 q-ml-md">{{ card.title }}</span>
        </div>
        <div class="col-auto">
          <q-btn 
            color="primary" 
            icon="edit" 
            label="Edit" 
            @click="showEditDialog = true"
            class="q-mr-sm"
          />
          <q-btn 
            color="negative" 
            icon="delete" 
            label="Delete" 
            @click="confirmDelete"
          />
        </div>
      </div>

      <!-- Card Content -->
      <div class="row q-gutter-lg">
        <!-- Left Column - Card Info -->
        <div class="col-md-7 col-sm-12">
          <q-card>
            <q-card-section>
              <div class="text-h6">Card Details</div>
            </q-card-section>

            <q-card-section>
              <div class="q-gutter-md">
                <div>
                  <div class="text-subtitle2 text-grey-7">Phrase</div>
                  <div class="text-h6">{{ card.phrase }}</div>
                </div>

                <div>
                  <div class="text-subtitle2 text-grey-7">Definition</div>
                  <div class="text-body1">{{ card.definition }}</div>
                </div>

                <div class="row q-gutter-md">
                  <div class="col">
                    <div class="text-subtitle2 text-grey-7">Status</div>
                    <q-chip
                      :color="card.enabled ? 'positive' : 'negative'"
                      :label="card.enabled ? 'Enabled' : 'Disabled'"
                    />
                  </div>
                  <div class="col">
                    <div class="text-subtitle2 text-grey-7">Views</div>
                    <div class="text-body1">{{ card.views }}</div>
                  </div>
                </div>

                <div>
                  <div class="text-subtitle2 text-grey-7">Tags</div>
                  <div class="q-gutter-xs">
                    <q-chip
                      v-for="tag in card.tags"
                      :key="tag.id"
                      :label="tag.name"
                      color="grey-4"
                      text-color="dark"
                    />
                    <span v-if="!card.tags.length" class="text-grey-7">No tags</span>
                  </div>
                </div>

                <div class="row q-gutter-md">
                  <div class="col">
                    <div class="text-subtitle2 text-grey-7">Created By</div>
                    <div class="text-body1">{{ card.created_by_username }}</div>
                  </div>
                  <div class="col">
                    <div class="text-subtitle2 text-grey-7">Created</div>
                    <div class="text-body1">{{ formatDate(card.created_at) }}</div>
                  </div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Right Column - Images -->
        <div class="col-md-4 col-sm-12">
          <q-card>
            <q-card-section>
              <div class="text-h6">Images</div>
            </q-card-section>

            <q-card-section>
              <!-- Front Photo -->
              <div class="q-mb-md">
                <div class="text-subtitle2 text-grey-7 q-mb-sm">Front Photo</div>
                <div v-if="card.front_photo" class="image-container">
                  <img 
                    :src="getImageUrl(card.front_photo)" 
                    alt="Front photo" 
                    class="card-image"
                  />
                  <q-btn
                    round
                    color="primary"
                    icon="edit"
                    size="sm"
                    class="absolute-top-right q-ma-sm"
                    @click="showImageDialog('front_photo')"
                  />
                </div>
                <div v-else class="image-placeholder" @click="showImageDialog('front_photo')">
                  <q-icon name="add_a_photo" size="48px" color="grey-5" />
                  <div class="text-grey-5 q-mt-sm">Upload front photo</div>
                </div>
              </div>

              <!-- Back Photo -->
              <div>
                <div class="text-subtitle2 text-grey-7 q-mb-sm">Back Photo</div>
                <div v-if="card.back_photo" class="image-container">
                  <img 
                    :src="getImageUrl(card.back_photo)" 
                    alt="Back photo" 
                    class="card-image"
                  />
                  <q-btn
                    round
                    color="primary"
                    icon="edit"
                    size="sm"
                    class="absolute-top-right q-ma-sm"
                    @click="showImageDialog('back_photo')"
                  />
                </div>
                <div v-else class="image-placeholder" @click="showImageDialog('back_photo')">
                  <q-icon name="add_a_photo" size="48px" color="grey-5" />
                  <div class="text-grey-5 q-mt-sm">Upload back photo</div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Version History -->
      <div class="q-mt-lg">
        <q-card>
          <q-card-section>
            <div class="text-h6">Version History</div>
          </q-card-section>

          <q-card-section>
            <q-timeline color="secondary">
              <q-timeline-entry
                v-for="(version, index) in card.versions"
                :key="version.id"
                :title="`Version ${version.version_number}`"
                :subtitle="`${formatDate(version.created_at)} by ${version.created_by_username}`"
                :icon="index === 0 ? 'star' : 'history'"
                :color="index === 0 ? 'primary' : 'secondary'"
              >
                <div class="q-mb-sm">
                  <q-chip 
                    v-if="index === 0" 
                    color="positive" 
                    text-color="white" 
                    label="Current Version" 
                    size="sm"
                  />
                </div>
                
                <div class="version-content">
                  <div class="q-mb-xs">
                    <strong>Title:</strong> {{ version.title }}
                  </div>
                  <div class="q-mb-xs">
                    <strong>Phrase:</strong> {{ version.phrase }}
                  </div>
                  <div class="q-mb-md">
                    <strong>Definition:</strong> {{ version.definition }}
                  </div>
                  
                  <q-btn
                    v-if="index !== 0"
                    flat
                    color="primary"
                    icon="restore"
                    label="Revert to this version"
                    size="sm"
                    @click="confirmRevert(version)"
                  />
                </div>
              </q-timeline-entry>
            </q-timeline>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Edit Dialog -->
    <card-form-dialog
      v-model="showEditDialog"
      :card="card"
      @saved="onCardSaved"
    />

    <!-- Image Upload Dialog -->
    <q-dialog v-model="showImageUpload" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Upload {{ imageTypeLabel }}</div>
        </q-card-section>

        <q-card-section>
          <q-file
            v-model="selectedFile"
            label="Choose image"
            outlined
            accept="image/*"
            @update:model-value="onFileSelected"
          >
            <template v-slot:prepend>
              <q-icon name="image" />
            </template>
          </q-file>

          <div v-if="imagePreview" class="q-mt-md text-center">
            <img :src="imagePreview" alt="Preview" style="max-width: 100%; max-height: 200px;" />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeImageDialog" />
          <q-btn
            flat
            label="Upload"
            color="primary"
            :disable="!selectedFile"
            :loading="uploading"
            @click="uploadImage"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCardStore } from 'src/stores/cards'
import { useQuasar } from 'quasar'
import CardFormDialog from 'src/components/CardFormDialog.vue'

export default defineComponent({
  name: 'CardDetailPage',

  components: {
    CardFormDialog
  },

  setup() {
    const route = useRoute()
    const router = useRouter()
    const cardStore = useCardStore()
    const $q = useQuasar()

    const showEditDialog = ref(false)
    const showImageUpload = ref(false)
    const selectedFile = ref(null)
    const imagePreview = ref('')
    const uploading = ref(false)
    const currentImageType = ref('')

    const card = computed(() => cardStore.selectedCard)

    const imageTypeLabel = computed(() => {
      return currentImageType.value === 'front_photo' ? 'Front Photo' : 'Back Photo'
    })

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }

    const getImageUrl = (imagePath) => {
      if (imagePath.startsWith('http')) {
        return imagePath
      }
      return `${process.env.API_BASE_URL || 'http://localhost:8000'}${imagePath}`
    }

    const showImageDialog = (imageType) => {
      currentImageType.value = imageType
      showImageUpload.value = true
    }

    const closeImageDialog = () => {
      showImageUpload.value = false
      selectedFile.value = null
      imagePreview.value = ''
      currentImageType.value = ''
    }

    const onFileSelected = (file) => {
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          imagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
      } else {
        imagePreview.value = ''
      }
    }

    const uploadImage = async () => {
      if (!selectedFile.value) return

      uploading.value = true
      try {
        await cardStore.uploadCardImage(
          card.value.id,
          selectedFile.value,
          currentImageType.value
        )
        $q.notify({
          color: 'positive',
          message: 'Image uploaded successfully'
        })
        closeImageDialog()
        // Refresh the card data after uploading image
        await cardStore.fetchCard(route.params.id)
      } catch (error) {
        $q.notify({
          color: 'negative',
          message: 'Failed to upload image'
        })
      } finally {
        uploading.value = false
      }
    }

    const confirmDelete = () => {
      $q.dialog({
        title: 'Confirm Delete',
        message: `Are you sure you want to delete "${card.value.title}"?`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          await cardStore.deleteCard(card.value.id)
          $q.notify({
            color: 'positive',
            message: 'Card deleted successfully'
          })
          router.push('/cards')
        } catch (error) {
          $q.notify({
            color: 'negative',
            message: 'Failed to delete card'
          })
        }
      })
    }

    const confirmRevert = (version) => {
      $q.dialog({
        title: 'Confirm Revert',
        message: `Are you sure you want to revert to version ${version.version_number}?`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          await cardStore.revertCardVersion(card.value.id, version.id)
          // Refresh the card data after reverting
          await cardStore.fetchCard(route.params.id)
          $q.notify({
            color: 'positive',
            message: 'Card reverted successfully'
          })
        } catch (error) {
          $q.notify({
            color: 'negative',
            message: 'Failed to revert card'
          })
        }
      })
    }

    const onCardSaved = async () => {
      showEditDialog.value = false
      // Refresh the card data after saving
      await cardStore.fetchCard(route.params.id)
    }

    onMounted(async () => {
      const cardId = route.params.id
      await cardStore.fetchCard(cardId)
    })

    return {
      cardStore,
      card,
      showEditDialog,
      showImageUpload,
      selectedFile,
      imagePreview,
      uploading,
      currentImageType,
      imageTypeLabel,
      formatDate,
      getImageUrl,
      showImageDialog,
      closeImageDialog,
      onFileSelected,
      uploadImage,
      confirmDelete,
      confirmRevert,
      onCardSaved
    }
  }
})
</script>

<style lang="sass" scoped>
.card-image
  width: 100%
  max-height: 200px
  object-fit: cover
  border-radius: 8px

.image-container
  position: relative
  cursor: pointer

.image-placeholder
  width: 100%
  height: 150px
  border: 2px dashed #ccc
  border-radius: 8px
  display: flex
  flex-direction: column
  align-items: center
  justify-content: center
  cursor: pointer
  transition: all 0.3s ease

  &:hover
    border-color: #1976d2
    background-color: rgba(25, 118, 210, 0.04)

.version-content
  background: rgba(0, 0, 0, 0.02)
  padding: 12px
  border-radius: 8px
  border-left: 3px solid #e0e0e0
</style>
