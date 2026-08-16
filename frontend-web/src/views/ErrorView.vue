<template>
  <div class="error-page">
    <div class="error-icon">😵</div>
    <h2>页面出现了问题</h2>
    <p>{{ message }}</p>
    <button class="btn btn-primary" @click="reload">重试</button>
    <router-link to="/" class="btn btn-secondary">返回首页</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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
  min-height: 60vh;
  padding: 80px 20px;
  text-align: center;
  gap: 16px;
  background: var(--m-bg-subtle);
}
.error-icon { font-size: 4rem; }
.error-page h2 { margin: 0; color: var(--m-on-surface); }
.error-page p { color: var(--m-grey-500); max-width: 400px; margin: 0; }
</style>
