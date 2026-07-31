// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useDictStore } from '@/stores/useDictStore'
import { initMotionStore } from '@/stores/motion'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)

initMotionStore()

pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()

const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})

app.mount('#app')
