import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 首页 (Landing)
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
    },
    // 登录/注册
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    // 新手引导
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/OnboardingView.vue'),
    },
    // 证书验证 (公开页)
    {
      path: '/verify',
      name: 'verify',
      component: () => import('@/views/VerifyView.vue'),
    },
    // 应用主体 (需要登录)
    {
      path: '/app',
      component: () => import('@/components/layout/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'works', name: 'works', component: () => import('@/views/WorksView.vue') },
        { path: 'works/:id', name: 'work-detail', component: () => import('@/views/WorkDetailView.vue') },
        { path: 'rights', name: 'rights', component: () => import('@/views/RightsView.vue') },
        { path: 'notary', redirect: '/app/rights' },
        { path: 'monitor', redirect: '/app/rights' },
        { path: 'ipr', name: 'ipr', component: () => import('@/views/IprView.vue') },
        { path: 'supply', name: 'supply', component: () => import('@/views/SupplyView.vue') },
        { path: 'supply/listings', name: 'listings', component: () => import('@/views/ListingListView.vue') },
        { path: 'supply/listings/:id', name: 'listing-detail', component: () => import('@/views/ListingDetailView.vue') },
        { path: 'supply/templates', name: 'templates', component: () => import('@/views/TemplateBrowserView.vue') },
        { path: 'publish', name: 'publish', component: () => import('@/views/PublishView.vue') },
        { path: 'business', name: 'business', component: () => import('@/views/BusinessView.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
        { path: 'integrations', name: 'integrations', component: () => import('@/views/IntegrationsView.vue') },
        { path: 'projects', name: 'projects', component: () => import('@/views/ProjectsView.vue') },
        { path: 'recycle', name: 'recycle', component: () => import('@/views/RecycleBinView.vue') },
        { path: 'settings/watermarks', name: 'watermarks', component: () => import('@/views/WatermarkPresetsView.vue') },
        { path: 'settings/templates', name: 'metadata-templates', component: () => import('@/views/MetadataTemplatesView.vue') },
        { path: 'works/:id/variants', name: 'work-variants', component: () => import('@/views/WorkVariantsView.vue') },
        { path: 'works/cull', name: 'culling', component: () => import('@/views/CullingView.vue') },
        { path: 'settings/subscriptions', name: 'subscriptions', component: () => import('@/views/SubscriptionView.vue') },
        { path: 'business/commissions', name: 'commissions', component: () => import('@/views/CommissionView.vue') },
        { path: 'business/commissions/:id', name: 'commission-detail', component: () => import('@/views/CommissionDetailView.vue') },
        { path: 'photographer', name: 'photographer', component: () => import('@/views/PhotographerView.vue') },
        { path: 'video', name: 'video', component: () => import('@/views/VideoCreatorView.vue') },
        { path: 'craftsman', name: 'craftsman', component: () => import('@/views/CraftsmanView.vue') },
        { path: 'musician', name: 'musician', component: () => import('@/views/MusicianView.vue') },
        { path: 'writer', name: 'writer', component: () => import('@/views/WriterView.vue') },
      ],
    },
    // 404
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// 路由守卫 (本地模式: 自动跳过登录)
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('oristudio-token')
    // 本地模式: 自动生成 token 跳过登录
    if (!token) {
      localStorage.setItem('oristudio-token', 'local-' + Date.now())
      localStorage.setItem('oristudio-user', JSON.stringify({ name: '创作者', role: '本地用户' }))
    }
  }
  next()
})

export default router
