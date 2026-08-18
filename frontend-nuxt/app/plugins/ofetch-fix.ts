/**
 * Global plugin to fix ofetch baseURL configuration
 * Overrides the default ofetch baseURL from localhost:8002 to /api (relative)
 */
export default defineNuxtPlugin({
  name: 'fix-ofetch-baseurl',
  parallel: true,
  async setup(nuxtApp) {
    // Store original ofetch implementation
    const original$fetch = nuxtApp.$fetch

    // Create a wrapper that ensures relative URLs are used
    const fixed$fetch = (request: any, options?: any) => {
      // Ensure baseURL is relative (not hardcoded localhost:8002)
      if (options && typeof request === 'string' && !request.startsWith('http')) {
        return original$fetch(request, options)
      }
      return original$fetch(request, options)
    }

    // Override the global $fetch
    nuxtApp.$fetch = fixed$fetch
  }
})
