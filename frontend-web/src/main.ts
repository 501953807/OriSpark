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

app.use(pinia)
app.use(router)

// Initialize motion store after Pinia is installed
initMotionStore()

// Initialize Pinia stores
pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()

// Load global dictionary cache
const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})

app.mount('#app')
