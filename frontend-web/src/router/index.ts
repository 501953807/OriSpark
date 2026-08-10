import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import client from '@/api/client'
import type { User } from '@/types/user'

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
        { path: 'risk-warning', name: 'risk-warning', component: () => import('@/views/RiskWarningView.vue') },
        { path: 'revenue', name: 'revenue', component: () => import('@/views/DiversityView.vue') },
        { path: 'contract-risk', name: 'contract-risk', component: () => import('@/views/ContractRiskView.vue') },
        { path: 'navigation', name: 'navigation', component: () => import('@/views/CreatorNavigationView.vue') },
        { path: 'insurance', name: 'insurance', component: () => import('@/views/InsuranceMarketView.vue') },
        { path: 'contract-market', name: 'contract-market', component: () => import('@/views/ContractMarketView.vue') },
        { path: 'capability', name: 'capability', component: () => import('@/views/CapabilityAssessmentView.vue') },
        { path: 'multimarket', name: 'multimarket', component: () => import('@/views/MultiMarketView.vue') },
        { path: 'enforcement-roi', name: 'enforcement-roi', component: () => import('@/views/EnforcementRoiView.vue') },
        { path: 'enforcement', name: 'enforcement-dashboard', component: () => import('@/views/EnforcementDashboardView.vue') },
        { path: 'private-traffic', name: 'private-traffic', component: () => import('@/views/PrivateTrafficView.vue') },
        { path: 'growth-stages', name: 'growth-stages', component: () => import('@/views/GrowthStageView.vue') },
        { path: 'ai-growth', name: 'ai-growth', component: () => import('@/views/AiGrowthView.vue') },
        { path: 'credit-improvement', name: 'credit-improvement', component: () => import('@/views/CreditImprovementView.vue') },
        { path: 'risk-center', name: 'risk-center', component: () => import('@/views/RiskWarningCenterView.vue') },
        { path: 'content-pipeline', name: 'content-pipeline', component: () => import('@/views/ContentPipelineView.vue') },
        { path: 'case-studies', name: 'case-studies', component: () => import('@/views/CaseStudyView.vue') },
        { path: 'copyright-guide', name: 'copyright-guide', component: () => import('@/views/CopyrightGuideView.vue') },
        { path: 'notary', redirect: '/app/rights' },
        { path: 'monitor', name: 'monitor', component: () => import('@/views/MonitorView.vue') },
        { path: 'ipr', name: 'ipr', component: () => import('@/views/IprView.vue') },
        { path: 'publish', name: 'publish', component: () => import('@/views/PublishView.vue') },
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
        { path: 'illustrator', name: 'illustrator', component: () => import('@/views/IllustratorView.vue') },
        { path: 'photographer', name: 'photographer', component: () => import('@/views/PhotographerView.vue') },
        { path: 'video', name: 'video', component: () => import('@/views/VideoCreatorView.vue') },
        { path: 'craftsman', name: 'craftsman', component: () => import('@/views/CraftsmanView.vue') },
        { path: 'etsy', name: 'etsy', component: () => import('@/views/EtsyView.vue') },
        { path: 'musician', name: 'musician', component: () => import('@/views/MusicianView.vue') },
        { path: 'writer', name: 'writer', component: () => import('@/views/WriterView.vue') },
        { path: 'fork-merge', name: 'fork-merge', component: () => import('@/views/ForkMergeView.vue') },
        { path: 'negotiation', name: 'negotiation', component: () => import('@/views/NegotiationView.vue') },
        { path: 'scr', name: 'scr-dash', component: () => import('@/views/SCRDashView.vue') },
        { path: 'tax', name: 'tax-settlement', component: () => import('@/views/TaxSettlementView.vue') },
        { path: 'distribution', name: 'distribution-hub', component: () => import('@/views/DistributionHubView.vue') },
        { path: 'attribution', name: 'attribution', component: () => import('@/views/AttributionView.vue') },
      ],
    },
    // 404
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// 路由守卫 — 集中 auth store 管理
router.beforeEach(async (to) => {
  // v6.0: 非创作者用户重定向到 OriSpark 交易后台
  const savedUser = localStorage.getItem('oristudio-user')
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser) as User
      const loginPlatform = user.login_platform || user.creator_type ? 'web' : 'nuxt'
      if (loginPlatform === 'nuxt' && to.path.startsWith('/app')) {
        // 非创作者访问创作者平台，重定向到 OriSpark
        window.location.href = window.location.origin.replace('5174', '3000')
        return false
      }
    } catch { /* ignore parse errors */ }
  }

  if (to.meta.requiresAuth) {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      // 本地模式: 通过后端真实 API 获取 token 和用户数据
      try {
        const resp = await client.post('/auth/local-login')
        const data = resp.data.data as { token: string; user: User }
        auth.token = data.token
        auth.user = data.user
        localStorage.setItem('oristudio-token', data.token)
        localStorage.setItem('oristudio-user', JSON.stringify(data.user))
        client.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
      } catch {
        // 后端不可用时 fallback（仅本地开发）
        const savedRole = localStorage.getItem('oristudio-participant-role')
        const fallbackUser: User = {
          id: 'local',
          username: '创作者',
          email: 'local@oristudio',
          role: '本地用户',
          participant_roles: savedRole ? [savedRole] : [],
          participant_role_names: savedRole ? [savedRole] : [],
          creator_type: 'illustrator',
        }
        auth.user = fallbackUser
        // 设置本地模式 token，使 API client 发送 Authorization header
        // mock 中间件会拦截这些请求并返回 mock 数据
        const localToken = 'local-developer-token'
        auth.token = localToken
        localStorage.setItem('oristudio-token', localToken)
        client.defaults.headers.common['Authorization'] = `Bearer ${localToken}`
      }
    }
  }
})

export default router
