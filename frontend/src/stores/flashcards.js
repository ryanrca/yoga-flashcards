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
      tags.value = response.data.results || response.data
      return { success: true, data: response.data }
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
    createTag
  }
})
