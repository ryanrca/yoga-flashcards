import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from 'src/boot/axios'

export const useFlashcardsStore = defineStore('flashcards', () => {
  // State
  const cards = ref([])
  const dailyCard = ref(null)
  const currentCard = ref(null)
  const tags = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    rowsPerPage: 10,
    rowsNumber: 0
  })

  // Actions
  const fetchCards = async (params = {}) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/api/cards/', { params })
      cards.value = response.data.results || response.data

      if (response.data.count !== undefined) {
        pagination.value.rowsNumber = response.data.count
      }

      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch cards'
      console.error('Error fetching cards:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchDailyCard = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/api/dailycard/')
      dailyCard.value = response.data
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch daily card'
      console.error('Error fetching daily card:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchCard = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/api/cards/${id}/`)
      currentCard.value = response.data
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch card'
      console.error('Error fetching card:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const createCard = async (cardData) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/api/cards/', cardData)
      cards.value.unshift(response.data)
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to create card'
      console.error('Error creating card:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const updateCard = async (id, cardData) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/api/cards/${id}/`, cardData)
      const index = cards.value.findIndex(card => card.id === id)
      if (index !== -1) {
        cards.value[index] = response.data
      }
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to update card'
      console.error('Error updating card:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const deleteCard = async (id) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/api/cards/${id}/`)
      cards.value = cards.value.filter(card => card.id !== id)
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to delete card'
      console.error('Error deleting card:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const fetchTags = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/api/tags/')
      const tagsData = response.data.results || response.data
      tags.value = tagsData
      console.log('Fetched tags:', tagsData)
      return { success: true, data: tagsData }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch tags'
      console.error('Error fetching tags:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const createTag = async (tagData) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/api/tags/', tagData)
      tags.value.push(response.data)
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to create tag'
      console.error('Error creating tag:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const updateTag = async (id, tagData) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/api/tags/${id}/`, tagData)
      const index = tags.value.findIndex(tag => tag.id === id)
      if (index !== -1) {
        tags.value[index] = response.data
      }
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to update tag'
      console.error('Error updating tag:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const deleteTag = async (id) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/api/tags/${id}/`)
      tags.value = tags.value.filter(tag => tag.id !== id)
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to delete tag'
      console.error('Error deleting tag:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // ---- AI card images (admin only) ----

  const fetchCardImages = async (cardId, lookAndFeelOverride = '') => {
    try {
      const params = lookAndFeelOverride ? { look_and_feel_override: lookAndFeelOverride } : {}
      const response = await api.get(`/api/cards/${cardId}/images/`, { params })
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error fetching card images:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to load images' }
    }
  }

  const generateCardImage = async (cardId, payload = {}) => {
    try {
      const response = await api.post(`/api/cards/${cardId}/images/`, payload)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error queueing image generation:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to queue generation' }
    }
  }

  const regenerateCardImage = async (imageId, payload = {}) => {
    try {
      const response = await api.post(`/api/card-images/${imageId}/regenerate/`, payload)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error regenerating image:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to regenerate' }
    }
  }

  const acceptCardImage = async (imageId) => {
    try {
      const response = await api.post(`/api/card-images/${imageId}/accept/`)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error accepting image:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to accept image' }
    }
  }

  const unacceptCardImage = async (imageId) => {
    try {
      const response = await api.post(`/api/card-images/${imageId}/unaccept/`)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error withdrawing image:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to withdraw image' }
    }
  }

  const fetchImageSettings = async () => {
    try {
      const response = await api.get('/api/image-settings/')
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error fetching image settings:', err)
      return { success: false, error: 'Failed to load image settings' }
    }
  }

  const updateImageSettings = async (payload) => {
    try {
      const response = await api.put('/api/image-settings/', payload)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Error saving image settings:', err)
      return { success: false, error: err.response?.data || 'Failed to save image settings' }
    }
  }

  const fetchCardVersions = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/api/cards/${id}/versions/`)
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch card versions'
      console.error('Error fetching card versions:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const revertCardVersion = async (cardId, versionId) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/api/cards/${cardId}/revert_version/`, {
        version_id: versionId
      })
      return { success: true, data: response.data }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to revert to version'
      console.error('Error reverting version:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    cards,
    dailyCard,
    currentCard,
    tags,
    loading,
    error,
    pagination,

    // Actions
    fetchCards,
    fetchDailyCard,
    fetchCard,
    createCard,
    updateCard,
    deleteCard,
    fetchTags,
    createTag,
    updateTag,
    deleteTag,
    fetchCardVersions,
    revertCardVersion,
    fetchCardImages,
    generateCardImage,
    regenerateCardImage,
    acceptCardImage,
    unacceptCardImage,
    fetchImageSettings,
    updateImageSettings
  }
})
