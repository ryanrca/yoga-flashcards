<template>
  <q-dialog v-model="dialogModel" persistent>
    <q-card style="min-width: 500px; max-width: 800px">
      <q-card-section>
        <div class="text-h6">{{ card ? 'Edit Card' : 'Create Card' }}</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="formData.title"
            label="Title"
            outlined
            :rules="[val => !!val || 'Title is required']"
            autofocus
          />

          <q-input
            v-model="formData.phrase"
            label="Phrase"
            outlined
            :rules="[val => !!val || 'Phrase is required']"
          />

          <q-input
            v-model="formData.definition"
            label="Definition"
            outlined
            type="textarea"
            rows="4"
            :rules="[val => !!val || 'Definition is required']"
          />

          <q-select
            v-model="selectedTags"
            :options="tagOptions"
            label="Tags"
            outlined
            multiple
            use-chips
            clearable
            option-label="name"
            option-value="id"
            emit-value
            map-options
          />

          <q-toggle
            v-model="formData.enabled"
            label="Enabled"
          />
        </q-form>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancel" @click="closeDialog" />
        <q-btn
          flat
          label="Save"
          color="primary"
          :loading="cardStore.loading"
          @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script>
import { defineComponent, ref, computed, watch, onMounted } from 'vue'
import { useCardStore } from 'src/stores/cards'
import { useTagStore } from 'src/stores/tags'
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'CardFormDialog',

  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    card: {
      type: Object,
      default: null
    }
  },

  emits: ['update:modelValue', 'saved'],

  setup(props, { emit }) {
    const cardStore = useCardStore()
    const tagStore = useTagStore()
    const $q = useQuasar()

    const formData = ref({
      title: '',
      phrase: '',
      definition: '',
      enabled: true
    })

    const selectedTags = ref([])

    const dialogModel = computed({
      get: () => props.modelValue,
      set: (val) => emit('update:modelValue', val)
    })

    const tagOptions = computed(() => tagStore.tags)

    const resetForm = () => {
      if (props.card) {
        formData.value = {
          title: props.card.title,
          phrase: props.card.phrase,
          definition: props.card.definition,
          enabled: props.card.enabled
        }
        selectedTags.value = props.card.tags.map(tag => tag.id)
      } else {
        formData.value = {
          title: '',
          phrase: '',
          definition: '',
          enabled: true
        }
        selectedTags.value = []
      }
    }

    const onSubmit = async () => {
      if (!formData.value.title || !formData.value.phrase || !formData.value.definition) {
        return
      }

      try {
        const cardData = {
          ...formData.value,
          tag_ids: selectedTags.value
        }

        if (props.card) {
          await cardStore.updateCard(props.card.id, cardData)
          $q.notify({
            color: 'positive',
            message: 'Card updated successfully'
          })
        } else {
          await cardStore.createCard(cardData)
          $q.notify({
            color: 'positive',
            message: 'Card created successfully'
          })
        }

        emit('saved')
      } catch (error) {
        $q.notify({
          color: 'negative',
          message: props.card ? 'Failed to update card' : 'Failed to create card'
        })
      }
    }

    const closeDialog = () => {
      dialogModel.value = false
    }

    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        resetForm()
      }
    })

    onMounted(async () => {
      await tagStore.fetchTags()
    })

    return {
      cardStore,
      formData,
      selectedTags,
      dialogModel,
      tagOptions,
      onSubmit,
      closeDialog
    }
  }
})
</script>
