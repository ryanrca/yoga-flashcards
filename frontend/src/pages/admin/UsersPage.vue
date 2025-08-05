<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12">
        <div class="row items-center q-mb-lg">
          <div class="col">
            <div class="text-h4 text-primary">Manage Users</div>
            <div class="text-subtitle1 text-grey-6">Admin access only</div>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              label="Add User"
              icon="person_add"
              @click="showCreateDialog = true"
            />
          </div>
        </div>

        <!-- Search Section -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="row q-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="searchQuery"
                  label="Search users..."
                  outlined
                  clearable
                  @update:model-value="searchUsers"
                  @keyup.enter="searchUsers"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </div>
              
              <div class="col-12 col-md-4">
                <q-select
                  v-model="roleFilter"
                  :options="roleOptions"
                  label="Filter by role"
                  outlined
                  clearable
                  @update:model-value="filterUsers"
                />
              </div>
              
              <div class="col-12 col-md-2">
                <q-btn
                  color="primary"
                  label="Clear"
                  @click="clearFilters"
                  class="full-width"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Loading State -->
        <div v-if="loading" class="text-center q-py-lg">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md">Loading users...</div>
        </div>

        <!-- Users Table -->
        <q-table
          v-else
          :rows="users"
          :columns="columns"
          :loading="loading"
          :pagination="pagination"
          @request="onRequest"
          row-key="id"
          flat
          bordered
        >
          <template v-slot:body-cell-email="props">
            <q-td :props="props">
              <div class="row items-center q-gutter-sm">
                <q-avatar color="primary" text-color="white">
                  {{ props.row.email.charAt(0).toUpperCase() }}
                </q-avatar>
                <div>
                  <div class="text-weight-medium">{{ props.value }}</div>
                  <div class="text-caption text-grey-6">{{ props.row.first_name }} {{ props.row.last_name }}</div>
                </div>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-role="props">
            <q-td :props="props">
              <q-chip
                :color="getRoleColor(props.value)"
                text-color="white"
                :label="props.value"
                size="sm"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-icon
                :name="props.value ? 'check_circle' : 'cancel'"
                :color="props.value ? 'green' : 'red'"
                size="sm"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-last_login="props">
            <q-td :props="props">
              {{ props.value ? formatDate(props.value) : 'Never' }}
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <div class="q-gutter-xs">
                <q-btn
                  flat
                  round
                  color="primary"
                  icon="edit"
                  @click="editUser(props.row)"
                  size="sm"
                >
                  <q-tooltip>Edit User</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  round
                  :color="props.row.is_active ? 'red' : 'green'"
                  :icon="props.row.is_active ? 'block' : 'check_circle'"
                  @click="toggleUserStatus(props.row)"
                  size="sm"
                >
                  <q-tooltip>
                    {{ props.row.is_active ? 'Deactivate' : 'Activate' }} User
                  </q-tooltip>
                </q-btn>
                <q-btn
                  v-if="props.row.id !== authStore.user?.id"
                  flat
                  round
                  color="red"
                  icon="delete"
                  @click="confirmDelete(props.row)"
                  size="sm"
                >
                  <q-tooltip>Delete User</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>

    <!-- Create/Edit User Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 500px;">
        <q-card-section>
          <div class="text-h6">{{ editingUser ? 'Edit User' : 'Create New User' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveUser" class="q-gutter-md">
            <q-input
              v-model="userForm.email"
              label="Email"
              type="email"
              outlined
              :rules="[
                val => !!val || 'Email is required',
                val => isValidEmail(val) || 'Please enter a valid email'
              ]"
            />

            <q-input
              v-model="userForm.first_name"
              label="First Name"
              outlined
            />

            <q-input
              v-model="userForm.last_name"
              label="Last Name"
              outlined
            />

            <q-select
              v-model="userForm.role"
              :options="roleOptions"
              label="Role"
              outlined
              :rules="[val => !!val || 'Role is required']"
            />

            <q-input
              v-if="!editingUser"
              v-model="userForm.password"
              label="Password"
              type="password"
              outlined
              :rules="[
                val => !!val || 'Password is required',
                val => val.length >= 8 || 'Password must be at least 8 characters'
              ]"
            />

            <q-toggle
              v-model="userForm.is_active"
              label="Active User"
            />
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeDialog" />
          <q-btn 
            color="primary" 
            :label="editingUser ? 'Update' : 'Create'" 
            @click="saveUser"
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
            Are you sure you want to delete user "{{ userToDelete?.email }}"?
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" />
          <q-btn 
            flat 
            label="Delete" 
            color="negative" 
            @click="deleteUser"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()

// Reactive data
const users = ref([])
const loading = ref(false)

// Search and filter
const searchQuery = ref('')
const roleFilter = ref(null)

// Pagination
const pagination = ref({
  sortBy: 'username',
  descending: false,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
})

// Dialogs
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingUser = ref(null)
const userToDelete = ref(null)

// Form data
const userForm = ref({
  email: '',
  first_name: '',
  last_name: '',
  role: 'user',
  password: '',
  is_active: true
})

const saving = ref(false)

// Options
const roleOptions = ['admin', 'curator', 'user']

// Table columns
const columns = [
  {
    name: 'email',
    required: true,
    label: 'User',
    align: 'left',
    field: 'email',
    sortable: true
  },
  {
    name: 'role',
    label: 'Role',
    align: 'left',
    field: 'role',
    sortable: true
  },
  {
    name: 'is_active',
    label: 'Status',
    align: 'center',
    field: 'is_active',
    sortable: true
  },
  {
    name: 'last_login',
    label: 'Last Login',
    align: 'left',
    field: 'last_login',
    sortable: true
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center',
    field: 'actions',
    sortable: false
  }
]

// Mock data (replace with real API calls)
const mockUsers = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    first_name: 'Admin',
    last_name: 'User',
    role: 'admin',
    is_active: true,
    last_login: new Date().toISOString()
  },
  {
    id: 2,
    username: 'curator1',
    email: 'curator@example.com',
    first_name: 'Yoga',
    last_name: 'Curator',
    role: 'curator',
    is_active: true,
    last_login: new Date(Date.now() - 86400000).toISOString()
  }
]

// Methods
const loadUsers = async () => {
  loading.value = true
  
  // Simulate API call
  setTimeout(() => {
    users.value = mockUsers
    pagination.value.rowsNumber = mockUsers.length
    loading.value = false
  }, 1000)
}

const onRequest = () => {
  // Handle pagination, sorting, etc.
  loadUsers()
}

const searchUsers = () => {
  // Implement search
  loadUsers()
}

const filterUsers = () => {
  // Implement role filtering
  loadUsers()
}

const clearFilters = () => {
  searchQuery.value = ''
  roleFilter.value = null
  loadUsers()
}

const getRoleColor = (role) => {
  switch (role) {
    case 'admin': return 'red'
    case 'curator': return 'orange'
    case 'user': return 'blue'
    default: return 'grey'
  }
}

const editUser = (user) => {
  editingUser.value = user
  userForm.value = {
    email: user.email,
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    role: user.role,
    password: '',
    is_active: user.is_active
  }
  showCreateDialog.value = true
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingUser.value = null
  userForm.value = {
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'user',
    password: '',
    is_active: true
  }
}

const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const saveUser = async () => {
  saving.value = true

  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    $q.notify({
      type: 'positive',
      message: editingUser.value ? 'User updated successfully!' : 'User created successfully!'
    })
    
    loadUsers()
    closeDialog()
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to save user'
    })
  }

  saving.value = false
}

const toggleUserStatus = async (user) => {
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    user.is_active = !user.is_active
    
    $q.notify({
      type: 'positive',
      message: `User ${user.is_active ? 'activated' : 'deactivated'} successfully`
    })
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to update user status'
    })
  }
}

const confirmDelete = (user) => {
  userToDelete.value = user
  showDeleteDialog.value = true
}

const deleteUser = async () => {
  if (!userToDelete.value) return

  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const index = users.value.findIndex(u => u.id === userToDelete.value.id)
    if (index !== -1) {
      users.value.splice(index, 1)
    }
    
    $q.notify({
      type: 'positive',
      message: 'User deleted successfully'
    })
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete user'
    })
  }

  showDeleteDialog.value = false
  userToDelete.value = null
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Lifecycle
onMounted(() => {
  loadUsers()
})
</script>
