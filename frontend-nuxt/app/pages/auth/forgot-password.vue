<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'default' })

const auth = useAuthStore()
const email = ref('')
const submitting = ref(false)
const errorMsg = ref('')
const sent = ref(false)

async function handleSubmit() {
  if (!email.value) { errorMsg.value = '请输入邮箱'; return }
  submitting.value = true
  errorMsg.value = ''
  await auth.forgotPassword(email.value)
  submitting.value = false
  sent.value = true
}
</script>

<template>
  <div class="auth-layout">
    <div class="auth-left">
      <div class="auth-left-bg">
        <div class="auth-left-shapes">
          <div class="auth-shape auth-shape-1" />
          <div class="auth-shape auth-shape-2" />
          <div class="auth-shape auth-shape-3" />
        </div>
      </div>
      <div class="auth-left-content">
        <div class="auth-illustration">
          <svg viewBox="0 0 400 400" class="auth-svg">
            <circle cx="200" cy="200" r="160" fill="rgba(255,255,255,0.1)" />
            <circle cx="200" cy="140" r="45" fill="rgba(255,255,255,0.9)" />
            <path d="M120 300 Q200 200 280 300" stroke="rgba(255,255,255,0.9)" stroke-width="20" fill="none" stroke-linecap="round" />
          </svg>
        </div>
        <h2 class="auth-left-title">重置密码</h2>
        <p class="auth-left-desc">我们会发送重置链接到您的邮箱</p>
      </div>
    </div>

    <div class="auth-right">
      <div class="auth-right-inner">
        <NuxtLink to="/auth/login" class="auth-back">← 返回登录</NuxtLink>
        <div class="auth-header">
          <NuxtLink to="/" class="auth-logo">
            <span class="auth-logo-icon">⚡</span>
            <span class="auth-logo-text">OriSpark</span>
          </NuxtLink>
          <p class="auth-welcome">{{ sent ? '检查您的邮箱' : '忘记密码？' }}</p>
          <p class="auth-desc">{{ sent ? '我们已发送重置链接到 ' + email + '，请点击链接重置密码' : '请输入您的邮箱，我们将发送重置密码的链接' }}</p>
        </div>

        <template v-if="!sent">
          <form @submit.prevent="handleSubmit" class="auth-form">
            <div class="form-field">
              <label class="form-label">邮箱</label>
              <div class="form-input-wrapper">
                <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
                </svg>
                <input v-model="email" type="email" class="form-input" placeholder="your@email.com" required />
              </div>
            </div>
            <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>
            <button type="submit" class="btn-primary" :disabled="submitting">发送重置链接</button>
          </form>
        </template>

        <NuxtLink to="/auth/login" class="auth-link-secondary">返回登录</NuxtLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-layout { min-height: 100dvh; display: flex; }
.auth-left { flex: 1; position: relative; background: linear-gradient(135deg, #5585FF 0%, #2A52B0 50%, #4A2D99 100%); display: flex; align-items: center; justify-content: center; overflow: hidden; min-height: 100dvh; }
.auth-left-bg { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(140,87,255,0.95) 0%, rgba(106,63,204,0.95) 100%); }
.auth-left-shapes { position: absolute; inset: 0; }
.auth-shape { position: absolute; border-radius: 50%; opacity: 0.15; background: white; }
.auth-shape-1 { width: 300px; height: 300px; top: -50px; right: -50px; }
.auth-shape-2 { width: 200px; height: 200px; bottom: 50px; left: -30px; }
.auth-shape-3 { width: 150px; height: 150px; bottom: -30px; right: 100px; }
.auth-left-content { position: relative; z-index: 1; text-align: center; padding: 2rem; color: white; }
.auth-illustration { margin-bottom: 1.5rem; }
.auth-svg { width: 150px; height: 150px; }
.auth-left-title { font-size: 1.5rem; font-weight: 700; margin: 0 0 0.5rem; }
.auth-left-desc { font-size: 0.9375rem; opacity: 0.8; margin: 0; }
.auth-right { flex: 1; display: flex; align-items: center; justify-content: center; background: #FFFFFF; padding: 2rem; }
.auth-right-inner { width: 100%; max-width: 420px; }
.auth-back { display: inline-block; font-size: 0.875rem; color: #5585FF; text-decoration: none; margin-bottom: 1.5rem; }
.auth-header { margin-bottom: 2rem; }
.auth-logo { display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; margin-bottom: 1rem; }
.auth-logo-icon { font-size: 2rem; }
.auth-logo-text { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #5585FF, #2A52B0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.auth-welcome { font-size: 1.25rem; font-weight: 600; color: #1F2937; margin: 0 0 0.5rem; }
.auth-desc { font-size: 0.875rem; color: #64748B; margin: 0 0 1.5rem; }
.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }
.form-field { display: flex; flex-direction: column; gap: 0.375rem; }
.form-label { font-size: 0.8125rem; font-weight: 500; color: rgba(46, 38, 61, 0.9); }
.form-input-wrapper { position: relative; display: flex; align-items: center; border: 1.5px solid #E5E7EB; border-radius: 8px; transition: all 0.15s; background: #FFFFFF; }
.form-input-wrapper:focus-within { border-color: #5585FF; box-shadow: 0 0 0 3px rgba(85, 133, 255, 0.1); }
.form-input-icon { position: absolute; left: 12px; color: #9CA3AF; pointer-events: none; }
.form-input { flex: 1; height: 44px; padding: 0 0.75rem 0 2.75rem; border: none; outline: none; font-size: 0.9375rem; font-family: inherit; color: #1F2937; background: transparent; }
.form-input::placeholder { color: #9CA3AF; }
.form-error { color: #EF4444; font-size: 0.8125rem; margin: 0; }
.btn-primary { height: 44px; padding: 0 1.5rem; background: linear-gradient(135deg, #5585FF 0%, #3D6DD6 100%); color: white; border: none; border-radius: 8px; font-size: 0.9375rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.btn-primary:hover:not(:disabled) { background: linear-gradient(135deg, #3D6DD6 0%, #2A52B0 100%); box-shadow: 0 4px 12px rgba(85, 133, 255, 0.4); }
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }
.auth-link-secondary { display: block; text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: #5585FF; text-decoration: none; }
@media (max-width: 768px) { .auth-left { display: none; } .auth-right { flex: 1; } }
</style>
