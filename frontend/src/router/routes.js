const routes = [
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue')
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { 
        path: '', 
        redirect: '/cards'
      },
      { 
        path: '/cards', 
        component: () => import('pages/CardsPage.vue') 
      },
      { 
        path: '/cards/:id', 
        component: () => import('pages/CardDetailPage.vue'),
        props: true
      },
      { 
        path: '/tags', 
        component: () => import('pages/TagsPage.vue') 
      }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
