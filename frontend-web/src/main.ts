// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useDictStore } from '@/stores/useDictStore'
import { wsClient } from '@/composables/useWebSocket'
import { useAuthStore } from '@/stores/useAuthStore'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
const app = createApp(App)

app.use(pinia)
app.use(router)

pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()

const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})

// 已登录时初始化 WebSocket 通知推送
const authStore = useAuthStore()
if (authStore.isLoggedIn) {
  wsClient.connect()
}

app.mount('#app')
