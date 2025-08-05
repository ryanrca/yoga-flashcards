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
  } else {
    $q.notify({
      type: 'negative',
      message: 'Failed to load card'
    })
    router.push('/admin/cards')
  }

  loading.value = false
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
      router.push('/admin/cards')
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

// Lifecycle
onMounted(() => {
  loadTags()
  if (isEditing.value) {
    loadCard()
  }
})
</script>
