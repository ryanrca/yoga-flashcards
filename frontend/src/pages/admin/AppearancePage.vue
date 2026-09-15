<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8">
        <div class="row items-center q-mb-md">
          <div class="col">
            <div class="text-h4 text-primary">Appearance</div>
            <div class="text-caption text-grey-7">
              The theme every visitor sees
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
            <div class="text-h6 q-mb-xs">Site theme</div>
            <div class="text-caption text-grey-7 q-mb-md">
              Selecting a theme previews it here immediately. Nothing changes for
              anyone else until you save. Visitors pick this up on their next page load.
            </div>

            <q-list bordered separator class="rounded-borders">
              <q-item
                v-for="option in themes"
                :key="option.id"
                v-ripple
                clickable
                :active="selected === option.id"
                @click="preview(option.id)"
              >
                <q-item-section avatar>
                  <q-radio v-model="selected" :val="option.id" @update:model-value="preview" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ option.label }}</q-item-label>
                  <q-item-label caption>{{ option.blurb }}</q-item-label>
                </q-item-section>
                <q-item-section v-if="option.id === savedTheme" side>
                  <q-badge outline color="primary" label="Live" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

          <q-separator />

          <q-card-actions align="right" class="q-pa-md">
            <div class="text-caption text-grey-7 col text-left">
              {{ updatedCaption }}
            </div>
            <q-btn
              flat
              label="Reset"
              :disable="loading || saving || !dirty"
              @click="reset"
            />
            <q-btn
              unelevated
              color="primary"
              label="Save"
              :loading="saving"
              :disable="loading || !dirty"
              @click="save"
            />
          </q-card-actions>
        </q-card>

        <div class="text-caption text-grey-7 q-mt-md">
          Changing the theme does not affect the admin area's own layout choices,
          only its colours - every screen reads the same tokens.
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useQuasar } from 'quasar'
import { useTheme } from 'src/composables/useTheme'

const $q = useQuasar()
const { themes, applyTheme, fetchSiteTheme, saveSiteTheme } = useTheme()

const loading = ref(false)
const saving = ref(false)
const error = ref('')

// What the server currently holds, and what is selected in the UI. They differ
// while previewing.
const savedTheme = ref('')
const selected = ref('')
const updatedAt = ref(null)
const updatedBy = ref('')

const dirty = computed(() => selected.value !== savedTheme.value)

const updatedCaption = computed(() => {
  if (!updatedAt.value) return ''
  const when = new Date(updatedAt.value).toLocaleString()
  return updatedBy.value ? `Last changed by ${updatedBy.value} on ${when}` : `Last changed ${when}`
})

// Preview applies the theme to this browser only. Saving is what makes it real.
const preview = (id) => {
  selected.value = id
  applyTheme(id)
}

const reset = () => {
  preview(savedTheme.value)
}

const load = async () => {
  loading.value = true
  error.value = ''

  const result = await fetchSiteTheme()
  if (result.success) {
    savedTheme.value = result.data.theme
    selected.value = result.data.theme
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

  const result = await saveSiteTheme(selected.value)
  if (result.success) {
    savedTheme.value = result.data.theme
    updatedAt.value = result.data.updated_at
    updatedBy.value = result.data.updated_by_username || ''
    $q.notify({ type: 'positive', message: `Site theme is now ${result.data.theme}` })
  } else {
    const detail = result.error
    error.value = typeof detail === 'string' ? detail : JSON.stringify(detail)
  }

  saving.value = false
}

onMounted(load)

// Leaving with an unsaved preview would strand this browser on a theme the
// site is not actually using, until the next reload. Put it back.
onBeforeUnmount(() => {
  if (dirty.value && savedTheme.value) applyTheme(savedTheme.value)
})
</script>
