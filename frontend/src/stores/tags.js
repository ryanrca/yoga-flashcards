import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useTagStore = defineStore('tags', {
  state: () => ({
    tags: [],
    loading: false
  }),

  actions: {
    async fetchTags() {
      this.loading = true
      try {
        const response = await api.get('/api/tags/')
        this.tags = response.data.results || response.data
        return this.tags
      } catch (error) {
        console.error('Error fetching tags:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createTag(tagData) {
      this.loading = true
      try {
        const response = await api.post('/api/tags/', tagData)
        await this.fetchTags() // Refresh list
        return response.data
      } catch (error) {
        console.error('Error creating tag:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateTag(id, tagData) {
      this.loading = true
      try {
        const response = await api.put(`/api/tags/${id}/`, tagData)
        await this.fetchTags() // Refresh list
        return response.data
      } catch (error) {
        console.error('Error updating tag:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteTag(id) {
      this.loading = true
      try {
        await api.delete(`/api/tags/${id}/`)
        await this.fetchTags() // Refresh list
        return true
      } catch (error) {
        console.error('Error deleting tag:', error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
