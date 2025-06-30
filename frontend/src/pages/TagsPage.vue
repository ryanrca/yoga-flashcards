<template>
  <q-page padding>
    <div class="row q-mb-lg">
      <div class="col">
        <h4 class="q-my-none">Tags</h4>
      </div>
      <div class="col-auto">
        <q-btn 
          color="primary" 
          icon="add" 
          label="New Tag" 
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <!-- Tags Table -->
    <q-table
      :rows="tagStore.tags"
      :columns="columns"
      row-key="id"
      :loading="tagStore.loading"
      :pagination="{ rowsPerPage: 0 }"
      :filter="searchInput"
      :filter-method="filterMethod"
    >
      <template v-slot:top-right>
        <q-input
          borderless
          dense
          debounce="300"
          v-model="searchInput"
          placeholder="Search tags"
        >
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            round
            dense
            icon="edit"
            @click="editTag(props.row)"
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

    <!-- Create/Edit Tag Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">{{ editingTag ? 'Edit Tag' : 'Create Tag' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <q-input
              v-model="tagName"
              label="Tag Name"
              outlined
              :rules="[val => !!val || 'Tag name is required']"
              autofocus
            />
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeDialog" />
          <q-btn
            flat
            label="Save"
            color="primary"
            :loading="tagStore.loading"
            @click="onSubmit"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue'
import { useTagStore } from 'src/stores/tags'
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'TagsPage',

  setup() {
    const tagStore = useTagStore()
    const $q = useQuasar()
    
    const showCreateDialog = ref(false)
    const editingTag = ref(null)
    const tagName = ref('')
    const searchInput = ref('')

    const columns = [
      {
        name: 'name',
        required: true,
        label: 'Name',
        align: 'left',
        field: 'name',
        sortable: true
      },
      {
        name: 'created_at',
        label: 'Created',
        align: 'left',
        field: 'created_at',
        sortable: true,
        format: (val) => new Date(val).toLocaleDateString()
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center'
      }
    ]

    const filterMethod = (rows, terms) => {
      if (!terms) return rows
      
      const searchTerm = terms.toLowerCase()
      return rows.filter(row => 
        row.name.toLowerCase().includes(searchTerm)
      )
    }

    const editTag = (tag) => {
      editingTag.value = tag
      tagName.value = tag.name
      showCreateDialog.value = true
    }

    const confirmDelete = (tag) => {
      $q.dialog({
        title: 'Confirm Delete',
        message: `Are you sure you want to delete the tag "${tag.name}"?`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          await tagStore.deleteTag(tag.id)
          $q.notify({
            color: 'positive',
            message: 'Tag deleted successfully'
          })
        } catch (error) {
          $q.notify({
            color: 'negative',
            message: 'Failed to delete tag'
          })
        }
      })
    }

    const onSubmit = async () => {
      if (!tagName.value.trim()) return

      try {
        if (editingTag.value) {
          await tagStore.updateTag(editingTag.value.id, { name: tagName.value.trim() })
          $q.notify({
            color: 'positive',
            message: 'Tag updated successfully'
          })
        } else {
          await tagStore.createTag({ name: tagName.value.trim() })
          $q.notify({
            color: 'positive',
            message: 'Tag created successfully'
          })
        }
        closeDialog()
      } catch (error) {
        $q.notify({
          color: 'negative',
          message: editingTag.value ? 'Failed to update tag' : 'Failed to create tag'
        })
      }
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      editingTag.value = null
      tagName.value = ''
    }

    onMounted(async () => {
      await tagStore.fetchTags()
    })

    return {
      tagStore,
      showCreateDialog,
      editingTag,
      tagName,
      searchInput,
      columns,
      filterMethod,
      editTag,
      confirmDelete,
      onSubmit,
      closeDialog
    }
  }
})
</script>
