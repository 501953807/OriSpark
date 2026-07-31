import { resolve } from 'path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'

const env = loadEnv('', process.cwd(), '')
const backendPort = parseInt(env.BACKEND_PORT || '8001', 10)

export default defineConfig({
  plugins: [
    vue(),
    electron([
      // Main process
      {
        entry: 'src/main/index.ts',
        vite: {
          build: {
            outDir: 'dist/electron',
            emptyOutDir: true,
            rollupOptions: {
              external: ['electron', 'three'],
            },
          },
        },
      },
      // Preload script
      {
        entry: 'src/main/preload.ts',
        onstart({ reload }) {
          reload()
        },
        vite: {
          build: {
            outDir: 'dist/electron',
            emptyOutDir: true,
            rollupOptions: {
              external: ['electron'],
            },
          },
        },
      },
    ]),
    renderer(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, '../frontend-web/src'),
    },
  },
  base: './',
  build: {
    outDir: 'dist/web',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, '../frontend-web/index.html'),
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
  },
  server: {
    port: 5175,
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
})
