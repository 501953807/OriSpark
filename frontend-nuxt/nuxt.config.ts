// nuxt.config.ts
export default {
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL || '/api',
    },
  },

  nitro: {
    serveStatic: true,
    // API 代理到后端
    routeRules: {
      '/api/**': { proxy: 'http://localhost:8001/api/**' },
    },
  },

  routeRules: {
    '/': { ssr: false },
    '/gallery': { ssr: false },
    '/contracts': { ssr: false },
    '/market': { ssr: false },
    '/opportunities': { ssr: false },
    '/works/**': { ssr: false },
    '/auth/**': { ssr: false },
  },

  css: ['assets/styles/global.css', 'assets/styles/brand-enhance.css'],

  app: {
    head: {
      title: 'OriSpark — AI Creator Trust Hub',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
        { property: 'og:title', content: 'OriSpark — AI Creator Trust Hub' },
        { property: 'og:description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: 'https://orispark.local' },
        { name: 'twitter:card', content: 'summary_large_image' },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@400;600;700&display=swap',
        },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/icon?family=Material+Icons' },
      ],
    },
  },

  future: {
    compatibilityVersion: 4,
  },

  features: {
    transitions: true,
    inlineStyles: true,
  },

  imports: {
    dirs: ['composables', 'stores'],
  },

  modules: [
    '@pinia/nuxt',
  ],

  plugins: [
    '~/plugins/ofetch-fix.ts',
  ],

  eslint: {
    config: { native: true },
  },
}
