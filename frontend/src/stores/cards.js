import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useCardStore = defineStore('cards', {
  state: () => ({
    cards: [],
    selectedCard: null,
    loading: false,
    pagination: {
      page: 1,
      rowsPerPage: 20,
      rowsNumber: 0
    },
    filter: {
      search: '',
      enabled: null,
      tags: []
    },
    sortBy: 'updated_at',
    descending: true
  }),

  actions: {
    async fetchCards(tableProps = null) {
      this.loading = true
      try {
        let params = {
          page: this.pagination.page,
          page_size: this.pagination.rowsPerPage,
          ordering: this.descending ? `-${this.sortBy}` : this.sortBy
        }

        // Handle table props if provided (from q-table)
        if (tableProps) {
          const { page, rowsPerPage, sortBy, descending } = tableProps.pagination
          params.page = page
          params.page_size = rowsPerPage
          
          // Update local pagination and sorting
          this.pagination.page = page
          this.pagination.rowsPerPage = rowsPerPage
          
          if (sortBy) {
            this.sortBy = sortBy
            this.descending = descending
            params.ordering = descending ? `-${sortBy}` : sortBy
          } else {
            params.ordering = this.descending ? `-${this.sortBy}` : this.sortBy
          }
        }

        // Add filters
        if (this.filter.search) {
          params.search = this.filter.search
        }
        if (this.filter.enabled !== null) {
          params.enabled = this.filter.enabled
        }
        if (this.filter.tags.length > 0) {
          params.tags = this.filter.tags.join(',')
        }

        const response = await api.get('/api/cards/', { params })
        this.cards = response.data.results
        this.pagination.rowsNumber = response.data.count
        return response.data
      } catch (error) {
        console.error('Error fetching cards:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCard(id) {
      this.loading = true
      try {
        const response = await api.get(`/api/cards/${id}/`)
        this.selectedCard = response.data
        return response.data
      } catch (error) {
        console.error('Error fetching card:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createCard(cardData) {
      this.loading = true
      try {
        const response = await api.post('/api/cards/', cardData)
        await this.fetchCards() // Refresh list
        return response.data
      } catch (error) {
        console.error('Error creating card:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateCard(id, cardData) {
      this.loading = true
      try {
        const response = await api.put(`/api/cards/${id}/`, cardData)
        this.selectedCard = response.data
        await this.fetchCards() // Refresh list
        return response.data
      } catch (error) {
        console.error('Error updating card:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteCard(id) {
      this.loading = true
      try {
        await api.post(`/api/cards/${id}/soft_delete/`)
        await this.fetchCards() // Refresh list
        return true
      } catch (error) {
        console.error('Error deleting card:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async revertCardVersion(cardId, versionId) {
      this.loading = true
      try {
        const response = await api.post(`/api/cards/${cardId}/revert_version/`, {
          version_id: versionId
        })
        this.selectedCard = response.data
        return response.data
      } catch (error) {
        console.error('Error reverting card version:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async uploadCardImage(cardId, imageFile, imageType) {
      this.loading = true
      try {
        const formData = new FormData()
        formData.append(imageType, imageFile)
        
        const response = await api.patch(`/api/cards/${cardId}/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        this.selectedCard = response.data
        return response.data
      } catch (error) {
        console.error('Error uploading image:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    setFilter(filterData) {
      this.filter = { ...this.filter, ...filterData }
      this.pagination.page = 1 // Reset to first page when filtering
    },

    clearFilter() {
      this.filter = {
        search: '',
        enabled: null,
        tags: []
      }
      this.pagination.page = 1
    }
  }
})
