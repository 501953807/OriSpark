import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

const backendPort = parseInt(process.env.BACKEND_PORT || '8000', 10)

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '5174', 10),
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://localhost:${backendPort}`,
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split large vendor chunks
          'vendor-echarts': ['echarts', 'vue-echarts'],
          'vendor-naive': ['naive-ui'],
          'vendor-plyr': ['plyr'],
        },
      },
    },
    // Increase chunk size warning limit for PublishView parts
    chunkSizeWarningLimit: 800,
  },
})
