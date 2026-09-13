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

          <!-- AI generated images: admin only -->
          <q-card v-if="authStore.isAdmin" class="q-mt-lg">
            <q-card-section class="row items-center">
              <div class="col">
                <div class="text-h6">Card Image</div>
                <div class="text-caption text-grey-7">
                  Prompts and unaccepted images are visible here only. Users see an
                  image once it is accepted.
                </div>
              </div>
              <div class="col-auto">
                <q-btn flat dense icon="refresh" :loading="imagesLoading" @click="loadImages">
                  <q-tooltip>Refresh</q-tooltip>
                </q-btn>
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section v-if="acceptedImage">
              <div class="text-subtitle2 q-mb-sm">
                Currently shown to users
                <q-chip dense color="green" text-color="white" label="Accepted" class="q-ml-sm" />
              </div>
              <q-img
                :src="acceptedImage.image_url"
                style="max-width: 380px; border-radius: 8px;"
              />
              <div class="q-mt-sm">
                <q-btn
                  flat
                  dense
                  color="negative"
                  icon="visibility_off"
                  label="Withdraw from public view"
                  @click="withdrawImage(acceptedImage)"
                />
              </div>
            </q-card-section>
            <q-card-section v-else class="text-grey-7">
              No accepted image yet, so users see no illustration for this card.
            </q-card-section>

            <q-separator />

            <!-- Generate -->
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">Generate a new image</div>

              <q-input
                v-model="promptDraft"
                type="textarea"
                outlined
                autogrow
                label="Prompt"
                hint="Seeded from this card's text. Edit freely and regenerate as often as you like."
                class="q-mb-md"
              />

              <q-input
                v-model="lookAndFeelOverride"
                type="textarea"
                outlined
                autogrow
                dense
                label="Look and feel override (optional)"
                hint="Leave blank to use the global look and feel."
                class="q-mb-md"
                @blur="refreshPreview"
              />

              <div class="row q-col-gutter-md items-center">
                <div class="col-12 col-sm-6">
                  <q-input v-model="modelDraft" outlined dense label="Model" />
                </div>
                <div class="col-12 col-sm-6 text-right">
                  <q-btn flat label="Reset prompt" :disable="generating" @click="resetPrompt" />
                  <q-btn
                    color="primary"
                    icon="auto_awesome"
                    label="Queue generation"
                    :loading="generating"
                    @click="queueGeneration"
                  />
                </div>
              </div>
              <div class="text-caption text-grey-7 q-mt-sm">
                Queued work is picked up by the bot; it does not run inline.
              </div>
            </q-card-section>

            <q-separator />

            <!-- History -->
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">
                History
                <span class="text-caption text-grey-7">({{ images.length }})</span>
              </div>

              <div v-if="!images.length" class="text-grey-7">
                Nothing generated yet for this card.
              </div>

              <q-list v-else bordered separator>
                <q-expansion-item
                  v-for="image in images"
                  :key="image.id"
                  :label="image.model"
                  :caption="formatDate(image.created_at)"
                >
                  <template v-slot:header>
                    <q-item-section avatar>
                      <q-img
                        v-if="image.image_url"
                        :src="image.image_url"
                        style="width: 56px; height: 56px; border-radius: 6px;"
                      />
                      <q-avatar v-else :color="statusColor(image.status)" text-color="white" icon="image" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>
                        {{ image.model }}
                        <q-chip
                          dense
                          :color="statusColor(image.status)"
                          text-color="white"
                          :label="image.status"
                          class="q-ml-sm"
                        />
                        <q-chip
                          v-if="image.is_accepted"
                          dense
                          color="green"
                          text-color="white"
                          label="Accepted"
                        />
                        <q-chip
                          v-if="image.is_auto"
                          dense
                          outline
                          color="grey-7"
                          label="Bot"
                        />
                      </q-item-label>
                      <q-item-label caption>
                        {{ formatDate(image.created_at) }}
                        <span v-if="image.requested_by_username"> by {{ image.requested_by_username }}</span>
                        <span v-if="image.attempts"> &middot; attempt {{ image.attempts }}</span>
                        <span v-if="image.cost_usd"> &middot; ${{ image.cost_usd }}</span>
                      </q-item-label>
                    </q-item-section>
                  </template>

                  <q-card>
                    <q-card-section>
                      <q-img
                        v-if="image.image_url"
                        :src="image.image_url"
                        style="max-width: 380px; border-radius: 8px;"
                        class="q-mb-md"
                      />

                      <div v-if="image.error" class="text-negative q-mb-sm">
                        <strong>Error:</strong> {{ image.error }}
                      </div>

                      <div class="text-caption text-grey-7">Prompt</div>
                      <div class="text-body2 q-mb-sm" style="white-space: pre-wrap;">{{ image.prompt }}</div>

                      <div v-if="image.look_and_feel_override" class="q-mb-sm">
                        <div class="text-caption text-grey-7">Look and feel override</div>
                        <div class="text-body2">{{ image.look_and_feel_override }}</div>
                      </div>
                    </q-card-section>

                    <q-card-actions align="right">
                      <q-btn flat dense label="Reuse prompt" @click="reusePrompt(image)" />
                      <q-btn flat dense label="Regenerate" @click="regenerateFrom(image)" />
                      <q-btn
                        v-if="image.status === 'succeeded' && !image.is_accepted"
                        flat
                        dense
                        color="positive"
                        icon="check"
                        label="Accept"
                        @click="acceptImage(image)"
                      />
                      <q-btn
                        v-if="image.is_accepted"
                        flat
                        dense
                        color="negative"
                        icon="visibility_off"
                        label="Withdraw"
                        @click="withdrawImage(image)"
                      />
                    </q-card-actions>
                  </q-card>
                </q-expansion-item>
              </q-list>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'
import { useAuthStore } from 'src/stores/auth'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()
const authStore = useAuthStore()

// Reactive data
const card = ref(null)
const loading = ref(false)
const error = ref('')

// Revert dialog
const showRevertDialog = ref(false)
const versionToRevert = ref(null)

// AI images (admin only)
const images = ref([])
const preview = ref(null)
const imagesLoading = ref(false)
const generating = ref(false)
const promptDraft = ref('')
const lookAndFeelOverride = ref('')
const modelDraft = ref('')

const acceptedImage = computed(() => images.value.find((image) => image.is_accepted) || null)

const statusColor = (status) => ({
  succeeded: 'green',
  queued: 'blue-grey',
  generating: 'orange',
  failed: 'red'
}[status] || 'grey')

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

const loadImages = async () => {
  if (!authStore.isAdmin) return
  imagesLoading.value = true
  const result = await flashcardsStore.fetchCardImages(route.params.id, lookAndFeelOverride.value)
  if (result.success) {
    images.value = result.data.images
    preview.value = result.data.preview
    // Only prefill an untouched box, so a draft in progress is never clobbered.
    if (!promptDraft.value) promptDraft.value = result.data.preview.prompt
    if (!modelDraft.value) modelDraft.value = result.data.preview.model
  } else {
    $q.notify({ type: 'negative', message: result.error })
  }
  imagesLoading.value = false
}

const refreshPreview = async () => {
  const result = await flashcardsStore.fetchCardImages(route.params.id, lookAndFeelOverride.value)
  if (result.success) {
    preview.value = result.data.preview
    promptDraft.value = result.data.preview.prompt
  }
}

const resetPrompt = () => {
  if (preview.value) promptDraft.value = preview.value.prompt
}

const reusePrompt = (image) => {
  promptDraft.value = image.prompt
  lookAndFeelOverride.value = image.look_and_feel_override || ''
  modelDraft.value = image.model
}

const queueGeneration = async () => {
  generating.value = true
  const result = await flashcardsStore.generateCardImage(route.params.id, {
    prompt: promptDraft.value,
    look_and_feel_override: lookAndFeelOverride.value,
    model: modelDraft.value
  })
  if (result.success) {
    $q.notify({ type: 'positive', message: 'Queued. The bot will generate it shortly.' })
    await loadImages()
  } else {
    $q.notify({ type: 'negative', message: result.error })
  }
  generating.value = false
}

const regenerateFrom = async (image) => {
  const result = await flashcardsStore.regenerateCardImage(image.id)
  if (result.success) {
    $q.notify({ type: 'positive', message: 'Queued a regeneration from that prompt.' })
    await loadImages()
  } else {
    $q.notify({ type: 'negative', message: result.error })
  }
}

const acceptImage = async (image) => {
  const result = await flashcardsStore.acceptCardImage(image.id)
  if (result.success) {
    $q.notify({ type: 'positive', message: 'Accepted. Users can now see this image.' })
    await loadImages()
  } else {
    $q.notify({ type: 'negative', message: result.error })
  }
}

const withdrawImage = async (image) => {
  const result = await flashcardsStore.unacceptCardImage(image.id)
  if (result.success) {
    $q.notify({ type: 'info', message: 'Withdrawn. Users no longer see an image for this card.' })
    await loadImages()
  } else {
    $q.notify({ type: 'negative', message: result.error })
  }
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

  const result = await flashcardsStore.revertCardVersion(
    route.params.id,
    versionToRevert.value.id
  )

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Reverted to the selected version'
    })

    // Reverting creates a new version with a new id, so follow it.
    const newCardId = result.data?.id
    if (newCardId && newCardId !== parseInt(route.params.id)) {
      router.push(`/admin/cards/${newCardId}`)
    } else {
      loadCard()
    }
  } else {
    $q.notify({
      type: 'negative',
      message: result.error || 'Failed to revert to version'
    })
  }

  showRevertDialog.value = false
  versionToRevert.value = null
}

// Lifecycle
onMounted(async () => {
  await loadCard()
  await loadImages()
})
</script>
