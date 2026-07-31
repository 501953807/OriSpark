// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useDictStore } from '@/stores/useDictStore'
import { initMotionStore, useMotionStore } from '@/stores/motion'

const pinia = createPinia()
const app = createApp(App)

// Initialize motion store (browser-safe)
initMotionStore()

app.use(pinia)
app.use(router)

// Initialize Pinia stores
pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()

// Load global dictionary cache
const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})

// Also initialize motion store directly for any component access
const motionStore = useMotionStore()
if (typeof window !== 'undefined') {
  motionStore.monitorFrameRate()
}

app.mount('#app')
