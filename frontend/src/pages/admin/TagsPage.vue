<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-8">
        <div class="row items-center q-mb-lg">
          <div class="col">
            <div class="text-h4 text-primary">Manage Tags</div>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              label="Create Tag"
              icon="add_circle"
              @click="showCreateDialog = true"
            />
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center q-py-lg">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md">Loading tags...</div>
        </div>

        <!-- Error State -->
        <q-banner v-else-if="error" type="negative" class="text-white q-mb-md">
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          {{ error }}
          <template v-slot:action>
            <q-btn flat color="white" label="Retry" @click="loadTags" />
          </template>
        </q-banner>

        <!-- Tags List -->
        <div v-else class="row q-gutter-md">
          <q-card 
            v-for="tag in tags" 
            :key="tag.id"
            class="col-12 col-sm-6 col-md-4"
          >
            <q-card-section>
              <div class="row items-center">
                <div class="col">
                  <div class="text-h6">{{ tag.name }}</div>
                  <div class="text-caption text-grey-6">
                    {{ tag.card_count || 0 }} cards
                  </div>
                </div>
                <div class="col-auto">
                  <q-btn-dropdown flat round icon="more_vert">
                    <q-list>
                      <q-item clickable @click="editTag(tag)" v-close-popup>
                        <q-item-section avatar>
                          <q-icon name="edit" />
                        </q-item-section>
                        <q-item-section>Edit</q-item-section>
                      </q-item>
                      <q-item clickable @click="confirmDelete(tag)" v-close-popup>
                        <q-item-section avatar>
                          <q-icon name="delete" />
                        </q-item-section>
                        <q-item-section>Delete</q-item-section>
                      </q-item>
                    </q-list>
                  </q-btn-dropdown>
                </div>
              </div>
            </q-card-section>

            <q-card-section v-if="tag.description" class="q-pt-none">
              <p class="text-body2">{{ tag.description }}</p>
            </q-card-section>

            <q-card-actions>
              <q-btn 
                flat 
                color="primary" 
                label="View Cards" 
                @click="viewTagCards(tag)"
              />
            </q-card-actions>
          </q-card>
        </div>

        <!-- Empty State -->
        <div v-if="!loading && !error && tags.length === 0" class="text-center q-py-xl">
          <q-icon name="local_offer" size="6em" color="grey-5" />
          <div class="text-h6 text-grey-6 q-mt-md">No tags created yet</div>
          <p class="text-grey-6 q-mb-lg">
            Create tags to organize your flashcards
          </p>
          <q-btn
            color="primary"
            label="Create First Tag"
            @click="showCreateDialog = true"
            icon="add_circle"
          />
        </div>
      </div>
    </div>

    <!-- Create/Edit Tag Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 400px;">
        <q-card-section>
          <div class="text-h6">{{ editingTag ? 'Edit Tag' : 'Create New Tag' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveTag" class="q-gutter-md">
            <q-input
              v-model="tagForm.name"
              label="Tag Name"
              outlined
              autofocus
              :rules="[val => !!val || 'Tag name is required']"
            />
            
            <q-input
              v-model="tagForm.description"
              label="Description"
              type="textarea"
              outlined
              rows="3"
              hint="Optional description for this tag"
            />
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeDialog" />
          <q-btn 
            color="primary" 
            :label="editingTag ? 'Update' : 'Create'" 
            @click="saveTag"
            :loading="saving"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete the tag "{{ tagToDelete?.name }}"?
          </span>
        </q-card-section>

        <q-card-section v-if="tagToDelete?.card_count > 0">
          <q-banner type="warning">
            This tag is used by {{ tagToDelete.card_count }} card(s). 
            Deleting it will remove the tag from all cards.
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" />
          <q-btn 
            flat 
            label="Delete" 
            color="negative" 
            @click="deleteTag"
            :loading="deleting"
          />
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
const tags = ref([])
const loading = ref(false)
const error = ref('')

// Dialogs
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingTag = ref(null)
const tagToDelete = ref(null)

// Form data
const tagForm = ref({
  name: '',
  description: ''
})

// Loading states
const saving = ref(false)
const deleting = ref(false)

// Methods
const loadTags = async () => {
  loading.value = true
  error.value = ''

  const result = await flashcardsStore.fetchTags()

  if (result.success) {
    tags.value = result.data
  } else {
    error.value = result.error || 'Failed to load tags'
  }

  loading.value = false
}

const editTag = (tag) => {
  editingTag.value = tag
  tagForm.value = {
    name: tag.name,
    description: tag.description || ''
  }
  showCreateDialog.value = true
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingTag.value = null
  tagForm.value = {
    name: '',
    description: ''
  }
}

const saveTag = async () => {
  if (!tagForm.value.name.trim()) {
    $q.notify({
      type: 'negative',
      message: 'Tag name is required'
    })
    return
  }

  saving.value = true

  let result
  if (editingTag.value) {
    // Update existing tag (this would need an update API endpoint)
    $q.notify({
      type: 'info',
      message: 'Tag editing feature coming soon!'
    })
    result = { success: false }
  } else {
    // Create new tag
    result = await flashcardsStore.createTag(tagForm.value)
  }

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: editingTag.value ? 'Tag updated successfully!' : 'Tag created successfully!'
    })
    loadTags()
    closeDialog()
  } else {
    $q.notify({
      type: 'negative',
      message: result.error || 'Failed to save tag'
    })
  }

  saving.value = false
}

const confirmDelete = (tag) => {
  tagToDelete.value = tag
  showDeleteDialog.value = true
}

const deleteTag = async () => {
  if (!tagToDelete.value) return

  deleting.value = true

  // This would need a delete tag API endpoint
  $q.notify({
    type: 'info',
    message: 'Tag deletion feature coming soon!'
  })

  // Simulate successful deletion
  setTimeout(() => {
    const index = tags.value.findIndex(t => t.id === tagToDelete.value.id)
    if (index !== -1) {
      tags.value.splice(index, 1)
    }
    
    $q.notify({
      type: 'positive',
      message: 'Tag deleted successfully'
    })
    
    showDeleteDialog.value = false
    tagToDelete.value = null
    deleting.value = false
  }, 1000)
}

const viewTagCards = (tag) => {
  // Navigate to cards page with tag filter
  router.push({
    name: 'admin-cards',
    query: { tags: tag.id }
  })
}

// Lifecycle
onMounted(() => {
  loadTags()
})
</script>
