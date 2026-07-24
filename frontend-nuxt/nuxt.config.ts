// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL || 'http://localhost:8000/api',
    },
  },

  routeRules: {
    '/': { prerender: true },
    '/gallery': { prerender: true },
    '/contracts': { prerender: true },
    '/market': { prerender: true },
    '/opportunities': { prerender: true },
  },

  css: ['~/assets/styles/global.css'],

  app: {
    head: {
      title: 'OriSpark — AI Creator Trust Hub',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'OriSpark — AI时代的创作者权益保护与多边撮合信任枢纽平台' },
        { property: 'og:title', content: 'OriSpark — AI Creator Trust Hub' },
        { property: 'og:description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
        { property: 'og:type', content: 'website' },
        { name: 'twitter:card', content: 'summary_large_image' },
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

  eslint: {
    config: { native: true },
  },
})
