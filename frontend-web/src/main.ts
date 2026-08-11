// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useDictStore } from '@/stores/useDictStore'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
const app = createApp(App)

app.use(pinia)
app.use(router)

pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()

const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})

app.mount('#app')
