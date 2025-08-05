const routes = [
  // Public Frontend Routes
  {
    path: '/',
    component: () => import('layouts/PublicLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('pages/public/HomePage.vue') },
      { path: 'daily', name: 'daily-card', component: () => import('pages/public/DailyCardPage.vue') },
      { path: 'login', name: 'login', component: () => import('pages/public/LoginPage.vue') },
      { path: 'signup', name: 'signup', component: () => import('pages/public/SignupPage.vue') },
      { path: 'cards', name: 'public-cards', component: () => import('pages/public/CardsPage.vue'), meta: { requiresAuth: true } },
      { path: 'profile', name: 'profile', component: () => import('pages/public/ProfilePage.vue'), meta: { requiresAuth: true } },
      { path: 'favorites', name: 'favorites', component: () => import('pages/public/FavoritesPage.vue'), meta: { requiresAuth: true } }
    ]
  },

  // Admin/Curator Backend Routes
  {
    path: '/admin',
    component: () => import('layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresCurator: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('pages/admin/DashboardPage.vue') },
      { path: 'cards', name: 'admin-cards', component: () => import('pages/admin/CardsPage.vue') },
      { path: 'cards/new', name: 'admin-card-new', component: () => import('pages/admin/CardEditPage.vue') },
      { path: 'cards/:id', name: 'admin-card-detail', component: () => import('pages/admin/CardDetailPage.vue') },
      { path: 'cards/:id/edit', name: 'admin-card-edit', component: () => import('pages/admin/CardEditPage.vue') },
      { path: 'tags', name: 'admin-tags', component: () => import('pages/admin/TagsPage.vue') },
      { path: 'users', name: 'admin-users', component: () => import('pages/admin/UsersPage.vue'), meta: { requiresAdmin: true } }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
