import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(router)
// Initialize theme and sidebar from localStorage
pinia.state.value.app?.initTheme?.()
pinia.state.value.app?.initSidebar?.()
app.mount('#app')
