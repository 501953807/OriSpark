import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useDictStore } from '@/stores/useDictStore'

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(router)
// Initialize theme and sidebar from localStorage
pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()
// Load global dictionary cache
const dictStore = useDictStore()
dictStore.loadCommon().catch(() => {})
app.mount('#app')
