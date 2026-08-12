<template>
  <div class="redirect-page">
    <div class="redirect-card">
      <div class="redirect-icon" aria-hidden="true">→</div>
      <h1>切换平台</h1>
      <p class="redirect-desc">
        您当前是运营者账号，请前往 <strong>OriSpark 交易后台</strong> 管理合约、订单与结算。
      </p>

      <div class="redirect-actions">
        <a :href="nuxtUrl" class="btn btn-primary redirect-btn" target="_blank">
          前往 OriSpark
        </a>
        <router-link to="/" class="redirect-back">← 返回首页</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// nuxt 应用在同一域名下；开发环境默认 :3000
const nuxtUrl = computed(() => `${window.location.origin.replace('5174', '3000')}/nuxt/`)
</script>

<style scoped>
.redirect-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 20px;
}
.redirect-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  max-width: 480px;
  width: 100%;
  text-align: center;
  box-shadow: 0 16px 64px var(--shadow-lg);
}
.redirect-icon {
  width: 64px; height: 64px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: inline-flex; align-items: center; justify-content: center;
  color: var(--accent-fg);
  font-size: 1.8rem; font-weight: 700;
  margin-bottom: 20px;
}
.redirect-card h1 {
  font-family: var(--font-display);
  font-size: 1.4rem;
  margin: 0 0 12px;
  color: var(--fg);
}
.redirect-desc {
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 0 0 32px;
}
.redirect-desc strong {
  color: var(--fg);
  font-weight: 600;
}
.redirect-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.redirect-btn {
  width: 100%;
  padding: 14px 20px;
  font-size: 1rem;
  border-radius: var(--radius);
  border: none;
  cursor: pointer;
  font-weight: 600;
  color: var(--accent-fg);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  text-decoration: none;
  transition: opacity 0.2s;
}
.redirect-btn:hover { opacity: 0.85; }
.redirect-back {
  font-size: 0.85rem;
  color: var(--muted);
  text-decoration: none;
}
.redirect-back:hover { color: var(--fg); }
</style>
