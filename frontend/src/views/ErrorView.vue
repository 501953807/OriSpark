<template>
  <AppLayout>
    <div class="error-page">
      <div class="error-icon">😵</div>
      <h2>页面出现了问题</h2>
      <p>{{ message }}</p>
      <button class="btn btn-primary" @click="reload">重试</button>
      <router-link to="/" class="btn btn-secondary">返回首页</router-link>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'

const message = ref('很抱歉，当前页面发生了错误。请尝试刷新页面。')

function reload() {
  window.location.reload()
}
</script>

<style scoped>
.error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  gap: 16px;
}
.error-icon { font-size: 4rem; }
.error-page h2 { margin: 0; }
.error-page p { color: var(--muted); max-width: 400px; }
</style>
