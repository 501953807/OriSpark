<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const submitting = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  if (!email.value || !password.value) {
    errorMsg.value = '请输入邮箱和密码'
    return
  }
  submitting.value = true
  errorMsg.value = ''
  const success = await auth.login(email.value, password.value)
  submitting.value = false
  if (success) {
    navigateTo('/market')
  } else {
    errorMsg.value = auth.error || '登录失败，请检查账号密码'
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <NuxtLink to="/" class="logo">
          <span class="logo-icon">⚡</span>
          <span class="logo-text">OriSpark</span>
        </NuxtLink>
        <p class="login-subtitle">登录交易后台，开启作品运营</p>
      </div>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="your@email.com"
            required
            autocomplete="email"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          />
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="btn-login" :disabled="submitting">
          {{ submitting ? '登录中...' : '登录' }}
        </button>
      </form>
      <div class="login-footer">
        <p>还没有账号？<NuxtLink to="/auth/register" class="link">立即注册</NuxtLink></p>
        <p class="hint">创作者请前往 <a href="http://localhost:5174" target="_blank">OriStudio</a> 登录</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 24px;
}
.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  padding: 40px 32px;
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  margin-bottom: 12px;
}
.logo-icon {
  font-size: 28px;
}
.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}
.login-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}
.form-group input {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.15s;
  outline: none;
}
.form-group input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}
.error-msg {
  color: #ef4444;
  font-size: 13px;
  margin: 0;
}
.btn-login {
  padding: 12px;
  background: #1e293b;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-login:hover:not(:disabled) {
  background: #334155;
}
.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}
.login-footer .link {
  color: #3b82f6;
  text-decoration: none;
}
.login-footer a {
  color: #3b82f6;
  text-decoration: none;
}
.login-footer .hint {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
