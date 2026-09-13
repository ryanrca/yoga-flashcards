<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8">
        <div class="row items-center q-mb-md">
          <div class="col">
            <div class="text-h4 text-primary">Card Image Generation</div>
            <div class="text-caption text-grey-7">
              Global settings for the bot that illustrates cards
            </div>
          </div>
          <div class="col-auto">
            <q-btn flat icon="arrow_back" label="Back" @click="$router.push('/admin')" />
          </div>
        </div>

        <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md" rounded>
          {{ error }}
        </q-banner>

        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-xs">Look and feel</div>
            <div class="text-caption text-grey-7 q-mb-md">
              Added to the prompt for every card. Each image can override it individually
              from the card's own page.
            </div>
            <q-input
              v-model="form.look_and_feel"
              type="textarea"
              outlined
              autogrow
              :disable="loading"
              placeholder="Serene minimalist illustration, soft natural light..."
            />
          </q-card-section>

          <q-separator />

          <q-card-section>
            <div class="text-h6 q-mb-xs">Model</div>
            <div class="text-caption text-grey-7 q-mb-md">
              Any OpenRouter image model slug. Type to enter one that is not listed.
            </div>
            <q-select
              v-model="form.model"
              :options="modelOptions"
              outlined
              use-input
              fill-input
              hide-selected
              new-value-mode="add-unique"
              :disable="loading"
              input-debounce="0"
              @new-value="onNewModel"
            />
          </q-card-section>

          <q-separator />

          <q-card-section>
            <div class="text-h6 q-mb-md">Bot behaviour</div>

            <q-toggle
              v-model="form.enabled"
              :disable="loading"
              label="Image generation enabled"
            />
            <div class="text-caption text-grey-7 q-mb-md q-ml-lg">
              Master switch. When off, nothing is generated and new requests are refused.
            </div>

            <q-toggle
              v-model="form.auto_generate_new_cards"
              :disable="loading"
              label="Automatically illustrate new cards"
            />
            <div class="text-caption text-grey-7 q-mb-md q-ml-lg">
              The bot generates one image the first time it sees a card, and never
              repeats it on its own. Regenerating is always a deliberate action.
            </div>

            <q-input
              v-model.number="form.max_attempts"
              type="number"
              outlined
              dense
              min="1"
              max="10"
              style="max-width: 160px"
              :disable="loading"
              label="Max attempts"
            />
            <div class="text-caption text-grey-7 q-mt-xs">
              Hard cap on tries per image, so a card that keeps failing cannot loop.
            </div>
          </q-card-section>

          <q-separator />

          <q-card-actions align="right">
            <div v-if="updatedCaption" class="text-caption text-grey-7 q-mr-md">
              {{ updatedCaption }}
            </div>
            <q-btn flat label="Reload" :disable="loading" @click="load" />
            <q-btn
              color="primary"
              label="Save settings"
              :loading="saving"
              :disable="loading"
              @click="save"
            />
          </q-card-actions>
        </q-card>

        <q-card flat bordered class="q-mt-md bg-grey-1">
          <q-card-section>
            <div class="text-subtitle2 q-mb-sm">How generation runs</div>
            <div class="text-body2 text-grey-8">
              Requests are queued, not run inline. The bot drains the queue when
              <code>manage.py generate_card_images</code> runs, so clicking generate
              repeatedly cannot start parallel jobs for the same card.
              The OpenRouter API key is read from the <code>OPENROUTER_API_KEY</code>
              environment variable and is never stored in the database or returned by the API.
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useFlashcardsStore } from 'src/stores/flashcards'

const $q = useQuasar()
const flashcardsStore = useFlashcardsStore()

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const updatedAt = ref(null)
const updatedBy = ref('')

const form = ref({
  look_and_feel: '',
  model: '',
  enabled: true,
  auto_generate_new_cards: true,
  max_attempts: 3
})

const modelOptions = ref([
  'black-forest-labs/flux.2-pro',
  'black-forest-labs/flux.2-max',
  'black-forest-labs/flux.2-flex',
  'google/gemini-2.5-flash-image'
])

const updatedCaption = computed(() => {
  if (!updatedAt.value) return ''
  const when = new Date(updatedAt.value).toLocaleString()
  return updatedBy.value ? `Last saved ${when} by ${updatedBy.value}` : `Last saved ${when}`
})

const onNewModel = (value, done) => {
  const slug = (value || '').trim()
  if (!slug) return
  if (!modelOptions.value.includes(slug)) modelOptions.value.push(slug)
  done(slug, 'add-unique')
}

const load = async () => {
  loading.value = true
  error.value = ''
  const result = await flashcardsStore.fetchImageSettings()
  if (result.success) {
    form.value = {
      look_and_feel: result.data.look_and_feel,
      model: result.data.model,
      enabled: result.data.enabled,
      auto_generate_new_cards: result.data.auto_generate_new_cards,
      max_attempts: result.data.max_attempts
    }
    if (result.data.model && !modelOptions.value.includes(result.data.model)) {
      modelOptions.value.push(result.data.model)
    }
    updatedAt.value = result.data.updated_at
    updatedBy.value = result.data.updated_by_username || ''
  } else {
    error.value = result.error
  }
  loading.value = false
}

const save = async () => {
  saving.value = true
  error.value = ''
  const result = await flashcardsStore.updateImageSettings(form.value)
  if (result.success) {
    updatedAt.value = result.data.updated_at
    updatedBy.value = result.data.updated_by_username || ''
    $q.notify({ type: 'positive', message: 'Image settings saved' })
  } else {
    const detail = result.error
    error.value = typeof detail === 'string' ? detail : JSON.stringify(detail)
    $q.notify({ type: 'negative', message: 'Failed to save settings' })
  }
  saving.value = false
}

onMounted(load)
</script>
